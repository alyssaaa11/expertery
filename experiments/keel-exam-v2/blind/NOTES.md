# Blind rebuild notes (keel-exam-v2)

All 30 programs written and run without Keel errors (H2 and H15 first failed on "pattern() after mirror()"; fixed by writing explicit calls, which is the tool's documented behaviour).

## Cross-cutting ambiguities
- Mirror order (manual: mirror copies "every hole, boss, pocket, slot and mount recorded so far"). Requests never say which features the mirror covers, so I assumed only the features named in the mirror sentence, and placed all other features AFTER the mirror call. Affects M12, H2, H7, H9, H12, H15.
- pattern() after mirror() raises, even with other features in between (it did for me in H2 and H15). Manual says only "After a mirror()". Requests don't warn about it; I had to write repeated holes/mounts explicitly.
- "Standard fillet" / "Vertical edges rounded with radius N": I used fillet() / fillet(r=N). Unambiguous for GSE parts. For FLIGHT parts with no fillet mention (M3, M10, M15, H1, H3, H4, H6, H8, H11, H12, H14) I assumed the automatic flight fillet only.
- Parts with no "flight" wording use cls GSE, so plain holes are allowed (M4 FRM, H2, H5, H13...). A request that says "flight bracket" but also "flight part" (H1) is consistent.
- Wall thickness is never stated; "standard wall" taken from the material row. Wall holes assumed to fit inside the wall (Keel raised no error).

## Per job
- M1: "Two KF-M4 holes with centres at..." no ambiguity beyond: plain holes (GSE) assumed since not flight. Wall "30 high" taken as height above stock top (manual definition).
- M4, M9, M13, H2, H6, H9, H13: FRM centre-origin conversions made per section 6 (x = L/2 + xr). M4 pocket "lower-left corner at (-30,-15)" -> (20,15). M9 slot centre line (-20,0)..(20,0) -> (20,40)..(60,40).
- M5: "the second 9 mm north of the first" -> origin (10,17); "west hole" = origin per manual. Fine.
- M6: "6 mm in from each corner (6 mm from both adjacent edges)" clear; pattern 2x2 with pitch 58/38 derived.
- M7: "15 mm along the wall from its west end and 18 above the stock top" -> at=(15,18). Clear.
- M8 and H3, H9, H15: "STAR-TRACKER-3 mount centred at (20,20)" read as origin = circle centre (manual: "about the origin"). H3: "centred on the foot" -> (20,20). H9: "centred at (0, 0)" is a FRM centre-coordinate -> (60,40); assumed the FRM conversion applies to mounts too. H15: PLT so datum coords.
- M10, H4, H12, H14: "counterbored/countersunk PETREL-MOUNT-x" -> finish="CB"/"CS".
- M12: "mirrored east-west and then north-south, giving four holes" clear, but the blind slot sentence comes after, so I placed it after the mirrors (so it is not mirrored). "6 wide and 2 deep" fine. Strict note: slot centre y=15=W/2 so mirror-ns would be harmless anyway.
- M13: "Standard walls ... north and south edges" with a FRM request: wall edges are not centre-dimensioned; fine. Pocket "(-50,-20)" -> (10,10).
- M14: "Three HARNESS-P2 mounts in a row ... each next one 30 mm east" -> pattern(3,1,30,0). "Vertical edges rounded with radius 2" -> fillet(r=2).
- M3/M15/H3/H11/H14: "countersunk/counterbored from the top of the boss" matches the manual's "local top" rule; hole position at boss centre so redundant but consistent.
- H1: "rows 8 mm from the south edge and 12 mm from the north edge" -> y=8 and y=38 (W=50); columns 8 from west/east -> x=8, 72; pattern 2x2 pitch 64/30. Mildly ambiguous whether "rows" means two holes per row; assumed 4 holes at the corners of that rectangle. "holes through the north wall, 20 and 50 mm along ... both 20 above the stock top" clear.
- H2: "Two pockets ... one with its lower-left corner at (-60,-30), the other its mirror image on the east side": mirror image of pocket (10,20,20x60) about x=70 gives lower-left (110,20). I used mirror("ew") right after the first pocket and put holes/mount after. Problem: the request lists holes first, pockets second; in listed order a mirror would also duplicate the holes. Also the mount is "counterbored PETREL-MOUNT-B ... (-30,-20)": hole centres are (40,30)..(100,70); fine.
- H5: wall holes "20 mm along the wall from its south end" for west wall, "50 mm from west end" for south wall: uses the manual's u convention. Clear. West and south walls overlap at the corner (assumed fine).
- H6: "A pocket 60 x 60" lacks the (east-west) x (north-south) labels, but is square so harmless. Walls on east/west edges, pocket fits between them.
- H7: "plus their mirror images east-west and north-south, eight holes in total": assumed mirror ew then ns of both holes (2->4->8). The harness mount is "plus" and was placed after the mirrors, otherwise it would be duplicated/mirrored. Note the mount is symmetric about x=50 (42.5 and 57.5), so a mirror would merely duplicate it.
- H8: "countersunk PETREL-MOUNT-A with its south-west hole at (10, 8)" + a wall at north (y 48-50 for SS316 wall 2.0); mount hole at y=38. Fine. Flight part's wall hole plain: exempt per manual.
- H10: "Three parallel through slots ... centre lines from y=8 to y=32 at x=25,40,55" -> slot + pattern(3,1,15,0). "Standard fillet" with a west wall: fillet is on stock vertical edges only; wall interaction unspecified. Assumed no error.
- H11: "A counterbored HARNESS-P2 mount" on a FLIGHT part -> finish="CB". The pattern for two bosses/holes used pattern(2,1,30,0) each; "Each boss has a countersunk hole" clear.
- H12: "the same mount mirrored east-west" -> mirror("ew") right after the mount; the rest placed after. "Pocket 40 (east-west) x 20 (north-south)" -> L=40, W=20.
- H13: "2 columns and 2 rows ... column pitch 80, row pitch 50" -> pattern(2,2,80,50), pocket seed at (10,10). "Three KF-M5 holes at (0,-45),(0,0),(0,45)" are FRM centre coords -> (80,5),(80,50),(80,95), pattern(1,3,0,45). Plain holes assumed since not flight. Easy trap: (0,-45) is 45 from centre, hole lands 5 from edge.
- H14: "Two KF-M5 holes through the east wall ... from its south end" east wall u convention applied. Boss hole "counterbored from the top of the boss" matches the local-top rule.
- H15: "Four HARNESS-P2 mounts in a row along the north side": "north side" is only descriptive, positions given. Mount ordering after mirror forced explicit calls (pattern after mirror error). Slot "10 wide" x 60-90 near the mounts: no conflict.
- M2 (REPLACED request, manual v2.1.0): "A counterbored PETREL-MOUNT-A with its south-west hole at (25, 20). One KF-M6 hole with its centre at (75, 55). Standard fillet." Mount -> origin=(25,20), finish="CB". "One KF-M6 hole" has no CB/CS wording and the part is not flight, so I used a plain KF-M6 (not counterbored, unlike the mount). Stainless fillet 0.5 via fillet(). Mount holes at x 25/65, y 20/50; the KF-M6 hole (75,55) is near the (65,50) mount hole (distance ~11.2) with a CB dia 8 and a clearance dia 6.6: no overlap, no ambiguity found. Mild: "Standard fillet" means material standard (0.5), taken from the table.
- Manual v2.1.0 re-read: new line "Cuts ... are always applied after all walls and bosses, whatever the order you call them in." This resolves call-order concerns for walls vs holes (e.g. wall_hole/hole before wall); my other programs added walls in various orders and are unaffected. No other change noticed; mirror/pattern text unchanged.
