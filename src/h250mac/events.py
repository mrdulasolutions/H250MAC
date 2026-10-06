"""Post a held key through CoreGraphics. macOS only."""

from __future__ import annotations

import ctypes
from ctypes import c_bool, c_uint16, c_uint32, c_void_p

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
_cf.CFRelease.argtypes = [c_void_p]
_cf.CFRelease.restype = None
_ax.AXIsProcessTrusted.argtypes = []
_ax.AXIsProcessTrusted.restype = c_bool


def accessibility_trusted() -> bool:
    return bool(_ax.AXIsProcessTrusted())


def post_key(keycode: int, down: bool) -> None:
    source = _cg.CGEventSourceCreate(HID_SOURCE)
    event = _cg.CGEventCreateKeyboardEvent(source, keycode, down)
    if not event:
        raise OSError("CoreGraphics did not create a key event")
    try:
        _cg.CGEventPost(HID_TAP, event)
    finally:
        _cf.CFRelease(event)
        if source:
            _cf.CFRelease(source)
