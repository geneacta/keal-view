#!/bin/sh
# tools/site-width.sh — does any page put a scrollbar under the whole document?
#
#   tools/site-width.sh
#
# A page whose content is wider than the window scrolls sideways as a whole:
# the nav runs off the right, the prose is cut mid-word, and on a phone the
# reader drags the page about to read a paragraph. It is invisible in a
# screenshot — headless Chrome will not make a window narrower than 500 points,
# so a capture asked for at 375 is a 500-point page cropped and looks exactly
# the same whether the defect is there or not. What tells the truth is
# `scrollWidth` against `clientWidth`, and this asks for it.
#
# **500 points, and that is enough.** It is the narrowest window Chrome will
# make, and everything below this site's 980-point breakpoint lays out the same
# way — so the only thing a narrower window could add is content that cannot
# shrink, and content that cannot shrink is a floor, which shows here as a
# document wider than 500. A first version measured six widths inside an
# iframe to get under the floor; the fonts inside a file:// iframe never
# finish loading under `--dump-dom`, so it measured a page set in fallback
# faces, which is narrower than the page a reader gets.
#
# It is measured after `document.fonts.ready` for the same reason: web fonts
# arrive later than `load`.
#
# Chrome renders the pages, so this is a thing a person runs and not a gate.
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
CHROME=${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}
[ -x "$CHROME" ] || { echo "no Chrome at $CHROME — set CHROME" >&2; exit 1; }
W=${W:-500}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"; rm -f "$ROOT"/site/.kv-width-probe.html "$ROOT"/site/fr/.kv-width-probe.html' EXIT

cat > "$TMP/probe.js" <<'JS'
document.fonts.ready.then(function(){
  var d = document.documentElement;
  document.title = 'KVW ' + d.scrollWidth + ' ' + d.clientWidth;
});
JS

bad=0
n=0
for f in "$ROOT"/site/*.html "$ROOT"/site/fr/*.html; do
  # The copy goes **beside the page**, not into a temp directory. A page links
  # its stylesheet by a relative path, so a copy somewhere else is a copy with
  # no stylesheet — and an unstyled page is wide, so the first version of this
  # reported twelve of twenty-four overflowing when none of them did. An
  # instrument has to be given the same world as the thing it measures.
  probe="$(dirname "$f")/.kv-width-probe.html"
  python3 - "$f" "$TMP" "$probe" <<'PY'
import sys
page, tmp, out = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(page, encoding="utf-8").read()
js = open(tmp + "/probe.js", encoding="utf-8").read()
open(out, "w", encoding="utf-8").write(
    s.replace("</body>", "<script>" + js + "</" + "script></body>"))
PY
  # The title element, and not the first thing in the page that looks like an
  # answer: `--dump-dom` prints the script's own source as well as its result,
  # and a pattern loose enough to match the source reports whatever the source
  # says. One did, for a day, on every page including a page that was 605 wide.
  out=$("$CHROME" --headless=new --disable-gpu --hide-scrollbars \
        --window-size="$W",800 --virtual-time-budget=8000 \
        --dump-dom "file://$probe" 2>/dev/null \
        | sed -n 's|.*<title>KVW \([0-9]*\) \([0-9]*\)</title>.*|\1 \2|p' | head -1)
  rm -f "$probe"
  n=$((n + 1))
  [ -n "$out" ] || { echo "NO ANSWER  ${f#$ROOT/}  — the probe never reported" >&2; exit 1; }
  scroll=${out% *}
  client=${out#* }
  if [ "$scroll" -gt "$client" ]; then
    bad=$((bad + 1))
    echo "WIDE  ${f#$ROOT/}  document $scroll in a window of $client"
  fi
done
if [ "$bad" -eq 0 ]; then
  echo "$n pages at $W points: every document is as wide as its window"
else
  echo "$bad of $n pages are wider than the window they are in" >&2
  exit 1
fi
