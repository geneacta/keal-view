#!/usr/bin/env python3
"""Everything the keal-view site says, in English and in French.

The machinery is in `build.py`; this file is the prose. They are separate for
the same reason the Keal site separates them: a change of wording should not
mean reading a page generator, and a change to the generator should not mean
scrolling past forty paragraphs to find it.

Every claim here is meant to be checkable against the repository. Where a
number appears — lines of code, assertions, defects found — it is the number
in the README at the time of writing, and the README is the thing to correct
first if it drifts.
"""

import os as _os
# The one place a version lives, read rather than repeated: `ci/band.py` puts
# the same number on the README's badge, so the page and the badge cannot
# disagree.
with open(_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                        "VERSION"), encoding="utf-8") as _f:
    VERSION = _f.read().strip()
BASE_URL = "https://geneacta.github.io/keal-view/"
KEAL_REPO = "https://github.com/geneacta/keal"
KEAL_SITE = "https://geneacta.github.io/keal/"
VIEW_REPO = "https://github.com/geneacta/keal-view"

# ---------------------------------------------------------------- chrome ---

NAV = {
    "en": [("index.html", "Home"), ("guide.html", "Guide"), ("widgets.html", "Reference"),
           ("gallery.html", "Gallery"), ("architecture.html", "Architecture"),
           ("coming-from.html", "Coming from…"), ("porting.html", "Porting")],
    "fr": [("index.html", "Accueil"), ("guide.html", "Le guide"), ("widgets.html", "Référence"),
           ("gallery.html", "Galerie"), ("architecture.html", "Architecture"),
           ("coming-from.html", "Je viens de…"), ("porting.html", "Portage")],
}

SWITCH = {"en": "Français", "fr": "English"}

FOOTER = {
    "en": {
        "base": "keal-view — application windows written in Keal, where the drawing is Keal too. "
                "Apache 2.0.",
        "cols": [
            ("PROJECT", [("index.html", "Home"), ("gallery.html", "Gallery"),
                         ("architecture.html", "Architecture"),
                         (VIEW_REPO, "keal-view on GitHub")]),
            ("DOCS", [("guide.html", "The guide"), ("widgets.html", "The reference"),
                      ("porting.html", "Porting to a new platform"),
                      ("coming-from.html", "Coming from another toolkit")]),
            ("KEAL", [(KEAL_SITE, "The language's site"), (KEAL_REPO, "Keal on GitHub"),
                      (KEAL_SITE + "docs.html", "Language docs"),
                      (KEAL_SITE + "tour.html", "The language tour")]),
        ],
    },
    "fr": {
        "base": "keal-view — des fenêtres d'application écrites en Keal, où le dessin est lui aussi "
                "du Keal. Apache 2.0.",
        "cols": [
            ("PROJET", [("index.html", "Accueil"), ("gallery.html", "Galerie"),
                        ("architecture.html", "Architecture"),
                        (VIEW_REPO, "keal-view sur GitHub")]),
            ("DOCS", [("guide.html", "Le guide"), ("widgets.html", "La référence"),
                      ("porting.html", "Porter sur une plateforme"),
                      ("coming-from.html", "Je viens d'une autre boîte à outils")]),
            ("KEAL", [(KEAL_SITE + "fr/", "Le site du langage"), (KEAL_REPO, "Keal sur GitHub"),
                      (KEAL_SITE + "fr/docs.html", "Docs du langage"),
                      (KEAL_SITE + "fr/tour.html", "Le tour du langage")]),
        ],
    },
}

# ------------------------------------------------------------- documents ---
# Converted from the repository's own markdown. The body stays in English in
# both languages, as on the Keal site: these are working documents, the
# repository's language is English, and a translation that drifts from the
# file it was made from is worse than an honest note saying which language it
# is in. The pages the site writes itself exist fully in both.

DOC_PAGES = [
    ("docs/guide.md", "guide.html", "The guide", "Le guide", "READ FIRST"),
    ("docs/widgets.md", "widgets.html", "The reference", "La référence", "READ FIRST"),
    ("docs/porting-test.md", "porting.html", "Testing a new backend",
     "Tester un nouveau backend", "PLATFORMS"),
]

SIDEBAR = {
    "en": [("GUIDE", [("guide.html", "The guide"), ("widgets.html", "The reference"),
                      ("architecture.html", "Architecture")]),
           ("PLATFORMS", [("porting.html", "Testing a new backend")]),
           ("ELSEWHERE", [("gallery.html", "Gallery"),
                          ("coming-from.html", "Coming from…")])],
    "fr": [("GUIDE", [("guide.html", "Le guide"), ("widgets.html", "La référence"),
                      ("architecture.html", "Architecture")]),
           ("PLATEFORMES", [("porting.html", "Tester un backend")]),
           ("AILLEURS", [("gallery.html", "Galerie"),
                         ("coming-from.html", "Je viens de…")])],
}

FR_DOC_NOTE = ('Ce document est rédigé en anglais, la langue de travail du dépôt, et il est '
               'converti tel quel depuis le fichier qui fait foi. Les pages que le site écrit '
               'lui-même — l\'accueil, la galerie, l\'architecture et les guides « je viens '
               'de… » — existent intégralement dans les deux langues.')

# --------------------------------------------------------------- landing ---

HOME = {
    "en": {
        "title": "keal-view — application windows, written in Keal",
        "desc": "A cross-platform GUI framework in which the drawing is Keal: the rasteriser, "
                "the TrueType engine, the layout, the widgets and the docking are all .keal "
                "files. The C underneath opens a window and shows a finished buffer.",
        "pill": "Verified on macOS, Windows and Linux",
        "h1": "The drawing is Keal.",
        "sub": "Not bindings to a toolkit, not a wrapper round a C canvas. The rasteriser, the "
               "TrueType engine, the layout, the widgets, the theme and the docking are "
               "<code>.keal</code> files. The C underneath opens a window, reports what the user "
               "did, and puts a finished buffer of pixels on the screen. It does not draw "
               "anything.",
        "cta1": "Read the guide →",
        "cta2": "Every widget there is",
        "codefile": "hello.keal",
        # The window that code opens, drawn under it in HTML. Not a screenshot:
        # a picture of a window would go stale the day a colour moved, and this
        # is three elements.
        "win_text": "Clicked 3 times",
        "win_btn": "Click me",
        "win_cap": "Every pixel above came out of a loop written in Keal.",
        "shot_alt": "A docked workspace built with keal-view",
        "shot_cap": "<b>Every pixel above</b> — the rounded corners, the anti-aliased borders, "
                    "the shadows, the glyphs — came out of a loop written in Keal.",
        "bars_h": "87 to 89 % of a running keal-view program is Keal.",
        "bars_p": "Which of the two it is depends on the backend it was built against, and none of "
                  "the other 11 to 13 % puts a pixel anywhere. The whole C surface is one "
                  "header: a framebuffer, a byte blob, an event struct, and accessors for each.",
        "bars": [("Keal", "5 598 lines", "100%", False),
                 ("C", "690-854 lines", "15.1%", True)],
        "barcap": "The Keal side is the whole framework: rasteriser, fonts, layout, widgets, "
                  "theme, docking, menus, the run loop. The C side is one window, one event "
                  "queue, and inline accessors: kv.h at 281 lines plus one backend of three — "
                  "Cocoa 409, X11 567, Win32 573. The bar shows the largest of them.",
        "why_h": "Why that is even possible",
        "why_p1": "One fact about the compiler decides the whole design. <code>native "
                  "\"\"\"…\"\"\"</code> pastes its C into the <b>same translation unit</b> as the "
                  "compiled program, so a <code>static inline</code> function declared there is "
                  "inlined into Keal's own code by the C compiler. A call across the boundary is "
                  "not a call — it is the instruction it contains.",
        "why_p2": "That line is one bounds-checked store. Measured at about half a nanosecond per "
                  "pixel from a Keal loop, which is what a C rasteriser costs, because after "
                  "inlining it <i>is</i> the C rasteriser. So there was no reason to write the "
                  "drawing in C, and every reason not to.",
        "cards_h": "What is in it",
        "cards": [
            ("Widgets", "Labels, buttons, checkboxes, radios, toggles, segmented controls, "
                        "selects, sliders, steppers, progress, fields, tabs, cards, panels, "
                        "scrolls — and <code>custom</code>, handed a clipped canvas, its "
                        "rectangle, the fonts, the theme and its own hover state."),
            ("Menus, dialogs and tooltips", "<code>openMenu</code>, <code>openDialog</code>, "
                                            "<code>openSheet</code> and <code>.tip(\"…\")</code>. "
                                            "Nothing has to be installed: the run loop composes "
                                            "that layer above the application's own overlay."),
            ("Layout", "One axis of flexbox and no more. There is no shrinking — content that "
                       "does not fit is clipped rather than squeezed, because a layout that "
                       "silently compresses fails only on small windows, which is the last place "
                       "anyone looks."),
            ("Text", "A TrueType parser and rasteriser in Keal: <code>cmap</code> formats 0, 4, 6 "
                     "and 12, <code>glyf</code> including composite glyphs, collections. Glyphs "
                     "are filled by the signed-area method and rasterised at the size they will "
                     "actually be drawn."),
            ("Drawing", "Anti-aliasing is analytic, not sampled: a straight edge's coverage is "
                        "its exact overlap with the pixel cell. There is no quality dial and no "
                        "frame that is quietly cheaper than the last."),
            ("Theme", "Dark and light, built from one surface ramp, one accent and three status "
                      "hues rather than a list of hex codes. <code>useTheme(lightTheme())</code> "
                      "is the whole change, including for widgets written afterwards."),
            ("Points, not pixels", "The rasteriser is the only thing that knows what a pixel is. "
                                   "One layout is correct on a Retina display and a projector; "
                                   "the numbers never change, the scale does."),
            ("An idle window costs nothing", "Between frames the loop is inside "
                                             "<code>kvWait</code>, which blocks until the system "
                                             "has something to say. Not a low duty cycle — none. "
                                             "On a laptop that is worth more than drawing speed."),
        ],
        "dock_h": "Docking that tells you where it will land",
        "dock_p1": "The arrangement is a binary tree of exactly two cases — a <b>leaf</b> holding "
                   "tabs, and a <b>split</b> holding two children with a fraction — which is few "
                   "enough that every arrangement it can be in is one you can reason about.",
        "dock_p2": "A panel is dragged by its tab; while it is moving, the highlight under the "
                   "pointer says where letting go would put it — left, right, above, below, or as "
                   "another tab — <i>before</i> it is let go. A panel is an ordinary view function "
                   "and does not know it is docked.",
        "plat_h": "Three platforms, one dozen functions",
        "plat_p": "All three backends were written against the same dozen functions, and nothing "
                  "above <code>runtime/</code> changed to add the second and third — which is the "
                  "point of having drawn the boundary where it is.",
        "plat_head": ["Platform", "Backend", "State"],
        "plat_rows": [
            ("macOS", "runtime/kv_cocoa.m", "Cocoa. <span class=\"ok\">Verified</span> — "
                                            "developed here"),
            ("Windows", "runtime/kv_win32.c", "Win32 and a BI_RGB DIB. <span class=\"ok\">"
                                              "Verified</span> on Windows 10 22H2 and 11 22H2, "
                                              "MinGW-w64"),
            ("Linux", "runtime/kv_x11.c", "Xlib only, no toolkit. <span class=\"ok\">Verified"
                                          "</span> on Ubuntu 26.04 aarch64, under Wayland "
                                          "through XWayland"),
        ],
        "plat_after": "Windows and Linux were each verified by someone on a real machine, going "
                      "through the porting checklist line by line, and between them it cost "
                      "nineteen defects — <b>twelve of which were above the backend</b>, and so "
                      "were on every platform including the one this was written on. Four things "
                      "remain unverified and are recorded rather than glossed.",
        "plat_link": "What that week found, and what it could not →",
        "start_h": "Running it",
        "start_p": "keal-view needs the Keal compiler beside it. There is no build system here: "
                   "<code>tools/build.sh</code> picks this platform's backend, compiles it once, "
                   "and hands the object file to <code>keal build</code>.",
        "start_win": "in a terminal",
        "free_h": "Two things every keal-view program understands for free",
        "free_p": "The first needs no display at all, which is how the framework is checked in "
                  "continuous integration and how every picture on this site was made.",
    },
    "fr": {
        "title": "keal-view — des fenêtres d'application, écrites en Keal",
        "desc": "Un framework d'interface graphique multiplateforme où le dessin est du Keal : "
                "le rasteriseur, le moteur TrueType, la mise en page, les widgets et le docking "
                "sont des fichiers .keal. Le C en dessous ouvre une fenêtre et pose une image "
                "finie.",
        "pill": "Vérifié sur macOS, Windows et Linux",
        "h1": "Le dessin est du Keal.",
        "sub": "Pas des liaisons vers une boîte à outils, pas une enveloppe autour d'une toile "
               "écrite en C. Le rasteriseur, le moteur TrueType, la mise en page, les widgets, le "
               "thème et le docking sont des fichiers <code>.keal</code>. Le C en dessous ouvre "
               "une fenêtre, rapporte ce que l'utilisateur a fait, et pose à l'écran un tampon de "
               "pixels déjà fini. Il ne dessine rien.",
        "cta1": "Lire le guide →",
        "cta2": "Tous les widgets qui existent",
        "codefile": "bonjour.keal",
        "win_text": "Clic\u00e9 3 fois",
        "win_btn": "Clique-moi",
        "win_cap": "Chaque pixel ci-dessus est sorti d\u2019une boucle \u00e9crite en Keal.",
        "shot_alt": "Un espace de travail à panneaux construit avec keal-view",
        "shot_cap": "<b>Chaque pixel ci-dessus</b> — les coins arrondis, les bordures "
                    "anti-crénelées, les ombres, les glyphes — est sorti d'une boucle écrite en "
                    "Keal.",
        "bars_h": "87 à 89 % d'un programme keal-view qui tourne est du Keal.",
        "bars_p": "Lequel des deux dépend du backend contre lequel il a été construit, et aucun "
                  "des 11 à 13 % restants ne pose un pixel où que ce soit. Toute la surface C "
                  "tient dans un en-tête : un tampon d'image, un bloc d'octets, une structure "
                  "d'événement, et les accesseurs de chacun.",
        "bars": [("Keal", "5 598 lignes", "100%", False),
                 ("C", "690-854 lignes", "15.1%", True)],
        "barcap": "Le côté Keal, c'est tout le framework : rasteriseur, polices, mise en page, "
                  "widgets, thème, docking, menus, boucle d'exécution. Le côté C, c'est une "
                  "fenêtre, une file d'événements et des accesseurs inlinés : kv.h à 281 lignes "
                  "plus un backend sur trois — Cocoa 409, X11 567, Win32 573. La barre montre le "
                  "plus gros des trois.",
        "why_h": "Pourquoi c'est seulement possible",
        "why_p1": "Un seul fait du compilateur décide de toute la conception. <code>native "
                  "\"\"\"…\"\"\"</code> colle son C dans <b>la même unité de traduction</b> que le "
                  "programme compilé, donc une fonction <code>static inline</code> déclarée là "
                  "est inlinée par le compilateur C dans le code de Keal lui-même. Un appel à "
                  "travers la frontière n'est pas un appel — c'est l'instruction qu'il contient.",
        "why_p2": "Cette ligne est une seule écriture avec vérification de bornes. Mesurée à "
                  "environ une demi-nanoseconde par pixel depuis une boucle Keal, ce qui est le "
                  "prix d'un rasteriseur C, parce qu'après inlining <i>c'est</i> le rasteriseur C. "
                  "Il n'y avait donc aucune raison d'écrire le dessin en C, et toutes les raisons "
                  "de ne pas le faire.",
        "cards_h": "Ce qu'il y a dedans",
        "cards": [
            ("Widgets", "Étiquettes, boutons, cases à cocher, boutons radio, interrupteurs, "
                        "contrôles segmentés, listes déroulantes, curseurs, incréments, "
                        "progression, champs, onglets, cartes, panneaux, zones défilantes — et "
                        "<code>custom</code>, à qui l'on remet une toile déjà découpée, son "
                        "rectangle, les polices, le thème et son propre état de survol."),
            ("Menus, dialogues et bulles", "<code>openMenu</code>, <code>openDialog</code>, "
                                           "<code>openSheet</code> et <code>.tip(\"…\")</code>. "
                                           "Rien à installer : la boucle compose cette couche "
                                           "au-dessus de la surcouche de l'application."),
            ("Mise en page", "Un axe de flexbox et pas davantage. Il n'y a pas de compression : "
                             "ce qui ne rentre pas est découpé plutôt que serré, parce qu'une "
                             "mise en page qui compresse en silence ne casse que sur les petites "
                             "fenêtres, l'endroit où personne ne regarde."),
            ("Texte", "Un analyseur et un rasteriseur TrueType écrits en Keal : formats "
                      "<code>cmap</code> 0, 4, 6 et 12, <code>glyf</code> avec les glyphes "
                      "composites, les collections. Les glyphes sont remplis par la méthode de "
                      "l'aire signée et rasterisés à la taille où ils seront réellement dessinés."),
            ("Dessin", "L'anti-crénelage est analytique, pas échantillonné : la couverture d'un "
                       "bord droit est son recouvrement exact avec la cellule du pixel. Il n'y a "
                       "pas de réglage de qualité, ni d'image discrètement moins chère que la "
                       "précédente."),
            ("Thème", "Sombre et clair, construits depuis une rampe de surfaces, un accent et "
                      "trois teintes d'état plutôt qu'une liste de codes hexadécimaux. "
                      "<code>useTheme(lightTheme())</code> est tout le changement, y compris pour "
                      "les widgets écrits après."),
            ("Des points, pas des pixels", "Le rasteriseur est la seule chose qui sache ce qu'est "
                                           "un pixel. Une mise en page est juste sur un écran "
                                           "Retina et sur un projecteur ; les nombres ne changent "
                                           "pas, l'échelle si."),
            ("Une fenêtre au repos ne coûte rien", "Entre deux images, la boucle est dans "
                                                   "<code>kvWait</code>, qui bloque jusqu'à ce que "
                                                   "le système ait quelque chose à dire. Pas un "
                                                   "faible taux d'activité — aucun. Sur un "
                                                   "portable, ça vaut plus que la vitesse de "
                                                   "dessin."),
        ],
        "dock_h": "Un docking qui dit d'avance où ça va tomber",
        "dock_p1": "L'agencement est un arbre binaire à exactement deux cas — une <b>feuille</b> "
                   "qui tient des onglets, et une <b>coupe</b> qui tient deux enfants et une "
                   "fraction — ce qui est assez peu pour que chaque état possible soit un état "
                   "sur lequel on peut raisonner.",
        "dock_p2": "Un panneau se traîne par son onglet ; pendant le déplacement, la zone mise en "
                   "évidence sous le pointeur dit où le lâcher le poserait — à gauche, à droite, "
                   "au-dessus, en dessous, ou comme onglet de plus — <i>avant</i> qu'on lâche. Un "
                   "panneau est une fonction de vue ordinaire et ignore qu'il est ancré.",
        "plat_h": "Trois plateformes, une douzaine de fonctions",
        "plat_p": "Les trois backends ont été écrits contre la même douzaine de fonctions, et "
                  "rien au-dessus de <code>runtime/</code> n'a changé pour ajouter le deuxième et "
                  "le troisième — ce qui est tout l'intérêt d'avoir tracé la frontière là.",
        "plat_head": ["Plateforme", "Backend", "État"],
        "plat_rows": [
            ("macOS", "runtime/kv_cocoa.m", "Cocoa. <span class=\"ok\">Vérifié</span> — développé "
                                            "ici"),
            ("Windows", "runtime/kv_win32.c", "Win32 et un DIB BI_RGB. <span class=\"ok\">Vérifié"
                                              "</span> sur Windows 10 22H2 et 11 22H2, MinGW-w64"),
            ("Linux", "runtime/kv_x11.c", "Xlib seul, aucune boîte à outils. <span class=\"ok\">"
                                          "Vérifié</span> sur Ubuntu 26.04 aarch64, sous Wayland "
                                          "à travers XWayland"),
        ],
        "plat_after": "Windows et Linux ont chacun été vérifiés par quelqu'un sur une vraie "
                      "machine, en suivant la liste de portage ligne à ligne, et à eux deux cela "
                      "a coûté dix-neuf défauts — <b>dont douze au-dessus du backend</b>, donc "
                      "présents sur toutes les plateformes, y compris celle où tout a été écrit. "
                      "Quatre choses restent non vérifiées et sont consignées plutôt que passées "
                      "sous silence.",
        "plat_link": "Ce que cette semaine a trouvé, et ce qu'elle n'a pas pu →",
        "start_h": "Le faire tourner",
        "start_p": "keal-view a besoin du compilateur Keal à côté de lui. Il n'y a pas de système "
                   "de construction ici : <code>tools/build.sh</code> choisit le backend de la "
                   "plateforme, le compile une fois, et remet le fichier objet à "
                   "<code>keal build</code>.",
        "start_win": "dans un terminal",
        "free_h": "Deux choses que tout programme keal-view comprend gratuitement",
        "free_p": "La première n'a besoin d'aucun écran, ce qui est la façon dont le framework "
                  "est vérifié en intégration continue et dont chaque image de ce site a été "
                  "faite.",
    },
}

HELLO_CODE = """<span class="k">import</span> <span class="s">"keal-view/keal-view.keal"</span>

<span class="k">val</span> clicks = state(<span class="s">0</span>)

runApp(<span class="s">"Hello"</span>, <span class="s">320</span>, <span class="s">200</span>, { -&gt;
    column([
        label(<span class="s">"Clicked ${clicks.get()} times"</span>).fontSize(<span class="s">20.0</span>).centered(),
        button(<span class="s">"Click me"</span>, { -&gt; clicks.set(clicks.get() + <span class="s">1</span>) }).kindOf(primary)
    ]).gaps(<span class="s">12.0</span>).padAll(<span class="s">24.0</span>).aligned(mainCenter, crossCenter).grows()
})"""

DOCK_CODE = """<span class="k">val</span> dock = Dock(
    beside(
        leaf([<span class="s">"files"</span>]),
        above(
            beside(leaf([<span class="s">"editor"</span>]), leaf([<span class="s">"props"</span>, <span class="s">"preview"</span>]), <span class="s">0.68</span>),
            leaf([<span class="s">"terminal"</span>]),
            <span class="s">0.72</span>),
        <span class="s">0.19</span>))

dock.add(panelOf(<span class="s">"files"</span>, <span class="s">"Files"</span>, { -&gt; filesPanel() }))"""

START_CODE = """<span class="c"># the compiler, then the framework</span>
git clone https://github.com/geneacta/keal
git clone https://github.com/geneacta/keal-view
<span class="k">cd</span> keal &amp;&amp; cargo build --release &amp;&amp; <span class="k">cd</span> ../keal-view

tools/build.sh examples/tour.keal    &amp;&amp; build/tour       <span class="c"># start here</span>
tools/build.sh examples/gallery.keal &amp;&amp; build/gallery    <span class="c"># every widget</span>
tools/test.sh                                   <span class="c"># 194 checks, no display</span>"""

FREE_CODE = """build/studio --snapshot frame.bmp 2          <span class="c"># one frame to a file, then exit</span>
build/studio --snapshot frame.bmp 2 900 1900 <span class="c"># …at a size of your choosing</span>
build/studio --window-id /tmp/id             <span class="c"># write its own window number out</span>"""

# --------------------------------------------------------------- gallery ---

GALLERY = {
    "en": {
        "title": "Gallery",
        "lede": "Five programs, photographed by themselves. Every one of these pictures was made "
                "by the program in it, with <code>--snapshot</code>, which draws one frame to a "
                "file and exits — so what you are looking at is the rasteriser's output and not a "
                "screen capture of it.",
        "shots": [
            ("studio.png", "The studio", "examples/studio.keal",
             "A docked workspace: a file list, a code editor, a properties panel with its own "
             "preview tab, and a terminal. The arrangement is a binary tree of leaves and splits. "
             "The editor and the coverage chart are both <code>custom</code> views — handed a "
             "clipped canvas and left to draw.", True),
            ("gallery.png", "The widget gallery", "examples/gallery.keal",
             "Documentation that runs: every widget there is, on one scrolling page. If a control "
             "is not in here it does not exist.", True),
            ("tour.png", "The guided tour", "examples/tour.keal",
             "A tour of keal-view written in keal-view. Eleven chapters, each showing a thing "
             "<i>running</i> next to the code that made it — a live counter, a live slider, a "
             "live dock you can drag a panel around inside.", True),
            ("calculator.png", "A calculator", "examples/calculator.keal",
             "The whole thing end to end — arithmetic, keypad, keyboard — in about two hundred "
             "lines. The keypad is five rows of four.", False),
            ("todo.png", "A to-do list", "examples/todo.keal",
             "State, a list rebuilt from it, and a field that keeps its caret when a row above it "
             "is deleted — because rows are keyed, and identity is what retained state hangs on.",
             False),
        ],
        "how_h": "How the pictures are made",
        "how_p": "Every keal-view program takes <code>--snapshot</code> without being told to. It "
                 "needs no display, which is how the framework is checked in continuous "
                 "integration on three platforms, and why these pictures cannot quietly drift "
                 "from what the code does.",
    },
    "fr": {
        "title": "Galerie",
        "lede": "Cinq programmes, photographiés par eux-mêmes. Chacune de ces images a été faite "
                "par le programme qui s'y trouve, avec <code>--snapshot</code>, qui dessine une "
                "image dans un fichier puis s'arrête — donc ce que vous regardez est la sortie du "
                "rasteriseur et pas une capture d'écran de celle-ci.",
        "shots": [
            ("studio.png", "L'atelier", "examples/studio.keal",
             "Un espace de travail à panneaux : une liste de fichiers, un éditeur de code, un "
             "panneau de propriétés avec son onglet d'aperçu, et un terminal. L'agencement est un "
             "arbre binaire de feuilles et de coupes. L'éditeur et le graphique de couverture "
             "sont deux vues <code>custom</code> — on leur remet une toile découpée et on les "
             "laisse dessiner.", True),
            ("gallery.png", "La galerie de widgets", "examples/gallery.keal",
             "De la documentation qui tourne : tous les widgets qui existent, sur une seule page "
             "défilante. Si un contrôle n'y est pas, il n'existe pas.", True),
            ("tour.png", "La visite guidée", "examples/tour.keal",
             "Une visite de keal-view écrite en keal-view. Onze chapitres, chacun montrant une "
             "chose <i>en marche</i> à côté du code qui l'a faite — un compteur vivant, un "
             "curseur vivant, un dock vivant dans lequel on peut traîner un panneau.", True),
            ("calculator.png", "Une calculatrice", "examples/calculator.keal",
             "Le tout de bout en bout — l'arithmétique, le clavier numérique, le clavier — en "
             "environ deux cents lignes. Le pavé est cinq rangées de quatre.", False),
            ("todo.png", "Une liste de tâches", "examples/todo.keal",
             "De l'état, une liste reconstruite depuis lui, et un champ qui garde son curseur "
             "d'insertion quand on supprime une ligne au-dessus — parce que les lignes ont une "
             "clé, et que l'identité est ce à quoi l'état retenu s'accroche.", False),
        ],
        "how_h": "Comment les images sont faites",
        "how_p": "Tout programme keal-view accepte <code>--snapshot</code> sans qu'on le lui ait "
                 "appris. Il n'a besoin d'aucun écran, ce qui est la façon dont le framework est "
                 "vérifié en intégration continue sur trois plateformes, et la raison pour "
                 "laquelle ces images ne peuvent pas s'écarter en douce de ce que fait le code.",
    },
}

# ---------------------------------------------------------- architecture ---

ARCH = {
    "en": {
        "title": "Architecture",
        "lede": "Where the boundary is, what a frame does, and what the language decided rather "
                "than the design.",
        "b_h": "The boundary",
        "b_p1": "The C underneath does four things: open a window, report what the user did, hand "
                "over a buffer of pixels, and go to sleep until something happens. It does not "
                "draw. The whole C surface is <code>runtime/kv.h</code> — a framebuffer, a byte "
                "blob, an event struct, and accessors for each, every hot one "
                "<code>static inline</code> and so inlined into Keal.",
        "b_p2": "That is why adding Windows and then Linux changed nothing above "
                "<code>runtime/</code>. A backend is one file against a dozen functions.",
        "tree_h": "The files",
        "frame_h": "What a frame is",
        "frame_p1": "Build the tree from the state, lay it out, hand it the events that arrived, "
                    "and — if a handler changed anything — build and lay it out once more before "
                    "drawing. Dispatching against a fresh layout rather than the last frame's is "
                    "what keeps a click landing on what was under the pointer when it happened, "
                    "even on the frame where the window was resized.",
        "frame_p2": "The tree is thrown away and made again. There is no diff, and so nothing to "
                    "forget to invalidate. What outlives it — hover, focus, scroll offsets, "
                    "carets — is keyed by identity in <code>ui.keal</code>, and a node's identity "
                    "is where it is unless it was given a key.",
        "frame_p3": "Between frames the loop is inside <code>kvWait</code>, which blocks. An idle "
                    "window uses no processor at all. That sentence sat in the README for two "
                    "days before anyone measured it, and when someone did it was false on "
                    "Windows: with the pointer resting anywhere over the window, the wait "
                    "returned instantly for ever and the process held 96 % of a core. It is "
                    "fixed, and the checklist now asks for the measurement twice.",
        "lang_h": "What the language decided",
        "lang_p": "One place where keal-view's shape is chosen by Keal rather than by the design: "
                  "a trait is not a type in Keal, so a <code>List&lt;Widget&gt;</code> of "
                  "different implementations cannot exist. One <code>View</code> class with a "
                  "<code>kind</code> is what the language offers. The constructors and the "
                  "chained modifiers are the real interface, and nothing outside "
                  "<code>view.keal</code> sets <code>kind</code> by hand.",
        "found_h": "And what building it found",
        "found_p": "This framework was the first real use anything had made of several corners of "
                   "the compiler, and it found four defects in it — a call whose callee is a "
                   "field of function type; a local that did not shadow an imported function of "
                   "the same name; a lambda that could not capture a top-level binding; and "
                   "<code>Int</code> having no bitwise operators. All four are fixed upstream, "
                   "and this repository was rewritten to suit.",
        "found_link": "The language they were fixed in →",
        "notyet_h": "What is not here yet",
        "notyet": ["multiple OS windows",
                   "a floating panel torn off a dock into a window of its own",
                   "text selection across lines",
                   "right-to-left and complex scripts — the font engine maps codepoints to glyphs "
                   "one at a time, which is honest for Latin, Greek and Cyrillic and wrong for "
                   "Arabic and Devanagari",
                   "<code>CFF&nbsp;</code> outlines, so an OpenType font with cubic curves loads "
                   "and reports that it has none",
                   "saving and restoring a dock arrangement",
                   "animation beyond a blinking caret",
                   "images"],
    },
    "fr": {
        "title": "Architecture",
        "lede": "Où passe la frontière, ce que fait une image, et ce que le langage a décidé "
                "plutôt que la conception.",
        "b_h": "La frontière",
        "b_p1": "Le C en dessous fait quatre choses : ouvrir une fenêtre, rapporter ce que "
                "l'utilisateur a fait, remettre un tampon de pixels, et se rendormir jusqu'à ce "
                "qu'il se passe quelque chose. Il ne dessine pas. Toute la surface C est "
                "<code>runtime/kv.h</code> — un tampon d'image, un bloc d'octets, une structure "
                "d'événement, et les accesseurs de chacun, tous les chauds en "
                "<code>static inline</code> et donc inlinés dans Keal.",
        "b_p2": "C'est pour ça qu'ajouter Windows puis Linux n'a rien changé au-dessus de "
                "<code>runtime/</code>. Un backend, c'est un fichier contre une douzaine de "
                "fonctions.",
        "tree_h": "Les fichiers",
        "frame_h": "Ce qu'est une image",
        "frame_p1": "Construire l'arbre depuis l'état, le mettre en page, lui remettre les "
                    "événements arrivés, et — si un gestionnaire a changé quelque chose — le "
                    "reconstruire et le remettre en page une fois de plus avant de dessiner. "
                    "Distribuer les événements contre une mise en page fraîche plutôt que celle "
                    "de l'image précédente est ce qui fait qu'un clic atterrit sur ce qui était "
                    "sous le pointeur au moment où il a eu lieu, y compris sur l'image où la "
                    "fenêtre a changé de taille.",
        "frame_p2": "L'arbre est jeté et refait. Il n'y a pas de comparaison d'arbres, donc rien "
                    "à oublier d'invalider. Ce qui lui survit — survol, focus, décalages de "
                    "défilement, curseurs d'insertion — est rangé par identité dans "
                    "<code>ui.keal</code>, et l'identité d'un nœud est l'endroit où il se trouve, "
                    "sauf si on lui a donné une clé.",
        "frame_p3": "Entre deux images, la boucle est dans <code>kvWait</code>, qui bloque. Une "
                    "fenêtre au repos n'utilise aucun processeur. Cette phrase est restée deux "
                    "jours dans le README avant que quiconque la mesure, et quand quelqu'un l'a "
                    "fait elle était fausse sous Windows : le pointeur posé n'importe où sur la "
                    "fenêtre, l'attente revenait aussitôt pour toujours et le processus tenait "
                    "96 % d'un cœur. C'est corrigé, et la liste de portage demande désormais la "
                    "mesure deux fois.",
        "lang_h": "Ce que le langage a décidé",
        "lang_p": "Un endroit où la forme de keal-view est choisie par Keal et non par la "
                  "conception : un trait n'est pas un type en Keal, donc une "
                  "<code>List&lt;Widget&gt;</code> d'implémentations différentes ne peut pas "
                  "exister. Une seule classe <code>View</code> avec un <code>kind</code> est ce "
                  "que le langage offre. Les constructeurs et les modificateurs chaînés sont la "
                  "véritable interface, et rien en dehors de <code>view.keal</code> ne pose "
                  "<code>kind</code> à la main.",
        "found_h": "Et ce que sa construction a trouvé",
        "found_p": "Ce framework a été le premier usage sérieux de plusieurs coins du "
                   "compilateur, et il y a trouvé quatre défauts — un appel dont l'appelé est un "
                   "champ de type fonction ; une variable locale qui ne masquait pas une fonction "
                   "importée du même nom ; une lambda qui ne pouvait pas capturer une liaison de "
                   "premier niveau ; et <code>Int</code> sans opérateurs bit à bit. Les quatre "
                   "sont corrigés en amont, et ce dépôt a été réécrit en conséquence.",
        "found_link": "Le langage où ils ont été corrigés →",
        "notyet_h": "Ce qui n'y est pas encore",
        "notyet": ["plusieurs fenêtres système",
                   "un panneau détaché d'un dock dans une fenêtre à lui",
                   "la sélection de texte sur plusieurs lignes",
                   "l'écriture de droite à gauche et les écritures complexes — le moteur de "
                   "polices associe les points de code aux glyphes un par un, ce qui est honnête "
                   "pour le latin, le grec et le cyrillique et faux pour l'arabe et la dévanagari",
                   "les contours <code>CFF&nbsp;</code>, donc une police OpenType à courbes "
                   "cubiques se charge et annonce qu'elle n'en a aucun",
                   "sauvegarder et restaurer un agencement de dock",
                   "l'animation au-delà d'un curseur qui clignote",
                   "les images"],
    },
}

TREE_CODE = """runtime/
  kv.h            <span class="c">the whole C surface: framebuffer, blob, event, accessors</span>
  kv_cocoa.m      <span class="c">macOS: NSWindow, a layer-backed view, a ring of events</span>
  kv_win32.c      <span class="c">Windows: the same, through Win32 and GDI</span>
  kv_x11.c        <span class="c">Linux: the same, through Xlib alone</span>
src/
  ffi.keal        <span class="c">the only file in keal-view that mentions C</span>
  color.keal      <span class="c">colour packed in an Int — the per-pixel loop</span>
  geom.keal       <span class="c">rectangles, insets, and the cell-coverage function</span>
  canvas.keal     <span class="c">the rasteriser</span>
  font.keal       <span class="c">TrueType, parsed and rasterised</span>
  text.keal       <span class="c">measuring, wrapping, ellipsising, caret hit-testing</span>
  theme.keal      <span class="c">the palettes, the metrics, and Paint</span>
  view.keal       <span class="c">the tree an application describes</span>
  layout.keal     <span class="c">measuring it and giving every node a rectangle</span>
  paint.keal      <span class="c">every widget's appearance, and icons drawn from strokes</span>
  ui.keal         <span class="c">what outlives a tree rebuilt every frame</span>
  event.keal      <span class="c">what happened, in points</span>
  state.keal      <span class="c">Cell&lt;T&gt; and one revision counter</span>
  dock.keal       <span class="c">splits, tabs, and dragging a panel between them</span>
  popup.keal      <span class="c">menus, dialogs and tooltips</span>
  app.keal        <span class="c">the loop, and how input gets back to the application</span>"""

# ----------------------------------------------------------- coming from ---

COMING = {
    "en": {
        "title": "Coming from another toolkit",
        "lede": "What you already write, and what it becomes here — plus the handful of things "
                "that will genuinely surprise you, which is the part a syntax table cannot carry.",
        "note": "One thing is true of every page below, so it is said once here: keal-view draws "
                "every pixel itself. It does not use the platform's widgets, so it does not "
                "inherit the platform's accessibility, its input methods, or its look. That is a "
                "real cost and the pages below do not pretend otherwise.",
    },
    "fr": {
        "title": "Je viens d'une autre boîte à outils",
        "lede": "Ce que vous écrivez déjà, et ce que ça devient ici — plus la poignée de choses "
                "qui vont vraiment vous surprendre, la part qu'un tableau de syntaxe ne peut pas "
                "porter.",
        "note": "Une chose est vraie de toutes les pages ci-dessous, alors elle est dite une fois "
                "ici : keal-view dessine lui-même chaque pixel. Il n'utilise pas les widgets de "
                "la plateforme, donc il n'hérite ni de son accessibilité, ni de ses méthodes de "
                "saisie, ni de son apparence. C'est un coût réel et les pages ci-dessous ne "
                "prétendent pas le contraire.",
    },
}

# Each: slug, name, blurb (en, fr), intro (en, fr), rows [(theirs, ours-en, ours-fr)],
# notes [(title_en, title_fr, body_en, body_fr)].
TOOLKITS = [
    {
        "slug": "from-qt", "name": "Qt",
        "blurb_en": "Widgets, signals and slots, and a layout engine",
        "blurb_fr": "Des widgets, signaux et slots, et un moteur de mise en page",
        "intro_en": "Qt and keal-view agree about more than they disagree: both put a retained "
                    "tree of widgets in front of you, both lay it out rather than positioning it, "
                    "and both draw their own controls rather than asking the platform. The "
                    "difference is what a widget <i>is</i> — a long-lived object you mutate in "
                    "Qt, and a description rebuilt from state here.",
        "intro_fr": "Qt et keal-view s'accordent sur plus de choses qu'ils n'en discordent : tous "
                    "deux mettent devant vous un arbre de widgets retenu, tous deux le mettent en "
                    "page plutôt que de le positionner, et tous deux dessinent leurs propres "
                    "contrôles au lieu de les demander à la plateforme. La différence est ce "
                    "qu'<i>est</i> un widget — un objet de longue vie qu'on modifie chez Qt, une "
                    "description reconstruite depuis l'état ici.",
        "rows": [
            ("QLabel(\"Hi\")", "label(\"Hi\")", "label(\"Salut\")"),
            ("QPushButton + connect(…)", "button(\"Go\", { -&gt; … })", "button(\"Go\", { -&gt; … })"),
            ("QVBoxLayout / QHBoxLayout", "column([…]) / row([…])", "column([…]) / row([…])"),
            ("setStretch / stretch factor", ".grows() and .shares()", ".grows() et .shares()"),
            ("QWidget::paintEvent + QPainter", "custom({ p -&gt; … })", "custom({ p -&gt; … })"),
            ("QDockWidget", "Dock, leaf and split", "Dock, leaf et split"),
            ("qApp-&gt;setStyleSheet(…)", "useTheme(lightTheme())", "useTheme(lightTheme())"),
        ],
        "notes": [
            ("There are no signals, because there is nothing to keep in step",
             "Il n'y a pas de signaux, parce qu'il n'y a rien à garder synchronisé",
             "A Qt widget holds state, so something has to tell it when the model changed — that "
             "is what a signal is for. Here the tree is thrown away and made again from the "
             "state, so a button's handler writes a <code>Cell</code> and the next frame is "
             "already right. There is no <code>connect</code> and nothing to disconnect.",
             "Un widget Qt tient de l'état, donc il faut bien que quelque chose lui dise que le "
             "modèle a changé — c'est à ça que sert un signal. Ici l'arbre est jeté et refait "
             "depuis l'état, donc le gestionnaire d'un bouton écrit une <code>Cell</code> et "
             "l'image suivante est déjà juste. Il n'y a pas de <code>connect</code>, et rien à "
             "déconnecter."),
            ("Nothing shrinks",
             "Rien ne se comprime",
             "Qt layouts negotiate: a widget has a minimum, a preferred and a maximum, and the "
             "engine finds a compromise. Here there is one axis of flexbox and no shrinking at "
             "all — what does not fit is clipped. That is a deliberate choice: a layout that "
             "silently compresses fails only on small windows, which is the last place anyone "
             "looks.",
             "Les mises en page de Qt négocient : un widget a un minimum, un préféré et un "
             "maximum, et le moteur trouve un compromis. Ici il y a un axe de flexbox et aucune "
             "compression — ce qui ne rentre pas est découpé. C'est un choix délibéré : une mise "
             "en page qui compresse en silence ne casse que sur les petites fenêtres, l'endroit "
             "où personne ne regarde."),
            ("No moc, no build system, no .ui files",
             "Pas de moc, pas de système de construction, pas de fichiers .ui",
             "<code>tools/build.sh yours.keal</code> compiles the backend once and hands the "
             "object file to <code>keal build</code>. There is no code generator in the loop and "
             "no interface description to keep in step with the code that uses it.",
             "<code>tools/build.sh votre.keal</code> compile le backend une fois et remet le "
             "fichier objet à <code>keal build</code>. Il n'y a pas de générateur de code dans la "
             "boucle, ni de description d'interface à garder synchronisée avec le code qui s'en "
             "sert."),
        ],
    },
    {
        "slug": "from-gtk", "name": "GTK",
        "blurb_en": "Containers, properties and a CSS-shaped theme",
        "blurb_fr": "Des conteneurs, des propriétés et un thème taillé comme du CSS",
        "intro_en": "GTK 4 already thinks in boxes that grow and align, so the layout will feel "
                    "familiar. What changes is the ownership: there is no widget to "
                    "<code>g_object_unref</code>, no property to bind, and no CSS file — the "
                    "theme is a value in the program, and one value in force.",
        "intro_fr": "GTK 4 raisonne déjà en boîtes qui grandissent et s'alignent, donc la mise en "
                    "page vous semblera familière. Ce qui change, c'est la propriété des objets : "
                    "pas de widget à <code>g_object_unref</code>, pas de propriété à lier, pas de "
                    "fichier CSS — le thème est une valeur dans le programme, et une seule valeur "
                    "en vigueur.",
        "rows": [
            ("gtk_label_new(\"Hi\")", "label(\"Hi\")", "label(\"Salut\")"),
            ("g_signal_connect(btn, \"clicked\", …)", "button(\"Go\", { -&gt; … })",
             "button(\"Go\", { -&gt; … })"),
            ("GtkBox, orientation vertical", "column([…])", "column([…])"),
            ("gtk_widget_set_hexpand", ".grows()", ".grows()"),
            ("GtkDrawingArea + draw func", "custom({ p -&gt; … })", "custom({ p -&gt; … })"),
            ("GtkCssProvider, style.css", "useTheme(darkTheme())", "useTheme(darkTheme())"),
            ("GtkPopover / GtkPopoverMenu", "openMenu(x, y, […])", "openMenu(x, y, […])"),
        ],
        "notes": [
            ("The theme is one value, not a cascade",
             "Le thème est une valeur, pas une cascade",
             "GTK's CSS is powerful and it is also a second language with its own selectors and "
             "specificity. Here there is one <code>Theme</code>: a surface ramp, an accent and "
             "three status hues, read by every widget including the ones you write. Changing it "
             "is one call, and it cannot half-apply.",
             "Le CSS de GTK est puissant, et c'est aussi un second langage avec ses sélecteurs et "
             "sa spécificité. Ici il y a un <code>Theme</code> : une rampe de surfaces, un accent "
             "et trois teintes d'état, lus par tous les widgets, y compris ceux que vous écrivez. "
             "En changer est un seul appel, et il ne peut pas s'appliquer à moitié."),
            ("There is no main loop to integrate with",
             "Il n'y a pas de boucle principale où s'intégrer",
             "<code>runApp</code> owns the loop, and between frames it blocks in "
                "<code>kvWait</code>. There is no <code>GMainContext</code> to attach a source to. "
                "If you need to wake the interface from elsewhere, you write a <code>Cell</code>; "
                "if you need it woken on a clock, you ask for the next frame in so many "
                "milliseconds.",
             "<code>runApp</code> possède la boucle, et entre deux images elle bloque dans "
             "<code>kvWait</code>. Il n'y a pas de <code>GMainContext</code> auquel attacher une "
             "source. Pour réveiller l'interface depuis ailleurs, on écrit une <code>Cell</code> ; "
             "pour la réveiller sur une horloge, on demande la prochaine image dans tant de "
             "millisecondes."),
            ("You lose the platform's accessibility",
             "Vous perdez l'accessibilité de la plateforme",
             "GTK hands ATK a real tree of real widgets, and a screen reader reads it. keal-view "
             "draws pixels; there is no accessibility tree behind them yet. This is the largest "
             "single thing GTK gives you that this does not.",
             "GTK remet à ATK un véritable arbre de véritables widgets, et un lecteur d'écran le "
             "lit. keal-view dessine des pixels ; il n'y a pas encore d'arbre d'accessibilité "
             "derrière. C'est, à elle seule, la plus grosse chose que GTK vous donne et que ceci "
             "ne donne pas."),
        ],
    },
    {
        "slug": "from-flutter", "name": "Flutter",
        "blurb_en": "A declarative tree rebuilt from state, drawn by the framework",
        "blurb_fr": "Un arbre déclaratif reconstruit depuis l'état, dessiné par le framework",
        "intro_en": "This is the closest neighbour on the list. Flutter also describes an "
                    "interface as a function of state, also rebuilds it, and also draws every "
                    "pixel itself rather than using the platform's controls. If you are coming "
                    "from Flutter, most of what you know transfers and the surprises are about "
                    "scale, not shape.",
        "intro_fr": "C'est le voisin le plus proche de la liste. Flutter décrit lui aussi une "
                    "interface comme une fonction de l'état, la reconstruit lui aussi, et dessine "
                    "lui aussi chaque pixel plutôt que d'utiliser les contrôles de la "
                    "plateforme. Si vous venez de Flutter, l'essentiel de ce que vous savez se "
                    "transpose et les surprises portent sur l'échelle, pas sur la forme.",
        "rows": [
            ("Text('Hi')", "label(\"Hi\")", "label(\"Salut\")"),
            ("ElevatedButton(onPressed: …)", "button(\"Go\", { -&gt; … })", "button(\"Go\", { -&gt; … })"),
            ("Column / Row", "column([…]) / row([…])", "column([…]) / row([…])"),
            ("Expanded / Flexible", ".grows() / .shares()", ".grows() / .shares()"),
            ("Padding(padding: …)", ".padAll(…) / .pad(…)", ".padAll(…) / .pad(…)"),
            ("CustomPaint + CustomPainter", "custom({ p -&gt; … })", "custom({ p -&gt; … })"),
            ("setState / ValueNotifier", "state(0) and .set(…)", "state(0) et .set(…)"),
            ("Stack + Positioned", "stack([…]) and .at(x, y)", "stack([…]) et .at(x, y)"),
        ],
        "notes": [
            ("There is no element tree and no keys to get wrong — almost",
             "Il n'y a pas d'arbre d'éléments, et donc presque aucune clé à rater",
             "Flutter keeps an element tree beside the widget tree and reconciles them, which is "
                "where keys earn their keep. Here the tree is simply rebuilt and thrown away, and "
                "the only thing that survives is per-node state — hover, focus, scroll, caret — "
                "keyed by position in the tree. Give a node <code>.keyed(\"…\")</code> and it "
                "keeps its caret when a row above it is deleted; leave it and it does not.",
             "Flutter garde un arbre d'éléments à côté de l'arbre de widgets et les réconcilie, "
             "et c'est là que les clés gagnent leur place. Ici l'arbre est simplement reconstruit "
             "et jeté, et la seule chose qui survit est l'état par nœud — survol, focus, "
             "défilement, curseur — rangé par position dans l'arbre. Donnez "
             "<code>.keyed(\"…\")</code> à un nœud et il garde son curseur quand on supprime une "
             "ligne au-dessus ; laissez-le sans clé et il ne le garde pas."),
            ("The whole framework is five thousand lines you can read",
             "Tout le framework tient en cinq mille lignes lisibles",
             "Flutter's rendering pipeline is large, layered and mostly opaque in practice. Here "
                "the rasteriser is <code>canvas.keal</code>, the fonts are "
                "<code>font.keal</code>, and the loop is the bottom of <code>app.keal</code>. "
                "When a glyph looks wrong you can open the file that drew it.",
             "Le pipeline de rendu de Flutter est vaste, en couches, et opaque en pratique. Ici "
             "le rasteriseur est <code>canvas.keal</code>, les polices sont <code>font.keal</code>, "
             "et la boucle est le bas de <code>app.keal</code>. Quand un glyphe a l'air faux, on "
             "peut ouvrir le fichier qui l'a dessiné."),
            ("No animation framework, and an idle window that truly sleeps",
             "Pas de framework d'animation, et une fenêtre au repos qui dort vraiment",
             "Flutter drives a ticker and repaints on a vsync. keal-view blocks until the system "
                "says something, and an idle window uses no processor at all. The price is that "
                "there is no animation beyond a blinking caret yet: implicit animations, curves "
                "and controllers have no equivalent here.",
             "Flutter entretient un ticker et repeint à la synchronisation verticale. keal-view "
             "bloque jusqu'à ce que le système parle, et une fenêtre au repos n'utilise aucun "
             "processeur. Le prix, c'est qu'il n'y a pas encore d'animation au-delà d'un curseur "
             "qui clignote : animations implicites, courbes et contrôleurs n'ont pas "
             "d'équivalent ici."),
        ],
    },
    {
        "slug": "from-imgui", "name": "Dear ImGui",
        "blurb_en": "An immediate-mode interface drawn every frame",
        "blurb_fr": "Une interface en mode immédiat, redessinée à chaque image",
        "intro_en": "Dear ImGui rebuilds its interface every frame from calls, which is the same "
                    "instinct as here. Two things differ: keal-view describes a tree and then "
                    "lays it out, rather than emitting geometry as it goes; and it does not run "
                    "at the frame rate of a game — it sleeps until something happens.",
        "intro_fr": "Dear ImGui reconstruit son interface à chaque image à partir d'appels, ce "
                    "qui est le même instinct qu'ici. Deux choses diffèrent : keal-view décrit un "
                    "arbre puis le met en page, au lieu d'émettre de la géométrie au fil de "
                    "l'eau ; et il ne tourne pas à la cadence d'un jeu — il dort jusqu'à ce qu'il "
                    "se passe quelque chose.",
        "rows": [
            ("ImGui::Text(\"Hi\")", "label(\"Hi\")", "label(\"Salut\")"),
            ("if (ImGui::Button(\"Go\")) { … }", "button(\"Go\", { -&gt; … })", "button(\"Go\", { -&gt; … })"),
            ("ImGui::SliderFloat(&amp;v, …)", "slider(v, { x -&gt; … })", "slider(v, { x -&gt; … })"),
            ("ImGui::SameLine()", "row([…])", "row([…])"),
            ("ImGui::PushStyleColor", "the theme, read by everything", "le thème, lu par tout"),
            ("ImDrawList", "custom({ p -&gt; p.canvas… })", "custom({ p -&gt; p.canvas… })"),
            ("DockBuilder", "Dock, leaf and split", "Dock, leaf et split"),
        ],
        "notes": [
            ("A handler runs when the click happens, not on the next frame",
             "Un gestionnaire s'exécute quand le clic a lieu, pas à l'image suivante",
             "In immediate mode a button reports last frame's click as this frame's return value. "
                "Here the tree is built, laid out, and <i>then</i> handed the events, so a "
                "handler runs against the layout the user actually clicked on — including on the "
                "frame where the window was resized.",
             "En mode immédiat, un bouton rapporte le clic de l'image précédente comme valeur de "
             "retour de celle-ci. Ici l'arbre est construit, mis en page, <i>puis</i> on lui "
             "remet les événements, donc un gestionnaire s'exécute contre la mise en page sur "
             "laquelle l'utilisateur a réellement cliqué — y compris sur l'image où la fenêtre a "
             "changé de taille."),
            ("There is no GPU, and that is the point",
             "Il n'y a pas de GPU, et c'est le propos",
             "Dear ImGui produces vertex buffers for a renderer you supply. keal-view fills a "
                "buffer of <code>0xAARRGGBB</code> pixels on the processor and hands it to the "
                "window. Anti-aliasing is analytic rather than multisampled, so a curve costs "
                "what its edge costs and there is no quality dial.",
             "Dear ImGui produit des tampons de sommets pour un moteur de rendu que vous "
             "fournissez. keal-view remplit un tampon de pixels <code>0xAARRGGBB</code> sur le "
             "processeur et le remet à la fenêtre. L'anti-crénelage est analytique plutôt que "
             "multi-échantillonné, donc une courbe coûte ce que coûte son bord et il n'y a pas de "
             "réglage de qualité."),
            ("State outlives the frame without you holding it",
             "L'état survit à l'image sans que vous le teniez",
             "ImGui keeps its own internal state keyed by an ID stack you have to reason about. "
                "Here the same problem is solved the same way — identity — but the identity is a "
                "node's position in the tree, and <code>.keyed(\"…\")</code> is how you say when "
                "position is the wrong answer.",
             "ImGui garde son état interne rangé par une pile d'identifiants sur laquelle il faut "
             "raisonner. Ici le même problème est résolu de la même manière — l'identité — mais "
             "l'identité est la position d'un nœud dans l'arbre, et <code>.keyed(\"…\")</code> "
             "est la façon de dire que la position est la mauvaise réponse."),
        ],
    },
    {
        "slug": "from-electron", "name": "Electron",
        "blurb_en": "HTML, CSS and a browser engine in every window",
        "blurb_fr": "HTML, CSS et un moteur de navigateur dans chaque fenêtre",
        "intro_en": "The shape is not far off: a declarative description, rebuilt when state "
                    "changes, laid out by a box model. What goes away is everything underneath — "
                    "no browser engine, no renderer process, no bundler, and a binary that is "
                    "measured in hundreds of kilobytes rather than hundreds of megabytes.",
        "intro_fr": "La forme n'est pas si loin : une description déclarative, reconstruite quand "
                    "l'état change, mise en page par un modèle de boîtes. Ce qui disparaît, c'est "
                    "tout ce qu'il y a en dessous — pas de moteur de navigateur, pas de processus "
                    "de rendu, pas d'empaqueteur, et un binaire qui se compte en centaines de "
                    "kilooctets plutôt qu'en centaines de mégaoctets.",
        "rows": [
            ("&lt;span&gt;Hi&lt;/span&gt;", "label(\"Hi\")", "label(\"Salut\")"),
            ("&lt;button onclick=…&gt;", "button(\"Go\", { -&gt; … })", "button(\"Go\", { -&gt; … })"),
            ("display: flex; flex-direction: column", "column([…])", "column([…])"),
            ("flex: 1", ".grows()", ".grows()"),
            ("&lt;canvas&gt; + 2D context", "custom({ p -&gt; p.canvas… })", "custom({ p -&gt; p.canvas… })"),
            ("a CSS variable theme", "useTheme(darkTheme())", "useTheme(darkTheme())"),
            ("useState / a store", "state(0) and .set(…)", "state(0) et .set(…)"),
        ],
        "notes": [
            ("There is no CSS, and there is no cascade",
             "Il n'y a pas de CSS, et pas de cascade",
             "Style is set on the node, by chained modifiers, or comes from the one theme in "
                "force. Nothing inherits from an ancestor by name and nothing is overridden by a "
                "more specific selector somewhere else in the program. Whether that is a loss "
                "depends entirely on how large your stylesheet had become.",
             "Le style est posé sur le nœud, par modificateurs chaînés, ou vient de l'unique "
             "thème en vigueur. Rien n'hérite d'un ancêtre par son nom et rien n'est écrasé par "
             "un sélecteur plus spécifique ailleurs dans le programme. Que ce soit une perte "
             "dépend entièrement de la taille qu'avait prise votre feuille de style."),
            ("One process, one language, no bridge",
             "Un processus, un langage, pas de pont",
             "There is no main process talking to a renderer over IPC, and no serialising values "
                "to cross it. The interface and the work it does are the same program, and a "
                "handler is an ordinary call.",
             "Il n'y a pas de processus principal qui parle à un processus de rendu par IPC, ni "
             "de valeurs à sérialiser pour traverser. L'interface et le travail qu'elle fait sont "
             "le même programme, et un gestionnaire est un appel ordinaire."),
            ("You give up the web platform, all of it",
             "Vous abandonnez la plateforme web, en entier",
             "No DOM, no npm, no devtools, no accessibility tree, no complex-script text shaping, "
                "no images yet. Electron's weight buys an enormous amount and it is worth being "
                "honest about how much. What you get instead is a program you can read the whole "
                "of, and a window that costs nothing when nobody is touching it.",
             "Pas de DOM, pas de npm, pas d'outils de développement, pas d'arbre "
             "d'accessibilité, pas de mise en forme des écritures complexes, pas encore "
             "d'images. Le poids d'Electron achète énormément et il vaut mieux être honnête sur "
             "la quantité. Ce que vous obtenez à la place, c'est un programme que vous pouvez "
             "lire en entier, et une fenêtre qui ne coûte rien quand personne n'y touche."),
        ],
    },
]
