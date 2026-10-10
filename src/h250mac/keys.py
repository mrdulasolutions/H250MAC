"""Mac virtual key codes from HIToolbox Events.h."""

from dataclasses import dataclass

# kCGEventFlagMaskControl and kCGEventFlagMaskAlternate.
FLAG_CONTROL = 0x00040000
FLAG_OPTION = 0x00080000

# Left-side modifier keys. Pressed around the letter so listeners see them too.
_CONTROL = 0x3B
_OPTION = 0x3A
_M = 0x2E
_SPACE = 0x31
_GRAVE = 0x32

KEYS = {
    "a": 0x00, "s": 0x01, "d": 0x02, "f": 0x03, "h": 0x04, "g": 0x05,
    "z": 0x06, "x": 0x07, "c": 0x08, "v": 0x09, "b": 0x0B, "q": 0x0C,
    "w": 0x0D, "e": 0x0E, "r": 0x0F, "y": 0x10, "t": 0x11, "1": 0x12,
    "2": 0x13, "3": 0x14, "4": 0x15, "6": 0x16, "5": 0x17, "=": 0x18,
    "9": 0x19, "7": 0x1A, "-": 0x1B, "8": 0x1C, "0": 0x1D, "]": 0x1E,
    "o": 0x1F, "u": 0x20, "[": 0x21, "i": 0x22, "p": 0x23, "l": 0x25,
    "j": 0x26, "'": 0x27, "k": 0x28, ";": 0x29, "\\": 0x2A, ",": 0x2B,
    "/": 0x2C, "n": 0x2D, "m": 0x2E, ".": 0x2F, "space": 0x31,
    "return": 0x24, "tab": 0x30, "escape": 0x35, "capslock": 0x39,
    "delete": 0x33,
    "`": _GRAVE,
    "grave": _GRAVE,
    "uptick": _GRAVE,
    "left": 0x7B, "right": 0x7C, "down": 0x7D, "up": 0x7E,
    "f1": 0x7A, "f2": 0x78, "f3": 0x63, "f4": 0x76, "f5": 0x60,
    "f6": 0x61, "f7": 0x62, "f8": 0x64, "f9": 0x65, "f10": 0x6D,
    "f11": 0x67, "f12": 0x6F, "f13": 0x69, "f14": 0x6B, "f15": 0x71,
    "f16": 0x6A, "f17": 0x40, "f18": 0x4F, "f19": 0x50, "f20": 0x5A,
}

DEFAULT_KEY = "f13"

# Uptick is this app's name for the ` key. Uptick-M holds that key and M.
_CHORDS = {
    "uptick-m": (_M, 0, (_GRAVE,)),
    "control-m": (_M, FLAG_CONTROL, (_CONTROL,)),
    "option-space": (_SPACE, FLAG_OPTION, (_OPTION,)),
    "control-space": (_SPACE, FLAG_CONTROL, (_CONTROL,)),
}

_CHORD_ALIASES = {
    "ctrl-m": "control-m",
    "ctl-m": "control-m",
    "backtick-m": "uptick-m",
    "grave-m": "uptick-m",
    "`-m": "uptick-m",
    "opt-space": "option-space",
    "alt-space": "option-space",
    "ctrl-space": "control-space",
    "ctl-space": "control-space",
}

_PLAIN_ALIASES = {
    "uptick": "`",
}


@dataclass(frozen=True)
class KeyChord:
    keycode: int
    flags: int = 0
    modifiers: tuple[int, ...] = ()


def _normalize(name: str) -> str:
    return name.strip().lower().replace(" ", "").replace("_", "-").replace("+", "-")


def canonical_key_name(name: str) -> str:
    """Return the stored name for a key or chord. Empty means no key."""
    if not name or not str(name).strip():
        return ""
    key = _normalize(name)
    key = _CHORD_ALIASES.get(key, _PLAIN_ALIASES.get(key, key))
    if key in _CHORDS or key in KEYS:
        return key
    examples = "f13, f18, space, v, uptick-m, control-m"
    raise ValueError(f"unknown key {name!r}. examples: {examples}")


def menu_key_name(raw: str, *, required: bool) -> str:
    """Parse a key typed into the menu bar prompt.

    Empty text and ``off`` clear an optional key. A required key must resolve.
    """
    text = str(raw).strip()
    if not text or text.lower() == "off":
        if required:
            raise ValueError("Choose a key such as f13, uptick-m, or control-m.")
        return ""
    name = canonical_key_name(text)
    if required and not name:
        raise ValueError("Choose a key such as f13, uptick-m, or control-m.")
    return name


def resolve_key(name: str) -> int:
    """Return the Mac virtual key code for a name such as ``f13`` or ``space``."""
    key = _normalize(name)
    key = _PLAIN_ALIASES.get(key, key)
    try:
        return KEYS[key]
    except KeyError as exc:
        examples = "f13, f18, space, v"
        raise ValueError(f"unknown key {name!r}. examples: {examples}") from exc


def resolve_chord(name: str) -> KeyChord:
    """Return the key, flags, and modifier keys for a plain key or a chord."""
    key = canonical_key_name(name)
    if not key:
        raise ValueError(f"unknown key {name!r}. examples: f13, uptick-m, control-m")
    if key in _CHORDS:
        code, flags, modifiers = _CHORDS[key]
        return KeyChord(code, flags, modifiers)
    return KeyChord(KEYS[key])
