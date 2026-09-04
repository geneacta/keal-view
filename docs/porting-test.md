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

**The compiler moves too.** keal-view uses language features that arrived
because keal-view asked for them, so `git pull` in `../keal` and
`cargo build --release` are part of updating this repository, not a separate
errand. A stale compiler refuses with `the C backend cannot compile …`,
naming the construct — that message means the compiler is behind, not that
your machine is at fault.

And do not pipe `tools/build.sh` into anything. A pipeline's exit status is
the last command's, so `tools/build.sh … | tail -2 && ./units` runs the old
binary after a failed build and tells you nothing about why it behaves
strangely. `tools/test.sh` prints the compiler it used, for the same reason.

---

## 1. Before the window: is the framework itself alright?

```sh
build/units                                        # or build/units.exe
build/gallery --snapshot frame.bmp 2 900 1900
python3 tools/bmp2png.py frame.bmp frame.png
```

`units` prints how many checks it ran; the number grows, so compare it against
what it says on a machine that works rather than against a number written
down here.

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
4. **Resizing** — drag a corner. It should redraw without lag or a white
   flash. A white flash on Windows is `WM_ERASEBKGND`, which the backend does
   not handle yet.

   **Tearing during a fast drag is not testable this way, and saying so is
   better than guessing.** Repeated screen capture tops out around sixty
   milliseconds between frames, and a tear lives inside one frame; `--trace`
   counts frames rather than looking at them. A report that says "neither seen
   nor ruled out" is worth more here than one that says "looks fine". It would
   take a capture card or a camera, and nobody has needed it enough yet.
5. **Scale.** On a display at 125 %, 150 % or 2×, everything should be
   *larger and still sharp*, never stretched and soft. If your screen is at
   100 % you cannot see this, and **you must not change the setting to find
   out** — it is not your machine. You can still check the half that does not
   need eyes, and it is the half worth checking: ask the live window whether
   it is DPI-aware at all. On Windows,
   `AreDpiAwarenessContextsEqual(GetWindowDpiAwarenessContext(hwnd), (void*)-4)`
   answers whether `PER_MONITOR_AWARE_V2` took. Beware
   `GetAwarenessFromDpiAwarenessContext`, which answers `2` for both V1 and
   V2 — the enumeration has no value for V2, and only the comparison
   distinguishes them. Windows asks
   `GetDpiForWindow` after `SetProcessDpiAwarenessContext`; X11 reads
   `Xft.dpi` from the resource database. Soft, stretched output means the
   process was not made DPI-aware and the system is scaling the window for
   it.
6. **The pointer shape.** An arrow over most things, an **I-beam** over the
   text fields in the gallery's *Saisie* section, and **↔** over the dividers
   in the studio. Flicker, or a shape that never changes, is the cursor path.
7. **Hover.** Buttons lighten under the pointer. This is the whole mouse-move
   path in one glance — with the window **focused**, which is the case to
   test. Whether hover also works while the window is *not* focused is left
   to the platform and is not a defect either way: Windows and X11 deliver
   pointer motion to an unfocused window and so it does, macOS delivers none
   to an inactive application and so it does not. Making them agree would mean
   overriding one platform's own convention, which is a worse answer than
   this sentence.
8. **Typing.** Click a field and type. Then type an accented character, and
   one outside Latin-1 if your keyboard has one. Both backends decode to
   UTF-8 by hand — Windows folds surrogate pairs, X11 takes what
   `XLookupString` gives — and neither path has ever run.
9. **Clipboard.** This one is only testable by hand: on X11 a selection is
   owned by a *window*, so `build/units` — which never opens one — skips it
   and says so, even on a machine whose display is answering. Select in a
   field of the gallery, **Ctrl+C**, then **Ctrl+V** somewhere
   else. On X11 this is a real selection owner answering real
   `SelectionRequest` events; try pasting into another application too, and
   copying *from* one. Do it **quickly**, several times: `OpenClipboard` on
   Windows is a lock the system's clipboard-history service also takes, and a
   write followed immediately by a read is where that shows. The backend
   retries; a failure here would mean it does not retry enough.
10. **The wheel**, over the scrolling list in the gallery's *Regroupements*
    section.
11. **A double click** in a text field should select a word's worth of
    ground — at minimum, `clicks` should reach 2.
12. **The title bar.** Dark where the system offers it: Windows tries
    `DwmSetWindowAttribute` 20 then 19, and older builds have neither — a
    light bar over a dark window there is **correct**, not a bug. X11 has no
    title bar of its own at all; the window manager draws it, and
    `_GTK_THEME_VARIANT` is a hint it may ignore.
13. **The processor at rest.** Window open, nothing animating, and — this is
    the part that matters — measure it **twice**: once with the pointer well
    away from the window, and once with the pointer resting *over* it and not
    moving. Both should be **0,0 %**; a stationary cursor is not an event.
    The second case was broken on Windows for two days while the first was
    perfect, so one reading here says almost nothing. Take it from accumulated
    processor time over several seconds rather than from a one-second sample,
    and run the same measurement against a text editor as a control.

14. **Closing.** The close box ends the process, with nothing left running.

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

## 2½. Before you report an input problem, run the control

Both false positives in this project's first two test passes came from the
harness rather than the framework, and both were caught the same way: doing
the same thing to a program that is known to work.

Arrow keys sent with `SendInput` and no `KEYEVENTF_EXTENDEDKEY` are treated as
the numeric keypad's, and Windows then cancels the Shift around them — so
Shift+Arrow selected nothing, in a way that looked exactly like a missing
selection. And a burst of synthesised keystrokes dropped characters, which
looked exactly like a full event queue, until the same burst was sent to
Notepad and dropped them there too.

So: if input seems to be lost or ignored, send the same input to a text editor
first. If it is lost there as well, the report is about your injection and not
about this framework.

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
