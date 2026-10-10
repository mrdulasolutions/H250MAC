#!/usr/bin/env bash
# Build ~/Applications/H250 PTT.app as an in-process arm64 launcher.
# macOS 26 shows a menu-bar icon only when the running image is the app's
# own Mach-O. A shell script that execs Python stays invisible.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/.venv"
APP_NAME="H250 PTT.app"
DEST="$HOME/Applications/$APP_NAME"
CLANG="/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang"
SDK_DIR="/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs"

if [[ ! -x "$VENV/bin/python" ]]; then
  echo "Create the venv first, using the Python you want the app to run:" >&2
  echo "  cd \"$ROOT\" && python3 -m venv .venv && source .venv/bin/activate" >&2
  echo "  python -m pip install -e \".[menubar]\"" >&2
  exit 1
fi

"$VENV/bin/python" -m pip install -e "$ROOT/.[menubar]"

chmod +x "$ROOT/scripts/generate_macos_icons.sh"
"$ROOT/scripts/generate_macos_icons.sh"

mkdir -p "$DEST/Contents/MacOS" "$DEST/Contents/Resources"
cp "$ROOT/macos/Info.plist" "$DEST/Contents/Info.plist"
cp "$ROOT/macos/AppIcon.icns" "$DEST/Contents/Resources/AppIcon.icns"

# Resolve the interpreter with the venv itself. macOS readlink has no -f.
# /usr/bin/python3 exits 69 until the Xcode license is accepted; do not accept it.
# base_prefix, headers, and site-packages follow the venv, so the same script
# works when $HOME is on an external volume or under /Users.
eval "$("$VENV/bin/python" - "$ROOT" <<'PY'
import os
import shlex
import sys
import sysconfig

root = sys.argv[1]
prefix = sys.base_prefix
ld = str(sysconfig.get_config_var("LDVERSION") or f"{sys.version_info.major}.{sys.version_info.minor}")
libdir = sysconfig.get_config_var("LIBDIR") or os.path.join(prefix, "lib")
include = sysconfig.get_config_var("INCLUDEPY") or os.path.join(prefix, "include", f"python{ld}")
site = sysconfig.get_path("purelib")
lib = os.path.join(libdir, f"libpython{ld}.dylib")

def emit(name: str, value: str) -> None:
    print(f"{name}={shlex.quote(value)}")

emit("PYTHON", os.path.realpath(sys.executable))
emit("PYHOME", prefix)
emit("PYLD", ld)
emit("PYINCLUDE", include)
emit("PYLIBDIR", libdir)
emit("PYLIB", lib)
emit("PYSITE", site)
emit("PYPATH", root + os.sep + "src" + os.pathsep + site)
PY
)"

fail() {
  echo "error: $*" >&2
  exit 1
}

SDK=""
if [[ -d "$SDK_DIR/MacOSX.sdk" ]]; then
  SDK="$SDK_DIR/MacOSX.sdk"
else
  SDK="$(ls -d "$SDK_DIR"/MacOSX*.sdk 2>/dev/null | tail -1 || true)"
fi

if [[ ! -x "$CLANG" ]]; then
  fail "Xcode toolchain clang is missing ($CLANG). This install does not fall back to a shell script or /usr/bin/clang: on macOS 26 that launcher never gets a menu-bar icon. Do not accept the Xcode license from this script."
fi
if [[ -z "$SDK" || ! -d "$SDK" ]]; then
  fail "MacOSX SDK is missing under $SDK_DIR. Install the Xcode SDK and run this script again."
fi
if [[ ! -f "$PYLIB" ]]; then
  fail "libpython${PYLD} was not found at $PYLIB (interpreter $PYTHON). The launcher links that library in-process."
fi
if [[ ! -d "$PYINCLUDE" ]]; then
  fail "Python headers were not found at $PYINCLUDE."
fi

LAUNCHER="$DEST/Contents/MacOS/H250 PTT"
LAUNCHER_SRC="$(mktemp "${TMPDIR:-/tmp}/h250-launcher.XXXXXX.c")"
# Write the C file from Python so a home path with spaces (or quotes) is escaped.
"$VENV/bin/python" - "$LAUNCHER_SRC" "$PYHOME" "$PYPATH" <<'PY'
import sys

path, home, pythonpath = sys.argv[1:]

def c_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')

source = f"""#include <stdlib.h>
#include <Python.h>
int main(void) {{
    setenv("PYTHONHOME", "{c_string(home)}", 1);
    setenv("PYTHONPATH", "{c_string(pythonpath)}", 1);
    Py_Initialize();
    int rc = PyRun_SimpleString("from h250mac.menubar import main; raise SystemExit(main() or 0)");
    return rc == 0 ? 0 : 1;
}}
"""
with open(path, "w", encoding="utf-8") as handle:
    handle.write(source)
PY

"$CLANG" -isysroot "$SDK" -arch arm64 -Os \
  -I"$PYINCLUDE" \
  -L"$PYLIBDIR" \
  -Wl,-rpath,"$PYLIBDIR" \
  -o "$LAUNCHER" "$LAUNCHER_SRC" -lpython"${PYLD}"
rm -f "$LAUNCHER_SRC"
chmod 755 "$LAUNCHER"
codesign --force --sign - --identifier com.mrdulasolutions.h250mac "$DEST"

echo "Installed $DEST"
echo "Open it from Finder → Applications → H250 PTT, or run:"
echo "  open \"$DEST\""
echo ""
echo "The launcher imports $ROOT/src on PYTHONPATH. Quit and reopen H250 PTT after a source edit. That does not need a recompile."
echo "Running this installer again re-signs the app and changes its cdhash."
echo "Turn H250 PTT off and on under System Settings → Privacy & Security → Accessibility, or the listener will refuse to post keys."
codesign -dv --verbose=4 "$LAUNCHER" 2>&1 | awk -F= '/^CDHash=/{print "cdhash " $2}'
