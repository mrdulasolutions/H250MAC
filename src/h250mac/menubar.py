"""Menu bar app: run the PTT listener and switch hotkeys from the status item."""

from __future__ import annotations

import subprocess
import sys
import threading

from h250mac.bindings import BindingStore
from h250mac.config import (
    PRIMARY_PRESETS,
    SECONDARY_PRESETS,
    HotkeyPreset,
    load_config,
    matching_labels,
    preset_keys,
    save_config,
    status_label,
)
from h250mac.events import accessibility_trusted, request_accessibility_prompt
from h250mac.keys import shortcut_label
from h250mac.listener import matching_devices, run_listener
from h250mac.macos_gui import (
    APP_BUNDLE_NAME,
    alert_icon_path,
    apply_application_icon,
    configure_menu_bar_extra,
    menubar_icon_path,
    reveal_status_item,
)

try:
    import rumps
except ImportError as exc:  # pragma: no cover - optional menubar extra
    raise SystemExit(
        "rumps is not installed. Install with: python -m pip install -e '.[menubar]'"
    ) from exc

ACCESSIBILITY_URL = (
    "x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension"
    "?Privacy_Accessibility"
)
LEGACY_ACCESSIBILITY_URL = (
    "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
)


def quiet_listener_log(msg: str) -> None:
    # No console in the menu bar app. Silence here is normal and does not
    # mean Accessibility was refused. The menu item shows that state.
    if msg.startswith("report["):
        return


class H250MenubarApp(rumps.App):
    def __init__(self) -> None:
        icon = menubar_icon_path()
        super().__init__(
            APP_BUNDLE_NAME,
            title="H250",
            icon=icon,
            template=False if icon else None,
            quit_button=None,
        )
        self.cfg = load_config()
        self.bindings = BindingStore(self.cfg.key, self.cfg.key2)
        self._stop = threading.Event()
        self._primary_items: list[rumps.MenuItem] = []
        self._secondary_items: list[rumps.MenuItem] = []
        self._primary_extra: rumps.MenuItem | None = None
        self._secondary_extra: rumps.MenuItem | None = None
        self._primary_status: rumps.MenuItem | None = None
        self._secondary_status: rumps.MenuItem | None = None
        self._build_menu()
        self._refresh_checks()
        self._update_device_line()
        self._update_accessibility_line()
        self._thread = threading.Thread(
            target=run_listener,
            kwargs={
                "bindings": self.bindings,
                "report_byte": self.cfg.byte,
                "dump": False,
                "log_fn": quiet_listener_log,
                "stop_event": self._stop,
            },
            daemon=True,
        )
        self._thread.start()

    def _build_menu(self) -> None:
        self._device_item = rumps.MenuItem("Handset: checking…")
        self._ax_item = rumps.MenuItem(
            "Accessibility: checking…",
            callback=self.enable_accessibility,
        )
        self._primary_status = rumps.MenuItem("Mac: …")
        self._secondary_status = rumps.MenuItem("Windows: …")
        self._primary_extra = self._extra_item(self._on_primary)
        self._secondary_extra = self._extra_item(self._on_secondary)
        primary_children = [
            self._primary_extra,
            *[self._make_primary_item(preset) for preset in PRIMARY_PRESETS],
        ]
        secondary_children = [
            self._secondary_extra,
            self._make_secondary_item(HotkeyPreset("Off", "")),
            *[self._make_secondary_item(preset) for preset in SECONDARY_PRESETS],
        ]
        self.menu = [
            self._device_item,
            self._ax_item,
            None,
            self._primary_status,
            rumps.MenuItem("Set Mac hotkey…", callback=self._prompt_primary),
            self._secondary_status,
            rumps.MenuItem("Set Windows hotkey…", callback=self._prompt_secondary),
            None,
            ("Mac", primary_children),
            ("Windows", secondary_children),
            None,
            rumps.MenuItem("Open Accessibility Settings…", callback=self.open_accessibility),
            rumps.MenuItem("Quit", callback=self.quit_app),
        ]
        self._show_extra(1, self.cfg.key, self.cfg.key_label)
        self._show_extra(2, self.cfg.key2, self.cfg.key2_label)

    def _extra_item(self, callback) -> rumps.MenuItem:
        item = rumps.MenuItem("Custom", callback=callback)
        item._h250_key = ""  # type: ignore[attr-defined]
        item.hidden = True
        return item

    def _make_primary_item(self, preset: HotkeyPreset) -> rumps.MenuItem:
        item = rumps.MenuItem(preset.label, callback=self._on_primary)
        item._h250_key = preset.key  # type: ignore[attr-defined]
        item._h250_label = preset.label  # type: ignore[attr-defined]
        self._primary_items.append(item)
        return item

    def _make_secondary_item(self, preset: HotkeyPreset) -> rumps.MenuItem:
        item = rumps.MenuItem(preset.label, callback=self._on_secondary)
        item._h250_key = preset.key  # type: ignore[attr-defined]
        item._h250_label = preset.label  # type: ignore[attr-defined]
        self._secondary_items.append(item)
        return item

    def _on_primary(self, sender: rumps.MenuItem) -> None:
        self._select_key(
            1,
            getattr(sender, "_h250_key", ""),
            getattr(sender, "_h250_label", ""),
        )

    def _on_secondary(self, sender: rumps.MenuItem) -> None:
        self._select_key(
            2,
            getattr(sender, "_h250_key", ""),
            getattr(sender, "_h250_label", ""),
        )

    def _prompt_primary(self, _sender: object) -> None:
        self._prompt_key(1)

    def _prompt_secondary(self, _sender: object) -> None:
        self._prompt_key(2)

    def _prompt_key(self, which: int) -> None:
        from h250mac.capture import capture_shortcut

        title = "Mac hotkey" if which == 1 else "Windows hotkey"
        captured = capture_shortcut(title, allow_off=which == 2)
        if captured is None:
            return
        if not captured:
            self._select_key(which, "", "Off")
            return
        self._select_key(which, captured, shortcut_label(captured))

    def _select_key(self, which: int, key_name: str, label: str = "") -> None:
        if which == 1:
            self.bindings.set_primary(key_name)
            self.cfg.key = self.bindings.primary
            self.cfg.key_label = "" if not self.cfg.key else label
        else:
            self.bindings.set_secondary(key_name)
            self.cfg.key2 = self.bindings.secondary
            self.cfg.key2_label = "" if not self.cfg.key2 else label
        shown = self.cfg.key_label if which == 1 else self.cfg.key2_label
        self._show_extra(which, self.cfg.key if which == 1 else self.cfg.key2, shown)
        save_config(self.cfg)
        self._refresh_checks()

    def _show_extra(self, which: int, key_name: str, label: str) -> None:
        extra = self._primary_extra if which == 1 else self._secondary_extra
        items = self._primary_items if which == 1 else self._secondary_items
        presets = PRIMARY_PRESETS if which == 1 else SECONDARY_PRESETS
        if extra is None:
            return
        if extra in items:
            items.remove(extra)
        preset_labels = set(matching_labels(presets, key_name))
        custom = bool(key_name) and (
            key_name not in preset_keys(presets)
            or (bool(label) and label not in preset_labels)
        )
        if custom:
            extra.hidden = False
            extra.title = label or shortcut_label(key_name)
            extra._h250_key = key_name  # type: ignore[attr-defined]
            extra._h250_label = extra.title  # type: ignore[attr-defined]
            items.append(extra)
        else:
            extra.hidden = True
            extra._h250_key = ""  # type: ignore[attr-defined]
            extra._h250_label = ""  # type: ignore[attr-defined]

    def _item_selected(self, item: rumps.MenuItem, which: int) -> bool:
        key = self.cfg.key if which == 1 else self.cfg.key2
        label = self.cfg.key_label if which == 1 else self.cfg.key2_label
        if getattr(item, "_h250_key", None) != key:
            return False
        item_label = getattr(item, "_h250_label", "")
        if label and item_label:
            return item_label == label
        return True

    def _refresh_checks(self) -> None:
        for item in self._primary_items:
            item.state = 1 if self._item_selected(item, 1) else 0
        for item in self._secondary_items:
            item.state = 1 if self._item_selected(item, 2) else 0
        if self._primary_status is not None:
            shown = status_label(PRIMARY_PRESETS, self.cfg.key, self.cfg.key_label)
            self._primary_status.title = f"Mac: {shown}"
        if self._secondary_status is not None:
            shown = status_label(SECONDARY_PRESETS, self.cfg.key2, self.cfg.key2_label)
            self._secondary_status.title = f"Windows: {shown}"

    def _update_device_line(self) -> None:
        try:
            present = bool(matching_devices())
        except RuntimeError:
            present = False
        self._device_item.title = (
            "Handset: connected" if present else "Handset: not connected"
        )

    def _update_accessibility_line(self) -> None:
        if accessibility_trusted():
            self._ax_item.title = "Accessibility: allowed"
        else:
            self._ax_item.title = "Accessibility: required — click to enable"

    def _show_accessibility_walkthrough(self) -> None:
        rumps.alert(
            "Allow push-to-talk keys",
            "H250 needs Accessibility access to hold your chosen hotkey while the "
            "side button is down.\n\n"
            "1. macOS may show a dialog — choose Open System Settings.\n"
            f"2. Turn on the switch for “{APP_BUNDLE_NAME}”.\n"
            "3. Leave Python and uv off. Those are different programs and "
            "cannot post keys for this app.\n\n"
            "You can reopen this flow from the Accessibility menu item. "
            "A startup alert is not shown, so the menu bar icon can appear first.",
            "Continue",
            icon_path=alert_icon_path(),
        )
        request_accessibility_prompt()

    @rumps.timer(2)
    def poll_handset(self, _timer: object) -> None:
        self._update_device_line()
        self._update_accessibility_line()

    def enable_accessibility(self, _sender: object) -> None:
        if not accessibility_trusted():
            self._show_accessibility_walkthrough()
        self.open_accessibility(_sender)
        self._update_accessibility_line()

    def open_accessibility(self, _sender: object) -> None:
        for url in (ACCESSIBILITY_URL, LEGACY_ACCESSIBILITY_URL):
            result = subprocess.run(["open", url], check=False)
            if result.returncode == 0:
                return

    def quit_app(self, _sender: object) -> None:
        self._stop.set()
        self._thread.join(timeout=2.0)
        rumps.quit_application()


def main() -> None:
    configure_menu_bar_extra()
    apply_application_icon()
    from rumps.rumps import NSApp

    app = H250MenubarApp()
    original = NSApp.initializeStatusBar

    def initialize(nsapp):
        original(nsapp)
        reveal_status_item(nsapp.nsstatusitem, app.icon)

    NSApp.initializeStatusBar = initialize
    app.run()


if __name__ == "__main__":
    sys.exit(main() or 0)
