import pytest

from h250mac.bindings import BindingStore
from h250mac.keys import (
    DEFAULT_KEY,
    FLAG_CONTROL,
    FLAG_OPTION,
    canonical_key_name,
    resolve_chord,
    resolve_key,
)


def test_default_is_f13():
    assert DEFAULT_KEY == "f13"
    assert resolve_key("f13") == 0x69
    assert resolve_key(" F13 ") == 0x69


def test_space_and_letter():
    assert resolve_key("space") == 0x31
    assert resolve_key("v") == 0x09
    assert resolve_key("m") == 0x2E


def test_backtick():
    assert resolve_key("`") == 0x32
    assert resolve_key("grave") == 0x32
    assert resolve_key("uptick") == 0x32
    assert canonical_key_name("uptick") == "`"


def test_unknown_key():
    with pytest.raises(ValueError, match="unknown key"):
        resolve_key("not-a-key")


def test_control_m_chord():
    chord = resolve_chord("Control + M")
    assert canonical_key_name("ctrl-m") == "control-m"
    assert chord.keycode == 0x2E
    assert chord.flags == FLAG_CONTROL
    assert chord.modifiers == (0x3B,)


def test_uptick_m_chord():
    chord = resolve_chord("uptick-m")
    assert canonical_key_name("`-m") == "uptick-m"
    assert chord.keycode == 0x2E
    assert chord.flags == 0
    assert chord.modifiers == (0x32,)


def test_teams_hold_keys():
    mac = resolve_chord("Option + Space")
    assert canonical_key_name("alt-space") == "option-space"
    assert mac.keycode == 0x31
    assert mac.flags == FLAG_OPTION
    assert mac.modifiers == (0x3A,)
    windows = resolve_chord("Ctrl + Space")
    assert windows.keycode == 0x31
    assert windows.flags == FLAG_CONTROL
    assert windows.modifiers == (0x3B,)


def test_plain_key_chord_has_no_modifier():
    chord = resolve_chord("f13")
    assert chord.keycode == 0x69
    assert chord.flags == 0
    assert chord.modifiers == ()


def test_binding_stores_chords():
    snap = BindingStore("control-m", "m").snapshot()
    assert snap.names[1] == "control-m"
    assert snap.chords[1].modifiers == (0x3B,)
    assert snap.chords[2].keycode == 0x2E
    assert snap.chords[2].modifiers == ()
    assert BindingStore("f13", "").snapshot().chords[2] is None


def test_menu_prompt_accepts_a_new_hotkey():
    from h250mac.keys import menu_key_name

    assert menu_key_name("Control + M", required=True) == "control-m"
    assert menu_key_name("uptick-m", required=True) == "uptick-m"
    assert menu_key_name("off", required=False) == ""
    assert menu_key_name("  ", required=False) == ""
    with pytest.raises(ValueError, match="Choose a key"):
        menu_key_name("off", required=True)
    with pytest.raises(ValueError, match="unknown key"):
        menu_key_name("option-m", required=True)


def test_post_chord_releases_modifier_if_letter_fails(monkeypatch):
    calls = []

    def record(keycode, down, flags=0):
        if keycode == 0x2E and down:
            raise OSError("boom")
        calls.append((keycode, down, flags))

    monkeypatch.setattr("h250mac.events.post_key", record)
    from h250mac.events import post_chord

    with pytest.raises(OSError, match="boom"):
        post_chord(resolve_chord("control-m"), True)
    assert calls == [(0x3B, True, 0), (0x3B, False, 0)]


def test_post_chord_presses_modifier_around_letter(monkeypatch):
    calls = []

    def record(keycode, down, flags=0):
        calls.append((keycode, down, flags))

    monkeypatch.setattr("h250mac.events.post_key", record)
    from h250mac.events import post_chord

    post_chord(resolve_chord("control-m"), True)
    assert calls == [(0x3B, True, 0), (0x2E, True, FLAG_CONTROL)]
    calls.clear()
    post_chord(resolve_chord("control-m"), False)
    assert calls == [(0x2E, False, FLAG_CONTROL), (0x3B, False, 0)]
