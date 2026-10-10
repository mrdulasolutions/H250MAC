import json

from h250mac.config import (
    PRIMARY_PRESETS,
    SECONDARY_PRESETS,
    AppConfig,
    config_path,
    load_config,
    save_config,
    status_label,
)
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


def test_load_canonicalizes_names_and_drops_unknown(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps({"key": "Control + M", "key2": "not-a-key", "byte": 2}),
        encoding="utf-8",
    )
    monkeypatch.setattr("h250mac.config.config_path", lambda: path)
    loaded = load_config()
    assert loaded.key == "control-m"
    assert loaded.key2 == ""

    path.write_text(json.dumps({"key": "   ", "key2": "ctrl-m"}), encoding="utf-8")
    loaded = load_config()
    assert loaded.key == DEFAULT_KEY
    assert loaded.key2 == "control-m"


def test_mac_presets_are_hold_to_talk_apps():
    assert [(item.label, item.key) for item in PRIMARY_PRESETS] == [
        ("Cursor", "control-m"),
        ("Zoom", "space"),
        ("Teams", "option-space"),
        ("Meet", "space"),
    ]
    assert [(item.label, item.key) for item in SECONDARY_PRESETS] == [
        ("Cursor", "control-m"),
        ("Zoom", "space"),
        ("Teams", "control-space"),
        ("Meet", "space"),
    ]
    assert status_label(PRIMARY_PRESETS, "control-m") == "Cursor"
    assert status_label(PRIMARY_PRESETS, "space", "Zoom") == "Zoom"
    assert status_label(SECONDARY_PRESETS, "control-space") == "Teams"
    assert status_label(SECONDARY_PRESETS, "") == "Off"


def test_saved_app_label_is_kept(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps({"key": "control-m", "key2": "space", "key_label": "Cursor", "key2_label": "Zoom"}),
        encoding="utf-8",
    )
    monkeypatch.setattr("h250mac.config.config_path", lambda: path)
    loaded = load_config()
    assert loaded.key_label == "Cursor"
    assert loaded.key2_label == "Zoom"

    path.write_text(
        json.dumps({"key": "control-m", "key_label": "Not an app"}),
        encoding="utf-8",
    )
    loaded = load_config()
    assert loaded.key == "control-m"
    assert loaded.key_label == ""


def test_config_path_under_application_support():
    path = config_path()
    assert path.name == "config.json"
    assert "h250mac" in path.parts
