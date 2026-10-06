import json

from h250mac.config import AppConfig, config_path, load_config, save_config
from h250mac.keys import DEFAULT_KEY
from h250mac.protocol import REPORT_BYTE


def test_defaults():
    cfg = AppConfig()
    assert cfg.key == DEFAULT_KEY
    assert cfg.key2 == ""
    assert cfg.byte == REPORT_BYTE


def test_save_and_load(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "h250mac.config.config_path",
        lambda: tmp_path / "config.json",
    )
    cfg = AppConfig(key="f18", key2="`", byte=2)
    save_config(cfg)
    loaded = load_config()
    assert loaded.key == "f18"
    assert loaded.key2 == "`"
    assert loaded.byte == 2
    data = json.loads((tmp_path / "config.json").read_text())
    assert data["key"] == "f18"
    assert data["key2"] == "`"


def test_load_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "h250mac.config.config_path",
        lambda: tmp_path / "missing.json",
    )
    assert load_config() == AppConfig()


def test_load_invalid_json(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr("h250mac.config.config_path", lambda: path)
    assert load_config() == AppConfig()


def test_config_path_under_application_support():
    path = config_path()
    assert path.name == "config.json"
    assert "h250mac" in path.parts
