# Blind rebuild notes (manual.md + job_texts.json only)

30 programs written, all 30 run OK. Ambiguities and assumptions below.

Revision after updated texts: H4 rewritten (holes now 6 mm in, pattern 128 x 78). H2, H3, H9, M12, H11, H14 re-read; clarifications (east-west/north-south axes, counterbore from boss top) match what was written, programs unchanged. Remaining doubt: hole() has no way to say which top the counterbore starts from, so I used the plain -CB code.

Revision after updated texts: H4 rewritten (holes now 6 mm in, pattern 128 x 78). H2, H3, H9, M12, H11, H14 re-read; clarifications (east-west/north-south axes, counterbore from boss top) match what was written, programs unchanged. The notes below for those points are resolved except: the manual's hole() has no way to say which top the counterbore starts from, so I used the plain -CB code.

## Cross-cutting
- "N high" for walls and bosses: assumed height ABOVE the stock top (manual: wall rises h above stock top), not total part height. Applies to every wall/boss job (H1 "each 40 high", H15 "50 high", etc.).
- "Standard fillet" / "Vertical edges rounded with radius R": assumed `p.fillet()` / `p.fillet(r=R)`.
- Part-number family and material: used the number given, default material.
- Hole "through the centre of the boss": assumed a plain through hole all the way down (manual says holes are always through).

## Per job
- M1: "Two KF-M5 holes, centres at (20, 12) and (20, 33)": assumed pattern(1,2,0,21); the two points are listed explicitly so no real doubt, but a pattern pitch had to be derived.
- M5: "A blind slot 6 wide and 2 deep": assumed depth is from the top face (manual says so). Slot width 6 from y 7 to 13 and the south wall (0 to 2.5) do not touch; fine.
- M7: "Standard walls on the north edge and on the east edge": the walls overlap at the NE corner; assumed union, no trimming. Also "18 high" see above.
- M8: "Each boss has a KF-M2 hole": the pattern call repeats only the last feature, so I patterned the boss and the hole separately. Assumed that is intended.
- M10: "Vertical edges rounded with radius 3": assumed this means fillet(r=3) only (same as "vertical").
- M11: "A wall on the west edge, 4 thick": assumed t=4 (non-standard), 22 high above stock.
- M13: "the second is the same slot moved 29 mm east": assumed centre line (37,8)-(37,17), width 4, through.
- M14: "Standard fillet" with no holes: assumed fillet applies only to the 4 vertical outer edges of the stock, not the pocket corners.
- M15: "Three KF-M4 holes on the line y = 15": explicit, no doubt. Wall on south edge: y 0 to 2.5, no clash.
- H1: "columns 20 mm from the west edge, on the centre line, and 20 mm from the east edge": assumed x = 20, 60, 100 (centre line x = 60). "rows 18 mm in from the south edge and 18 mm in from the north edge": assumed y = 18 and 42 (measured from the stock edge, NOT from the inner wall face, since the walls sit on the edge). "U-channel" with walls 40 high: height above stock top.
- H2: "evenly spaced: the outer hole centres are 15 mm in from the ... edges": derived pitch 40 (x) and 35 (y), x = 15..135, y = 15..85. "A pocket 30 x 20 ... centred on the plate": assumed 30 along X and 20 along Y, lower-left (60,40). Counterbore is 8 dia on a 5 thick plate with 4 deep CB; leaves 1 mm floor, assumed acceptable. Hole at x=55/95, y=50 CB radius 4 comes within 1 mm of the pocket edge (x 60..90); assumed no conflict.
- H3: "A counterbored KF-M6 hole (KF-M6-CB) through the centre of the boss": manual says the counterbore is "from the top face". Unclear whether that is the top of the stock (z=6, deep inside the boss, i.e. a blind pocket the boss would fill/be cut through) or the top of the boss (z=31). I assumed the keel tool decides (call hole as written, no position argument). Also the counterbore depth 6 vs boss height 25: unclear which top face is meant. "central boss": assumed (25,25). Four M4 holes "6 mm in from each corner" -> (6,6) etc.
- H4: "the second 65 mm east of the first, leaving a 10 mm rib": consistent (55+10=65), second pocket at (75,10). Assumed 55 is along X and 70 along Y (L x W). The KF-M5 clearance hole (5.5 dia) at (8,8) extends to 10.75 and so cuts into the first pocket corner at (10,10); assumed that overlap is intended/ignored. Possible genuine design conflict.
- H5: "A KF-M3 hole at the centre of each round end of the slot": assumed the round-end centres are the centre-line endpoints (15,15) and (65,15). Hole goes through the slot floor (blind slot 3 deep in 6 stock). Slot 10 wide starting at x=10 vs west wall 0 to 2.5: no clash.
- H6: "on a square grid with 30 mm pitch; the south-west boss is centred at (35, 20)": assumed 2x2 grid (four bosses) -> (35,20),(65,20),(35,50),(65,50). "A wall on the west edge, 4 thick and 45 high": t=4.
- H7: "Five KF-M3 holes evenly spaced along the south edge and five along the north edge: ... first and last holes are 10 mm from the west and east edges": derived x = 10,30,50,70,90 (pitch 20), y = 6 and 54. "hole centres 6 mm in from that edge" assumed measured to the hole centre. The through slot (30,30)-(70,30) 12 wide is clear of the holes.
- H8: "A pocket 90 x 90, 8 deep, centred on the stock": lower-left (15,15). Counterbore holes at 9 mm are outside the pocket. Wall "30 high" on north edge. No real ambiguity beyond the global ones.
- H9: "counterbored KF-M5 (KF-M5-CB) through its centre": same top-face doubt as H3 (counterbore 10 x 5 in a boss 18 dia, 20 high). "one at the middle of each edge with its centre 5 mm in from that edge": assumed (18,5),(18,31),(5,18),(31,18). Fillet radius 6 on a 36 square: legal.
- H10: "centre lines from y = 10 to y = 30 at x = 20, 35 and 50": assumed slot (x,10)->(x,30). "Standard walls on the south and north edges": walls 0 to 2.5 do not touch slots.
- H11: "A wall on the east edge, 6 thick and 35 high": t=6 at x 74 to 80. "in 2 columns and 2 rows: first centre at (12, 12), column pitch 40, row pitch 26": x=12,52; y=12,38. Pocket 20 x 30 assumed L=20 (X), W=30 (Y).
- H12: "6 columns by 4 rows with 20 mm pitch both ways, centred on the plate": derived first hole (10,10). Hole at x=10 is 7.5 clear of the west wall (0 to 2.5); fine.
- H13: "A blind slot 8 wide and 4 deep": slot depth from the top face of the stock (z=8), assumed, rather than from top of the walls (walls are at the edges, not over the slot). Counterbored holes at (10,10) sit next to the 2.5 south wall.
- H14: "Two bosses ... centres 15 mm in from the west and east edges": (15,15) and (45,15). "A through slot 5 wide between them, centre line from (25, 15) to (35, 15)": round ends extend to x=22.5/37.5, boss edges at 22 / 38; assumed fine (0.5 mm clearance).
- H15: "grid of KF-M5 holes, 3 columns by 3 rows: first hole centre at (25, 25), pitch 25 both ways": x,y = 25,50,75. "gusset base" is just a name. Fillet radius 5 on the corners where the walls meet the stock: assumed the fillet touches only stock edges.
