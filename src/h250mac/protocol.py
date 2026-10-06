"""HID identity and button byte for the TEC H250-USB.

Taken from TEC's Windows mapper, H250_PTT.exe 3.1.0, which ships on the
handset CD. That program finds the C-Media HID interface, reads one input
report, and calls SendInput. Speaker and microphone are ordinary USB audio
and do not pass through this module.
"""

VID = 0x0D8C
PIDS = (0x0013,) + tuple(range(0xAAA0, 0xAAB0))

# H250_PTT reads this offset of the HID input report.
REPORT_BYTE = 2


def button_nibble(report: list[int] | bytes, index: int = REPORT_BYTE) -> int:
    """Return 1 or 2 while that control is held, otherwise 0.

    Values 0x00 through 0x0F are released. Above that, the high nibble
    selects the control: 1 is the side push-to-talk button, 2 is the
    second side control. Any other high nibble is ignored.
    """
    if index < 0 or index >= len(report):
        return 0
    value = report[index]
    if value <= 0x0F:
        return 0
    high = (value & 0xF0) >> 4
    if high in (1, 2):
        return high
    return 0
