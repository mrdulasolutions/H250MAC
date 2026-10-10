"""Persisted settings under ~/Library/Application Support/h250mac/."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from h250mac.keys import DEFAULT_KEY, canonical_key_name, shortcut_label
from h250mac.protocol import REPORT_BYTE

@dataclass(frozen=True)
class HotkeyPreset:
    label: str
    key: str


# Hold-to-talk keys. The side button uses the Mac list. The second control
# uses the Windows list. Labels are the app, not the key name.
PRIMARY_PRESETS = (
    HotkeyPreset("Cursor", "control-m"),
    HotkeyPreset("Zoom", "space"),
    HotkeyPreset("Teams", "option-space"),
    HotkeyPreset("Meet", "space"),
)

SECONDARY_PRESETS = (
    HotkeyPreset("Cursor", "control-m"),
    HotkeyPreset("Zoom", "space"),
    HotkeyPreset("Teams", "control-space"),
    HotkeyPreset("Meet", "space"),
)

_DISPLAY_NAMES = {
    "`": "` (uptick)",
    "uptick-m": "Uptick-M",
    "m": "M",
    "control-m": "Control-M",
    "option-space": "Option-Space",
    "control-space": "Control-Space",
}


@dataclass
class AppConfig:
    key: str = DEFAULT_KEY
    key2: str = ""
    byte: int = REPORT_BYTE
    key_label: str = ""
    key2_label: str = ""


def preset_keys(presets: tuple[HotkeyPreset, ...]) -> frozenset[str]:
    return frozenset(preset.key for preset in presets)


def matching_labels(presets: tuple[HotkeyPreset, ...], key_name: str) -> tuple[str, ...]:
    return tuple(preset.label for preset in presets if preset.key == key_name)


def display_name(name: str) -> str:
    return _DISPLAY_NAMES.get(name, name)


def status_label(
    presets: tuple[HotkeyPreset, ...],
    key_name: str,
    saved_label: str = "",
) -> str:
    """Menu text for a binding. A saved app label wins when it still matches."""
    if not key_name:
        return "Off"
    matches = matching_labels(presets, key_name)
    if saved_label and (
        saved_label in matches
        or not matches
        or saved_label == shortcut_label(key_name)
    ):
        return saved_label
    if matches:
        return ", ".join(matches)
    return shortcut_label(key_name)


def _keep_label(presets: tuple[HotkeyPreset, ...], key_name: str, label: str) -> str:
    if not isinstance(label, str) or not label:
        return ""
    matches = matching_labels(presets, key_name)
    if matches and label not in matches and label != shortcut_label(key_name):
        return ""
    return label


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
    try:
        key = canonical_key_name(key) or DEFAULT_KEY
    except ValueError:
        key = DEFAULT_KEY
    try:
        key2 = canonical_key_name(key2)
    except ValueError:
        key2 = ""
    key_label = _keep_label(PRIMARY_PRESETS, key, data.get("key_label", ""))
    key2_label = _keep_label(SECONDARY_PRESETS, key2, data.get("key2_label", ""))
    return AppConfig(
        key=key,
        key2=key2,
        byte=byte,
        key_label=key_label,
        key2_label=key2_label,
    )


def save_config(config: AppConfig) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "key": config.key,
        "key2": config.key2,
        "byte": config.byte,
        "key_label": config.key_label,
        "key2_label": config.key2_label,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
