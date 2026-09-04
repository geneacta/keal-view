# Reference

Everything public, in one place. The [guide](guide.md) explains how the pieces
fit; this says what each one is.

All sizes are in **logical points**. All colours are `Int`s holding
`0xAARRGGBB` — build them with `rgb`, `rgba`, `web` or the theme.

---

## Running

| | |
|---|---|
| `runApp(title, w, h, build)` | open a window and run until it is closed |
| `App(title, w, h)` | the same, when you want to set more than `build` |
| `run(app)` | run one |
| `snapshot(app, w, h, scale, path)` | draw one frame to a BMP, no window |

An `App` has `build`, `overlay`, `onKey`, `onStart` and `onStop`. Every
program also understands `--snapshot <file> [scale] [w h]` and
`--window-id <file>` on its command line without being told to.

## State

| | |
|---|---|
| `state(initial)` | a `Cell<T>` holding a value |
| `cell.get()` / `cell.set(v)` | read it, write it |
| `cell.update({ v -> … })` | read and write in one go |
| `invalidate()` | something changed that is not in a cell |
| `revision()` | how many times anything has been written |

## Containers

| | |
|---|---|
| `column(kids)` | stacked downwards |
| `row(kids)` | stacked across |
| `stack(kids)` | one on top of another, last nearest the viewer |
| `box(kid)` | one child, somewhere to hang a background or a padding |
| `card(kids)` | a surface with a border, a corner and room to breathe |
| `raisedCard(kids)` | the same, with a shadow |
| `panel(title, kids)` | a titled surface with a heading strip |
| `scroll(kids)` | scrolls vertically when the content is taller than the box |
| `tabView(titles, index, onChange, content)` | a tab strip with its content under it |

## Space

| | |
|---|---|
| `spacer()` | takes everything left over — two of them centre what is between |
| `gapV(h)` / `gapH(w)` | a fixed gap |
| `divider()` | a hairline across the container |
| `nothing()` | no size, no ink, no answer to the pointer |

## Text

| | |
|---|---|
| `label(s)` | one line |
| `caption(s)` | smaller and quieter |
| `heading(s)` | a section heading |
| `title(s)` | a page title |
| `paragraph(s)` | wraps to the width it is given |
| `badge(s)` | a small pill — a count, a status, a tag |
| `link(s, onTap)` | a line of text that acts on a click |
| `banner(level, s)` | something to say: `0` plain, `1` good, `2` warning, `3` failure |

## Controls

| | |
|---|---|
| `button(s, onTap)` | with `.kindOf(primary \| plain \| quiet \| danger)` |
| `iconButton(name, onTap)` | a button that is only an icon |
| `menuButton(name, choices, onPick)` | an icon button that opens a menu |
| `checkbox(s, on, changed)` | a box that is ticked or not |
| `radio(s, on, chose)` | one of several, shown as a dot |
| `toggle(s, on, changed)` | the same choice as a switch |
| `segmented(choices, index, onChange)` | a row of choices, one pressed |
| `select(choices, index, onChange)` | a dropdown, opening a menu of them |
| `slider(value, lo, hi, changed)` | a value chosen by dragging |
| `stepper(value, lo, hi, step, changed)` | a number with a minus and a plus |
| `progress(value)` | a bar showing a fraction, taking no input |
| `field(value, hint, changed)` | a line of text the user types |
| `secretField(value, hint, changed)` | the same, showing dots |
| `tabs(titles, selected, chose)` | a strip of tabs on its own |
| `icon(name)` | a shape drawn from strokes |

Every control reports **what it would become**, not what it is: a checkbox
hands you `true` when it is off. Nothing flips itself; the tree is rebuilt
from your state.

### Icon names

`check` `close` `plus` `minus` `chevron-up` `chevron-down` `chevron-left`
`chevron-right` `menu` `dot` `search` `play` `pause` `warning` `folder`
`file` `trash` `gear` `backspace`

An unknown name draws a hollow square, so a typo is visible rather than
silent.

## Drawing your own

| | |
|---|---|
| `custom(draw)` | a view that paints itself |
| `underlay(draw)` | the same, taking up no room — a background inside a `stack` |

`draw` is given a `Paint`:

| | |
|---|---|
| `p.canvas` | a `Canvas`, already clipped to this view |
| `p.area` | this view's rectangle, in points |
| `p.theme` `p.fonts` | what everything else is drawn with |
| `p.hot` `p.pressed` | whether the pointer is over it, and over it with a button down. "Over" does not require the view to take clicks — but it is false wherever something that *does* has the pointer instead, so while a popup is open nothing beneath it is under the pointer |
| `p.text(s, r, align, style, col)` | one line in a box, cut with an ellipsis if it must be |
| `p.line(s, x, baseline, style, col)` | one line on a baseline; answers where the pen ended |
| `p.width(s, st)` `p.lineHeight(st)` `p.ascent(st)` | measuring |

`Canvas`: `clear` `fillRect` `fillRound` `strokeRound` `fillCircle` `line`
`gradient` `shadow` `mask` `plot` `run` `push` `pop` `clip` `bounds`.

## Modifiers

Each answers the same view, so they chain. A newline after `)` ends a
statement in Keal, so keep a chain on one line or break it into statements.

### Size and space

| | |
|---|---|
| `.w(v)` `.h(v)` `.sized(w, h)` | a fixed size |
| `.least(w, h)` | a floor; the content may still ask for more |
| `.grows()` | a share of the room, starting from **nothing** (CSS `flex: 1`) |
| `.growsBy(f)` | a named share, on the same terms |
| `.fills()` | what the content needs **and** a share of what is left |
| `.shares()` | on a container: children divide the room in exact proportion |
| `.pads(insets)` `.padAll(v)` `.padXY(h, v)` | space inside |
| `.margin(v)` | space outside |
| `.gaps(v)` | space between children |
| `.aligned(main, cross)` | how children sit along and across the axis |
| `.at(x, y)` | inside a `stack`: sit here, at your own size |

Alignment values: `mainStart` `mainCenter` `mainEnd` `mainBetween`, and
`crossStart` `crossCenter` `crossEnd` `crossStretch` (stretch is the default).

### Look

| | |
|---|---|
| `.bg(col)` | a background |
| `.outline(col, width)` | a border |
| `.rounded(r)` | corners |
| `.raised(blur)` | a shadow this many points across |
| `.color(col)` | the text colour |
| `.font(style)` `.fontSize(v)` `.bold()` `.mono()` | the text |
| `.centered()` `.trailing()` | where the text sits in its box |
| `.wrapping()` | wrap instead of cutting with an ellipsis |
| `.kindOf(v)` | a button's family: `plain` `primary` `quiet` `danger` |
| `.withIcon(name)` | an icon before the label |

### Behaviour

| | |
|---|---|
| `.off()` / `.offWhen(c)` | grey it out and stop it responding |
| `.shownWhen(c)` | draw it, or do not |
| `.keyed(s)` | give it a name, so its own state follows **it** and not its position — required for anything in a list that can be reordered, inserted into or deleted from |
| `.tip(s)` | a note beside the pointer while it rests here |
| `.pointer(c)` | the pointer shape: `cursorArrow` `cursorHand` `cursorText` `cursorResizeH` `cursorResizeV` |
| `.tappable(f)` | take a click without being a control |
| `.dragged(grab, move, drop)` | answer the pointer with a drag; a press that never moved is a click |

## Over the interface

| | |
|---|---|
| `openMenu(x, y, choices, selected, onPick)` | a list of choices at a point |
| `openIconMenu(x, y, choices, icons, selected, onPick)` | the same, with icons |
| `openDialog(title, content)` | a modal box over a dimmed interface |
| `openSheet(title, content)` | the same, dismissed by a click outside or Escape |
| `closePopup()` `popupOpen()` | put it away, ask whether anything is showing |
| `.tip(s)` | a tooltip, as a modifier rather than a call |

Nothing needs installing: the run loop draws this layer above the
application's own overlay, every frame.

## Theme

| | |
|---|---|
| `theme()` | the one in force — everything reads it |
| `useTheme(t)` | change it |
| `flipTheme()` | swap dark and light |
| `darkTheme()` `lightTheme()` | the two built in |

A `Theme` holds `bg` `surface` `surfaceHi` `surfaceDown` `border`
`borderStrong` · `textPrimary` `textSecondary` `textMuted` `textOnAccent` ·
`accent` `accentHover` `accentDown` `accentSoft` · `success` `warning`
`danger` `shadow` · `radiusSm` `radiusMd` `radiusLg` `radiusPill` · `unit`
`hairline` · `fontSm` `fontBase` `fontLg` `fontTitle` · `control` `strip` ·
`dark`.

And `t.gap(n)` for `n` units of the spacing grid, `t.body()` `t.small()`
`t.heading()` `t.title()` for the text styles.

## Colour

| | |
|---|---|
| `rgb(r, g, b)` `rgba(r, g, b, a)` `gray(v)` | channels, 0–255 |
| `web("#3b82f6")` | three, six or eight hex digits, with or without the `#` |
| `redOf` `greenOf` `blueOf` `alphaOf` | back out again |
| `withAlpha(c, a)` `fade(c, f)` | change the opacity |
| `mix(a, b, t)` `lighten(c, f)` `darken(c, f)` | between colours |
| `luma(c)` `contrasting(c)` | how bright it reads; black or white on top of it |
| `over(dst, src, cov)` | composite — the per-pixel operation |

An unreadable `web` string answers opaque magenta, which is easier to see on
screen than it is to miss in a log.

## Geometry

`Rect(x, y, w, h)` `Pt(x, y)` `Size(w, h)` `Insets(l, t, r, b)`, and
`all(v)` `axes(h, v)`.

| | |
|---|---|
| `right` `bottom` `centerX` `centerY` `center` `sizeOf` `isEmpty` | reading one |
| `holds(r, x, y)` | is the point inside? Left and top edges belong to it, right and bottom do not |
| `inset` `shrink` `grow` `offset` | moving one |
| `intersect` `union` `overlaps` `centered` | two of them |
| `cut(r, edge, amount)` / `cutRest(…)` | take a strip off an edge, or keep the rest |
| `clampF` `clampI` `lerpF` `floorI` `ceilI` `roundI` | arithmetic |

## Docking

| | |
|---|---|
| `Dock(node)` `dockOf(ids)` | an arrangement |
| `leaf(ids)` | a group of tabs |
| `beside(a, b, f)` `above(a, b, f)` | a split, `a` taking fraction `f` |
| `panelOf(id, title, body)` | a dockable panel |
| `dock.add(panel)` `dock.panel(id)` `dock.holder(id)` | registering and finding |
| `dock.reveal(id)` | bring a panel to the front of its group |
| `dock.detach(id)` | take it out; empty groups and their splits are pruned |
| `dock.dropInto(nid, zone, id)` | put it back: `zoneLeft` `zoneRight` `zoneTop` `zoneBottom` `zoneCentre` |
| `dockView(dock)` | the arrangement, as views |
| `dockOverlay(dock)` | the highlight while a panel is being dragged — give it to `app.overlay` |

## Events

An `Event` has `kind` `x` `y` `button` `key` `mods` `clicks` `dx` `dy` `text`,
and `e.cmd()` (Command on macOS, Control elsewhere), `e.shift()`, `e.alt()`,
`e.has(mod)`.

Kinds: `evNone` `evClose` `evResize` `evMove` `evDown` `evUp` `evScroll`
`evKeyDown` `evKeyUp` `evText` `evFocus` `evBlur` `evExpose`.

Named keys: `keyLeft` `keyRight` `keyUp` `keyDown` `keyEnter` `keyTab`
`keyBackspace` `keyDelete` `keyEscape` `keyHome` `keyEnd` `keyPageUp`
`keyPageDown` `keySpace`. Printable characters arrive as `evText` instead.
