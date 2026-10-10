# H250 on a Mac

This is the setup from the video. You plug in a TEC handset, choose a key, and hold the side button while you talk. The Mac already plays the earpiece and uses the microphone. This app holds the key down for you, the same way TEC's Windows tray app does.

The side button is not a keyboard key. Leave TEC's Windows installer on the CD. It does not run on a Mac.

## Get the handset

Buy the [TEC Devices H-250 USB handset](https://tec-devices.com/product/h-250-usb-handset/). That is the handset in the video.

Plug it into a USB-C port. A USB-A to USB-C adapter is fine. In System Settings → Sound, choose the H-250 for both output and input. Audio does not go through this app.

## Install it with your AI

You do not have to type the install commands yourself. Clone the project, open the folder in Cursor, and paste the prompt below.

```bash
git clone https://github.com/mrdulasolutions/H250MAC.git
cd H250MAC
```

Open that `H250MAC` folder in Cursor, then paste:

```text
Install H250 PTT by following README.md.
Put the app in /Applications/H250 PTT.app on the startup disk.
Use the project's install script. Use the Xcode toolchain clang, not /usr/bin/clang.
Do not accept the Xcode license.
Do not install the app into the home folder.
When it is installed, open /Applications/H250 PTT.app.
Tell me to turn on H250 PTT under Privacy & Security → Accessibility, and to leave Python and uv off.
```

The app lands in `/Applications`, next to your other Mac apps. It has no Dock icon. Look for **H250** in the menu bar.

If you would rather run the install yourself:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[menubar]"
chmod +x scripts/install_menubar_app.sh
./scripts/install_menubar_app.sh
open "/Applications/H250 PTT.app"
```

Python 3.11 or newer is enough. You do not need Homebrew.

On first use, click **H250** in the menu bar. If it says **Accessibility: required — click to enable**, follow that and turn on **H250 PTT**. Leave Python and uv off. This app does not need Full Disk Access.

Run only one copy. A second copy can see the handset but cannot open the side button.

Quit and reopen **H250 PTT** after a source change. You do not need to install again for that. Running the installer again changes the app's signature. After that, turn **H250 PTT** off and on under Accessibility, or the button will be detected and the key will not be posted.

## Use it

1. Plug in the handset and select it for sound input and output.
2. Click **H250** in the menu bar.
3. Choose the app you talk into. The side button holds the Mac key. The second side control holds the Windows key.

| App | Mac (side button) | Windows (second control) |
| --- | --- | --- |
| Cursor | Control-M | Control-M |
| Zoom | Space | Space |
| Teams | Option-Space | Control-Space |
| Meet | Space | Space |

4. Hold the side button to talk, then let go. The key is released when you release the button.

To use a different shortcut, click **Set Mac hotkey…** or **Set Windows hotkey…** and press the keys. The menu shows the Mac symbols: ⌃ Control, ⌥ Option, ⇧ Shift, ⌘ Command. Control-M appears as ⌃M. Click **Set**. On the Windows side, **Off** clears that control.

Zoom and Meet both use the space bar, so pick the name of the app you have open. Teams on a Mac is Option-Space. Teams on Windows is Control-Space. Discord has no default key, so record the one you set inside Discord.

The choice is saved. The next time you open **H250**, it uses the same keys.

## If the button does nothing

- The menu should say the handset is connected. If not, try another USB port.
- The menu should say Accessibility is allowed, and the switch must be **H250 PTT**, not Python.
- Quit any other **H250 PTT**. Only one copy can hold the side button.
- In the app you are talking to, click the text field or meeting window first. The held key goes to whatever is in front.

## Notes for later

The command-line listener is `h250-ptt`. `h250-ptt --check` reports whether the handset is plugged in. `h250-ptt --dump` prints each button report and does not press a key. Saved keys live in `~/Library/Application Support/h250mac/config.json`.

The handset is USB vendor `0x0D8C`, product `0x0013` or `0xAAA0`–`0xAAAF`. The side button is a press in the HID report. On a Mac that press shows up one byte earlier than in TEC's Windows app (`00 11 00 00` held, `00 01 00 00` released). This project checks both.

Tests do not need the handset:

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

## License

Proprietary. Copyright (c) 2026 MRDula Solutions. All rights reserved.
