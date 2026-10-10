"""Post a held key through CoreGraphics. macOS only."""

from __future__ import annotations

import ctypes
from ctypes import c_bool, c_uint16, c_uint32, c_uint64, c_void_p

from h250mac.keys import KeyChord

# kCGHIDEventTap. The focused app sees the key the same way as a real one.
HID_TAP = 0
# kCGEventSourceStateHIDSystemState
HID_SOURCE = 1

_cg = ctypes.cdll.LoadLibrary(
    "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
)
_cf = ctypes.cdll.LoadLibrary(
    "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
)
_ax = ctypes.cdll.LoadLibrary(
    "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices"
)

_cg.CGEventSourceCreate.argtypes = [c_uint32]
_cg.CGEventSourceCreate.restype = c_void_p
_cg.CGEventCreateKeyboardEvent.argtypes = [c_void_p, c_uint16, c_bool]
_cg.CGEventCreateKeyboardEvent.restype = c_void_p
_cg.CGEventPost.argtypes = [c_uint32, c_void_p]
_cg.CGEventPost.restype = None
_cg.CGEventSetFlags.argtypes = [c_void_p, c_uint64]
_cg.CGEventSetFlags.restype = None
_cf.CFRelease.argtypes = [c_void_p]
_cf.CFRelease.restype = None
_ax.AXIsProcessTrusted.argtypes = []
_ax.AXIsProcessTrusted.restype = c_bool


def accessibility_trusted() -> bool:
    return bool(_ax.AXIsProcessTrusted())


def request_accessibility_prompt() -> bool:
    """Ask macOS to show the Accessibility permission dialog when possible."""
    try:
        from Foundation import NSDictionary, NSNumber
        from ApplicationServices import AXIsProcessTrustedWithOptions
    except ImportError:
        return accessibility_trusted()

    options = NSDictionary.dictionaryWithObject_forKey_(
        NSNumber.numberWithBool_(True),
        "AXTrustedCheckOptionPrompt",
    )
    return bool(AXIsProcessTrustedWithOptions(options))


def post_key(keycode: int, down: bool, flags: int = 0) -> None:
    source = _cg.CGEventSourceCreate(HID_SOURCE)
    event = _cg.CGEventCreateKeyboardEvent(source, keycode, down)
    if not event:
        raise OSError("CoreGraphics did not create a key event")
    try:
        if flags:
            _cg.CGEventSetFlags(event, flags)
        _cg.CGEventPost(HID_TAP, event)
    finally:
        _cf.CFRelease(event)
        if source:
            _cf.CFRelease(source)


def post_chord(chord: KeyChord, down: bool) -> None:
    """Hold or release a key, including modifier keys around a chord."""
    if not chord.modifiers and not chord.flags:
        post_key(chord.keycode, down)
        return
    if down:
        pressed: list[int] = []
        try:
            for modifier in chord.modifiers:
                post_key(modifier, True)
                pressed.append(modifier)
            post_key(chord.keycode, True, chord.flags)
        except Exception:
            for modifier in reversed(pressed):
                post_key(modifier, False)
            raise
        return
    post_key(chord.keycode, False, chord.flags)
    for modifier in reversed(chord.modifiers):
        post_key(modifier, False)
