# Expertery exam build report

| job | status | readers passed | phrase | why |
|---|---|---|---|---|
| B1 | FLAGGED | 1/2 | Two 5.5 mm holes go through the upright (along Y), 20 either side of the centre line, 35 above the bottom. | Phrase is ambiguous whether this is an additional second pair of holes distinct from the base pair, whether '(along Y)' means hole-axis = Y (through-thickness) vs position along Y, and whether '35 above the bottom' is measured from Z=0 (bottom of base) vs Z=4 (top of base/bottom of upright). Reader interpreted it as not adding new holes / or as invalid and cut only the 2 vertical base holes, leaving volume ~190 mm³ high (+0.9%) and COM y=29.76 z=15.49 vs correct y~29.68 z~15.31. |
| B10 | FLAGGED | 1/2 | each gusset's short sides run 35 along each leg, measured from the inside faces | The datum for '35' is ambiguous. 'Along each leg' could be read as along the outer face from the outside corner (X=0,Z=0) including the 5mm thickness, giving an effective inside-contact length of only 30mm, versus along the inside face from the inside corner line (X=5,Z=5) giving a true 35mm leg. Correct inside-datum gives each gusset 0.5*35*35*4=2450 mm3 (two =4900) and with legs 19000 and 4 holes -684 gives reference volume ~23215.76 and bbox 0,0,0 to 50,40,50. Outside-datum gives 0.5*30*30*4=1800 each (3600 total) and volume ~21915.76, ~1300mm3 low with bbox unchanged, so error is only detectable by volume. |
| B11 | FLAGGED | 1/2 | Three 5 mm holes: in the bar 10 from each end on its centre line, and in the stem on its centre line 10 from its bottom end. | Ambiguous whether '5 mm' is diameter or radius (and whether holes are through-holes with axis along Z through the 4 mm thickness), whether '10 from each end/bottom' is measured to hole centre or to hole edge, and which 'centre line' is meant (longitudinal mid-line Y=10 for the bar and X=0 for the stem vs transverse). Different interpretations change removed area/volume and can place holes on/over edges, producing invalid non-manifold geometry and the observed volume/area/COM mismatch. |
| B12 | READY | 2/2 |  |  |
| B13 | FLAGGED | 1/2 |  |  |
| B14 | READY | 2/2 |  |  |
| B15 | READY | 2/2 |  |  |
| B16 | FLAGGED | 0/2 | Two sides go up from the inner ends of the feet: X from -16 to -13 and from 13 to 16, up to Z = 20. | Omits lower Z bound. 'go up from' was read as Z=3 to 20 sitting on top of the feet, giving only edge-line contact at X=-16/X=16,Z=3, so the two feet remain disconnected (2 solids) and sides+bridge overlap becomes the 3rd solid = solids=3, volume 3864.57 vs 4134.57 (missing 270mm3 = 2*3*15*3 lower portions of sides). Intended is Z=0 to 20 sharing a 15x3 face with feet for a single fused solid. |
| B17 | READY | 2/2 |  |  |
| B18 | READY | 2/2 |  |  |
| B19 | READY | 2/2 |  |  |
| B2 | READY | 2/2 |  |  |
| B20 | FLAGGED | 1/2 | two 5.5 mm holes go through the upright along Y, 10 from each side and 30 above the bottom | Does not specify datum or reference: 'along Y' vs positioned along Y, '10 from each side' does not say X-side faces vs Y-faces nor center vs edge, and '30 above the bottom' does not say overall bottom Z=0 vs upright bottom Z=5. Reader interpreting 10 mm as Y-offset finds no valid placement inside 5 mm Y-thickness and omits both holes, leaving volume high by ~237.6 mm3 (2x pi*2.75^2*5) and COM at 28.607,13.092 instead of ~28.51,12.91. |
| B3 | FLAGGED | 1/2 | 11 from its free end | Does not specify datum for the 11 mm dimension — whether it is to the hole center/axis or to the nearest edge of the hole, measured along X from the outer face. A reader assuming 'to edge' will place the center at 14.25 mm (11 + 6.5/2), shifting the hole while bbox and volume stay the same. |
| B4 | FLAGGED | 1/2 | with all four corners rounded to radius 5 when seen from above | Ambiguous whether this is a 2D sketch/vertex rounding before extrusion or a 3D fillet of the extruded solid's vertical edges. 'when seen from above' suggests a plan-view profile but does not state to extrude first then fillet the four vertical edges, so attempt 1 tried cq.Workplane.rect().vertices().fillet(5).extrude(3) on a wire with no solid and failed with 'Cannot find a solid on the stack'. |
| B5 | READY | 2/2 |  |  |
| B6 | READY | 2/2 |  |  |
| B7 | DEFERRED | 0/2 |  |  |
| B8 | DEFERRED | 0/1 |  |  |
| B9 | READY | 1/1 |  |  |

Totals: 20 jobs (2 DEFERRED, 8 FLAGGED, 10 READY).
spent_estimate: $1.5721 (cap $1.50).
A FLAGGED job is not a model failure: the wording may be read two ways. A person decides.
