"""Persisted settings under ~/Library/Application Support/h250mac/."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from h250mac.keys import DEFAULT_KEY
from h250mac.protocol import REPORT_BYTE

MENU_PRESETS = ("f13", "f14", "f15", "f16", "f18", "`", "space", "v")


@dataclass
class AppConfig:
    key: str = DEFAULT_KEY
    key2: str = ""
    byte: int = REPORT_BYTE


def config_path() -> Path:
    return Path.home() / "Library/Application Support/h250mac/config.json"


def load_config() -> AppConfig:
    path = config_path()
    if not path.is_file():
        return AppConfig()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return AppConfig()
    if not isinstance(data, dict):
        return AppConfig()
    key = data.get("key", DEFAULT_KEY)
    key2 = data.get("key2", "")
    try:
        byte = int(data.get("byte", REPORT_BYTE))
    except (TypeError, ValueError):
        byte = REPORT_BYTE
    if not isinstance(key, str):
        key = DEFAULT_KEY
    if not isinstance(key2, str):
        key2 = ""
    return AppConfig(key=key.strip().lower(), key2=key2.strip().lower(), byte=byte)


def save_config(config: AppConfig) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"key": config.key, "key2": config.key2, "byte": config.byte}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
