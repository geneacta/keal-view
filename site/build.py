#!/usr/bin/env python3
"""Builds the whole keal-view site, in English and in French.

    python3 site/build.py

Every page is generated: the landing page, the gallery, the architecture
page, the "coming from" guides, and the reference documents converted from
`docs/*.md`. English lands in `site/`, French in `site/fr/`, and each page
links to its counterpart.

No dependencies and no build step beyond this file: the output is plain HTML
that GitHub Pages serves as it stands, which is also why it is committed
rather than built in the workflow.

The prose lives in `content.py`. This file is the machinery.
"""

import html
import os
import re
import shutil
import sys

import content as C

# Every file this reads and writes is UTF-8 and every line it writes ends in
# `\n`, and both have to be said out loud: Python opens text files in the
# machine's locale codepage, which on a French Windows is cp1252, where the
# first `→` in a page raises — after the file has been truncated for writing,
# which turns a failed build into a deleted page.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")

# The window glyph in the corner: the thing this framework makes. Inline
# rather than a file, so there is no binary asset to keep in step with the
# palette it is drawn in.
MARK = ('<svg width="24" height="24" viewBox="0 0 26 26" fill="none" aria-hidden="true">'
        '<rect x="1.6" y="3.6" width="22.8" height="18.8" rx="4.5" stroke="#3b82f6" '
        'stroke-width="2"/><path d="M2 9.6h22" stroke="#3b82f6" stroke-width="2"/>'
        '<circle cx="6.2" cy="6.6" r="1.25" fill="#3b82f6"/></svg>')

FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 26 26'%3E"
           "%3Crect x='1.6' y='3.6' width='22.8' height='18.8' rx='4.5' fill='none' "
           "stroke='%233b82f6' stroke-width='2'/%3E%3Cpath d='M2 9.6h22' stroke='%233b82f6' "
           "stroke-width='2'/%3E%3Ccircle cx='6.2' cy='6.6' r='1.25' fill='%233b82f6'/%3E%3C/svg%3E")


# ---- a small markdown converter -----------------------------------------
# Enough of markdown for the documents this repository actually writes. It is
# deliberately not a general one: a general converter would be larger than
# the pages it produces, and every construct it did not meet here would be
# untested.

def slug(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "section"


def inline(text, base=""):
    """Inline markdown, on text that has already been escaped.

    Code spans and links are found in one pass rather than one after the
    other. Splitting on backticks first — which is the obvious way to write
    this — silently loses every link whose label is code, and the documents
    here are full of them: `[`examples/tour.keal`](../examples/tour.keal)`
    came out as its own source.
    """
    out, pos = [], 0
    for m in _TOKEN.finditer(text):
        out.append(_emph(text[pos:m.start()]))
        if m.group(1) is not None:
            out.append("<code>%s</code>" % m.group(1))
        else:
            out.append(_link(m.group(2), m.group(3), base))
        pos = m.end()
    out.append(_emph(text[pos:]))
    return "".join(out)


# Either a code span, or a link whose label may itself hold one.
_TOKEN = re.compile(r"`([^`]+)`|\[((?:[^\[\]`]|`[^`]*`)+)\]\(([^)\s]+)\)")


def _emph(text):
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", text)


def _label(text):
    """A link's label: code spans and emphasis, but no nested link."""
    parts = re.split(r"`([^`]+)`", text)
    return "".join("<code>%s</code>" % p if i % 2 else _emph(p)
                   for i, p in enumerate(parts))


# The three documents that have a page here. Everything else a document links
# to is a file in the repository, and on the site that has to point at the
# repository rather than at a path that does not exist beside the HTML.
_PAGES = {"docs/guide.md": "guide.html",
          "docs/widgets.md": "widgets.html",
          "docs/porting-test.md": "porting.html"}


def _link(label, href, base):
    if not href.startswith(("http://", "https://", "#", "mailto:")):
        # Resolve against the document's own directory, the way a reader of
        # the markdown would: `../examples/x.keal` inside `docs/` is
        # `examples/x.keal` from the root, not a sibling of the HTML.
        path = os.path.normpath(os.path.join(base, href)).replace(os.sep, "/")
        href = _PAGES.get(path, C.VIEW_REPO + "/blob/main/" + path)
    return '<a href="%s">%s</a>' % (html.escape(href, quote=True), _label(label))


def markdown(text, base=""):
    """Returns (html, table-of-contents) for one document."""
    lines = text.split("\n")
    out, toc = [], []
    i, n = 0, len(lines)
    para = []

    def flush():
        if para:
            out.append("<p>%s</p>" % inline(html.escape("\n".join(para)), base))
            del para[:]

    while i < n:
        line = lines[i]

        if line.startswith("```"):
            flush()
            i += 1
            block = []
            while i < n and not lines[i].startswith("```"):
                block.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>%s</code></pre>" % html.escape("\n".join(block)))
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush()
            level, title = len(m.group(1)), m.group(2).strip()
            # The document's own H1 is the page title; the site prints its
            # own, so it is not repeated in the body.
            anchor = slug(re.sub(r"[`*]", "", title))
            if level <= 2:
                toc.append((anchor, re.sub(r"[`*]", "", title)))
            out.append('<h%d id="%s">%s</h%d>' % (level, anchor, inline(html.escape(title), base), level))
            i += 1
            continue

        if re.match(r"^\s*([-*+]|\d+\.)\s+", line):
            flush()
            ordered = bool(re.match(r"^\s*\d+\.\s+", line))
            items, cur = [], None
            while i < n and (re.match(r"^\s*([-*+]|\d+\.)\s+", lines[i])
                             or (cur is not None and lines[i].strip()
                                 and lines[i].startswith((" ", "\t")))):
                mm = re.match(r"^\s*(?:[-*+]|\d+\.)\s+(.*)$", lines[i])
                if mm:
                    if cur is not None:
                        items.append(cur)
                    cur = mm.group(1)
                else:
                    cur = cur + "\n" + lines[i].strip()
                i += 1
            if cur is not None:
                items.append(cur)
            tag = "ol" if ordered else "ul"
            out.append("<%s>%s</%s>" % (
                tag, "".join("<li>%s</li>" % inline(html.escape(it), base) for it in items), tag))
            continue

        if line.startswith(">"):
            flush()
            quote = []
            while i < n and lines[i].startswith(">"):
                quote.append(lines[i].lstrip("> ").rstrip())
                i += 1
            out.append("<blockquote>%s</blockquote>" % inline(html.escape(" ".join(quote)), base))
            continue

        if line.startswith("|") and i + 1 < n and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            flush()
            rows = []
            while i < n and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            head, body = rows[0], rows[2:]
            th = "".join("<th>%s</th>" % inline(html.escape(c), base) for c in head)
            tr = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(html.escape(c), base)
                                                 for c in r) for r in body)
            out.append('<div class="tablewrap"><table><thead><tr>%s</tr></thead>'
                       "<tbody>%s</tbody></table></div>" % (th, tr))
            continue

        if re.match(r"^\s*(---+|\*\*\*+|___+)\s*$", line):
            flush()
            out.append("<hr>")
            i += 1
            continue

        if not line.strip():
            flush()
            i += 1
            continue

        para.append(line.strip())
        i += 1

    flush()
    return "".join(out), toc


# ---- the page -----------------------------------------------------------

def page(lang, filename, title, description, body, active=None):
    prefix = "" if lang == "en" else "../"
    other = ("fr/" + filename) if lang == "en" else ("../" + filename)
    links = "".join(
        '<a href="%s"%s>%s</a>' % (href, ' class="tab-active"' if href == active else "", label)
        for href, label in C.NAV[lang])
    foot = C.FOOTER[lang]
    cols = []
    for head, items in foot["cols"]:
        rows = "".join('<a href="%s">%s</a>' % (html.escape(h, quote=True), html.escape(t))
                       for h, t in items)
        cols.append('<div class="fcol"><span class="h">%s</span>%s</div>' % (head, rows))

    return """<!doctype html>
<html lang="%(lang)s">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<link rel="canonical" href="%(canonical)s">
<link rel="alternate" hreflang="en" href="%(alt_en)s">
<link rel="alternate" hreflang="fr" href="%(alt_fr)s">
<link rel="alternate" hreflang="x-default" href="%(alt_en)s">
<meta property="og:type" content="website">
<meta property="og:site_name" content="keal-view">
<meta property="og:locale" content="%(locale)s">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(canonical)s">
<meta property="og:image" content="%(image)s">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%(title)s">
<meta name="twitter:description" content="%(desc)s">
<meta name="twitter:image" content="%(image)s">
<link rel="icon" href="%(favicon)s">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="%(prefix)sstyle.css">
</head>
<body>
<div class="wrap">
<nav class="nav">
  <div class="nav-left">
    <a class="mark" href="index.html">%(mark)s<span class="wm">keal-view</span></a>
    <div class="nav-links">%(links)s</div>
  </div>
  <div class="nav-right">
    <span class="badge">%(version)s</span>
    <a class="btn-lang" href="%(other)s">%(other_label)s</a>
    <a class="btn-keal" href="%(keal_site)s">Keal</a>
    <a class="btn-gh" href="%(repo)s">GitHub</a>
  </div>
</nav>
%(body)s
<footer>
  <div><p class="base">%(base)s</p></div>
  %(cols)s
</footer>
</div>
<script src="%(prefix)ssite.js"></script>
</body>
</html>
""" % {
        "lang": lang,
        "title": html.escape(title),
        "desc": html.escape(description),
        "prefix": prefix,
        "canonical": C.BASE_URL + ("" if lang == "en" else "fr/") + filename,
        "alt_en": C.BASE_URL + filename,
        "alt_fr": C.BASE_URL + "fr/" + filename,
        "locale": "en_GB" if lang == "en" else "fr_FR",
        "image": C.BASE_URL + "assets/studio.png",
        "favicon": FAVICON,
        "mark": MARK,
        "links": links,
        "version": "v" + C.VERSION,
        "other": other,
        "other_label": C.SWITCH[lang],
        "keal_site": C.KEAL_SITE if lang == "en" else C.KEAL_SITE + "fr/",
        "repo": C.VIEW_REPO,
        "body": body,
        "base": foot["base"],
        "cols": "".join(cols),
    }


def write(lang, filename, text):
    out_dir = SITE if lang == "en" else os.path.join(SITE, "fr")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, filename), "w", encoding="utf-8", newline="") as f:
        f.write(text)


def cwin(name, code):
    return ('<div class="cwin"><div class="cwin-bar"><span class="f">%s</span></div>'
            "<pre>%s</pre></div>" % (html.escape(name), code))


def shot(lang, filename, alt, caption, prefix=""):
    return ('<div class="shot"><img src="%sassets/%s" alt="%s" loading="lazy">'
            '<div class="cap">%s</div></div>'
            % (prefix, filename, html.escape(alt), caption))


# ---- the pages ----------------------------------------------------------

def home(lang):
    L = C.HOME[lang]
    p = "" if lang == "en" else "../"

    bars = []
    for label, value, width, quiet in L["bars"]:
        bars.append('<div class="barrow"><span class="bl">%s</span>'
                    '<span class="bar%s"><div data-w="%s"></div></span>'
                    '<span class="bv">%s</span></div>'
                    % (label, " quiet" if quiet else "", width, value))

    cards = "".join('<div class="card"><h3>%s</h3><p>%s</p></div>' % (t, b) for t, b in L["cards"])

    rows = "".join("<tr><td><b>%s</b></td><td><code>%s</code></td><td>%s</td></tr>"
                   % r for r in L["plat_rows"])
    head = "".join("<th>%s</th>" % h for h in L["plat_head"])

    body = """
<section class="hero">
  <div>
    <div class="pill"><span class="dot"></span>%(pill)s</div>
    <h1>%(h1)s</h1>
    <p class="sub">%(sub)s</p>
    <div class="ctas"><a class="cta" href="guide.html">%(cta1)s</a>
      <a class="cta-line" href="gallery.html">%(cta2)s</a></div>
  </div>
  <div>%(hello)s</div>
</section>

<section class="band">%(shot)s</section>

<section class="duo">
  <div>
    <h2>%(bars_h)s</h2>
    <p>%(bars_p)s</p>
    <p class="barcap">%(barcap)s</p>
  </div>
  <div class="bars">%(bars)s</div>
</section>

<section class="band">
  <h2>%(why_h)s</h2>
  <p class="lede">%(why_p1)s</p>
  %(extern)s
  <p class="lede">%(why_p2)s</p>
</section>

<section class="band"><h2>%(cards_h)s</h2></section>
<section class="cards">%(cards)s</section>

<section class="duo">
  <div><h2>%(dock_h)s</h2><p>%(dock_p1)s</p><p>%(dock_p2)s</p></div>
  <div>%(dock)s</div>
</section>

<section class="band">
  <h2>%(plat_h)s</h2>
  <p class="lede">%(plat_p)s</p>
  <div class="tablewrap"><table><thead><tr>%(head)s</tr></thead><tbody>%(rows)s</tbody></table></div>
  <p class="lede">%(plat_after)s</p>
  <p><a class="cta-line" href="porting.html">%(plat_link)s</a></p>
</section>

<section class="duo">
  <div><h2>%(start_h)s</h2><p>%(start_p)s</p></div>
  <div>%(start)s</div>
</section>

<section class="band">
  <h2>%(free_h)s</h2>
  <p class="lede">%(free_p)s</p>
  %(free)s
</section>
""" % {
        "pill": L["pill"], "h1": L["h1"], "sub": L["sub"],
        "cta1": L["cta1"], "cta2": L["cta2"],
        "hello": cwin(L["codefile"], C.HELLO_CODE),
        "shot": shot(lang, "studio.png", L["shot_alt"], L["shot_cap"], p),
        "bars_h": L["bars_h"], "bars_p": L["bars_p"], "barcap": L["barcap"],
        "bars": "".join(bars),
        "why_h": L["why_h"], "why_p1": L["why_p1"], "why_p2": L["why_p2"],
        "extern": cwin("src/ffi.keal",
                       '<span class="k">extern func</span> kvPxSet(x: <span class="t">Int</span>, '
                       'y: <span class="t">Int</span>, argb: <span class="t">Int</span>): '
                       '<span class="t">Int</span> = <span class="s">"kv_set"</span>'),
        "cards_h": L["cards_h"], "cards": cards,
        "dock_h": L["dock_h"], "dock_p1": L["dock_p1"], "dock_p2": L["dock_p2"],
        "dock": cwin("examples/studio.keal", C.DOCK_CODE),
        "plat_h": L["plat_h"], "plat_p": L["plat_p"], "head": head, "rows": rows,
        "plat_after": L["plat_after"], "plat_link": L["plat_link"],
        "start_h": L["start_h"], "start_p": L["start_p"],
        "start": cwin(L["start_win"], C.START_CODE),
        "free_h": L["free_h"], "free_p": L["free_p"],
        "free": cwin(L["start_win"], C.FREE_CODE),
    }
    return page(lang, "index.html", L["title"], L["desc"], body, active="index.html")


def gallery_page(lang):
    L = C.GALLERY[lang]
    p = "" if lang == "en" else "../"
    wide, narrow = [], []
    for filename, name, source, caption, is_wide in L["shots"]:
        cap = "<b>%s</b> — <code>%s</code><br>%s" % (name, source, caption)
        block = shot(lang, filename, name, cap, p)
        (wide if is_wide else narrow).append(block)
    body = ('<section class="band"><h1>%s</h1><p class="lede">%s</p></section>'
            '<section class="grid2 wide">%s</section>'
            '<section class="grid2">%s</section>'
            '<section class="band"><h2>%s</h2><p class="lede">%s</p>%s</section>'
            % (L["title"], L["lede"], "".join(wide), "".join(narrow),
               L["how_h"], L["how_p"], cwin("shell", C.FREE_CODE)))
    return page(lang, "gallery.html", "keal-view — " + L["title"], L["lede"][:180], body,
                active="gallery.html")


def architecture(lang):
    L = C.ARCH[lang]
    items = "".join("<li>%s</li>" % it for it in L["notyet"])
    body = """
<section class="band"><h1>%(title)s</h1><p class="lede">%(lede)s</p></section>

<section class="duo">
  <div><h2>%(b_h)s</h2><p>%(b_p1)s</p><p>%(b_p2)s</p></div>
  <div>%(tree)s</div>
</section>

<section class="band">
  <h2>%(frame_h)s</h2>
  <p class="lede">%(frame_p1)s</p>
  <p class="lede">%(frame_p2)s</p>
  <p class="lede">%(frame_p3)s</p>
</section>

<section class="band">
  <h2>%(lang_h)s</h2>
  <p class="lede">%(lang_p)s</p>
  <h2 style="margin-top:44px">%(found_h)s</h2>
  <p class="lede">%(found_p)s</p>
  <p><a class="cta-line" href="%(keal)s">%(found_link)s</a></p>
</section>

<section class="band">
  <h2>%(notyet_h)s</h2>
  <div class="prose"><ul>%(items)s</ul></div>
</section>
""" % {
        "title": L["title"], "lede": L["lede"],
        "b_h": L["b_h"], "b_p1": L["b_p1"], "b_p2": L["b_p2"],
        "tree": cwin("the files", C.TREE_CODE),
        "frame_h": L["frame_h"], "frame_p1": L["frame_p1"],
        "frame_p2": L["frame_p2"], "frame_p3": L["frame_p3"],
        "lang_h": L["lang_h"], "lang_p": L["lang_p"],
        "found_h": L["found_h"], "found_p": L["found_p"], "found_link": L["found_link"],
        "keal": C.KEAL_SITE if lang == "en" else C.KEAL_SITE + "fr/",
        "notyet_h": L["notyet_h"], "items": items,
    }
    return page(lang, "architecture.html", "keal-view — " + L["title"], L["lede"], body,
                active="architecture.html")


def coming_index(lang):
    L = C.COMING[lang]
    cards = []
    for tk in C.TOOLKITS:
        blurb = tk["blurb_en"] if lang == "en" else tk["blurb_fr"]
        cards.append('<a class="card" href="%s.html"><h3>%s</h3><p>%s</p></a>'
                     % (tk["slug"], html.escape(tk["name"]), html.escape(blurb)))
    body = ('<section class="band"><h1>%s</h1><p class="lede">%s</p>'
            '<div class="callout"><span class="st">✦</span><p>%s</p></div></section>'
            '<section class="cards">%s</section>'
            % (L["title"], L["lede"], L["note"], "".join(cards)))
    return page(lang, "coming-from.html", "keal-view — " + L["title"], L["lede"][:180], body,
                active="coming-from.html")


def toolkit_page(lang, tk):
    name = tk["name"]
    intro = tk["intro_en"] if lang == "en" else tk["intro_fr"]
    title = ("Coming from %s" if lang == "en" else "Je viens de %s") % name
    theirs_h = name
    ours_h = "keal-view"
    rows = []
    for a, b_en, b_fr in tk["rows"]:
        rows.append("<tr><td><code>%s</code></td><td><code>%s</code></td></tr>"
                    % (a, b_en if lang == "en" else b_fr))
    notes = []
    for t_en, t_fr, b_en, b_fr in tk["notes"]:
        notes.append('<div class="card"><h3>%s</h3><p>%s</p></div>'
                     % (t_en if lang == "en" else t_fr, b_en if lang == "en" else b_fr))
    back = "All the toolkits" if lang == "en" else "Toutes les boîtes à outils"
    surprises = "What will surprise you" if lang == "en" else "Ce qui va vous surprendre"
    body = ('<section class="band"><h1>%s</h1><p class="lede">%s</p>'
            '<div class="tablewrap"><table><thead><tr><th>%s</th><th>%s</th></tr></thead>'
            "<tbody>%s</tbody></table></div></section>"
            '<section class="band"><h2>%s</h2></section>'
            '<section class="cards">%s</section>'
            '<section class="band"><a class="cta-line" href="coming-from.html">← %s</a></section>'
            % (title, intro, theirs_h, ours_h, "".join(rows), surprises, "".join(notes), back))
    return page(lang, tk["slug"] + ".html", "keal-view — " + title, intro[:180], body,
                active="coming-from.html")


def sidebar_html(lang, filename):
    parts = []
    for group, items in C.SIDEBAR[lang]:
        parts.append('<div class="grp">%s</div>' % group)
        for href, label in items:
            cls = ' class="on"' if href == filename else ""
            parts.append('<a href="%s"%s>%s</a>' % (href, cls, html.escape(label)))
    return '<div class="dside">%s</div>' % "".join(parts)


def doc_page(lang, source, filename, title):
    with open(os.path.join(ROOT, source), encoding="utf-8") as f:
        text = f.read()
    # The document's own first heading becomes the page's H1, printed by the
    # site rather than by the converter, so it is not shown twice.
    text = re.sub(r"\A#\s+[^\n]*\n", "", text)
    body, toc = markdown(text, os.path.dirname(source))
    note = ""
    if lang == "fr":
        note = '<div class="callout"><span class="st">✦</span><p>%s</p></div>' % C.FR_DOC_NOTE
    crumb = ('<div class="crumb"><a href="index.html">keal-view</a> <span class="sl">/</span> '
             '<span class="here">%s</span></div>' % html.escape(title))
    head = "ON THIS PAGE" if lang == "en" else "SUR CETTE PAGE"
    entries = "".join('<a href="#%s">%s</a>' % (a, html.escape(t)) for a, t in toc)
    tocbox = ('<div class="dtoc"><div class="h">%s</div><div class="dtoc-items">%s</div></div>'
              % (head, entries))
    layout = ('<div class="dgrid">%s<div class="dmain prose">%s%s<h1>%s</h1>%s</div>%s</div>'
              % (sidebar_html(lang, filename), crumb, note, html.escape(title), body, tocbox))
    return page(lang, filename, "keal-view — " + title, title, layout, active=filename)


# ---- assets and the small files -----------------------------------------

def copy_assets():
    out = os.path.join(SITE, "assets")
    os.makedirs(out, exist_ok=True)
    copied = []
    for name in sorted(os.listdir(os.path.join(ROOT, "docs"))):
        if name.endswith(".png"):
            shutil.copyfile(os.path.join(ROOT, "docs", name), os.path.join(out, name))
            copied.append(name)
    return copied


def small_files(pages):
    with open(os.path.join(SITE, "robots.txt"), "w", encoding="utf-8", newline="") as f:
        f.write("User-agent: *\nAllow: /\nSitemap: %ssitemap.xml\n" % C.BASE_URL)
    urls = []
    for filename in pages:
        for lang in ("en", "fr"):
            loc = C.BASE_URL + ("" if lang == "en" else "fr/") + filename
            urls.append("  <url><loc>%s</loc></url>" % loc)
    with open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8", newline="") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                + "\n".join(urls) + "\n</urlset>\n")


# ---- main ---------------------------------------------------------------

def main():
    pages = []
    for lang in ("en", "fr"):
        write(lang, "index.html", home(lang))
        write(lang, "gallery.html", gallery_page(lang))
        write(lang, "architecture.html", architecture(lang))
        write(lang, "coming-from.html", coming_index(lang))
        for tk in C.TOOLKITS:
            write(lang, tk["slug"] + ".html", toolkit_page(lang, tk))
        for source, filename, t_en, t_fr, _group in C.DOC_PAGES:
            write(lang, filename, doc_page(lang, source, filename,
                                           t_en if lang == "en" else t_fr))
    pages = ["index.html", "gallery.html", "architecture.html", "coming-from.html"]
    pages += [tk["slug"] + ".html" for tk in C.TOOLKITS]
    pages += [f for _s, f, _a, _b, _g in C.DOC_PAGES]

    assets = copy_assets()
    small_files(pages)
    print("%d pages in each language, %d assets" % (len(pages), len(assets)))
    print("  en: %s" % SITE)
    print("  fr: %s" % os.path.join(SITE, "fr"))


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
