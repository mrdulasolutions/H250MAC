from h250mac.protocol import PIDS, VID, button_from_report, button_nibble


def test_identity_matches_the_windows_mapper():
    assert VID == 0x0D8C
    assert 0x0013 in PIDS
    assert 0xAAA0 in PIDS
    assert 0xAAAF in PIDS
    assert 0xAAB0 not in PIDS


def test_released_values():
    for value in (0x00, 0x01, 0x0F):
        assert button_nibble([0, 0, value]) == 0


def test_side_button_is_high_nibble_1():
    assert button_nibble([0, 0, 0x10]) == 1
    assert button_nibble([0, 0, 0x1F]) == 1


def test_second_control_is_high_nibble_2():
    assert button_nibble([0, 0, 0x20]) == 2
    assert button_nibble([0, 0, 0x2A]) == 2


def test_other_high_nibbles_are_ignored():
    assert button_nibble([0, 0, 0x30]) == 0
    assert button_nibble([0, 0, 0xF0]) == 0


def test_short_report_is_released():
    assert button_nibble([]) == 0
    assert button_nibble([0x10]) == 0
    assert button_nibble([0x10, 0x10]) == 0


def test_byte_index_can_move():
    assert button_nibble([0, 0x10, 0x00], index=1) == 1
    assert button_nibble(bytes([0, 0, 0x20])) == 2


def test_macos_handset_press_is_one_byte_earlier():
    assert button_from_report([0x00, 0x01, 0x00, 0x00]) == 0
    assert button_from_report([0x00, 0x11, 0x00, 0x00]) == 1
    assert button_from_report([0x00, 0x00, 0x11, 0x00]) == 1
    assert button_from_report([0x00, 0x00, 0x21, 0x00]) == 2
