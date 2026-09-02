# Testing a backend that has never run

`runtime/kv_cocoa.m` is verified: keal-view was developed on a Mac.
`runtime/kv_win32.c` and `runtime/kv_x11.c` were written against the same
dozen functions, compile on their own platforms in CI, and **have never opened
a window**. This is the checklist for the first person who does.

Read it top to bottom. The order matters: it separates "the framework is
broken" from "the backend is broken" before you have to guess.

---

## 0. What you need

**Windows** — MinGW-w64 in a **POSIX-threads** flavour, or LLVM clang
targeting mingw32. MSVC cannot compile Keal's runtime: it uses GCC's overflow
builtins. `keal doctor` says which compiler it found. You also need a `bash`
— Git Bash or MSYS2 — because `tools/build.sh` is a `/bin/sh` script.

**Linux** — a C compiler and `libx11-dev` (Debian, Ubuntu) or `libX11-devel`
(Fedora), plus a TrueType font: `fonts-dejavu-core` is what CI installs.

Both — Rust, to build the Keal compiler.

```sh
git clone https://github.com/geneacta/keal
git clone https://github.com/geneacta/keal-view
cd keal && cargo build --release && cd ../keal-view
tools/build.sh examples/gallery.keal
```

---

## 1. Before the window: is the framework itself alright?

```sh
build/units                                        # or build/units.exe
build/gallery --snapshot frame.bmp 2 900 1900
python3 tools/bmp2png.py frame.bmp frame.png
```

Neither touches the window, the event queue or the platform's drawing at all.
The first asserts 131 things about colour, geometry, layout, docking, fonts
and input dispatch. The second exercises the rasteriser, the TrueType engine
and the layout, and writes the result to a file.

**This is the bisection.** If `frame.png` is right and the window is wrong,
the fault is in the backend and nowhere else. If `frame.png` is wrong, the
fault is above the backend and every platform has it.

Look for, in `frame.png`:

* **letters, not empty rectangles.** Rectangles mean `kvp_font_path` found no
  font. It tries `segoeui.ttf`, `tahoma.ttf`, `arial.ttf` under
  `C:\Windows\Fonts`; on Linux, DejaVu, Liberation, FreeSans and Noto under
  the usual `/usr/share/fonts` paths. Add yours to that list if it is
  somewhere else.
* **sharp text**, not blurred or doubled.
* **round corners that are round**, and borders one pixel thick.

---

## 2. The window, in the order things go wrong

1. **It opens, and comes to the front.** A process started from a terminal is
   not always allowed the foreground.
2. **The picture is the right way up.** Windows passes a DIB of *negative*
   height for top-down rows; X11 sets the image's `byte_order` to `LSBFirst`
   and lets Xlib convert. If everything is upside down, that is the line.
3. **The colours are right.** The framebuffer is `0xAARRGGBB` in a
   `uint32_t`, and all three platforms are supposed to read that without
   conversion. Red and blue swapped means they do not, on yours.
4. **Resizing** — drag a corner. It should redraw without lag, tearing or a
   white flash. A white flash on Windows is `WM_ERASEBKGND`, which the
   backend does not handle yet.
5. **Scale.** On a display at 125 %, 150 % or 2×, everything should be
   *larger and still sharp*, never stretched and soft. Windows asks
   `GetDpiForWindow` after `SetProcessDpiAwarenessContext`; X11 reads
   `Xft.dpi` from the resource database. Soft, stretched output means the
   process was not made DPI-aware and the system is scaling the window for
   it.
6. **The pointer shape.** An arrow over most things, an **I-beam** over the
   text fields in the gallery's *Saisie* section, and **↔** over the dividers
   in the studio. Flicker, or a shape that never changes, is the cursor path.
7. **Hover.** Buttons lighten under the pointer. This is the whole mouse-move
   path in one glance.
8. **Typing.** Click a field and type. Then type an accented character, and
   one outside Latin-1 if your keyboard has one. Both backends decode to
   UTF-8 by hand — Windows folds surrogate pairs, X11 takes what
   `XLookupString` gives — and neither path has ever run.
9. **Clipboard.** Select in a field, **Ctrl+C**, then **Ctrl+V** somewhere
   else. On X11 this is a real selection owner answering real
   `SelectionRequest` events; try pasting into another application too, and
   copying *from* one.
10. **The wheel**, over the scrolling list in the gallery's *Regroupements*
    section.
11. **A double click** in a text field should select a word's worth of
    ground — at minimum, `clicks` should reach 2.
12. **The title bar.** Dark where the system offers it: Windows tries
    `DwmSetWindowAttribute` 20 then 19, and older builds have neither — a
    light bar over a dark window there is **correct**, not a bug. X11 has no
    title bar of its own at all; the window manager draws it, and
    `_GTK_THEME_VARIANT` is a hint it may ignore.
13. **Closing.** The close box ends the process, with nothing left running.

Then the two real applications:

```sh
build/calculator        # digits, +, Enter, Escape from the keyboard too
build/studio            # the one that matters
```

In the studio: **drag a panel by its tab** onto another one. A blue region
should show where letting go would put it, *before* you let go — left, right,
above, below, or as another tab. Drag the dividers between panels. Close a tab
with its ×. Press *Ranger* to put it all back.

---

## 3. Reporting

What helps, in order: the exact error text if there is one; otherwise **what
you see**, said plainly — "the text is upside down", "the red buttons are
blue", "nothing happens on hover". A screenshot if you can attach one
anywhere; the description is enough otherwise.

Say which of the two the snapshot in step 1 was. That one fact decides which
half of the codebase to look in.

## 4. What will not work on your platform, and should not

* `tools/shot.sh` photographs a window by its number through macOS's
  `screencapture`. There is no portable equivalent; take a screenshot the
  usual way.
* `--window-id` answers an `HWND` on Windows and an X11 `Window` on Linux.
  Both are the system's real handle, and neither is any use to
  `screencapture`.
