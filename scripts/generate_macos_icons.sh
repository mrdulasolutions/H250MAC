#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="$ROOT/macos/AppIconSource.jpg"
ICONSET="$ROOT/macos/AppIcon.iconset"
ICNS="$ROOT/macos/AppIcon.icns"
MENUBAR="$ROOT/src/h250mac/assets/menubar.png"
ALERT="$ROOT/src/h250mac/assets/alert.png"

if [[ ! -f "$SOURCE" ]]; then
  echo "Missing $SOURCE"
  exit 1
fi

rm -rf "$ICONSET"
mkdir -p "$ICONSET" "$(dirname "$MENUBAR")"

make_png() {
  local size="$1"
  local out="$2"
  sips -s format png -z "$size" "$size" "$SOURCE" --out "$out" >/dev/null
}

make_png 16 "$ICONSET/icon_16x16.png"
make_png 32 "$ICONSET/icon_16x16@2x.png"
make_png 32 "$ICONSET/icon_32x32.png"
make_png 64 "$ICONSET/icon_32x32@2x.png"
make_png 128 "$ICONSET/icon_128x128.png"
make_png 256 "$ICONSET/icon_128x128@2x.png"
make_png 256 "$ICONSET/icon_256x256.png"
make_png 512 "$ICONSET/icon_256x256@2x.png"
make_png 512 "$ICONSET/icon_512x512.png"
make_png 1024 "$ICONSET/icon_512x512@2x.png"

iconutil -c icns "$ICONSET" -o "$ICNS"
rm -rf "$ICONSET"

# Status item (menu bar); 22pt @2x for Retina.
sips -s format png -z 44 44 "$SOURCE" --out "$MENUBAR" >/dev/null
# Dialogs / application icon while running under Python.
sips -s format png -z 256 256 "$SOURCE" --out "$ALERT" >/dev/null

echo "Wrote $ICNS"
echo "Wrote $MENUBAR"
echo "Wrote $ALERT"
