# The keal-view guide

Everything you need to build an interface, in the order you need it. There is
one idea to hold on to and the rest follows from it:

> **An application is a function from its state to a tree of views.**
> You never say *redraw*. You change a value, and the function runs again.

---

## 1. A window

```keal
import "keal-view/keal-view.keal"

runApp("Hello", 320, 200, { ->
    column([
        label("Hello, keal-view")
    ]).padAll(24.0)
})
```

```sh
tools/build.sh hello.keal && build/hello
```

One import brings the whole framework into scope. `runApp` opens a window and
runs until it is closed. The lambda is the interface — it is called whenever
anything changes, and its job is to describe what should be on screen *now*,
not to change what is there.

Note the `{ -> …}`. A lambda with no arguments needs the arrow; `{ … }` on its
own is an empty map in Keal.

---

## 2. State

State lives in a `Cell`. Read it with `get()`, write it with `set()`. Writing
is what makes the next frame happen.

```keal
val clicks = state(0)

runApp("Counter", 320, 200, { ->
    column([
        label("Clicked ${clicks.get()} times").fontSize(20.0),
        button("Click me", { -> clicks.set(clicks.get() + 1) }).kindOf(primary)
    ]).gaps(12.0).padAll(24.0).aligned(mainCenter, crossCenter).grows()
})
```

There is no diff and no dependency graph: a write rebuilds the whole tree.
Building a few hundred nodes is tens of microseconds, and what you get for it
is that the view function is a pure function of the state, with nothing to
invalidate and nothing to forget to invalidate.

`update` reads and writes in one go, and `invalidate()` says "something
changed" for anything that does not live in a cell:

```keal
clicks.update({ n -> n + 1 })
invalidate()                      // a timer fired, a file finished loading
```

---

## 2¾. Where the state lives

Cells are one answer and they are the right one for a small program. Past a
certain size an application usually wants its state and the things that change
it in the same object — and a lambda can capture `this`, so it can:

```keal
class TodoList {
    var tasks: List<Task> = []
    var draft: String = ""

    proc add() {
        if (this.draft != "") { this.tasks.add(newTask(this.draft)); this.draft = "" }
        invalidate()
    }

    func view(): View {
        return column([
            field(this.draft, "what next?", { s -> this.draft = s }),
            button("Add", { -> this.add() }).kindOf(primary)
        ]).gaps(8.0).padAll(16.0)
    }
}

val list = TodoList()
runApp("Tasks", 460, 520, { -> list.view() })
```

The object holds the truth, `view()` is a pure function of it, and `invalidate()`
says the frame is stale — the same contract a `Cell` has, written out by hand.
[`examples/todo.keal`](../examples/todo.keal) is this, finished.

Two things the language decides for you here, and both are improvements:

**A parameter's contents belong to whoever passed them.** A `Task` received as
an argument cannot be changed; only the list that owns it may. So things are
addressed by identity — `toggle(id)`, not `toggle(task)` — and the question of
who is allowed to write never comes up.

**Careful with a closure you keep.** A lambda that captures `this` and is
stored *inside* the object is a cycle, and reference counting will not collect
it:

```keal
this.render = { -> this.name }        // the object holds the closure that holds it
```

Handlers hung on a view are fine — the tree is thrown away every frame, so
nothing survives to close the loop. It is caching a view, or a callback, in a
long-lived object that does it. `weak` on the back edge breaks one, and
`keal build --audit` names any that are left.

---

## 2½. What persists, and the one trap in it

The tree is thrown away every frame, so anything a *widget* remembers by
itself — a scroll position, a text caret, which end of a selection is which —
cannot live in the tree. It lives beside it, in a map, keyed by **where the
node sits in the tree**.

That is right almost always: the same tree is rebuilt sixty times a second and
every node lands back on its own state. It is wrong exactly once, and it is
worth knowing before it happens to you:

```keal
column(tasks.get().map({ t -> field(t.title, "", { s -> rename(t, s) }) }))
```

Delete the first task. Everything below moves up a place — and the state moves
with the *place*, not with the task. The caret, the selection and the
keystroke you had not finished typing are now in the row underneath. Nothing
crashes; the wrong row is simply focused, and you get to explain it to
somebody.

Give the row a name of its own and the problem disappears:

```keal
field(t.title, "", { s -> rename(t, s) }).keyed(t.id)
```

**The rule: key anything in a list that can be reordered, inserted into or
deleted from.** A fixed layout — a toolbar, a form, a settings page — never
needs one, because nothing ever moves.

---

## 3. Laying things out

Two containers do almost everything.

```keal
column([a, b, c])     // stacked downwards
row([a, b, c])        // stacked across
```

Each child takes the size it asks for. **What is left over goes to the
children that asked for it:**

```keal
row([
    label("left"),
    spacer(),                 // takes everything left over
    label("right")
])
```

```keal
column([
    header().h(48.0),         // a fixed height
    body().grows(),           // everything else
    footer().h(24.0)
])
```

`grows()` is CSS's `flex: 1` — take a share of the room, **starting from
nothing**. Two views with `grows()` split the room evenly; `growsBy(2.0)`
against `growsBy(1.0)` splits it two to one.

There is one trap and it is worth knowing now. `grows()` starts from nothing,
so inside a container that is itself sized by its content there is nothing
left over and a growing child gets zero height. When you want *"at least my
content, and more if there is room"*, use `fills()`:

```keal
card([
    tabs(["One", "Two"], tab.get(), { i -> tab.set(i) }),
    body().fills()            // grows() would collapse it to nothing here
])
```

Spacing and padding:

```keal
column([…]).gaps(8.0)          // between children
column([…]).padAll(16.0)       // inside the container
column([…]).padXY(16.0, 8.0)   // across, then down
column([…]).pads(Insets(8.0, 4.0, 8.0, 12.0))
```

Alignment, along the stacking axis and across it:

```keal
row([…]).aligned(mainCenter, crossCenter)
// main:  mainStart  mainCenter  mainEnd  mainBetween
// cross: crossStart crossCenter crossEnd crossStretch   (stretch is default)
```

Sizes:

```keal
.w(200.0)  .h(48.0)  .sized(200.0, 48.0)   // fixed
.least(120.0, 0.0)                         // a floor, content may ask for more
```

**Nothing shrinks.** Content that does not fit is clipped, not squeezed. A
layout that silently compresses fails only on small windows, which is the last
place anyone looks.

### Layers

`stack` puts children one on top of another in the same rectangle, last one
nearest the viewer. It is how a badge sits on an avatar, and how anything gets
over the interface:

```keal
stack([
    chart(),
    row([spacer(), badge("live")]).padAll(8.0)
])
```

Inside a `stack`, `.at(x, y)` places a child absolutely, at its own size.

---

## 4. Widgets

The full list is in [widgets.md](widgets.md); these are the ones you will
reach for first.

```keal
label("text")                 heading("Section")        title("Page")
caption("small and quiet")    paragraph("wraps to its width")
badge("3")                    icon("check")

button("Save", { -> save() }).kindOf(primary)
iconButton("trash", { -> del() }).tip("Delete")
link("read more", { -> open() })

checkbox("I agree", agreed.get(), { v -> agreed.set(v) })
toggle("Live reload", live.get(), { v -> live.set(v) })
radio("Yearly", plan.get() == 1, { -> plan.set(1) })
segmented(["S", "M", "L"], size.get(), { i -> size.set(i) })
select(["Small", "Medium"], size.get(), { i -> size.set(i) })

slider(volume.get(), 0.0, 1.0, { v -> volume.set(v) })
stepper(count.get(), 0.0, 10.0, 1.0, { v -> count.set(v) })
progress(0.62)

field(name.get(), "your name", { s -> name.set(s) })
secretField(pass.get(), "password", { s -> pass.set(s) })

card([ … ])                   banner(2, "Careful.")
tabView(titles, tab.get(), { i -> tab.set(i) }, body())
scroll([ … ])                 divider()   spacer()   gapV(12.0)
```

Every widget reports **what it would become**, not what it is: a checkbox
hands you `true` when it is off and you were about to turn it on. It never
flips itself — the tree is rebuilt from your state, so your state is the only
thing that decides.

```keal
checkbox("I agree", agreed.get(), { v -> agreed.set(v) })
//                  ↑ what it shows        ↑ what you do about it
```

---

## 5. Style

Any view can carry a background, a border, a corner and a shadow. That is what
makes a plain `column` able to be a card without a card widget existing.

```keal
column([ … ])
    .bg(theme().surface)
    .rounded(12.0)
    .outline(theme().border, 1.0)
    .raised(14.0)              // a shadow, this many points across
    .padAll(16.0)
```

Text:

```keal
label("…").fontSize(20.0).bold().mono().color(theme().accent)
label("…").centered()          // or .trailing()
```

Colours come from the theme, or from you:

```keal
theme().accent      theme().textSecondary     theme().surfaceHi
web("#3b82f6")      rgb(59, 130, 246)         rgba(59, 130, 246, 128)
mix(a, b, 0.5)      lighten(c, 0.1)           fade(c, 0.5)
```

### Themes

There is one theme in force, and everything reads it:

```keal
theme()                       // the one in use
useTheme(lightTheme())        // change it — the next frame is in the new one
flipTheme()                   // swap between dark and light
```

To change how everything looks, change the theme rather than the widgets:

```keal
val t = darkTheme()
t.accent = web("#8b5cf6")
t.radiusMd = 4.0
t.fontBase = 14.0
useTheme(t)
```

**Everything measures in points, never pixels.** The rasteriser is the only
thing that knows what a pixel is, so one layout is correct on a Retina display
and on a projector.

---

## 6. Menus, dialogs and tooltips

These appear *over* an interface rather than in it, so they are calls rather
than nodes in your tree. Nothing needs installing.

```keal
openMenu(x, y, ["Open…", "Save", "Close"], -1, { i -> did(i) })
openIconMenu(x, y, names, icons, selected, { i -> … })

openDialog("Delete the project?", { ->
    column([
        paragraph("This cannot be undone."),
        row([spacer(),
             button("Cancel", { -> closePopup() }).kindOf(quiet),
             button("Delete", { -> closePopup(); del() }).kindOf(danger)])
    ])
})

openSheet(…)     // the same, but a click outside or Escape puts it away
closePopup()
```

A tooltip is a modifier, not a call:

```keal
iconButton("trash", { -> del() }).tip("Delete this file")
```

---

## 7. A view that draws itself

When no widget fits, draw. `custom` is handed a `Paint`: a canvas already
clipped to its own rectangle, that rectangle in points, the fonts, the theme,
and whether the pointer is on it.

```keal
custom({ p ->
    val r = shrink(p.area, 8.0)
    p.canvas.fillRound(r, 8.0, p.theme.surfaceHi)
    p.canvas.line(r.x, bottom(r), right(r), r.y, 2.0, p.theme.accent)
    p.text("a chart", Rect(r.x, r.y, r.w, 18.0), 0, p.theme.small(), p.theme.textMuted)
    if (p.hot) { p.canvas.strokeRound(r, 8.0, 1.0, p.theme.accent) }
}).h(120.0)
```

The canvas has `fillRect` `fillRound` `strokeRound` `fillCircle` `line`
`gradient` `shadow` `clear` `push`/`pop` (clipping) and `mask`. `Paint` adds
`text` `line` `width` `lineHeight` `ascent` for anything with letters in it.

A custom view can take input too:

```keal
custom({ p -> … })
    .tappable({ -> chose() })
    .dragged({ x, y -> start(x, y) }, { x, y -> moved(x, y) }, { x, y -> dropped(x, y) })
```

`grab`, `move` and `drop` are all given window points. A press that never
moved is a click and fires `onTap` instead — you never have to tell them
apart yourself.

---

## 8. Keyboard

Tab walks the controls that can take focus, in the order you declared them.
Text fields handle typing, selection, Home/End, and copy, cut and paste with
the platform's own modifier. Escape puts away a popup, then gives up focus.

For shortcuts of your own:

```keal
val app = App("Editor", 900, 600)
app.build = { -> … }
app.onKey = { e ->
    if (e.cmd() and (e.text == "s")) { save(); true }
    else { if (e.key == keyEscape()) { deselect(); true } else { false } }
}
run(app)
```

`e.cmd()` is Command on macOS and Control everywhere else, so one line covers
both. Answer `true` to say you handled it.

---

## 9. Docking

For an application whose panels the user arranges: splits, tab groups, and
dragging a panel from one to another.

```keal
val dock = Dock(
    beside(
        leaf(["files"]),
        above(leaf(["editor"]), leaf(["terminal"]), 0.7),
        0.2))

dock.add(panelOf("files",    "Files",    { -> filesPanel() }))
dock.add(panelOf("editor",   "main.keal", { -> editorPanel() }))
dock.add(panelOf("terminal", "Terminal", { -> terminalPanel() }))

app.build   = { -> column([toolbar(), dockView(dock).grows()]).grows() }
app.overlay = { -> dockOverlay(dock) }
```

`beside(a, b, f)` puts them side by side with `a` taking fraction `f`;
`above(a, b, f)` stacks them. A panel is an ordinary view function and does
not know it is docked. `dock.reveal("files")` brings one to the front;
`dock.detach("files")` takes it out.

The overlay is what draws the highlight while a panel is being dragged. Give
it to `app.overlay` or the drag has no feedback.

---

## 10. Seeing what you built

Every keal-view program understands two flags for free:

```sh
build/app --snapshot frame.bmp 2            # one frame to a file, no window
build/app --snapshot frame.bmp 2 900 1900   # …at a size of your choosing
build/app --window-id /tmp/id               # its own window number
```

The first needs no display at all, which is how this framework is tested in
continuous integration. `tools/bmp2png.py` turns the result into a PNG, and
`tools/shot.sh build/app out.png` uses the second to photograph a running
window without capturing anything else on the screen.

---

## Where to look next

* [`widgets.md`](widgets.md) — every constructor and modifier
* [`examples/gallery.keal`](../examples/gallery.keal) — all of it, running
* [`examples/calculator.keal`](../examples/calculator.keal) — a small whole app
* [`examples/studio.keal`](../examples/studio.keal) — docking, and two views
  that draw themselves
