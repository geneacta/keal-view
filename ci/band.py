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
SHIELD = ("https://img.shields.io/badge/%s-%s-3b82f6"
          "?style=flat-square&labelColor=2b2b2b")


def read(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return f.read()


def version():
    v = read("VERSION").strip()
    if not v:
        raise SystemExit("ci/band.py: VERSION is empty")
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


def band():
    one, lo, hi = share()
    pct = ("%d" % one) if one is not None else ("%d--%d" % (lo, hi))
    repo = "https://github.com/geneacta/keal-view"
    return "\n".join([
        START,
        '<p align="center">',
        '  <a href="%s/releases"><img alt="version" src="%s"></a>'
        % (repo, SHIELD % ("version", version())),
        '  <a href="%s/tree/main/src"><img alt="written in Keal" src="%s"></a>'
        % (repo, SHIELD % ("written%20in%20Keal", pct + "%25")),
        "</p>",
        END,
    ])


def main():
    path = os.path.join(ROOT, "README.md")
    text = read("README.md")
    if START not in text or END not in text:
        raise SystemExit("ci/band.py: README.md has no %s … %s markers" % (START, END))
    now = text[:text.index(START)] + band() + text[text.index(END) + len(END):]
    if "--check" in sys.argv:
        if now != text:
            print("ci/band.py: the badge band in README.md is out of date.")
            print("  Run python3 ci/band.py and commit what changes.")
            sys.exit(1)
        print("the badge band says what the repository says")
        return
    if now == text:
        print("the badge band was already current")
        return
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(now)
    print("rewrote the badge band in README.md")


if __name__ == "__main__":
    main()
