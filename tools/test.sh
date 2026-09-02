#!/bin/sh
# tools/test.sh — build and run everything that can be checked without a screen.
#
# The unit tests assert; the render tests draw a frame to a BMP and are checked
# by being looked at, or by `tools/bmp2png.py` and a pair of eyes. Both build
# the whole framework, so a compile error anywhere fails here.
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)

"$ROOT/tools/build.sh" "$ROOT/tests/units.keal" >/dev/null
"$ROOT/tools/build.sh" "$ROOT/tests/shapes.keal" >/dev/null
"$ROOT/tools/build.sh" "$ROOT/tests/text.keal" >/dev/null
"$ROOT/tools/build.sh" "$ROOT/examples/calculator.keal" >/dev/null
"$ROOT/tools/build.sh" "$ROOT/examples/studio.keal" >/dev/null
"$ROOT/tools/build.sh" "$ROOT/examples/gallery.keal" >/dev/null

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
echo "frames drawn: $(cd "$ROOT/build" && ls -1 *.bmp | tr '\n' ' ')"
