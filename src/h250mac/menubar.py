"""Menu bar app: run the PTT listener and switch hotkeys from the status item."""

from __future__ import annotations

import subprocess
import sys
import threading

from h250mac.bindings import BindingStore
from h250mac.config import MENU_PRESETS, load_config, save_config
from h250mac.events import accessibility_trusted, request_accessibility_prompt
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


def preset_label(name: str) -> str:
    if name == "`":
        return "` (backtick)"
    return name


def quiet_listener_log(msg: str) -> None:
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
        self._primary_items: dict[str, rumps.MenuItem] = {}
        self._secondary_items: dict[str, rumps.MenuItem] = {}
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
        primary_children = [
            self._make_primary_item(name) for name in MENU_PRESETS
        ]
        secondary_children = [
            self._make_secondary_item("", "Off"),
        ] + [self._make_secondary_item(name) for name in MENU_PRESETS]
        self.menu = [
            self._device_item,
            self._ax_item,
            None,
            ("Primary key", primary_children),
            ("Secondary key", secondary_children),
            None,
            rumps.MenuItem("Open Accessibility Settings…", callback=self.open_accessibility),
            rumps.MenuItem("Quit", callback=self.quit_app),
        ]

    def _make_primary_item(self, key_name: str) -> rumps.MenuItem:
        item = rumps.MenuItem(preset_label(key_name), callback=self._on_primary)
        item._h250_key = key_name  # type: ignore[attr-defined]
        self._primary_items[key_name] = item
        return item

    def _make_secondary_item(self, key_name: str, label: str | None = None) -> rumps.MenuItem:
        text = label if label is not None else preset_label(key_name)
        item = rumps.MenuItem(text, callback=self._on_secondary)
        item._h250_key = key_name  # type: ignore[attr-defined]
        self._secondary_items[key_name] = item
        return item

    def _on_primary(self, sender: rumps.MenuItem) -> None:
        key_name = getattr(sender, "_h250_key", "")
        self._select_key(1, key_name)

    def _on_secondary(self, sender: rumps.MenuItem) -> None:
        key_name = getattr(sender, "_h250_key", "")
        self._select_key(2, key_name)

    def _select_key(self, which: int, key_name: str) -> None:
        if which == 1:
            self.bindings.set_primary(key_name)
            self.cfg.key = key_name
        else:
            self.bindings.set_secondary(key_name)
            self.cfg.key2 = key_name
        save_config(self.cfg)
        self._refresh_checks()

    def _refresh_checks(self) -> None:
        for name, item in self._primary_items.items():
            item.state = 1 if name == self.cfg.key else 0
        for name, item in self._secondary_items.items():
            item.state = 1 if name == self.cfg.key2 else 0

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
            f"2. Turn on the switch for “{APP_BUNDLE_NAME}” (or Python if you run "
            "from Terminal).\n"
            "3. If the app is missing, click + and add it from Applications.\n\n"
            "You can reopen this flow anytime from the Accessibility menu item.",
            "Continue",
            icon_path=alert_icon_path(),
        )
        request_accessibility_prompt()

    @rumps.timer(0.5)
    def onboarding(self, sender: rumps.Timer) -> None:
        sender.stop()
        if not accessibility_trusted():
            self._show_accessibility_walkthrough()
        self._update_accessibility_line()

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
