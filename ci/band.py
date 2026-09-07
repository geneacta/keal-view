#!/usr/bin/env python3
"""Keeps the badge band at the top of README.md current.

    python3 ci/band.py            rewrite it
    python3 ci/band.py --check    fail if it would change

Two numbers, both counted here rather than remembered: the version, from
`VERSION`, which the site reads too so that the badge and the page cannot say
different things; and the share of this framework that is Keal, which is the
README's own headline claim and the one a reader is most entitled to check.

That share is a **range**, and the range is the honest form of it: the C is
`kv.h` plus one backend of three, and the three are not the same size. Quoting
the smallest was how this number came to say 89 % when the platform you are on
decides whether it is 87 or 89.

Everything counted here is in this repository, so it can only go stale when
somebody here changes something — which is exactly when a gate should speak.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
START = "<!-- keal-view-band:start -->"
END = "<!-- keal-view-band:end -->"
# The same two numbers again, spelled out. The badge said 89–91 % and the table
# under it said where that came from — and only the badge was generated, so the
# table went stale the first time a file grew and nothing said so. Two claims
# from one count means one of them is a copy, and a copy is what drifts.
TSTART = "<!-- keal-view-count:start -->"
TEND = "<!-- keal-view-count:end -->"
# The badges' look belongs to whoever owns the README, not to this script:
# alignment, style and colour are copied from what is there rather than chosen
# here. What this script owns is the two numbers in them, which is the only
# part that can be wrong.
SHIELD = "https://img.shields.io/badge/%s-%s-%s?style=flat"
ALIGN = "right"


def read(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return f.read()


def version():
    v = read("VERSION").strip()
    if not v:
        raise SystemExit("ci/band.py: VERSION is empty")
    return v


def keal_version():
    """Which Keal this is built against, from `KEAL_VERSION`.

    Declared in a file because it was declared nowhere: no manifest, no
    pinned tag, no workflow that fetches one. Beside `VERSION`, which this
    repository already keeps for its own, and read the same way — a number
    kept in a second place is a number that is wrong the day the first one
    moves.
    """
    v = read("KEAL_VERSION").strip()
    if not v:
        raise SystemExit("ci/band.py: KEAL_VERSION is empty")
    return v


def counts():
    """Keal, and the C — the header plus each backend, separately."""
    keal = len(read("keal-view.keal").splitlines())
    src = os.path.join(ROOT, "src")
    keal += sum(len(read("src/" + n).splitlines())
                for n in sorted(os.listdir(src)) if n.endswith(".keal"))
    header = len(read("runtime/kv.h").splitlines())
    backends = [len(read("runtime/" + n).splitlines())
                for n in sorted(os.listdir(os.path.join(ROOT, "runtime")))
                if n.startswith("kv_")]
    return keal, header, backends


def share():
    keal, header, backends = counts()
    lo = round(keal * 100 / (keal + header + max(backends)))
    hi = round(keal * 100 / (keal + header + min(backends)))
    return (lo if lo == hi else None), lo, hi


def table():
    """The lines, and where the C is — the badge's own working, shown."""
    keal, header, backends = counts()
    one, lo, hi = share()
    names = {"kv_cocoa.m": "Cocoa", "kv_x11.c": "X11", "kv_win32.c": "Win32"}
    each = sorted(
        (len(read("runtime/" + n).splitlines()), names.get(n, n))
        for n in sorted(os.listdir(os.path.join(ROOT, "runtime")))
        if n.startswith("kv_"))
    c_lo, c_hi = header + min(backends), header + max(backends)
    c = "%d" % c_lo if c_lo == c_hi else "%d-%d" % (c_lo, c_hi)
    pct = ("%d %%" % one) if one is not None else ("%d to %d %%" % (lo, hi))
    rest = ("%d %%" % (100 - lo)) if one is not None \
        else ("%d to %d %%" % (100 - hi, 100 - lo))
    return "\n".join([
        TSTART,
        "```",
        "              lines    what it is",
        "  Keal        %6d   the whole framework: rasteriser, fonts, layout," % keal,
        "                       widgets, theme, docking, menus, pictures, the run loop",
        "  C         %8s   one window, one event queue, and inline accessors:" % c,
        # Two lines rather than one, because the first would otherwise run
        # past the width of everything around it in a plain-text block that
        # nothing wraps.
        "                       kv.h (%d) plus one backend of three — %s %d,"
        % (header, each[0][1], each[0][0]),
        "                       %s"
        % ", ".join("%s %d" % (nm, n) for n, nm in each[1:]),
        "```",
        "",
        "**%s of a running keal-view program is Keal**, depending on which" % pct,
        "backend it was built against, and none of the other %s puts a pixel" % rest,
        "anywhere. Both this and the badge above are counted by `ci/band.py` from",
        "these same files, so neither can drift from them — or from each other,",
        "which is the way a number in a README usually goes wrong.",
        TEND,
    ])


def band():
    one, lo, hi = share()
    pct = ("%d" % one) if one is not None else ("%d--%d" % (lo, hi))
    repo = "https://github.com/geneacta/keal-view"
    return "\n".join([
        START,
        '<p align="%s">' % ALIGN,
        '  <a href="%s/releases"><img alt="version" src="%s"></a>'
        % (repo, SHIELD % ("version", version(), "blue")),
        '  <a href="%s/tree/main/src"><img alt="written in Keal" src="%s"></a>'
        % (repo, SHIELD % ("written%20in%20Keal", pct + "%25", "brightgreen")),
        '  <a href="%s"><img alt="Keal" src="%s"></a>'
        % ("https://github.com/geneacta/keal/releases/tag/v" + keal_version(),
           SHIELD % ("Keal", keal_version(), "orange")),
        "</p>",
        END,
    ])


def main():
    path = os.path.join(ROOT, "README.md")
    text = read("README.md")
    # Counted, not just found. This script rewrites between the *first* start
    # and the *first* end, so a second pair further down is a region it would
    # never touch and never mention — which is how an empty duplicate of these
    # two lines sat in the README through a green run of the check that owns
    # them. A gate that cannot see a thing should refuse rather than pass.
    for a, b in ((START, END), (TSTART, TEND)):
        if a not in text or b not in text:
            raise SystemExit("ci/band.py: README.md has no %s … %s markers" % (a, b))
        if text.count(a) != 1 or text.count(b) != 1:
            raise SystemExit("ci/band.py: README.md has %d %s and %d %s; there must "
                             "be exactly one of each."
                             % (text.count(a), a, text.count(b), b))
    now = text[:text.index(START)] + band() + text[text.index(END) + len(END):]
    now = now[:now.index(TSTART)] + table() + now[now.index(TEND) + len(TEND):]
    if "--check" in sys.argv:
        if now != text:
            print("ci/band.py: what README.md counts is out of date.")
            print("  Run python3 ci/band.py and commit what changes.")
            sys.exit(1)
        print("the badge and the table say what the repository says")
        return
    if now == text:
        print("the badge and the table were already current")
        return
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(now)
    print("rewrote what README.md counts")


if __name__ == "__main__":
    main()
