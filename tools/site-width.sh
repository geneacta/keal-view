#!/bin/sh
# tools/site-width.sh — does any page put a scrollbar under the whole document?
#
#   tools/site-width.sh
#
# A page whose content is wider than the window scrolls sideways as a whole:
# the nav runs off the right, the prose is cut mid-word, and on a phone the
# reader drags the page about to read a paragraph. It is invisible in a
# screenshot — headless Chrome will not make a window narrower than 500 points,
# so a capture asked for at 375 is a 500-point page cropped, and it looks
# exactly the same whether the defect is there or not. **What tells the truth
# is `scrollWidth` against `clientWidth`**, and this asks for it.
#
# Two defects came out of it the first time it ran: a grid column that would
# not go narrower than the code block in it, on every page, and a
# seventy-five-character name in running text that put a 605-point floor under
# the porting guide at every window below 700.
#
# Chrome renders the pages, so this is a thing a person runs and not a gate.
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
CHROME=${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}
[ -x "$CHROME" ] || { echo "no Chrome at $CHROME — set CHROME" >&2; exit 1; }
WIDTHS=${WIDTHS:-320 375 414 500 700 900}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# Each page is loaded in an iframe of a chosen width, because the width that
# matters is the one below the window Chrome will make.
list=$(echo "$WIDTHS" | tr ' ' ',')
bad=0
n=0
for f in "$ROOT"/site/*.html "$ROOT"/site/fr/*.html; do
  cat > "$TMP/f.html" <<HTML
<style>body{margin:0}iframe{border:0;display:block;height:300px}</style>
<script>
var widths = [$list], made = 0, res = [];
widths.forEach(function(w){
  var i = document.createElement('iframe');
  i.width = w; i.src = 'file://$f';
  i.onload = function(){
    var d = i.contentDocument.documentElement;
    if (d.scrollWidth > d.clientWidth) { res.push(w + ':' + d.scrollWidth); }
    if (++made === widths.length) { document.title = 'R ' + res.join(' '); }
  };
  document.body.appendChild(i);
});
</script>
HTML
  out=$("$CHROME" --headless=new --disable-gpu --allow-file-access-from-files \
        --virtual-time-budget=6000 --dump-dom "file://$TMP/f.html" 2>/dev/null \
        | grep -o "R [0-9: ]*" | head -1)
  n=$((n + 1))
  over=$(echo "$out" | sed 's/^R *//')
  if [ -n "$over" ]; then
    bad=$((bad + 1))
    echo "WIDE  ${f#$ROOT/}  (window:document) $over"
  fi
done
if [ "$bad" -eq 0 ]; then
  echo "$n pages at $WIDTHS points: every document is as wide as its window"
else
  echo "$bad of $n pages are wider than the window they are in" >&2
  exit 1
fi
