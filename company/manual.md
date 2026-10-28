# Keel manual (internal wiki)

*Quillon Orbital Works · Structures team · Keel v2.1.0 · QX-2 controlled: on-prem only.*
*Fictional company, made for the Forge demo.*

Keel is our small internal tool for describing machined satellite parts in Python.
A Keel program is a short recipe: start from a base block, add walls and bosses,
cut holes, pockets and slots, and finish with exactly one solid. Keel compiles
the recipe to a solid model internally, and the Gauge station checks the result
against the design request. If you can write the recipe, you can make the part.

v2 adds company knowledge: materials that change the standards, flight-part
rules, countersinks, holes in walls, standard mounts, and mirroring. Every v1
program still builds exactly the same solid.

## 1. Conventions (read this first)

All dimensions are millimetres. The datum is the part's **lower-left-bottom
corner** at (0, 0, 0): +X points east, +Y points north, +Z points up. Nothing is
centred unless the call says so; every position is measured from the datum.
Exception: **FRM requests are dimensioned from the frame centre** (section 6).

The four edges of the base stock have names: **north** (+Y side), **south**
(−Y side), **east** (+X side), **west** (−X side).

Holes never use raw diameters. Always use a **company fastener code** from
table KF below; the Gauge station checks the exact diameters, so a 4 mm drill
where a KF-M4 belongs will FAIL the part.

Standards depend on the material (section 2). Whenever a request says
"standard", use your material's row. "Flight part" in a request means
`cls="FLIGHT"` (section 3).

Part numbers tell you the family: BRK (bracket), PLT (plate), FRM (frame),
STD (standoff), CLP (clip).

A program has a fixed shape: one `stock()` call first, then features, then
`p.finish()` last. `finish()` returns the single solid.

## 2. Materials and fastener table KF

| Material | Standard wall | Standard fillet | Minimum wall |
|----------|---------------|-----------------|--------------|
| AL6061 (aluminium) | 2.5 | 1.0 | 1.5 |
| TI6AL4V (titanium) | 3.0 | 1.5 | 2.0 |
| SS316 (stainless) | 2.0 | 0.5 | 1.2 |

A wall thinner than your material's minimum is rejected with a KeelError.
An unknown material is rejected; the three codes above are the only ones.

| Code  | Clearance hole Ø | Counterbore Ø × depth | Countersink Ø at top |
|-------|------------------|-----------------------|-----------------------|
| KF-M2 | 2.4              | 4.4 × 2.0             | 4.3                   |
| KF-M3 | 3.4              | 6.5 × 3.0             | 6.3                   |
| KF-M4 | 4.5              | 8.0 × 4.0             | 8.4                   |
| KF-M5 | 5.5              | 10.0 × 5.0            | 10.4                  |
| KF-M6 | 6.6              | 11.0 × 6.0            | 12.4                  |

Suffix `-CB` means counterbored from the local top face, e.g. `KF-M4-CB`.
Suffix `-CS` means a 90° countersink from the local top face, e.g. `KF-M4-CS`:
a cone from the countersink Ø at the local top narrowing at 45° down to the
clearance Ø, then the through hole. "Local top" is the highest added material
covering the hole position (a wall or boss top if the hole sits on one, else
the stock top) — the same rule counterbores use.

## 3. API

```python
import keel
p = keel.part("BRK-0412", material="AL6061", cls="GSE")
```

`cls` is `"GSE"` (default) or `"FLIGHT"`. FLIGHT rules: (1) `finish()` applies
your material's standard fillet to the stock's vertical edges automatically if
you never called `fillet()` (an explicit `fillet(r=...)` wins); (2) every base
hole must be `-CB` or `-CS` — a plain code raises
`keel: flight parts need -CB or -CS fasteners (KF-M4 at (6, 6))`. Wall holes
are exempt (they are always plain).

**stock(L, W, T)** — the base block, x in [0, L], y in [0, W], z in [0, T].
Exactly one per part, and it must be the first call.

```python
p.stock(60, 40, 4)
```

**wall(edge, h, t=None)** — a wall standing on the top face along a named
edge (`north`, `south`, `east`, `west`). It sits flush with that edge, runs the
full edge length, and rises `h` above the stock top. `t` defaults to your
material's standard wall, and must not be below its minimum wall.

```python
p.wall("north", 25)
```

**boss(at=(x, y), dia, h)** — a cylinder on the top face centred at (x, y),
`h` high.

```python
p.boss(at=(15, 15), dia=12, h=10)
```

**hole(code, at=(x, y))** — a through hole, all the way down, using a KF code.
`-CB` adds the counterbore, `-CS` the countersink, both from the local top.

```python
p.hole("KF-M4-CB", at=(8, 8))
```

**wall_hole(edge, code, at=(u, z))** — a plain KF clearance hole drilled
horizontally through the wall on `edge`, perpendicular to the wall, all the way
through its thickness. `u` is the distance along the wall: from the **west
end** for north/south walls, from the **south end** for east/west walls. `z` is
the hole-centre height **above the stock top**. Add the wall before its wall
holes. It is a KeelError if there is no wall on that edge, if the code has
`-CB`/`-CS`, or if the hole edge leaves the wall face.

```python
p.wall("north", 25)
p.wall_hole("north", "KF-M3", at=(30, 12))
```

**mount(name, origin=(x, y), finish="plain")** — a company standard mount: a
fixed group of base holes. `finish` is `"plain"`, `"CB"` or `"CS"`, applied to
every hole of the mount (FLIGHT rule 2 applies). Offsets are from `origin`:

| Name | Fastener | Holes (offsets from origin) |
|------|----------|-----------------------------|
| PETREL-MOUNT-A | KF-M4 | (0,0), (40,0), (0,30), (40,30); origin = south-west hole |
| PETREL-MOUNT-B | KF-M5 | (0,0), (60,0), (0,40), (60,40); origin = south-west hole |
| STAR-TRACKER-3 | KF-M3 | 3 holes on a circle of diameter 30 about the origin, at 90°, 210°, 330° (0° = east, counter-clockwise) |
| HARNESS-P2 | KF-M2 | (0,0), (15,0); origin = west hole |

A mount counts as one feature for `pattern()` (the whole mount is repeated)
and for `mirror()`.

```python
p.mount("PETREL-MOUNT-A", origin=(10, 10), finish="CS")
```

**pocket(at=(x, y), L, W, depth)** — a rectangular pocket cut from the top
face. (x, y) is the pocket's lower-left corner; `depth` must be less than the
stock thickness.

```python
p.pocket(at=(10, 10), L=40, W=20, depth=2)
```

Cuts (holes, mounts, pockets, slots, wall holes) are always applied after all walls and bosses, whatever the order you call them in.

**slot(at=(x1, y1), to=(x2, y2), width, depth="thru")** — a straight slot with
round ends along the centre line from start to end. `depth="thru"` cuts all the
way through; a number cuts a blind slot that deep from the top face.

```python
p.slot(at=(10, 15), to=(40, 15), width=5)
```

**pattern(nx, ny, dx, dy)** — repeats the LAST feature call in a grid, `nx`
by `ny` positions spaced `dx`, `dy` apart. The total is nx × ny instances
including the original call's position. Only boss, hole, pocket, slot and
mount can be patterned (a mount seed repeats the whole mount). After a
`mirror()`, `pattern()` raises a KeelError — there is nothing left to repeat.
(A leading text label, e.g. `pattern("hole", 2, 2, 48, 28)`, is accepted and
ignored.)

```python
p.hole("KF-M4", at=(6, 6))
p.pattern(2, 2, 48, 28)
```

**mirror(axis)** — copies every hole, boss, pocket, slot and mount recorded so
far to the mirror position: `axis="ew"` about the stock centre line x = L/2,
`axis="ns"` about y = W/2. Originals stay. Walls and wall holes are not
mirrored.

```python
p.hole("KF-M5", at=(5, 5))
p.mirror("ew")   # second hole appears at (L-5, 5)
```

**fillet(edges="vertical", r=None)** — rounds the stock's 4 vertical outer
edges. `r` defaults to your material's standard fillet. Only `edges="vertical"`
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
- `keel: unknown material 'AL7075'; materials are AL6061, TI6AL4V, SS316 ...`.
- `keel: wall thickness 1.0 is thinner than the AL6061 minimum wall 1.5 ...`.
- `keel: flight parts need -CB or -CS fasteners (KF-M4 at (6, 6))` — FLIGHT
  parts need counterbored or countersunk base holes.
- `keel: wall_hole() on the 'north' edge with no wall; ...` — add the wall first.
- `keel: wall_hole() takes a plain KF code without -CB/-CS, got ...`.
- `keel: unknown mount 'PETREL-MOUNT-C'; mounts are ...`.
- `keel: pattern() after mirror(); there is nothing to repeat ...`.

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

Flight titanium bracket with a wall hole (auto fillet 1.5, CB holes):

```python
import keel
p = keel.part("BRK-0142", material="TI6AL4V", cls="FLIGHT")
p.stock(60, 40, 4)
p.wall("north", 25)          # standard titanium wall is 3.0
p.hole("KF-M4-CB", at=(6, 6))
p.pattern(2, 2, 48, 28)
p.wall_hole("north", "KF-M3", at=(30, 12))
solid = p.finish()           # FLIGHT auto fillet, no fillet() call needed
```

Frame dimensioned from the centre (request: holes at (±45, ±35) from the frame
centre; convert x = 50 + xr, y = 40 + yr, mirror the west pair):

```python
import keel
p = keel.part("FRM-1031", material="AL6061")
p.stock(100, 80, 6)
p.wall("north", 12)
p.wall("south", 12)
p.hole("KF-M5", at=(5, 5))
p.hole("KF-M5", at=(5, 75))
p.mirror("ew")               # east pair appears at x = 95
p.pocket(at=(10, 10), L=80, W=60, depth=4)
solid = p.finish()
```

New here? Copy one example, change the numbers to match your design request,
and run it through the Gauge station before ordering metal.

## 6. Reading design requests

- BRK, PLT, STD and CLP requests give positions from the datum corner, exactly
  as Keel takes them.
- **FRM requests are dimensioned from the frame centre** (x east, y north, can
  be negative), because frames are symmetric. Convert before coding:
  x = L/2 + x_request, y = W/2 + y_request.
- "Flight part" means `cls="FLIGHT"`. A material named in a request must be
  passed as `material=`: "titanium" = TI6AL4V, "stainless" = SS316,
  "aluminium" = AL6061.
