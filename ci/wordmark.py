#!/usr/bin/env python3
"""Makes the dark-background wordmark from the light one.

    python3 ci/wordmark.py            write docs/keal-view-dark.png
    python3 ci/wordmark.py --check    fail if it is not what it should be

`keal-view.png` is the wordmark as it was drawn: #0e5b56 through an alpha
channel. Against GitHub's light page that measures 7.9:1 and is right; against
its dark page it measures **2.4:1**, under the 3:1 that a graphic has to reach
to be seen. The site does not have this problem because CSS can paint the
shape through its own alpha in whatever colour the page wants — but a README
is markdown, there is no stylesheet, and the only way to give GitHub two
colours is to give it two files.

So this makes the second one, rather than anybody drawing it: same shape, same
alpha, one ink swapped. It cannot drift from the original because it is not
kept, it is derived.

`--check` compares pixels rather than file bytes. Two zlib versions compress
the same picture differently and are both correct, so a gate that compared
bytes would fail on somebody else's machine for no reason at all.
"""

import os
import sys
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "keal-view.png")
DST = os.path.join(ROOT, "docs", "keal-view-dark.png")

# Light enough to be seen on #0d1117 — 9.4:1 — and still the same teal. Going
# to the site's near-white would read at 15:1 and stop looking like a mark.
INK = (0x4F, 0xC9, 0xBE)


def read_rgba(path):
    """Width, height and RGBA rows of a PNG. Only the one shape this reads."""
    d = open(path, "rb").read()
    if d[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("%s: not a PNG" % path)
    o, idat, hdr = 8, b"", None
    while o < len(d):
        n = int.from_bytes(d[o:o + 4], "big")
        kind, data = d[o + 4:o + 8], d[o + 8:o + 8 + n]
        if kind == b"IHDR":
            hdr = data
        elif kind == b"IDAT":
            idat += data
        o += 12 + n
    w = int.from_bytes(hdr[0:4], "big")
    h = int.from_bytes(hdr[4:8], "big")
    depth, colour, _, _, interlace = hdr[8], hdr[9], hdr[10], hdr[11], hdr[12]
    if (depth, colour, interlace) != (8, 6, 0):
        raise SystemExit("%s: expected 8-bit RGBA, not interlaced" % path)
    raw, stride, rows, prev = zlib.decompress(idat), w * 4, [], bytearray(w * 4)
    i = 0
    for _ in range(h):
        f, line, i = raw[i], bytearray(raw[i + 1:i + 1 + stride]), i + 1 + stride
        for x in range(stride):
            a = line[x - 4] if x >= 4 else 0
            b = prev[x]
            c = prev[x - 4] if x >= 4 else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + b) & 255
            elif f == 3:
                line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc
                                      else (b if pb <= pc else c))) & 255
        rows.append(bytes(line))
        prev = line
    return w, h, rows


def tinted(rows):
    out = []
    for row in rows:
        line = bytearray(row)
        for x in range(0, len(line), 4):
            line[x], line[x + 1], line[x + 2] = INK
        out.append(bytes(line))
    return out


def write_rgba(path, w, h, rows):
    raw = b"".join(b"\x00" + r for r in rows)

    def chunk(kind, data):
        return (len(data).to_bytes(4, "big") + kind + data
                + (zlib.crc32(kind + data) & 0xffffffff).to_bytes(4, "big"))

    ihdr = w.to_bytes(4, "big") + h.to_bytes(4, "big") + bytes((8, 6, 0, 0, 0))
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
                           + chunk(b"IDAT", zlib.compress(raw, 9))
                           + chunk(b"IEND", b""))


def main():
    w, h, rows = read_rgba(SRC)
    want = tinted(rows)
    if "--check" in sys.argv:
        if not os.path.exists(DST):
            print("ci/wordmark.py: docs/keal-view-dark.png is missing.")
            print("  Run python3 ci/wordmark.py and commit it.")
            sys.exit(1)
        gw, gh, got = read_rgba(DST)
        if (gw, gh, got) != (w, h, want):
            print("ci/wordmark.py: docs/keal-view-dark.png is not the wordmark "
                  "recoloured.")
            print("  Run python3 ci/wordmark.py and commit what changes.")
            sys.exit(1)
        print("the dark wordmark is the light one, recoloured")
        return
    write_rgba(DST, w, h, want)
    print("wrote docs/keal-view-dark.png (%dx%d)" % (w, h))


if __name__ == "__main__":
    main()
