"""Mac virtual key codes from HIToolbox Events.h."""

from dataclasses import dataclass

# kCGEventFlagMask* values. These match NSEvent modifier flags.
FLAG_SHIFT = 0x00020000
FLAG_CONTROL = 0x00040000
FLAG_OPTION = 0x00080000
FLAG_COMMAND = 0x00100000

# Left-side modifier keys. Pressed around the letter so listeners see them too.
_SHIFT = 0x38
_CONTROL = 0x3B
_OPTION = 0x3A
_COMMAND = 0x37
_M = 0x2E
_SPACE = 0x31
_GRAVE = 0x32

# Apple's shortcut order: Control, Option, Shift, Command.
_MODIFIER_ORDER = ("control", "option", "shift", "command")
_MODIFIER_FLAGS = {
    "control": FLAG_CONTROL,
    "option": FLAG_OPTION,
    "shift": FLAG_SHIFT,
    "command": FLAG_COMMAND,
}
_MODIFIER_CODES = {
    0x3B: "control",
    0x3E: "control",
    0x3A: "option",
    0x3D: "option",
    0x38: "shift",
    0x3C: "shift",
    0x37: "command",
    0x36: "command",
}
_SYMBOL_MODIFIERS = {
    "⌃": "control",
    "⌥": "option",
    "⇧": "shift",
    "⌘": "command",
}
_MODIFIER_SYMBOLS = {name: symbol for symbol, name in _SYMBOL_MODIFIERS.items()}
_MODIFIER_ALIASES = {
    "ctrl": "control",
    "ctl": "control",
    "opt": "option",
    "alt": "option",
    "cmd": "command",
}

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
    "shift": _SHIFT, "control": _CONTROL, "option": _OPTION, "command": _COMMAND,
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


def _decode_symbols(text: str) -> str | None:
    """Turn ``⌃M`` or ``⌘⇧K`` into a stored chord name."""
    raw = str(text).strip()
    if not any(symbol in raw for symbol in _SYMBOL_MODIFIERS):
        return None
    modifiers: list[str] = []
    rest: list[str] = []
    for char in raw:
        if char in _SYMBOL_MODIFIERS:
            modifiers.append(_SYMBOL_MODIFIERS[char])
        elif char not in " +_-":
            rest.append(char)
    key = "".join(rest).strip().lower()
    if key in ("spacebar",):
        key = "space"
    ordered = [name for name in _MODIFIER_ORDER if name in modifiers]
    if not key:
        return "-".join(ordered) if ordered else None
    return "-".join([*ordered, key])


def _alias_modifier(name: str) -> str:
    return _MODIFIER_ALIASES.get(name, name)


def _compose_chord(key: str) -> str | None:
    parts = [_alias_modifier(part) for part in key.split("-") if part]
    if len(parts) < 2:
        return None
    if all(part in _MODIFIER_FLAGS for part in parts):
        ordered = [name for name in _MODIFIER_ORDER if name in parts]
        if len(ordered) != len(set(parts)):
            return None
        return "-".join(ordered)
    *modifiers, base = parts
    if base not in KEYS or base in _MODIFIER_FLAGS:
        return None
    if any(modifier not in _MODIFIER_FLAGS for modifier in modifiers):
        return None
    ordered = [name for name in _MODIFIER_ORDER if name in modifiers]
    if len(ordered) != len(set(modifiers)):
        return None
    return "-".join([*ordered, base])


def canonical_key_name(name: str) -> str:
    """Return the stored name for a key or chord. Empty means no key."""
    if not name or not str(name).strip():
        return ""
    decoded = _decode_symbols(name)
    if decoded is not None:
        name = decoded
    key = _normalize(name)
    key = _CHORD_ALIASES.get(key, _PLAIN_ALIASES.get(key, key))
    if key in _CHORDS or key in KEYS:
        return key
    composed = _compose_chord(key)
    if composed:
        return composed
    examples = "f13, ⌃M, ⌘K, uptick-m, control-m"
    raise ValueError(f"unknown key {name!r}. examples: {examples}")


def _binding_parts(name: str) -> tuple[tuple[str, ...], str]:
    key = canonical_key_name(name)
    if key == "uptick-m":
        return (("uptick",), "m")
    if key in _MODIFIER_FLAGS:
        return ((key,), "")
    parts = key.split("-")
    if len(parts) > 1 and all(part in _MODIFIER_FLAGS for part in parts):
        return (tuple(parts), "")
    if (
        len(parts) > 1
        and all(part in _MODIFIER_FLAGS for part in parts[:-1])
        and parts[-1] in KEYS
    ):
        return (tuple(parts[:-1]), parts[-1])
    return ((), key)


def _key_title(name: str) -> str:
    titles = {
        "space": "Space",
        "return": "Return",
        "tab": "Tab",
        "escape": "Esc",
        "delete": "Delete",
        "capslock": "Caps Lock",
        "left": "←",
        "right": "→",
        "up": "↑",
        "down": "↓",
        "`": "`",
    }
    if name in titles:
        return titles[name]
    if len(name) == 1:
        return name.upper()
    if name.startswith("f") and name[1:].isdigit():
        return name.upper()
    return name


def shortcut_label(name: str) -> str:
    """Mac menu label, such as ``⌃M`` or ``⇧⌘K``."""
    modifiers, key = _binding_parts(name)
    symbols = "".join(_MODIFIER_SYMBOLS.get(modifier, "`" if modifier == "uptick" else "") for modifier in modifiers)
    if not key:
        return symbols
    return symbols + _key_title(key)


def key_name_for_code(key_code: int) -> str | None:
    for name, code in KEYS.items():
        if code == key_code and name not in ("grave", "uptick", "shift", "control", "option", "command"):
            return name
    return None


def chord_from_keycode(key_code: int, flags: int) -> str:
    """Return the stored name for a pressed Mac key and its modifier flags."""
    flags &= 0xFFFF0000
    flags &= ~0x00010000  # Caps Lock is not part of the shortcut.
    held = [name for name in _MODIFIER_ORDER if flags & _MODIFIER_FLAGS[name]]
    if key_code in _MODIFIER_CODES:
        return "-".join(held)
    key = key_name_for_code(key_code)
    if key is None:
        raise ValueError(f"unsupported key code {key_code:#x}")
    return canonical_key_name("-".join([*held, key]))


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
    modifiers, base = _binding_parts(key)
    flag_mods = tuple(modifier for modifier in modifiers if modifier in _MODIFIER_FLAGS)
    flags = 0
    codes: list[int] = []
    for modifier in flag_mods:
        flags |= _MODIFIER_FLAGS[modifier]
        codes.append(KEYS[modifier])
    if not base:
        if len(codes) == 1:
            return KeyChord(codes[0], flags, ())
        *earlier, last = codes
        return KeyChord(last, flags, tuple(earlier))
    return KeyChord(KEYS[base], flags, tuple(codes))
