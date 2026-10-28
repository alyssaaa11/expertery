# First test: draft list of the 40 jobs (titles + key sizes)

Status: DRAFT for the user's review. After approval, each job gets full wording with every coordinate, a reference
solution, 2 wrong versions and a check, and passes the blind rebuild (PLAN.md section 4). Sizes are in mm. All parts
are made-up, generic engineering parts, not anyone's real designs.

## Easy (10): one shape with simple features (sanity check)
| # | Part | Key sizes |
|---|---|---|
| E1 | Mounting plate with 4 corner holes | 60×40×5, Ø4 holes 5 from each corner |
| E2 | Washer | outer Ø20, inner Ø8, 2 thick |
| E3 | Rounded block | 30×20×10, vertical edges filleted R3 |
| E4 | Cylinder with bore | Ø30 × 15, Ø10 through hole |
| E5 | Hex nut blank | 13 across flats, 6 thick, Ø6.5 hole |
| E6 | Rectangular tube | outer 30×20, wall 2, length 50 |
| E7 | Disk with bolt circle | Ø50 × 4, six Ø5 holes on a Ø40 circle |
| E8 | Chamfered cube | 25 cube, 2 chamfer on all edges |
| E9 | Plate with a slot | 50×20×4, obround slot 20×6 centred |
| E10 | Cone frustum | base Ø30, top Ø15, height 20 |

## Medium (15): 2–3 features placed relative to each other
| # | Part | Key sizes |
|---|---|---|
| M1 | L-bracket with 2 holes | base 40×20×3, wall 40×3×20 flush at the back, Ø5 holes at X ±15 |
| M2 | T-profile bar | flange 30×4, web 4×26, length 60 |
| M3 | Open box | outside 60×40×30, walls and floor 2 |
| M4 | Lid with a lip that fits M3 | plate 60×40×2, lip 1.5 thick inset to fit inside |
| M5 | Stepped shaft | Ø20×30, then Ø15×20, then Ø10×15, same axis |
| M6 | Flange with hub | disk Ø60×8, hub Ø30×20, Ø20 bore, 4 bolt holes Ø6 on Ø45 |
| M7 | U-channel | outside 30×20, wall 3, length 50 |
| M8 | Plate with 4 standoffs | 50×50×3, bosses Ø8 tall 10 at (±18, ±18), Ø3 holes |
| M9 | Phone stand | base 80×60×5, back plate tilted 15° back, 70 tall, front lip 5 high |
| M10 | Counterbored plate | 40×40×10, Ø6.6 through hole, Ø11 counterbore 6.5 deep |
| M11 | Shelf bracket with gusset | two 50×30×4 plates at 90°, triangular gusset with 25 legs, 4 thick |
| M12 | V-groove pulley | Ø40 × 12, groove 4 deep at 40°, Ø8 bore |
| M13 | Cable clip with tab | ring outer Ø16, inner Ø10, 8 wide; tab 20×8×3 with a Ø4 hole |
| M14 | Hinge leaf | plate 40×30×2, Ø6 knuckle along one 40 edge, Ø3 pin hole |
| M15 | Drawer handle | bar 100×10×10 on two 10×10×20 posts at X ±40, Ø3.3 holes 8 deep in the posts |

## Hard (15): many features with exact relations
| # | Part | Key sizes |
|---|---|---|
| H1 | Electronics enclosure with screw bosses | outside 80×50×30, wall 2; 4 inner bosses Ø6 × 25 with Ø2.5 holes, 5 from the inner corners |
| H2 | Circuit-board mounting plate | 100×70×3, 4 standoffs Ø6 × 5 on a 58×49 pattern (offset), 2 cable slots |
| H3 | Gear blank with keyway | Ø40 × 8, 12 tooth cut-outs 3 wide 4 deep, Ø8 bore with a 3×1.5 keyway |
| H4 | Camera mount (3 fins) | base 20×20×4, three fins 3 thick with 3 gaps, 15 tall, Ø5 hole through all fins |
| H5 | 3-way corner bracket | three 30×30×3 plates forming a cube corner, a Ø4 hole centred in each |
| H6 | Bearing housing | block 50×40×25, Ø22 pocket 7 deep, Ø10 through, 2 mounting holes Ø5 at X ±20 |
| H7 | Spacer with hex pocket | Ø20 × 12, hex pocket 10 across flats × 5 deep, Ø5.5 through |
| H8 | Snap-fit hook | block 20×10×5, arm 30×10×2, tip hook 2 high with a 45° ramp |
| H9 | Heat sink | base 60×40×4, nine fins 1.5 thick 20 tall, evenly spaced along X |
| H10 | Pipe saddle clamp | half-ring 3 thick for a Ø25 pipe, two feet 15×20×3 with Ø5 holes |
| H11 | Stair block | 4 steps, each 10 deep, 8 high, 30 wide |
| H12 | Grip knob with D-shaft hole | Ø30 × 15, 18 grip grooves Ø3, D-hole Ø6 with a flat at 4.5 |
| H13 | Wall hook | plate 30×60×4, 2 countersunk holes (Ø4 / Ø8, 90°), arm 30 out curling up 15 |
| H14 | Z-bracket | 3 thick, two flanges offset by 20, a 5×15 slot in each, slots aligned |
| H15 | Vented lid | 80×50×2, a 5×8 grid of 4×4 square vents at 8 pitch, 4 corner holes Ø3 |

## Rules for every job
- One solid part per job (no assemblies), so every check can measure it exactly.
- Full wording gives every position from a fixed origin, so there's no guessing (the bracket lesson from Glimmer test 1).
- No job is a near-copy of another, so one shared misunderstanding can't sink many jobs at once.
