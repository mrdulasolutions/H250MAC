import pytest

from h250mac.keys import DEFAULT_KEY, resolve_key


def test_default_is_f13():
    assert DEFAULT_KEY == "f13"
    assert resolve_key("f13") == 0x69
    assert resolve_key(" F13 ") == 0x69


def test_space_and_letter():
    assert resolve_key("space") == 0x31
    assert resolve_key("v") == 0x09


def test_unknown_key():
    with pytest.raises(ValueError, match="unknown key"):
        resolve_key("not-a-key")
