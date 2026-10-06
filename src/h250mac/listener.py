"""Watch the H250-USB HID interface and hold a Mac key while the button is down."""

from __future__ import annotations

import argparse
import signal
import sys
import threading
import time
from collections.abc import Callable

from h250mac.bindings import BindingStore
from h250mac.config import load_config
from h250mac.events import accessibility_trusted, post_key
from h250mac.keys import DEFAULT_KEY, resolve_key
from h250mac.protocol import PIDS, REPORT_BYTE, VID, button_nibble

try:
    import hid
except ImportError:  # pragma: no cover - exercised only on a broken install
    hid = None


def log(msg: str) -> None:
    print(msg, flush=True)


def matching_devices() -> list[dict]:
    if hid is None:
        raise RuntimeError("hidapi is not installed. Reinstall this package with pip.")
    found = []
    seen = set()
    for pid in PIDS:
        for info in hid.enumerate(VID, pid):
            path = info.get("path")
            if path in seen:
                continue
            seen.add(path)
            found.append(info)
    return found


def open_devices() -> list[tuple[dict, object]]:
    opened = []
    for info in matching_devices():
        dev = hid.device()
        try:
            dev.open_path(info["path"])
            dev.set_nonblocking(True)
        except OSError as exc:
            log(f"skipped an interface ({exc})")
            continue
        opened.append((info, dev))
    return opened


def describe(info: dict) -> str:
    product = info.get("product_string") or "H250-USB"
    usage_page = info.get("usage_page") or 0
    usage = info.get("usage") or 0
    return (
        f"{product} vid={info['vendor_id']:04x} pid={info['product_id']:04x} "
        f"iface={info.get('interface_number')} usage={usage_page:04x}:{usage:04x}"
    )


def hex_report(report: list[int]) -> str:
    return " ".join(f"{byte:02x}" for byte in report)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="h250-ptt",
        description="Hold a Mac key while the TEC H250-USB side button is down.",
    )
    parser.add_argument(
        "--key",
        default=None,
        help=f"key to hold while the side button is down (default: config or {DEFAULT_KEY})",
    )
    parser.add_argument(
        "--key2",
        default=None,
        help="optional key for the second side control (default: from config)",
    )
    parser.add_argument(
        "--byte",
        type=int,
        default=None,
        help=f"input-report byte that carries the button (default: config or {REPORT_BYTE})",
    )
    parser.add_argument(
        "--dump",
        action="store_true",
        help="print HID reports and do not post keys",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report whether the handset HID interface is present, then exit",
    )
    return parser


def _sync_bindings(
    bindings: BindingStore,
    held: dict[int, bool],
    keycodes: dict[int, int | None],
    names: dict[int, str],
    dump: bool,
    log_fn: Callable[[str], None],
) -> None:
    snap = bindings.snapshot()
    for button in (1, 2):
        new_code = snap.keycodes[button]
        old_code = keycodes[button]
        if new_code == old_code and snap.names[button] == names[button]:
            continue
        if held[button] and old_code is not None and not dump:
            post_key(old_code, False)
            held[button] = False
        keycodes[button] = new_code
        names[button] = snap.names[button]


def run_listener(
    bindings: BindingStore,
    *,
    report_byte: int,
    dump: bool = False,
    log_fn: Callable[[str], None] = log,
    stop_event: threading.Event | None = None,
) -> int:
    def should_stop() -> bool:
        return stop_event is not None and stop_event.is_set()

    snap = bindings.snapshot()
    key_name = snap.names[1]
    if dump:
        log_fn("dump only. keys will not be posted.")
    elif accessibility_trusted():
        log_fn(f"accessibility permission is on. holding {key_name} while the side button is down.")
    else:
        log_fn(
            "accessibility permission is off, so the button will be detected "
            "but the key cannot be posted yet. System Settings → Privacy & "
            "Security → Accessibility, and enable the app you launched this from."
        )

    held = {1: False, 2: False}
    keycodes = dict(snap.keycodes)
    names = dict(snap.names)

    def release_all() -> None:
        for which, is_down in list(held.items()):
            if is_down and keycodes[which] is not None and not dump:
                post_key(keycodes[which], False)
            held[which] = False

    devs: list[tuple[dict, object]] = []
    announced = False
    last_report: dict[object, tuple[int, ...]] = {}

    try:
        while not should_stop():
            _sync_bindings(bindings, held, keycodes, names, dump, log_fn)
            if not devs:
                devs = open_devices()
                if not devs:
                    if not announced:
                        log_fn("waiting for the H250-USB. Plug it into a USB-C port.")
                        announced = True
                    time.sleep(0.5)
                    continue
                announced = False
                for info, _dev in devs:
                    log_fn("listening on " + describe(info))
                log_fn("press the side button. each new report is printed once.")

            closed = False
            for info, dev in devs:
                if should_stop():
                    break
                try:
                    report = dev.read(64, timeout_ms=30)
                except OSError as exc:
                    log_fn(f"handset read failed ({exc}). waiting for it to come back.")
                    closed = True
                    break
                if not report:
                    continue
                path = info["path"]
                signature = tuple(report)
                if last_report.get(path) == signature:
                    continue
                last_report[path] = signature
                which = button_nibble(report, report_byte)
                shown = report[report_byte] if report_byte < len(report) else "-"
                log_fn(f"report[{report_byte}]={shown}  {hex_report(report)}")
                _sync_bindings(bindings, held, keycodes, names, dump, log_fn)
                for button in (1, 2):
                    down = which == button
                    if down == held[button]:
                        continue
                    code = keycodes[button]
                    if code is None:
                        held[button] = down
                        if down:
                            log_fn(f"control {button} is down (no key mapped).")
                        continue
                    if not dump:
                        if not accessibility_trusted():
                            log_fn(
                                f"control {button} {'down' if down else 'up'}, "
                                "key not posted (Accessibility is off)."
                            )
                        else:
                            post_key(code, down)
                            log_fn(f"{names[button]} {'down' if down else 'up'}")
                    held[button] = down
            if closed:
                release_all()
                for _info, dev in devs:
                    try:
                        dev.close()
                    except OSError:
                        pass
                devs = []
                last_report.clear()
    finally:
        release_all()
        for _info, dev in devs:
            try:
                dev.close()
            except OSError:
                pass
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    file_config = load_config()
    key_name = args.key if args.key is not None else file_config.key
    key2_name = args.key2 if args.key2 is not None else file_config.key2
    report_byte = args.byte if args.byte is not None else file_config.byte

    try:
        resolve_key(key_name)
    except ValueError as exc:
        log(str(exc))
        return 2
    if key2_name:
        try:
            resolve_key(key2_name)
        except ValueError as exc:
            log(str(exc))
            return 2

    if args.check:
        found = matching_devices()
        if not found:
            log("H250-USB HID interface is not present. Plug the handset into a USB-C port.")
            return 1
        for info in found:
            log("found " + describe(info))
        return 0

    bindings = BindingStore(key_name, key2_name)
    stop_event = threading.Event()

    def handle_stop(_signum, _frame) -> None:
        stop_event.set()

    signal.signal(signal.SIGINT, handle_stop)
    signal.signal(signal.SIGTERM, handle_stop)

    return run_listener(
        bindings,
        report_byte=report_byte,
        dump=args.dump,
        log_fn=log,
        stop_event=stop_event,
    )


if __name__ == "__main__":
    sys.exit(main())
