"""Watch the H250-USB HID interface and hold a Mac key while the button is down."""

from __future__ import annotations

import argparse
import signal
import sys
import time

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
        default=DEFAULT_KEY,
        help=f"key to hold while the side button is down (default: {DEFAULT_KEY})",
    )
    parser.add_argument(
        "--key2",
        default="",
        help="optional key for the second side control",
    )
    parser.add_argument(
        "--byte",
        type=int,
        default=REPORT_BYTE,
        help=f"input-report byte that carries the button (default: {REPORT_BYTE})",
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


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        keycode = resolve_key(args.key)
    except ValueError as exc:
        log(str(exc))
        return 2
    key2 = None
    if args.key2:
        try:
            key2 = resolve_key(args.key2)
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

    key_name = args.key.strip().lower()
    if args.dump:
        log("dump only. keys will not be posted.")
    elif accessibility_trusted():
        log(f"accessibility permission is on. holding {key_name} while the side button is down.")
    else:
        log(
            "accessibility permission is off, so the button will be detected "
            "but the key cannot be posted yet. System Settings → Privacy & "
            "Security → Accessibility, and enable the app you launched this from."
        )

    held = {1: False, 2: False}
    keycodes = {1: keycode, 2: key2}
    names = {1: key_name, 2: args.key2.strip().lower() if args.key2 else ""}
    stop = False

    def release_all() -> None:
        for which, is_down in list(held.items()):
            if is_down and keycodes[which] is not None and not args.dump:
                post_key(keycodes[which], False)
            held[which] = False

    def handle_stop(_signum, _frame) -> None:
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, handle_stop)
    signal.signal(signal.SIGTERM, handle_stop)

    devs: list[tuple[dict, object]] = []
    announced = False
    last_report: dict[object, tuple[int, ...]] = {}

    try:
        while not stop:
            if not devs:
                devs = open_devices()
                if not devs:
                    if not announced:
                        log("waiting for the H250-USB. Plug it into a USB-C port.")
                        announced = True
                    time.sleep(0.5)
                    continue
                announced = False
                for info, _dev in devs:
                    log("listening on " + describe(info))
                log("press the side button. each new report is printed once.")

            closed = False
            for info, dev in devs:
                try:
                    report = dev.read(64, timeout_ms=30)
                except OSError as exc:
                    log(f"handset read failed ({exc}). waiting for it to come back.")
                    closed = True
                    break
                if not report:
                    continue
                path = info["path"]
                signature = tuple(report)
                if last_report.get(path) == signature:
                    continue
                last_report[path] = signature
                which = button_nibble(report, args.byte)
                shown = report[args.byte] if args.byte < len(report) else "-"
                log(f"report[{args.byte}]={shown}  {hex_report(report)}")
                for button in (1, 2):
                    down = which == button
                    if down == held[button]:
                        continue
                    code = keycodes[button]
                    if code is None:
                        held[button] = down
                        if down:
                            log(f"control {button} is down (no key mapped).")
                        continue
                    if not args.dump:
                        if not accessibility_trusted():
                            log(
                                f"control {button} {'down' if down else 'up'}, "
                                "key not posted (Accessibility is off)."
                            )
                        else:
                            post_key(code, down)
                            log(f"{names[button]} {'down' if down else 'up'}")
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


if __name__ == "__main__":
    sys.exit(main())
