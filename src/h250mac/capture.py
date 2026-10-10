"""Record a Mac shortcut from the keys the user presses."""

from __future__ import annotations

import objc
from AppKit import (
    NSApp,
    NSBackingStoreBuffered,
    NSButton,
    NSEvent,
    NSFont,
    NSMakeRect,
    NSModalPanelWindowLevel,
    NSTextAlignmentCenter,
    NSTextField,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskTitled,
)
from Foundation import NSObject

from h250mac.keys import chord_from_keycode, shortcut_label

_KEY_DOWN = 1 << 10
_FLAGS_CHANGED = 1 << 12
_ESCAPE = 0x35
_DELETE = 0x33


class _CaptureDelegate(NSObject):
    def init(self):
        self = objc.super(_CaptureDelegate, self).init()
        if self is None:
            return None
        self.result = None
        self.captured = ""
        self.pending = ""
        self.label = None
        self._done = False
        return self

    def _show(self) -> None:
        if self.label is None:
            return
        if self.captured:
            self.label.setStringValue_(shortcut_label(self.captured))
        elif self.pending:
            self.label.setStringValue_(shortcut_label(self.pending))
        else:
            self.label.setStringValue_("Press a shortcut")

    def handleEvent_(self, event) -> None:
        key_code = int(event.keyCode())
        flags = int(event.modifierFlags())
        key_down = int(event.type()) == 10  # NSEventTypeKeyDown
        if key_down and key_code == _ESCAPE:
            self.cancelPressed_(None)
            return
        modifier_bits = flags & 0xFFFF0000 & ~0x00010000
        if key_down and key_code == _DELETE and not modifier_bits:
            self.captured = ""
            self.pending = ""
            self._show()
            return
        try:
            name = chord_from_keycode(key_code, flags)
        except ValueError:
            if self.label is not None:
                self.label.setStringValue_("Unsupported key")
            return
        if key_down:
            self.captured = name
        else:
            self.pending = name
        self._show()

    def setPressed_(self, _sender) -> None:
        choice = self.captured or self.pending
        if not choice:
            self.label.setStringValue_("Press a shortcut")
            return
        self.result = choice
        self._finish()

    def offPressed_(self, _sender) -> None:
        self.result = ""
        self._finish()

    def cancelPressed_(self, _sender) -> None:
        self.result = None
        self._finish()

    def windowWillClose_(self, _notification) -> None:
        self._finish()

    def _finish(self) -> None:
        if self._done:
            return
        self._done = True
        NSApp.stopModal()


def _label(text: str, frame, size: float) -> NSTextField:
    field = NSTextField.alloc().initWithFrame_(frame)
    field.setStringValue_(text)
    field.setBezeled_(False)
    field.setDrawsBackground_(False)
    field.setEditable_(False)
    field.setSelectable_(False)
    field.setRefusesFirstResponder_(True)
    field.setAlignment_(NSTextAlignmentCenter)
    field.setFont_(NSFont.systemFontOfSize_(size))
    return field


def _button(title: str, frame, target, action: str) -> NSButton:
    button = NSButton.alloc().initWithFrame_(frame)
    button.setTitle_(title)
    button.setBezelStyle_(1)
    button.setTarget_(target)
    button.setAction_(action)
    return button


def capture_shortcut(title: str, *, allow_off: bool = False) -> str | None:
    """Show a panel and return the shortcut the user presses.

    ``None`` means Cancel. An empty string means Off, and only when
    ``allow_off`` is set.
    """
    delegate = _CaptureDelegate.alloc().init()
    window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        NSMakeRect(0, 0, 420, 188),
        NSWindowStyleMaskTitled | NSWindowStyleMaskClosable,
        NSBackingStoreBuffered,
        False,
    )
    window.setTitle_(title)
    window.setLevel_(NSModalPanelWindowLevel)
    window.setDelegate_(delegate)
    content = window.contentView()
    hint = _label(
        "Press the keys to hold.  ⌃ Control   ⌥ Option   ⇧ Shift   ⌘ Command",
        NSMakeRect(16, 118, 388, 40),
        13,
    )
    shown = _label("Press a shortcut", NSMakeRect(16, 68, 388, 46), 32)
    delegate.label = shown
    content.addSubview_(hint)
    content.addSubview_(shown)
    content.addSubview_(_button("Set", NSMakeRect(228, 16, 80, 32), delegate, "setPressed:"))
    content.addSubview_(_button("Cancel", NSMakeRect(316, 16, 88, 32), delegate, "cancelPressed:"))
    if allow_off:
        content.addSubview_(_button("Off", NSMakeRect(16, 16, 80, 32), delegate, "offPressed:"))

    def handler(event):
        delegate.handleEvent_(event)
        return None

    monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
        _KEY_DOWN | _FLAGS_CHANGED,
        handler,
    )
    NSApp.activateIgnoringOtherApps_(True)
    window.center()
    window.makeKeyAndOrderFront_(None)
    try:
        NSApp.runModalForWindow_(window)
    finally:
        NSEvent.removeMonitor_(monitor)
        window.orderOut_(None)
    return delegate.result
