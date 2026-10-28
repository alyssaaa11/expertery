# Keel manual (internal wiki)

*Quillon Orbital Works · Structures team · Keel v1.0.0 · QX-2 controlled: on-prem only.*
*Fictional company, made for the Forge demo.*

Keel is our small internal tool for describing machined satellite parts in Python.
A Keel program is a short recipe: start from a base block, add walls and bosses,
cut holes, pockets and slots, and finish with exactly one solid. Keel compiles
the recipe to a solid model internally, and the Gauge station checks the result
against the design request. If you can write the recipe, you can make the part.

## 1. Conventions (read this first)

All dimensions are millimetres. The datum is the part's **lower-left-bottom
corner** at (0, 0, 0): +X points east, +Y points north, +Z points up. Nothing is
centred unless the call says so; every position is measured from the datum.

The four edges of the base stock have names: **north** (+Y side), **south**
(−Y side), **east** (+X side), **west** (−X side).

Holes never use raw diameters. Always use a **company fastener code** from
table KF below; the Gauge station checks the exact diameters, so a 4 mm drill
where a KF-M4 belongs will FAIL the part.

Two company standards apply whenever a request says "standard": wall thickness
**2.5 mm**, fillet radius **1.0 mm**.

Part numbers tell you the family: BRK (bracket), PLT (plate), FRM (frame),
STD (standoff), CLP (clip). The `material=` argument (default `AL6061`) is
metadata only and never changes the shape.

A program has a fixed shape: one `stock()` call first, then features, then
`p.finish()` last. `finish()` returns the single solid.

## 2. Fastener table KF

| Code  | Clearance hole Ø | Counterbore Ø × depth |
|-------|------------------|-----------------------|
| KF-M2 | 2.4              | 4.4 × 2.0             |
| KF-M3 | 3.4              | 6.5 × 3.0             |
| KF-M4 | 4.5              | 8.0 × 4.0             |
| KF-M5 | 5.5              | 10.0 × 5.0            |
| KF-M6 | 6.6              | 11.0 × 6.0            |

Suffix `-CB` means counterbored from the top face, e.g. `KF-M4-CB`.

## 3. API

```python
import keel
p = keel.part("BRK-0412", material="AL6061")
```

**stock(L, W, T)** — the base block, x in [0, L], y in [0, W], z in [0, T].
Exactly one per part, and it must be the first call.

```python
p.stock(60, 40, 4)
```

**wall(edge, h, t=None)** — a wall standing on the top face along a named
edge (`north`, `south`, `east`, `west`). It sits flush with that edge, runs the
full edge length, and rises `h` above the stock top. `t` defaults to the
standard wall of 2.5.

```python
p.wall("north", 25)
```

**boss(at=(x, y), dia, h)** — a cylinder on the top face centred at (x, y),
`h` high.

```python
p.boss(at=(15, 15), dia=12, h=10)
```

**hole(code, at=(x, y))** — a through hole, all the way down, using a KF code.
A `-CB` code adds the counterbore from the top face.

```python
p.hole("KF-M4-CB", at=(8, 8))
```

**pocket(at=(x, y), L, W, depth)** — a rectangular pocket cut from the top
face. (x, y) is the pocket's lower-left corner; `depth` must be less than the
stock thickness.

```python
p.pocket(at=(10, 10), L=80, W=60, depth=4)
```

**slot(at=(x1, y1), to=(x2, y2), width, depth="thru")** — a straight slot with
round ends along the centre line from start to end. `depth="thru"` cuts all the
way through; a number cuts a blind slot that deep from the top face.

```python
p.slot(at=(10, 15), to=(40, 15), width=5)
```

**pattern(nx, ny, dx, dy)** — repeats the LAST feature call in a grid, `nx`
by `ny` positions spaced `dx`, `dy` apart. The total is nx × ny instances
including the original call's position. Only boss, hole, pocket and slot can
be patterned. (A leading text label, e.g. `pattern("hole", 2, 2, 48, 28)`, is
accepted and ignored.)

```python
p.hole("KF-M4", at=(6, 6))
p.pattern(2, 2, 48, 28)
```

**fillet(edges="vertical", r=None)** — rounds the stock's 4 vertical outer
edges. `r` defaults to the standard fillet of 1.0. Only `edges="vertical"`
exists.

```python
p.fillet()
```

**finish()** — returns the part as exactly one solid. Must be the last call;
every program ends with `solid = p.finish()`.

```python
solid = p.finish()
```

**keel.render(p, path)** — writes an SVG preview of a finished part for the
dashboard catalogue. It needs a finished part, so call it after `finish()`.

```python
keel.render(p, "brk_0101.svg")
```

## 4. Error messages

Keel errors are plain sentences starting with `keel:`. The common ones:

- `keel: unknown fastener code 'M4'; holes use company codes KF-M2 ...` — you
  used a raw size instead of a KF code.
- `keel: stock() called twice; a part has exactly one base block ...` — delete
  the second `stock()`.
- `keel: hole() called before stock(); every part starts with p.stock(L, W, T)`
  — `stock()` must be the first call.
- `keel: unknown edge 'top'; edges are named 'north', 'south', 'east' or 'west'`.
- `keel: pattern() with no previous feature; call a feature first`.
- `keel: render() before p.finish(); finish the part first ...`.

## 5. Worked examples

L-bracket, 60 × 40 base with a north wall and four corner holes:

```python
import keel
p = keel.part("BRK-0101", material="AL6061")
p.stock(60, 40, 4)
p.wall("north", 25)
p.hole("KF-M4", at=(6, 6))
p.pattern(2, 2, 48, 28)
p.fillet()
solid = p.finish()
```

Standoff: a foot with a centre boss, drilled through the boss:

```python
import keel
p = keel.part("STD-0044", material="AL6061")
p.stock(30, 30, 4)
p.boss(at=(15, 15), dia=12, h=10)
p.hole("KF-M4", at=(15, 15))
p.hole("KF-M3", at=(5, 5))
p.pattern(2, 2, 20, 20)
solid = p.finish()
```

Clip with a through slot and an end wall:

```python
import keel
p = keel.part("CLP-0012", material="AL6061")
p.stock(50, 30, 4)
p.slot(at=(10, 15), to=(40, 15), width=5)
p.wall("west", 10)
p.hole("KF-M3", at=(45, 8))
p.pattern(1, 2, 0, 14)
solid = p.finish()
```

New here? Copy one example, change the numbers to match your design request,
and run it through the Gauge station before ordering metal.
