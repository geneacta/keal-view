#!/bin/sh
# tools/test.sh — build and run everything that can be checked without a screen.
#
# Three things, in order of how much they tell you when they fail:
#
#   1. the generated C, read under the warnings that mean the backend slipped
#   2. the assertions, which say what the framework believes
#   3. a frame from every example, drawn to a file
#
# All of it runs with no display, which is how this project is checked in
# continuous integration and on a machine whose window has never opened.
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)

if [ -n "$KEAL" ]; then KEAL_BIN=$KEAL
elif [ -x "$ROOT/../keal/target/release/keal" ]; then KEAL_BIN=$ROOT/../keal/target/release/keal
else KEAL_BIN=keal
fi

"$ROOT/tools/build.sh" "$ROOT/tests/units.keal" >/dev/null
"$ROOT/tools/build.sh" "$ROOT/tests/shapes.keal" >/dev/null
"$ROOT/tools/build.sh" "$ROOT/tests/text.keal" >/dev/null
"$ROOT/tools/build.sh" "$ROOT/examples/calculator.keal" >/dev/null
"$ROOT/tools/build.sh" "$ROOT/examples/studio.keal" >/dev/null
"$ROOT/tools/build.sh" "$ROOT/examples/gallery.keal" >/dev/null

# `keal build` compiles without warnings, so this is the only place anyone
# looks at them. Every miscompilation found in this project so far announced
# itself as one of these three and went unread: a call to a function that was
# never declared, a pointer where an integer was expected, an integer where a
# pointer was.
CHECK=$ROOT/build/emit-check.c
for prog in tests/units examples/gallery examples/studio examples/calculator; do
  "$KEAL_BIN" emit-c "$ROOT/$prog.keal" > "$CHECK" 2>/dev/null
  "${CC:-cc}" -fsyntax-only -std=c11 -I"$ROOT/runtime" \
      -Werror=implicit-function-declaration \
      -Werror=incompatible-pointer-types \
      -Werror=int-conversion \
      "$CHECK" \
   || { echo "FAIL  the C generated for $prog.keal says the backend slipped" >&2; exit 1; }
done
rm -f "$CHECK"
echo "generated C: clean under the three miscompilation warnings"

cd "$ROOT/build"

# Windows names the executable with an extension and nothing else does.
run() { p=$1; shift; if [ -x "./$p.exe" ]; then "./$p.exe" "$@"; else "./$p" "$@"; fi; }

run units
run shapes >/dev/null
run text >/dev/null
run calculator --snapshot calculator.bmp 2
run studio --snapshot studio.bmp 2
run gallery --snapshot gallery.bmp 2 900 1900

for f in shapes text calculator studio gallery; do
  [ -s "$f.bmp" ] || { echo "FAIL  $f drew nothing" >&2; exit 1; }
done
echo "frames drawn: $(ls -1 ./*.bmp | tr '\n' ' ')"
