#!/bin/sh
# tools/build.sh — compile a keal-view program to a native executable.
#
#   tools/build.sh examples/calculator.keal
#
# What it does is small enough to read: pick this platform's backend, compile
# it once to an object file, and hand that object plus the platform's link
# flags to `keal build`. Everything else — the whole framework — is Keal, and
# `keal build` compiles it the way it compiles any other program.
set -e

ROOT=$(cd "$(dirname "$0")/.." && pwd)
SRC=${1:?usage: tools/build.sh path/to/app.keal}
[ -f "$SRC" ] || { echo "no such file: $SRC" >&2; exit 1; }
SRC=$(cd "$(dirname "$SRC")" && pwd)/$(basename "$SRC")
NAME=$(basename "$SRC" .keal)
OUT=$ROOT/build
mkdir -p "$OUT"

# The compiler: $KEAL wins, then a checked-out sibling, then the path.
if [ -n "$KEAL" ]; then :
elif [ -x "$ROOT/../keal/target/release/keal" ]; then KEAL=$ROOT/../keal/target/release/keal
elif command -v keal >/dev/null 2>&1; then KEAL=keal
else echo "no keal compiler found — set KEAL, or build ../keal" >&2; exit 1
fi

case $(uname -s) in
  Darwin)
    BACKEND=$ROOT/runtime/kv_cocoa.m
    LINK="-framework Cocoa -framework QuartzCore -framework CoreGraphics"
    ;;
  Linux)
    BACKEND=$ROOT/runtime/kv_x11.c
    LINK="-lX11"
    ;;
  MINGW*|MSYS*|CYGWIN*|Windows_NT)
    BACKEND=$ROOT/runtime/kv_win32.c
    # `-static` is not tidiness. A keal-view program built here imports one
    # non-system DLL, `libwinpthread-1.dll`, and Windows resolves that along
    # the PATH. The ordinary developer machine has **two** of them and they
    # are different files — Git for Windows ships one in `Git\mingw64\bin`
    # and a separate MinGW ships the `gcc` this needs. Whichever comes first
    # wins, and when Git's wins the threads that drain a child process's pipes
    # never finish: `runCommand` spins one thread at 100% forever, with no
    # error of any kind.
    #
    # Measured on Windows 11 by reducing it to eleven lines — a window that
    # runs `git --version` — which spins when the child can be started and
    # exits cleanly when it cannot, and flips on nothing but the PATH order.
    # Linking statically removes the import and the failure with it.
    #
    # Two wrong explanations were offered for why the released binaries never
    # showed it, one each, and `objdump -p` settled it: their whole import
    # table is GDI32, KERNEL32, USER32. **No pthread DLL at all** — so a
    # download was never exposed, on any machine, however many MinGWs it has.
    # The CI's gcc produces a binary with nothing for the loader to resolve.
    #
    # So this flag protects the **developer**, not the download, and it earns
    # its place by making the property explicit rather than accidental: a
    # runner image that changes its toolchain would otherwise start shipping
    # the import with nobody noticing until a download span.
    #
    # And the requirement that creates the import is our own. Keal's error
    # says a Windows build needs "MinGW-w64 (a POSIX-threads build, which
    # actors need)" — so the machine that follows the instructions correctly
    # is the machine that gets bitten.
    LINK="-static -lgdi32 -luser32"
    ;;
  *) echo "keal-view has no backend for $(uname -s)" >&2; exit 1 ;;
esac
. "$ROOT/tools/cc.sh"
CC=$(kv_cc)

OBJ=$OUT/$(basename "$BACKEND" | sed 's/\.[^.]*$//').o
if [ ! -f "$OBJ" ] || [ "$BACKEND" -nt "$OBJ" ] || [ "$ROOT/runtime/kv.h" -nt "$OBJ" ]; then
  echo "cc  $(basename "$BACKEND")"
  "$CC" -c -O2 -I"$ROOT/runtime" -o "$OBJ" "$BACKEND"
fi

# `keal build` writes the executable, and the C it generated, into the working
# directory under the source file's stem — so it runs in the output directory.
echo "keal $(basename "$SRC")"
cd "$OUT"
# shellcheck disable=SC2086
"$KEAL" build "$SRC" "$OBJ" -I"$ROOT/runtime" $LINK
# Windows adds the extension; everywhere else the stem is the whole name.
if [ -f "$NAME.exe" ]; then echo "→ build/$NAME.exe"; else echo "→ build/$NAME"; fi
