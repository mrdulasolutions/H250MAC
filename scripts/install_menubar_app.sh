#!/usr/bin/env bash
# Install H250 PTT.app into /Applications on the startup disk.
# macOS 26 shows a menu-bar icon only when the running image is the app's
# own Mach-O. A shell script that execs Python stays invisible.
# The Mach-O contains no home directory. Python paths live in the app bundle.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/.venv"
APP_NAME="H250 PTT.app"
DEST="/Applications/${APP_NAME}"
CLANG="/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang"
SDK_DIR="/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs"

if [[ $# -ne 0 ]]; then
  echo "H250 PTT installs to /Applications. Do not pass a destination." >&2
  exit 2
fi

if [[ ! -w /Applications ]]; then
  echo "Cannot write /Applications. Install H250 PTT there on the startup disk." >&2
  exit 1
fi

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
# The venv reports its own prefix, headers, and site-packages.
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

# Paths stay out of the Mach-O. They live inside the app in /Applications.
"$VENV/bin/python" - "$DEST" "$PYHOME" "$PYPATH" <<'PY'
import os
import sys

dest, pythonhome, pythonpath = sys.argv[1:]
bundle = os.path.join(dest, "Contents", "Resources", "runtime.path")
os.makedirs(os.path.dirname(bundle), exist_ok=True)
with open(bundle, "w", encoding="utf-8") as handle:
    handle.write(f"PYTHONHOME={pythonhome}\nPYTHONPATH={pythonpath}\n")
PY

LAUNCHER="$DEST/Contents/MacOS/H250 PTT"
LAUNCHER_SRC="$(mktemp "${TMPDIR:-/tmp}/h250-launcher.XXXXXX.c")"
cat > "$LAUNCHER_SRC" <<'EOF'
#include <limits.h>
#include <mach-o/dyld.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <Python.h>

static int load_runtime(const char *path) {
    FILE *file = fopen(path, "r");
    char line[8192];
    int got_home = 0;
    int got_path = 0;
    if (!file) {
        return 0;
    }
    while (fgets(line, sizeof line, file)) {
        char *newline = strchr(line, '\n');
        char *equals;
        if (newline) {
            *newline = 0;
        }
        if (line[0] == '#' || line[0] == 0) {
            continue;
        }
        equals = strchr(line, '=');
        if (!equals) {
            continue;
        }
        *equals = 0;
        if (strcmp(line, "PYTHONHOME") == 0) {
            setenv("PYTHONHOME", equals + 1, 1);
            got_home = 1;
        } else if (strcmp(line, "PYTHONPATH") == 0) {
            setenv("PYTHONPATH", equals + 1, 1);
            got_path = 1;
        }
    }
    fclose(file);
    return got_home && got_path;
}

static int bundle_runtime(char *out, size_t out_len) {
    char exe[PATH_MAX];
    char *slash;
    uint32_t size = sizeof exe;
    int wrote;
    if (_NSGetExecutablePath(exe, &size) != 0) {
        return 0;
    }
    slash = strrchr(exe, '/');
    if (!slash) {
        return 0;
    }
    *slash = 0;
    slash = strrchr(exe, '/');
    if (!slash) {
        return 0;
    }
    *slash = 0;
    wrote = snprintf(out, out_len, "%s/Resources/runtime.path", exe);
    return wrote > 0 && (size_t)wrote < out_len;
}

int main(void) {
    char path[PATH_MAX];
    int rc;
    if (!bundle_runtime(path, sizeof path) || !load_runtime(path)) {
        fprintf(stderr, "H250 PTT could not read runtime.path inside the app.\n");
        fprintf(stderr, "Run scripts/install_menubar_app.sh. The app installs to /Applications.\n");
        return 1;
    }
    Py_Initialize();
    rc = PyRun_SimpleString("from h250mac.menubar import main; raise SystemExit(main() or 0)");
    return rc == 0 ? 0 : 1;
}
EOF

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
echo "Python paths are inside that app at Contents/Resources/runtime.path."
echo "Quit and reopen H250 PTT after a source edit. That does not need a recompile."
echo "Only one copy should run. A second copy cannot open the handset."
echo "Running this installer again re-signs the app and changes its cdhash."
echo "Turn H250 PTT off and on under System Settings → Privacy & Security → Accessibility, or the listener will refuse to post keys."
echo "Do not enable Python or uv under Accessibility. This app does not need Full Disk Access."
codesign -dv --verbose=4 "$LAUNCHER" 2>&1 | awk -F= '/^CDHash=/{print "cdhash " $2}'
