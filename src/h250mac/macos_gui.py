"""macOS menu bar presentation (PyObjC via rumps dependency)."""

from __future__ import annotations

import shutil
from importlib import resources
from pathlib import Path

APP_BUNDLE_NAME = "H250 PTT"
_SUPPORT_FOLDER = "H250"


def configure_menu_bar_extra() -> None:
    """Menu-bar-only: hide the Dock icon and show the status item."""
    from AppKit import NSApplication, NSApplicationActivationPolicyAccessory

    NSApplication.sharedApplication().setActivationPolicy_(
        NSApplicationActivationPolicyAccessory
    )


def _support_dir() -> Path:
    try:
        from rumps import application_support

        return Path(application_support(_SUPPORT_FOLDER))
    except ImportError:  # pragma: no cover
        return Path.home() / "Library/Application Support" / _SUPPORT_FOLDER


def _copy_packaged_asset(asset_name: str, dest: Path) -> bool:
    try:
        ref = resources.files("h250mac.assets").joinpath(asset_name)
        with resources.as_file(ref) as path:
            if path.is_file():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, dest)
                return True
    except (ModuleNotFoundError, FileNotFoundError, TypeError, OSError):
        pass
    fallback = Path(__file__).resolve().parent / "assets" / asset_name
    if fallback.is_file():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(fallback, dest)
        return True
    return False


def _stable_asset_path(asset_name: str) -> str | None:
    dest = _support_dir() / asset_name
    if not _copy_packaged_asset(asset_name, dest):
        return None
    return str(dest)


def menubar_icon_path() -> str | None:
    """Stable on-disk path for the status item image (rumps keeps the path, not bytes)."""
    return _stable_asset_path("menubar.png")


def alert_icon_path() -> str | None:
    """Handset image for rumps alerts and the running app's icon image."""
    return _stable_asset_path("alert.png")


def reveal_status_item(item, icon_path: str | None) -> None:
    """Put a real title and image on the status button.

    rumps still calls the deprecated NSStatusItem setters. On current macOS
    those leave an empty button, and a new item can be parked off the visible
    menu bar until it has its own autosave name.
    """
    from AppKit import (
        NSImage,
        NSImageLeft,
        NSStatusItemBehaviorRemovalAllowed,
        NSVariableStatusItemLength,
    )

    item.setAutosaveName_("H250PTT")
    item.setBehavior_(NSStatusItemBehaviorRemovalAllowed)
    item.setLength_(NSVariableStatusItemLength)
    item.setVisible_(True)
    try:
        from Foundation import NSUserDefaults

        item._clearAutosavedPreferredPosition()
        prefs = NSUserDefaults.alloc().initWithSuiteName_("com.apple.controlcenter")
        key = item._preferredPositionDefaultsKey()
        visible_key = item._visibleDefaultsKey()
        if prefs is not None and key:
            # Same range as Wi‑Fi / Bluetooth, which sit in the right-hand cluster.
            # The default slot on a 16-inch MacBook is under the notch.
            prefs.setInteger_forKey_(360, key)
            if visible_key:
                prefs.setBool_forKey_(True, visible_key)
            prefs.synchronize()
        item._restorePreferencesFromAutosaveName()
    except Exception:
        pass

    button = item.button()
    if button is None:
        return
    button.setTitle_("H250")
    if icon_path:
        image = NSImage.alloc().initWithContentsOfFile_(icon_path)
        if image is not None:
            image.setSize_((18.0, 18.0))
            button.setImage_(image)
            button.setImagePosition_(NSImageLeft)


def apply_application_icon() -> None:
    """Use the handset artwork instead of the Python default in dialogs."""
    path = alert_icon_path()
    if not path:
        return
    try:
        from AppKit import NSApplication, NSImage
    except ImportError:  # pragma: no cover
        return
    image = NSImage.alloc().initWithContentsOfFile_(path)
    if image is not None:
        NSApplication.sharedApplication().setApplicationIconImage_(image)
