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

CC=${CC:-cc}
case $(uname -s) in
  Darwin)
    BACKEND=$ROOT/runtime/kv_cocoa.m
    LINK="-framework Cocoa -framework QuartzCore -framework CoreGraphics"
    ;;
  Linux)
    BACKEND=$ROOT/runtime/kv_x11.c
    LINK="-lX11 -lXext"
    ;;
  MINGW*|MSYS*|CYGWIN*|Windows_NT)
    BACKEND=$ROOT/runtime/kv_win32.c
    LINK="-lgdi32 -luser32"
    ;;
  *) echo "keal-view has no backend for $(uname -s)" >&2; exit 1 ;;
esac

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
echo "→ build/$NAME"
