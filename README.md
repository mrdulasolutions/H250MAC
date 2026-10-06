# H250 Mac

Holds a Mac key while the side button is down on a [TEC Devices H250-USB](https://tec-devices.com/product/h-250-usb-handset/) handset.

The handset is a USB headset. macOS already plays audio and records the mic once it is plugged in. The side button is not a keyboard key. TEC's Windows tray app reads a HID report and synthesizes the key. This program does that on macOS.

The Windows installer does not run on a Mac. Leave it on the CD.

## Install on a Mac

Python 3.11 or newer. The `hidapi` package ships its own library, so Homebrew is not required.

```bash
git clone https://github.com/mrdulasolutions/H250MAC.git
cd H250MAC
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
h250-ptt --check
h250-ptt
```

`h250-ptt --check` exits 0 when the handset's HID interface is present. Until then the listener waits and prints a line when you plug the handset into a USB-C port.

Audio is separate from this program. In System Settings → Sound, choose the H250-USB device for output and input.

## The key

The default key is **F13**. It does not type a character and does not toggle Caps Lock, so a radio app or a voice app can bind it as push-to-talk.

```bash
h250-ptt --key f18
h250-ptt --key space
h250-ptt --key v --key2 f14
```

`--key2` is the second side control. With no `--key2`, that control is printed and ignored.

The first launch needs permission to post keys: System Settings → Privacy & Security → Accessibility, and enable the terminal (or other app) you started `h250-ptt` from. `--dump` prints each HID report and does not post a key, so you can confirm the button before granting that permission.

Stop the listener with Ctrl-C. If a key is still down, the program releases it on the way out.

Saved hotkeys live in `~/Library/Application Support/h250mac/config.json`. When you omit `--key`, `--key2`, or `--byte`, `h250-ptt` reads that file.

## Menu bar app

Install the **H250** app into Applications (recommended). It runs from the top menu bar only (no Dock icon) and walks you through Accessibility on first launch. macOS lists it as **H250**, not Python.

```bash
python3 -m venv .venv
source .venv/bin/activate
chmod +x scripts/install_menubar_app.sh
./scripts/install_menubar_app.sh
open ~/Applications/H250.app
```

On first launch, follow the alert and enable **H250** under System Settings → Privacy & Security → Accessibility (the handset photo is the app icon there). Use the menu item **Accessibility: required — click to enable** if you need the prompt again.

Icons are built from `macos/AppIconSource.jpg` when you run the install script. To refresh them after changing the source image: `./scripts/generate_macos_icons.sh`.

Presets include F13–F16, F18, backtick (`` ` ``), space, and V. Secondary can be **Off** or any of those keys.

For development without the `.app` bundle:

```bash
python -m pip install -e ".[menubar]"
h250-ptt-menubar
```

macOS lists that process as **Python**. Use `open ~/Applications/H250.app` when you want the permission dialog to say **H250**.

## What the button report looks like

The handset enumerates as USB vendor `0x0D8C`, product `0x0013` (or `0xAAA0`–`0xAAAF` if that unit was given its own id). The Windows mapper reads input-report byte 2:

| Byte 2 | Meaning |
| --- | --- |
| `0x00`–`0x0F` | released |
| high nibble `1` (`0x10`–`0x1F`) | side button held |
| high nibble `2` (`0x20`–`0x2F`) | second side control held |

If a live press moves a different byte, the log shows the whole report. Point the listener at the byte that changes:

```bash
h250-ptt --dump --byte 1
```

## Tests

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

The tests cover the report byte and the key names. They do not need the handset.

## License

Proprietary. Copyright (c) 2026 MRDula Solutions. All rights reserved.
