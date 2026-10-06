#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/.venv"
APP_NAME="H250 PTT.app"
DEST="$HOME/Applications/$APP_NAME"

if [[ ! -x "$VENV/bin/python" ]]; then
  echo "Create the venv first:"
  echo "  cd \"$ROOT\" && python3 -m venv .venv && source .venv/bin/activate"
  echo "  python -m pip install -e \".[menubar]\""
  exit 1
fi

"$VENV/bin/python" -m pip install -e "$ROOT/.[menubar]"

chmod +x "$ROOT/scripts/generate_macos_icons.sh"
"$ROOT/scripts/generate_macos_icons.sh"

mkdir -p "$DEST/Contents/MacOS" "$DEST/Contents/Resources"
cp "$ROOT/macos/Info.plist" "$DEST/Contents/Info.plist"
cp "$ROOT/macos/AppIcon.icns" "$DEST/Contents/Resources/AppIcon.icns"

PYTHON="$VENV/bin/pythonw"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="$VENV/bin/python"
fi

cat > "$DEST/Contents/MacOS/H250 PTT" <<EOF
#!/usr/bin/env bash
exec "$PYTHON" -m h250mac.menubar
EOF
chmod +x "$DEST/Contents/MacOS/H250 PTT"

echo "Installed $DEST"
echo "Open it from Finder → Applications → H250 PTT, or run:"
echo "  open \"$DEST\""
echo ""
echo "On first launch, allow Accessibility for “H250 PTT” when macOS prompts you."
