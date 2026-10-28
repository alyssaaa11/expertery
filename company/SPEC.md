# Quillon Orbital Works: company, private tool "Keel", and internal dashboard (SPEC, draft)

Status: **draft for the user's review** (2026-10-28). Written by Claude (plan/spec role). To be built by **Muse Code**
after the user approves. Nothing here is a real company: "Quillon Orbital Works" was checked with a web search on
2026-10-28 and no company of that name was found. Every page must show "Fictional company, made for the Forge demo".

## 1. Why this exists
Forge must prove that a small private model (Muse Glimmer 30B) can learn a company tool that **no AI has seen on the
internet**. CadQuery is public, so both models already knew it. Keel is a new, private tool with its own names, units
convention and company tables. The only ways to learn it are the company manual or Forge training.
Keel compiles to CadQuery internally, so the existing exact referee (`experiments/first-test/checks.py`: one solid,
bbox, volume, area, centre of mass, overlap mismatch ≤ 0.2%) still judges every answer.

## 2. The company (story shown in the dashboard)
- **Quillon Orbital Works**: builds structural parts for small satellites (brackets, mounting plates, panel frames,
  standoffs, harness clips) for its smallsat bus **"Petrel"** (programmes Petrel-1, Petrel-2).
- Designs are **export-controlled** (fictional "QX-2" control level): they may not be sent to cloud AI. That is why
  the AI design assistant runs on one in-house GPU ("on-prem"), which is the Forge story.
- Small team (fictional): Structures, Avionics Integration, Quality. Engineers file **design requests** like
  "BRK-0412: base plate 60 × 40 × 4, four KF-M4 clearance holes 6 mm in from each corner, north wall 25 high".

## 3. The private tool: Keel (Python library `keel`)
Design goals: (a) clearly different from CadQuery (names, datum, tables), so knowing CadQuery is not enough;
(b) small and fully documented in the manual; (c) every Keel program becomes exactly one CadQuery solid;
(d) deterministic, no randomness.

### 3.1 Company conventions (the "unwritten rules" a new engineer must learn)
- Units are millimetres. **Datum = the part's lower-left-bottom corner** at (0,0,0). +X = "east", +Y = "north",
  +Z = "up". Nothing is centred unless the call says so.
- Edges of the base stock are named **north, south, east, west**.
- Holes use **company fastener codes**, never raw diameters (table KF below).
- "Standard wall" thickness = **2.5 mm**; "standard fillet" = **1.0 mm** (used when a request says "standard").
- Part numbers: BRK- (bracket), PLT- (plate), FRM- (frame), STD- (standoff), CLP- (clip).

### 3.2 Fastener table KF (company table; values are the exact diameters the referee uses)
| Code | Clearance hole Ø | Counterbore Ø × depth |
|---|---|---|
| KF-M2 | 2.4 | 4.4 × 2.0 |
| KF-M3 | 3.4 | 6.5 × 3.0 |
| KF-M4 | 4.5 | 8.0 × 4.0 |
| KF-M5 | 5.5 | 10.0 × 5.0 |
| KF-M6 | 6.6 | 11.0 × 6.0 |
Suffix `-CB` = counterbored from the top face (e.g. `KF-M4-CB`).

### 3.3 API (first version; Muse Code may propose changes in its report, not silently)
```python
import keel
p = keel.part("BRK-0412", material="AL6061")       # material is metadata only
p.stock(L, W, T)                 # base block: x∈[0,L], y∈[0,W], z∈[0,T]. Exactly one per part, first call.
p.wall(edge, h, t=None)          # wall standing on the top face along a named edge, flush with that edge,
                                 # full edge length, height h above the stock top; t defaults to standard wall 2.5
p.boss(at=(x, y), dia, h)        # cylinder on the top face, centre at (x, y)
p.hole(code, at=(x, y))          # through hole (all the way down) using table KF; "-CB" adds the counterbore
p.pocket(at=(x, y), L, W, depth) # rectangular pocket from the top face; (x, y) = pocket's lower-left corner
p.slot(at=(x1, y1), to=(x2, y2), width, depth="thru")  # straight slot with round ends, centre line x1,y1→x2,y2
p.pattern(feature, nx, ny, dx, dy)   # repeat the LAST feature call nx × ny times with spacing dx, dy
p.fillet(edges="vertical", r=None)   # round the stock's 4 vertical outer edges; r defaults to standard 1.0
solid = p.finish()               # returns the CadQuery solid; must be the last call
```
- Errors are company-style and helpful (e.g. `KeelError: unknown fastener code 'M4'; use KF-M4`), because a real
  internal tool has its own error messages and the student must learn them too.
- `keel.render(p, path)` writes an SVG preview for the dashboard (CadQuery SVG export).

### 3.4 What the answer looks like
The model writes a short Keel program ending in `solid = p.finish()`. The runner executes it and the referee compares
`solid` with the reference solid built by the job's own Keel reference program.

## 4. The company manual (`company/manual.md`)
Written like a real internal wiki page: intro, conventions (3.1), table KF, every API call with one example each,
error messages, 3 worked examples. Target ≤ 4,000 tokens. It must contain **no** exam jobs.

## 5. The internal dashboard (`company/dashboard/index.html`)
A static, **offline** web page (no CDN, no server, opens with a double-click; fits the "nothing leaves the building"
story). Reads `company/dashboard/data.json`, which a script (`company/dashboard/build_data.py`) creates from the
company files and Forge results. Look: a clean engineering intranet (dark navy + white, one accent colour), with the
"Fictional company" banner.

Sections:
1. **Header**: Quillon Orbital Works · Engineering Portal · "QX-2 controlled: on-prem only" badge.
2. **Company**: what we build, the Petrel programmes, the teams (short cards).
3. **Tools**: Keel (version, link to the manual), Fastener table KF, Design rules, **Gauge** (the automatic checking
   station = our referee), **Forge assistant** (the on-prem AI). One card each: what it is, its status.
4. **Parts catalog**: grid of example parts (from practice families only, never exam jobs), each with its SVG
   preview, part number, Keel code (click to show) and key sizes.
5. **Design requests**: a table of requests with status: open / AI draft / Gauge PASS / Gauge FAIL (with reason:
   wrong shape, wrong position, error).
6. **Forge assistant panel**: where it runs (1 GPU, on-prem), the scoreboard (Glimmer + manual, Forge-trained
   Glimmer, teacher Spark Open) on the held-out exam, training status, cost. Shows "not measured yet" until results
   exist; never invented numbers.

## 6. Acceptance checks (Muse Code must run them and report)
- `selftest`: every example part's Keel program builds exactly one valid solid; the referee scores every reference
  against itself PASS, and two deliberately wrong versions per example FAIL.
- Error messages: an unknown code, a second `stock()` call and a missing `finish()` each raise a clear `KeelError`.
- The dashboard opens offline (no network requests: grep for `http` in the HTML/JS = only text, no fetches to the web)
  and renders with the current `data.json`. Scoreboard shows "not measured yet" where there is no result file.
- No exam job text or exam part appears in the catalog, manual or examples (the exam is written later, separately).

## 7. Not in this step
The 30-job held-out exam (written separately, frozen and blind-rebuilt as before), the practice generator, the
teacher run, training. Budget for this build: one Muse Code session, ~$0.50–0.80 Meta credit, user approval first.

---

# Keel v2: realistic company tool (SPEC addendum, 2026-10-28 ~23:30, user: "do it more realistic")

Why: v1 is close to plain CAD; a small model with the manual may already do well, leaving Forge nothing to improve.
Real internal tools carry company knowledge: named standards, rules that depend on material and part class, family-
specific drawing conventions, and traps in the order of operations. v2 adds these. Everything stays exactly
checkable (each program still compiles to exactly one CadQuery solid) and fully documented in the manual: nothing
is secret from a careful reader, but a lot must be remembered and combined.
All v1 calls keep working unchanged. Version 2.0.0.

## V2.1 Materials (changes the shape through the standards)
`keel.part(number, material="AL6061", cls="GSE")`. Material now matters:
| Material | Standard wall | Standard fillet | Minimum wall (KeelError if thinner) |
|---|---|---|---|
| AL6061 | 2.5 | 1.0 | 1.5 |
| TI6AL4V | 3.0 | 1.5 | 2.0 |
| SS316 | 2.0 | 0.5 | 1.2 |
Unknown material → KeelError listing the three codes.

## V2.2 Part class
`cls="GSE"` (ground support equipment, default) or `cls="FLIGHT"` (flies on the satellite). FLIGHT rules:
1. `finish()` applies the material's standard fillet to the stock's vertical edges automatically if `fillet()` was
   not called (an explicit `fillet(r=...)` wins).
2. Every fastener hole on the base must be counterbored (`-CB`) or countersunk (`-CS`); a plain code raises
   `KeelError: flight parts need -CB or -CS fasteners (KF-M4 at (x, y))`. Wall holes (V2.4) are exempt.

## V2.3 Countersinks
Suffix `-CS`: 90° countersink from the local top (same "local top" rule as counterbores). Table KF gains a column:
| Code | Countersink Ø at the top |
|---|---|
| KF-M2 | 4.3 |
| KF-M3 | 6.3 |
| KF-M4 | 8.4 |
| KF-M5 | 10.4 |
| KF-M6 | 12.4 |
Geometry: a cone from the countersink Ø at the local top narrowing at 45° (half-angle) down to the clearance Ø, then
the through hole.

## V2.4 Holes in walls
`p.wall_hole(edge, code, at=(u, z))`: a plain KF clearance hole drilled horizontally through the wall on `edge`,
perpendicular to the wall, all the way through its thickness. `u` = distance along the wall: from the **west end**
for north and south walls, from the **south end** for east and west walls. `z` = height of the hole centre **above
the stock top**. KeelError if there is no wall on that edge, if the code has -CB/-CS, or if the hole does not fit
inside the wall (hole edge closer than 0 to the wall's top or ends).

## V2.5 Company standard mounts
`p.mount(name, origin=(x, y), finish="plain")`, `finish` = "plain", "CB" or "CS" (applied to every hole of the
mount; FLIGHT rule 2 applies). Hole offsets are from `origin`:
| Name | Fastener | Holes (offsets from origin) |
|---|---|---|
| PETREL-MOUNT-A | KF-M4 | (0,0), (40,0), (0,30), (40,30); origin = the south-west hole |
| PETREL-MOUNT-B | KF-M5 | (0,0), (60,0), (0,40), (60,40); origin = the south-west hole |
| STAR-TRACKER-3 | KF-M3 | 3 holes on a circle of diameter 30 around the origin, at 90°, 210° and 330° (0° = east, counter-clockwise) |
| HARNESS-P2 | KF-M2 | (0,0), (15,0); origin = the west hole |
`mount()` counts as one feature for `pattern()` (the whole mount is repeated) and for `mirror()`.

## V2.6 Mirror
`p.mirror(axis)`: `axis="ew"` copies every hole, boss, pocket, slot and mount recorded so far to the mirror position
about the stock's centre line x = L/2; `axis="ns"` about y = W/2. Originals stay. Walls and wall holes are not
mirrored. After a mirror, `pattern()` raises KeelError (nothing to repeat).

## V2.7 Reading design requests (manual section; a drawing convention, not code)
- BRK, PLT, STD and CLP requests give positions from the datum corner (as in v1).
- **FRM requests are dimensioned from the frame centre** (x east, y north, can be negative), because frames are
  symmetric. Keel always uses the corner datum, so convert: x = L/2 + x_request, y = W/2 + y_request.
- "Flight part" in a request means `cls="FLIGHT"`. A material named in a request (e.g. "titanium" = TI6AL4V,
  "stainless" = SS316, "aluminium" = AL6061) must be passed as `material=`.

## V2.8 Build changes (for Muse Code)
- Library v2.0.0 in `company/keel/` (keep v1 behaviour for v1 calls; KeelError messages company-style).
- Manual v2 in `company/manual.md`: add sections for V2.1–V2.7 with one example each, plus 2 new worked examples
  that combine several rules. Target ≤ 6,000 tokens. It must contain no exam job (exam part numbers are in the
  BRK-2xxx…5xxx range and must not be used in the manual or examples; use 0xxx–1xxx numbers).
- Examples: keep the 8; add 4 v2 examples (a FLIGHT titanium bracket with a wall hole, a frame dimensioned from the
  centre with a mirror, a plate with PETREL-MOUNT-A countersunk, a stainless part with STAR-TRACKER-3).
- `company/selftest.py`: extend to every new rule (each error case, each mount, the auto fillet, the countersink
  cone, wall_hole positions, mirror). Use the Keel-exam referee tolerance (0.01%: import
  `experiments/keel-exam/referee.py`) for the wrong-variant checks.
- Dashboard: Keel v2.0.0; new cards/tables for Materials, Part classes, Standard mounts; Gauge card says overlap
  0.01%; label request statuses as "sample data" until real results exist.
