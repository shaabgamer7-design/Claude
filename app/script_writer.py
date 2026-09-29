"""Scripts written in the avatar's own voice.

Two free ways:
  * A local LLM through Ollama (https://ollama.com), fully offline. A 3B model
    such as qwen2.5:3b runs fine on a 4-core CPU with 16 GB RAM.
  * "Copy prompt": a ready-made prompt to paste into Claude.
"""
import json
import urllib.error
import urllib.request

from .config import load_settings

WORDS_PER_SECOND = 2.4


def target_words(seconds):
    return max(8, int(seconds * WORDS_PER_SECOND))


def build_prompt(avatar, topic, seconds, hook_style="question"):
    words = target_words(seconds)
    persona = [
        f"Name: {avatar.get('name')}",
        f"Tagline: {avatar.get('tagline')}" if avatar.get("tagline") else "",
        f"Niche: {avatar.get('niche')}" if avatar.get("niche") else "",
        f"Tone: {avatar.get('tone')}" if avatar.get("tone") else "",
        f"Personality and behaviour: {avatar.get('personality')}" if avatar.get("personality") else "",
        f"Audience: {avatar.get('audience')}" if avatar.get("audience") else "",
        f"Signature phrases (use at most one, only if natural): {avatar.get('catchphrases')}"
        if avatar.get("catchphrases") else "",
        f"Call to action: {avatar.get('cta')}" if avatar.get("cta") else "",
    ]
    persona = "\n".join(p for p in persona if p)
    language = avatar.get("language") or "English"
    return f"""You are the scriptwriter for a talking-head short video (Reels / TikTok / Shorts).
Write what this creator says to camera, in their voice.

CREATOR PERSONA
{persona}

TOPIC: {topic}

RULES
- Language: {language}. Write it in the normal script for that language.
- About {words} words in total (the video is {int(seconds)} seconds long). Never more than {words + 5}.
- Line 1 is a scroll-stopping hook ({hook_style} style) in under 8 words.
- Short, spoken sentences. Contractions. No hashtags, no emojis, no stage directions,
  no quotation marks, no headings.
- End with the call to action if one is given, otherwise a punchy closing line.
- Output ONLY the words to be spoken, nothing else."""


def _clean(text):
    text = text.strip().strip('"').strip()
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln and not ln.lower().startswith(("here's", "here is", "script:"))]
    return " ".join(lines)


def ollama_status():
    s = load_settings()
    try:
        with urllib.request.urlopen(s["ollama_url"].rstrip("/") + "/api/tags", timeout=2) as r:
            models = [m["name"] for m in json.load(r).get("models", [])]
        return {"running": True, "models": models, "model": s["ollama_model"],
                "model_installed": any(m.split(":")[0] == s["ollama_model"].split(":")[0]
                                       for m in models)}
    except Exception:
        return {"running": False, "models": [], "model": s["ollama_model"],
                "model_installed": False}


def write_with_ollama(avatar, topic, seconds, hook_style="question"):
    s = load_settings()
    body = json.dumps({
        "model": s["ollama_model"],
        "prompt": build_prompt(avatar, topic, seconds, hook_style),
        "stream": False,
        "options": {"temperature": 0.85, "num_predict": 300},
    }).encode()
    req = urllib.request.Request(s["ollama_url"].rstrip("/") + "/api/generate", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return _clean(json.load(r).get("response", ""))
    except urllib.error.URLError as exc:
        raise RuntimeError("Local AI (Ollama) is not running. Install it from ollama.com, then "
                           f"run: ollama pull {s['ollama_model']}") from exc
