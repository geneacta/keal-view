#!/bin/sh
# tools/shot.sh — run a keal-view program and photograph its window.
#
#   tools/shot.sh build/calculator docs/calculator.png [seconds]
#
# The program is asked for its window number, `screencapture` is pointed at
# exactly that window, and the program is stopped again. Nothing else on the
# screen is captured, and nothing has to be moved out of the way first.
set -e
BIN=${1:?usage: tools/shot.sh <program> <out.png> [settle-seconds]}
OUT=${2:?usage: tools/shot.sh <program> <out.png> [settle-seconds]}
SETTLE=${3:-1}
IDFILE=$(mktemp /tmp/kealview-winid.XXXXXX)
"$BIN" --window-id "$IDFILE" &
PID=$!
trap 'kill $PID 2>/dev/null || true; rm -f "$IDFILE"' EXIT
n=0
while [ ! -s "$IDFILE" ] && [ $n -lt 60 ]; do sleep 0.1; n=$((n+1)); done
[ -s "$IDFILE" ] || { echo "the program never reported a window" >&2; exit 1; }
sleep "$SETTLE"
screencapture -x -o -l "$(tr -d '[:space:]' < "$IDFILE")" "$OUT"
echo "$OUT"
