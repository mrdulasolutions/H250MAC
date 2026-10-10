# H250 on a Mac

This is the setup from the video. You plug in a TEC handset, choose a key, and hold the side button while you talk. The handset's speaker and microphone are a normal USB sound device. This app only holds the key down, the same way TEC's Windows tray app does.

The side button is not a keyboard key. On Windows, TEC's own installer maps that button. On a Mac, use this project instead. You can still use the earpiece and microphone on either system.

## Get the handset

Buy the [TEC Devices H-250 USB handset](https://tec-devices.com/product/h-250-usb-handset/). That is the handset in the video. The rugged version is the [mil-spec H-250 USB handset](https://tec-devices.com/product/h250-usb-handset-mil-spec/). Both are listed in the [TEC shop](https://tec-devices.com/shop/) under [audio devices](https://tec-devices.com/product-category/audio-device/).

Plug it into a USB port. A USB-A to USB-C adapter is fine.

## Windows installer

TEC includes Windows button-mapping software with the handset. It maps the side button to a keyboard key and turns on zero-latency sidetone on Intel-based Windows PCs. It does not run on a Mac. The copy this project was checked against is `H250_PTT.exe` 3.1.0, from the CD in the box.

TEC also keeps that software on the product page:

- [H-250 USB handset](https://tec-devices.com/product/h-250-usb-handset/). Open the **Product Manual** tab. If you are signed out, the page says "Please Login To Download Attachment." Sign in to a TEC account, then download it.
- [Mil-spec H-250 USB handset](https://tec-devices.com/product/h250-usb-handset-mil-spec/). Same tab, for the rugged handset.
- The CD that ships with the handset, if you already have the box.
- [TEC contact](https://tec-devices.com/contact-us/) or support@tec-devices.com if the download is not there. Phone 813.863.1568.

You do not need that Windows program to use the Mac app, or to use the handset as a microphone and speaker.

## Use the handset audio

Audio does not go through this app. The handset is its own USB sound card. Set it as the speaker and microphone only if you want to hear and talk through the handset. Leave the Mac or PC speakers selected if you do not.

### Mac

1. Plug the handset in.
2. Open **System Settings → Sound**.
3. Under Output, choose the H-250. It may appear as H-250 or H250-USB.
4. Under Input, choose the same device. Speak into the handset and confirm the input level moves.
5. In Zoom, Teams, Meet, or Cursor, open that app's microphone and speaker settings and choose the H-250 there too. Otherwise the app can stay on the Mac's built-in mic.

TEC's zero-latency sidetone, hearing your own voice in the earpiece, is part of their Windows software. On a Mac, choosing the handset in Sound is what turns the mic and speaker on.

### Windows

1. Plug the handset in. Windows sees it as a USB sound device. The mic and speaker do not need a separate driver.
2. Open **Settings → System → Sound**. Set Output and Input to the H-250.
3. If an app still uses another device, open the old Sound panel (`mmsys.cpl`). On **Playback** and **Recording**, set the H-250 as the Default Device.
4. In the app you talk in, choose the H-250 microphone and speaker.
5. Install TEC's Windows mapper, from the product page or the CD, when you want the side button mapped on Windows or when you want their sidetone. That program is separate from this Mac app.

## Install it with your AI

You do not need Cursor, and you do not have to type the install commands yourself. You need an AI that can use the computer, such as Grok CLI, Claude Desktop, OpenWork, or Cursor. Any of those can follow this README.

Clone the project, open that folder in the AI, and paste the prompt below.

```bash
git clone https://github.com/mrdulasolutions/H250MAC.git
cd H250MAC
```

```text
Install H250 PTT by following README.md in this folder.
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

1. Plug in the handset. If you want to hear and talk through it, select it for sound input and output.
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
