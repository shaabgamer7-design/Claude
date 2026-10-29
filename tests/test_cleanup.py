from types import SimpleNamespace

import pytest

from freeflow import cleanup
from freeflow.cleanup import (
    ClaudeBackend,
    CleanupError,
    Polisher,
    Snippets,
    apply_replacements,
    rule_clean,
)
from freeflow.config import CleanupConfig, Config, StyleRule
from freeflow.context import AppContext, pick_style


class FakeBackend:
    name = "fake"

    def __init__(self, reply="", error=None):
        self.reply, self.error, self.calls = reply, error, []

    def complete(self, system, user, effort):
        self.calls.append((system, user, effort))
        if self.error:
            raise self.error
        return self.reply


def test_rule_clean_removes_fillers_and_repeats():
    assert rule_clean("um so I I think uh we should go") == "So I think we should go"
    assert rule_clean("Hmm, okay. Umm let's do it.") == "Okay. Let's do it."


def test_rule_clean_spoken_line_breaks():
    assert rule_clean("Hello. New line. how are you? new paragraph bye") == (
        "Hello.\nHow are you?\n\nBye"
    )


def test_rule_clean_keeps_words_containing_fillers():
    assert rule_clean("The umbrella was huge") == "The umbrella was huge"


def test_snippets_exact_and_tokens():
    s = Snippets({"my email": "me@example.com", "calendar link": "https://cal.com/me"})
    assert s.exact("My email.") == "me@example.com"
    assert s.exact("my email is broken") is None
    assert s.expand("Send it to [[S1]] or book at [[ s2 ]].") == (
        "Send it to me@example.com or book at https://cal.com/me."
    )
    assert s.expand("keep [[S9]]") == "keep [[S9]]"


def test_replacements_are_case_insensitive_whole_words():
    reps = {"chat gpt": "ChatGPT", "k8s": "Kubernetes"}
    assert apply_replacements("I asked Chat GPT about k8s.", reps) == (
        "I asked ChatGPT about Kubernetes."
    )
    assert apply_replacements("k8sfoo", reps) == "k8sfoo"


def test_dictation_uses_backend_and_style():
    backend = FakeBackend("Let's meet Wednesday.")
    cfg = Config(dictionary=["Anthropic"], snippets={"my email": "me@example.com"})
    result = Polisher(cfg, backend).dictation(
        "um let's meet tuesday no wait wednesday", AppContext(app="Slack")
    )
    assert result.text == "Let's meet Wednesday."
    assert result.used_llm and result.style == "casual"
    system, user, effort = backend.calls[0]
    assert "- Anthropic" in system
    assert '[[S1]]: "my email"' in system
    assert "me@example.com" not in system  # expansions stay local
    assert "<transcript>\num let's meet tuesday no wait wednesday\n</transcript>" in user
    assert "chat message" in user
    assert effort == "low"


def test_dictation_expands_snippet_tokens_and_replacements():
    backend = FakeBackend("Email [[S1]] about Chat GPT.")
    cfg = Config(snippets={"my email": "me@example.com"}, replacements={"chat gpt": "ChatGPT"})
    result = Polisher(cfg, backend).dictation("email my email about chat gpt", AppContext())
    assert result.text == "Email me@example.com about ChatGPT."


def test_exact_snippet_skips_backend():
    backend = FakeBackend("should not be used")
    cfg = Config(snippets={"my address": "1 Main St"})
    assert Polisher(cfg, backend).dictation("My address.", AppContext()).text == "1 Main St"
    assert backend.calls == []


def test_backend_failure_falls_back_to_rules():
    backend = FakeBackend(error=CleanupError("offline"))
    result = Polisher(Config(), backend).dictation("um hello there", AppContext())
    assert result.text == "Hello there"
    assert not result.used_llm and result.note == "offline"


def test_answer_instead_of_cleanup_is_discarded():
    backend = FakeBackend("Paris is the capital of France. " * 10)
    result = Polisher(Config(), backend).dictation("what is the capital of france", AppContext())
    assert result.text == "What is the capital of france"
    assert result.note == "discarded long output"


def test_wrapper_tags_and_quotes_are_stripped():
    backend = FakeBackend('<text>\n"Hello there."\n</text>')
    assert Polisher(Config(), backend).dictation("hello there", AppContext()).text == "Hello there."


def test_translate_to_changes_language_rule():
    cfg = Config(cleanup=CleanupConfig(translate_to="English"))
    backend = FakeBackend("Hello")
    Polisher(cfg, backend).dictation("hola", AppContext())
    assert "Write the final text in English" in backend.calls[0][0]


def test_command_mode_with_selection():
    backend = FakeBackend("Dear team, thank you.")
    result = Polisher(Config(), backend).command("make this formal", "thx team", AppContext())
    assert result.text == "Dear team, thank you."
    system, user, effort = backend.calls[0]
    assert system == cleanup.COMMAND_SYSTEM
    assert "<selected_text>\nthx team\n</selected_text>" in user
    assert effort == "medium"


def test_command_mode_requires_backend():
    with pytest.raises(CleanupError):
        Polisher(Config(), None).command("write a haiku", "", AppContext())


def test_rules_only_mode():
    result = Polisher(Config(), None).dictation("uh testing testing one two", AppContext())
    assert result.text == "Testing one two"


def test_pick_style_word_boundaries_and_user_rules():
    assert pick_style(AppContext(app="Linear"), []) == "formal"
    assert pick_style(AppContext(app="1Password"), []) == "default"
    assert pick_style(AppContext(app="Google Chrome", title="Inbox - Gmail"), []) == "email"
    assert pick_style(AppContext(app="Code.exe"), []) == "code"
    rules = [StyleRule(["chrome"], "casual")]
    assert pick_style(AppContext(app="Google Chrome", title="Inbox - Gmail"), rules) == "casual"


class _FakeMessages:
    def __init__(self, response):
        self.response, self.kwargs = response, None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return self.response


def _claude(model="", response=None):
    backend = ClaudeBackend(CleanupConfig(model=model))
    messages = _FakeMessages(response)
    backend.client = SimpleNamespace(beta=SimpleNamespace(messages=messages))
    return backend, messages


def _response(text="Hi.", stop_reason="end_turn"):
    return SimpleNamespace(
        stop_reason=stop_reason,
        content=[SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text=text)],
    )


def test_claude_request_shape():
    backend, messages = _claude(response=_response("Hello."))
    assert backend.complete("SYS", "USER", "low") == "Hello."
    kw = messages.kwargs
    assert kw["model"] == "claude-opus-5-5"
    assert kw["output_config"] == {"effort": "low"}
    assert kw["fallbacks"] == "default"
    assert kw["betas"] == ["server-side-fallback-2026-07-01"]
    assert kw["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert "temperature" not in kw and "thinking" not in kw


def test_claude_haiku_skips_fallbacks():
    backend, messages = _claude(model="claude-haiku-5-5", response=_response())
    backend.complete("SYS", "USER", "low")
    assert "fallbacks" not in messages.kwargs


def test_claude_refusal_raises():
    backend, _ = _claude(response=_response(stop_reason="refusal"))
    with pytest.raises(CleanupError):
        backend.complete("SYS", "USER", "low")
