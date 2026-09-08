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

# Which compiler, said out loud: keal-view uses language features that arrived
# because it asked for them, so a stale one refuses in ways that look like this
# repository's fault.
#
# **And where it came from.** The compiler is preferred from a sibling checkout
# of the language, which is what lets the two be developed together and is how
# every language defect this project found was found early. On a machine where
# somebody else is working in that checkout, it also means a build here depends
# on their uncommitted state — and the version string does not say so, because
# a working tree calls itself whatever the last release was.
#
# That cost an hour once: a half-finished rename in the language's runtime made
# every program here fail to compile, and the report that went out named a
# *released* version as broken. It was a working tree. So the line below says
# which revision, and whether that tree is clean, before anything is built with
# it.
say_compiler() {
  where=$1
  dir=$(cd "$(dirname "$where")" && pwd)
  rev=""
  if git -C "$dir" rev-parse --git-dir >/dev/null 2>&1; then
    rev=$(git -C "$dir" describe --tags --always --dirty 2>/dev/null)
    if [ -n "$(git -C "$dir" status --porcelain 2>/dev/null)" ]; then
      rev="$rev — a working tree with uncommitted changes, not a release"
    fi
  fi
  if [ -n "$rev" ]; then
    echo "compiler: $("$KEAL_BIN" version) at $KEAL_BIN [$rev]"
  else
    echo "compiler: $("$KEAL_BIN" version) at $KEAL_BIN"
  fi
}
say_compiler "$KEAL_BIN"

"$ROOT/tools/build.sh" "$ROOT/tests/units.keal" >/dev/null
# Compiled and not run: it needs a window, and a person. Built here so that it
# cannot rot between the days somebody uses it — which is the only reason a
# bench nobody runs automatically stays worth having.
"$ROOT/tools/build.sh" "$ROOT/tests/bench.keal" >/dev/null
"$ROOT/tools/build.sh" "$ROOT/tests/shapes.keal" >/dev/null
"$ROOT/tools/build.sh" "$ROOT/tests/text.keal" >/dev/null
"$ROOT/tools/build.sh" "$ROOT/examples/calculator.keal" >/dev/null
"$ROOT/tools/build.sh" "$ROOT/examples/studio.keal" >/dev/null
"$ROOT/tools/build.sh" "$ROOT/examples/gallery.keal" >/dev/null
"$ROOT/tools/build.sh" "$ROOT/examples/todo.keal" >/dev/null
"$ROOT/tools/build.sh" "$ROOT/examples/tour.keal" >/dev/null

# `keal build` compiles without warnings, so this is the only place anyone
# looks at them. Every miscompilation found in this project so far announced
# itself as one of these three and went unread: a call to a function that was
# never declared, a pointer where an integer was expected, an integer where a
# pointer was.
. "$ROOT/tools/cc.sh"
# Said before the loop, so that a missing compiler is a missing compiler and
# not six identical accusations against the code generator.
command -v "$(kv_cc)" >/dev/null 2>&1 || {
  echo "no C compiler: $(kv_cc) is not on the path — set CC" >&2; exit 1; }
CHECK=$ROOT/build/emit-check.c
for prog in tests/units examples/gallery examples/studio examples/calculator examples/todo examples/tour; do
  "$KEAL_BIN" emit-c "$ROOT/$prog.keal" > "$CHECK" 2>/dev/null
  "$(kv_cc)" -fsyntax-only -std=c11 -I"$ROOT/runtime" \
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
run todo --snapshot todo.bmp 2
run tour --snapshot tour.bmp 2 1000 900

for f in shapes text calculator studio gallery todo tour; do
  [ -s "$f.bmp" ] || { echo "FAIL  $f drew nothing" >&2; exit 1; }
done
echo "frames drawn: $(ls -1 ./*.bmp | tr '\n' ' ')"

# The badge and the line table in the README are counted from files in this
# repository, so they can only go stale when somebody here changes one — which
# is exactly when a gate should speak. It caught the headline percentage
# drifting the first time it ran.
#
# Skipped rather than failed when there is no Python, and said out loud: this
# script is the instrument somebody uses on a machine they are porting to, and
# it must not report a fault in the framework because an interpreter that
# nothing else here needs is missing. Everything above this line ran without
# it.
# Asked to *run*, not merely to exist. Windows ships an execution-alias stub
# at WindowsApps/python3 which is on the PATH, is executable, and which
# `command -v` finds — and which prints "Python est introuvable" and exits 49.
# Under `set -e` that killed the suite before its first test on a machine
# where the skip below was written precisely to keep it alive. Python absent
# and Python false are different states, and only one of them is a skip that
# `command -v` can see.
if python3 -c "" >/dev/null 2>&1; then
  python3 "$ROOT/ci/band.py" --check
else
  echo "no working python3: the README's badge was not checked"
fi

# The same frame again as a PNG, because the writer is Keal and a full window
# is the only thing that puts it over a stored block's 65535 bytes. The
# assertions in `units` write pictures of a few hundred pixels; this writes
# one of a few million, and checks that what came out begins the way a PNG
# begins rather than only that something was written.
run calculator --snapshot calculator.png 1
[ -s calculator.png ] || { echo "FAIL  no PNG was written" >&2; exit 1; }
head -c 8 calculator.png | od -An -tu1 | tr -s ' ' \
  | grep -q '137 80 78 71 13 10 26 10' \
  || { echo "FAIL  what --snapshot wrote does not begin like a PNG" >&2; exit 1; }
echo "and one of them again as a PNG: $(wc -c < calculator.png | tr -d ' ') bytes"
