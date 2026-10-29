import logging

import pytest

from freeflow import config
from freeflow.config import Config, tomllib


def test_default_template_matches_dataclass_defaults():
    parsed = config.from_dict(tomllib.loads(config.default_toml()))
    assert parsed == Config()


def test_load_merges_sections(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text(
        """
[hotkeys]
dictate = "alt_r"
[audio]
min_seconds = 1
[dictionary]
words = ["Kubernetes", "Anthropic"]
[snippets]
"my email" = "me@example.com"
[[styles]]
match = "linear"
style = "formal"
""",
        encoding="utf-8",
    )
    cfg = config.load(path)
    assert cfg.hotkeys.dictate == "alt_r"
    assert cfg.hotkeys.double_tap_window == 0.4
    assert cfg.audio.min_seconds == 1.0
    assert cfg.dictionary == ["Kubernetes", "Anthropic"]
    assert cfg.snippets == {"my email": "me@example.com"}
    assert cfg.styles[0].match == ["linear"]


def test_wrong_type_is_an_error():
    with pytest.raises(ValueError):
        config.from_dict({"audio": {"sounds": "yes"}})


def test_unknown_keys_warn(caplog):
    with caplog.at_level(logging.WARNING):
        config.from_dict({"audio": {"volume": 3}, "extras": {}})
    assert "volume" in caplog.text and "extras" in caplog.text


def test_write_default_refuses_to_overwrite(tmp_path):
    path = tmp_path / "sub" / "config.toml"
    config.write_default(path)
    with pytest.raises(FileExistsError):
        config.write_default(path)
    config.write_default(path, overwrite=True)


def test_app_dir_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("FREEFLOW_HOME", str(tmp_path))
    assert config.config_path() == tmp_path / "config.toml"
