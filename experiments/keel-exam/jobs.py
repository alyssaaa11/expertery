"""Keel held-out exam: 30 design requests (15 medium + 15 hard) for Quillon Orbital Works' private tool Keel.

Written by Claude (not by a Meta model, so the teacher's family did not write its own exam), before any model run.
Each job: the request text in company words, the reference Keel program body, and two deliberately wrong versions
(each one textual change to the reference). These jobs must never appear in practice data, the manual or examples.
A program body runs after `import keel` and `p = keel.part(<id>)`; the part is `p.finish()`.
"""

JOBS = {
    # ------------------------------------------------------------------ medium
    "M1": dict(id="BRK-2210", text=(
        "BRK-2210 angle bracket. Base stock 70 x 45 x 5. A standard wall on the west edge, 30 high. "
        "Two KF-M5 holes, centres at (20, 12) and (20, 33)."),
        ref='p.stock(70, 45, 5)\np.wall("west", 30)\np.hole("KF-M5", at=(20, 12))\np.hole("KF-M5", at=(20, 33))\n',
        wrong=[[('"west"', '"east"')], [('"KF-M5", at=(20, 12)', '"KF-M4", at=(20, 12)')]]),
    "M2": dict(id="PLT-2304", text=(
        "PLT-2304 mounting plate. Stock 90 x 50 x 3. A grid of KF-M3 holes, 3 columns by 2 rows: first hole "
        "centre at (15, 12), column pitch 30, row pitch 26. Standard fillet."),
        ref='p.stock(90, 50, 3)\np.hole("KF-M3", at=(15, 12))\np.pattern(3, 2, 30, 26)\np.fillet()\n',
        wrong=[[("p.pattern(3, 2, 30, 26)", "p.pattern(3, 2, 29, 26)")], [("p.fillet()\n", "")]]),
    "M3": dict(id="STD-2411", text=(
        "STD-2411 standoff. Foot 24 x 24 x 5 with a boss of diameter 10, 12 high, centred at (12, 12). "
        "A KF-M3 hole through the centre of the boss."),
        ref='p.stock(24, 24, 5)\np.boss(at=(12, 12), dia=10, h=12)\np.hole("KF-M3", at=(12, 12))\n',
        wrong=[[("h=12", "h=10")], [('"KF-M3"', '"KF-M4"')]]),
    "M4": dict(id="FRM-2502", text=(
        "FRM-2502 frame blank. Stock 80 x 60 x 8. A pocket 60 x 40, 5 deep, with its lower-left corner at "
        "(10, 10). Four KF-M4 holes with centres 5 mm in from each corner (5 mm from both adjacent edges)."),
        ref='p.stock(80, 60, 8)\np.pocket(at=(10, 10), L=60, W=40, depth=5)\np.hole("KF-M4", at=(5, 5))\np.pattern(2, 2, 70, 50)\n',
        wrong=[[("depth=5", "depth=4")], [("at=(10, 10)", "at=(11, 10)")]]),
    "M5": dict(id="CLP-2603", text=(
        "CLP-2603 cable clip. Stock 60 x 20 x 4. A blind slot 6 wide and 2 deep, centre line from (12, 10) to "
        "(48, 10). A standard wall on the south edge, 8 high."),
        ref='p.stock(60, 20, 4)\np.slot(at=(12, 10), to=(48, 10), width=6, depth=2)\np.wall("south", 8)\n',
        wrong=[[(", depth=2)", ")")], [("width=6", "width=5")]]),
    "M6": dict(id="PLT-2705", text=(
        "PLT-2705 cover plate. Stock 50 x 50 x 4. Four counterbored KF-M4 holes (KF-M4-CB), centres 7 mm in "
        "from each corner (7 mm from both adjacent edges)."),
        ref='p.stock(50, 50, 4)\np.hole("KF-M4-CB", at=(7, 7))\np.pattern(2, 2, 36, 36)\n',
        wrong=[[('"KF-M4-CB"', '"KF-M4"')], [("at=(7, 7))\np.pattern(2, 2, 36, 36)", "at=(6, 6))\np.pattern(2, 2, 38, 38)")]]),
    "M7": dict(id="BRK-2812", text=(
        "BRK-2812 corner bracket. Stock 40 x 30 x 6. Standard walls on the north edge and on the east edge, "
        "both 18 high. One KF-M6 hole with its centre at (15, 12)."),
        ref='p.stock(40, 30, 6)\np.wall("north", 18)\np.wall("east", 18)\np.hole("KF-M6", at=(15, 12))\n',
        wrong=[[('p.wall("east", 18)', 'p.wall("west", 18)')], [('p.wall("north", 18)', 'p.wall("north", 16)')]]),
    "M8": dict(id="STD-2920", text=(
        "STD-2920 double standoff. Stock 40 x 20 x 4. Two bosses of diameter 8, 6 high, centred at (10, 10) and "
        "(30, 10). Each boss has a KF-M2 hole through its centre."),
        ref='p.stock(40, 20, 4)\np.boss(at=(10, 10), dia=8, h=6)\np.pattern(2, 1, 20, 0)\np.hole("KF-M2", at=(10, 10))\np.pattern(2, 1, 20, 0)\n',
        wrong=[[("dia=8", "dia=9")], [('"KF-M2"', '"KF-M3"')]]),
    "M9": dict(id="FRM-3001", text=(
        "FRM-3001 rail. Stock 100 x 40 x 5. A through slot 8 wide, centre line from (20, 20) to (80, 20). "
        "Four KF-M4 holes with centres 8 mm in from each corner (8 mm from both adjacent edges)."),
        ref='p.stock(100, 40, 5)\np.slot(at=(20, 20), to=(80, 20), width=8)\np.hole("KF-M4", at=(8, 8))\np.pattern(2, 2, 84, 24)\n',
        wrong=[[("to=(80, 20)", "to=(78, 20)")], [("width=8", "width=7")]]),
    "M10": dict(id="PLT-3110", text=(
        "PLT-3110 thin shim plate. Stock 64 x 48 x 2.5. A grid of KF-M2 holes, 4 columns by 2 rows: first hole "
        "centre at (8, 8), column pitch 16, row pitch 32. Vertical edges rounded with radius 3."),
        ref='p.stock(64, 48, 2.5)\np.hole("KF-M2", at=(8, 8))\np.pattern(4, 2, 16, 32)\np.fillet(r=3)\n',
        wrong=[[("p.fillet(r=3)", "p.fillet()")], [("p.pattern(4, 2, 16, 32)", "p.pattern(3, 2, 16, 32)")]]),
    "M11": dict(id="BRK-3204", text=(
        "BRK-3204 bracket. Stock 55 x 35 x 4. A wall on the west edge, 4 thick and 22 high. One counterbored "
        "KF-M5 hole (KF-M5-CB) with its centre at (30, 17.5)."),
        ref='p.stock(55, 35, 4)\np.wall("west", 22, t=4)\np.hole("KF-M5-CB", at=(30, 17.5))\n',
        wrong=[[(", t=4)", ")")], [('"KF-M5-CB"', '"KF-M5"')]]),
    "M12": dict(id="STD-3307", text=(
        "STD-3307 tall standoff. Foot 30 x 30 x 3 with a boss of diameter 16, 15 high, centred at (15, 15). "
        "A counterbored KF-M5 hole (KF-M5-CB) through the centre of the boss, counterbored from the top of the boss."),
        ref='p.stock(30, 30, 3)\np.boss(at=(15, 15), dia=16, h=15)\np.hole("KF-M5-CB", at=(15, 15))\n',
        wrong=[[('"KF-M5-CB"', '"KF-M5"')], [("dia=16", "dia=14")]]),
    "M13": dict(id="CLP-3402", text=(
        "CLP-3402 strap clip. Stock 45 x 25 x 5. Two through slots 4 wide running north-south: the first has its "
        "centre line from (8, 8) to (8, 17), the second is the same slot moved 29 mm east."),
        ref='p.stock(45, 25, 5)\np.slot(at=(8, 8), to=(8, 17), width=4)\np.pattern(2, 1, 29, 0)\n',
        wrong=[[("p.pattern(2, 1, 29, 0)", "p.pattern(2, 1, 28, 0)")], [("width=4", "width=5")]]),
    "M14": dict(id="FRM-3509", text=(
        "FRM-3509 square frame. Stock 70 x 70 x 6. A pocket 50 x 50, 3 deep, with its lower-left corner at "
        "(10, 10). Standard fillet."),
        ref='p.stock(70, 70, 6)\np.pocket(at=(10, 10), L=50, W=50, depth=3)\np.fillet()\n',
        wrong=[[("L=50", "L=48")], [("p.fillet()\n", "")]]),
    "M15": dict(id="PLT-3603", text=(
        "PLT-3603 strip plate. Stock 80 x 30 x 4. Three KF-M4 holes on the line y = 15, centres at x = 15, 40 "
        "and 65. A standard wall on the south edge, 10 high."),
        ref='p.stock(80, 30, 4)\np.hole("KF-M4", at=(15, 15))\np.pattern(3, 1, 25, 0)\np.wall("south", 10)\n',
        wrong=[[('"south"', '"north"')], [("p.pattern(3, 1, 25, 0)", "p.pattern(3, 1, 24, 0)")]]),

    # ------------------------------------------------------------------ hard
    "H1": dict(id="BRK-4105", text=(
        "BRK-4105 U-channel bracket. Stock 120 x 60 x 6 with standard walls on both the north and the south "
        "edge, each 40 high. Six KF-M5 holes in 3 columns and 2 rows: columns 20 mm from the west edge, on the "
        "centre line, and 20 mm from the east edge; rows 18 mm in from the south edge and 18 mm in from the "
        "north edge. Vertical edges rounded with radius 4."),
        ref='p.stock(120, 60, 6)\np.wall("north", 40)\np.wall("south", 40)\np.hole("KF-M5", at=(20, 18))\np.pattern(3, 2, 40, 24)\np.fillet(r=4)\n',
        wrong=[[("at=(20, 18))\np.pattern(3, 2, 40, 24)", "at=(20, 16))\np.pattern(3, 2, 40, 28)")], [("p.fillet(r=4)", "p.fillet()")]]),
    "H2": dict(id="PLT-4210", text=(
        "PLT-4210 avionics tray. Stock 150 x 100 x 5. Twelve counterbored KF-M4 holes (KF-M4-CB) in 4 columns "
        "and 3 rows, evenly spaced: the outer hole centres are 15 mm in from the west, east, south and north "
        "edges. A pocket 30 (east-west) x 20 (north-south), 3 deep, centred on the plate. Standard fillet."),
        ref='p.stock(150, 100, 5)\np.hole("KF-M4-CB", at=(15, 15))\np.pattern(4, 3, 40, 35)\np.pocket(at=(60, 40), L=30, W=20, depth=3)\np.fillet()\n',
        wrong=[[("p.pattern(4, 3, 40, 35)", "p.pattern(4, 3, 39, 35)")], [("at=(60, 40)", "at=(55, 40)")]]),
    "H3": dict(id="STD-4302", text=(
        "STD-4302 heavy standoff. Foot 50 x 50 x 6 with a central boss of diameter 20, 25 high. A counterbored "
        "KF-M6 hole (KF-M6-CB) through the centre of the boss, counterbored from the top of the boss. Four KF-M4 holes with centres 6 mm in from each "
        "corner (6 mm from both adjacent edges). Standard fillet."),
        ref='p.stock(50, 50, 6)\np.boss(at=(25, 25), dia=20, h=25)\np.hole("KF-M6-CB", at=(25, 25))\np.hole("KF-M4", at=(6, 6))\np.pattern(2, 2, 38, 38)\np.fillet()\n',
        wrong=[[('"KF-M6-CB"', '"KF-M6"')], [('at=(6, 6))\np.pattern(2, 2, 38, 38)', 'at=(8, 8))\np.pattern(2, 2, 34, 34)')]]),
    "H4": dict(id="FRM-4407", text=(
        "FRM-4407 twin-bay frame. Stock 140 x 90 x 10. Two pockets, each 55 (east-west) x 70 (north-south) and 6 deep: the first with its "
        "lower-left corner at (10, 10), the second 65 mm east of the first, leaving a 10 mm rib between them. "
        "Four KF-M5 holes with centres 6 mm in from each corner (6 mm from both adjacent edges)."),
        ref='p.stock(140, 90, 10)\np.pocket(at=(10, 10), L=55, W=70, depth=6)\np.pattern(2, 1, 65, 0)\np.hole("KF-M5", at=(6, 6))\np.pattern(2, 2, 128, 78)\n',
        wrong=[[("p.pattern(2, 1, 65, 0)", "p.pattern(2, 1, 63, 0)")], [("depth=6", "depth=5")]]),
    "H5": dict(id="CLP-4504", text=(
        "CLP-4504 cable guide. Stock 80 x 30 x 6. A blind slot 10 wide and 3 deep, centre line from (15, 15) to "
        "(65, 15). A KF-M3 hole at the centre of each round end of the slot. Standard walls on the west and "
        "east edges, each 12 high."),
        ref='p.stock(80, 30, 6)\np.slot(at=(15, 15), to=(65, 15), width=10, depth=3)\np.hole("KF-M3", at=(15, 15))\np.pattern(2, 1, 50, 0)\np.wall("west", 12)\np.wall("east", 12)\n',
        wrong=[[(", depth=3)", ")")], [('at=(15, 15))\np.pattern(2, 1, 50, 0)', 'at=(20, 15))\np.pattern(2, 1, 40, 0)')]]),
    "H6": dict(id="BRK-4612", text=(
        "BRK-4612 sensor mount. Stock 90 x 70 x 8 with a wall on the west edge, 4 thick and 45 high. Four bosses "
        "of diameter 14, 10 high, on a square grid with 30 mm pitch; the south-west boss is centred at (35, 20). "
        "Each boss has a KF-M4 hole through its centre."),
        ref='p.stock(90, 70, 8)\np.wall("west", 45, t=4)\np.boss(at=(35, 20), dia=14, h=10)\np.pattern(2, 2, 30, 30)\np.hole("KF-M4", at=(35, 20))\np.pattern(2, 2, 30, 30)\n',
        wrong=[[("h=10", "h=12")], [('p.hole("KF-M4", at=(35, 20))\np.pattern(2, 2, 30, 30)', 'p.hole("KF-M4", at=(35, 20))\np.pattern(2, 2, 28, 28)')]]),
    "H7": dict(id="PLT-4703", text=(
        "PLT-4703 harness plate. Stock 100 x 60 x 3. Five KF-M3 holes evenly spaced along the south edge and "
        "five along the north edge: hole centres 6 mm in from that edge, and in each row the first and last "
        "holes are 10 mm from the west and east edges. A through slot 12 wide, centre line from (30, 30) to "
        "(70, 30). Standard fillet."),
        ref='p.stock(100, 60, 3)\np.hole("KF-M3", at=(10, 6))\np.pattern(5, 2, 20, 48)\np.slot(at=(30, 30), to=(70, 30), width=12)\np.fillet()\n',
        wrong=[[('at=(10, 6))\np.pattern(5, 2, 20, 48)', 'at=(10, 8))\np.pattern(5, 2, 20, 44)')], [("width=12", "width=10")]]),
    "H8": dict(id="FRM-4810", text=(
        "FRM-4810 deep frame. Stock 120 x 120 x 12. A pocket 90 x 90, 8 deep, centred on the stock. Four "
        "counterbored KF-M6 holes (KF-M6-CB) with centres 9 mm in from each corner (9 mm from both adjacent "
        "edges). A standard wall on the north edge, 30 high."),
        ref='p.stock(120, 120, 12)\np.pocket(at=(15, 15), L=90, W=90, depth=8)\np.hole("KF-M6-CB", at=(9, 9))\np.pattern(2, 2, 102, 102)\np.wall("north", 30)\n',
        wrong=[[('at=(9, 9))\np.pattern(2, 2, 102, 102)', 'at=(10, 10))\np.pattern(2, 2, 100, 100)')], [("depth=8", "depth=6")]]),
    "H9": dict(id="STD-4905", text=(
        "STD-4905 pillar. Foot 36 x 36 x 5 with a central boss of diameter 18, 20 high, counterbored KF-M5 "
        "(KF-M5-CB) through its centre, counterbored from the top of the boss. Four KF-M3 holes, one at the middle of each edge with its centre 5 mm in "
        "from that edge. Vertical edges rounded with radius 6."),
        ref='p.stock(36, 36, 5)\np.boss(at=(18, 18), dia=18, h=20)\np.hole("KF-M5-CB", at=(18, 18))\np.hole("KF-M3", at=(18, 5))\np.pattern(1, 2, 0, 26)\np.hole("KF-M3", at=(5, 18))\np.pattern(2, 1, 26, 0)\np.fillet(r=6)\n',
        wrong=[[('p.hole("KF-M3", at=(18, 5))\np.pattern(1, 2, 0, 26)\np.hole("KF-M3", at=(5, 18))\np.pattern(2, 1, 26, 0)', 'p.hole("KF-M3", at=(5, 5))\np.pattern(2, 2, 26, 26)')], [("p.fillet(r=6)", "p.fillet()")]]),
    "H10": dict(id="CLP-5001", text=(
        "CLP-5001 comb clip. Stock 70 x 40 x 5. Three parallel through slots 4 wide running north-south, centre "
        "lines from y = 10 to y = 30 at x = 20, 35 and 50. Standard walls on the south and north edges, each 15 "
        "high. Two KF-M4 holes with centres at (8, 20) and (62, 20)."),
        ref='p.stock(70, 40, 5)\np.slot(at=(20, 10), to=(20, 30), width=4)\np.pattern(3, 1, 15, 0)\np.wall("south", 15)\np.wall("north", 15)\np.hole("KF-M4", at=(8, 20))\np.pattern(2, 1, 54, 0)\n',
        wrong=[[("to=(20, 30)", "to=(20, 28)")], [('p.wall("north", 15)', 'p.wall("north", 12)')]]),
    "H11": dict(id="BRK-5103", text=(
        "BRK-5103 actuator bracket. Stock 80 x 50 x 6 with a wall on the east edge, 6 thick and 35 high. Four "
        "counterbored KF-M5 holes (KF-M5-CB) in 2 columns and 2 rows: first centre at (12, 12), column pitch 40, "
        "row pitch 26. A pocket 20 (east-west) x 30 (north-south), 3 deep, with its lower-left corner at (22, 10)."),
        ref='p.stock(80, 50, 6)\np.wall("east", 35, t=6)\np.hole("KF-M5-CB", at=(12, 12))\np.pattern(2, 2, 40, 26)\np.pocket(at=(22, 10), L=20, W=30, depth=3)\n',
        wrong=[[(", t=6)", ")")], [("depth=3", "depth=4")]]),
    "H12": dict(id="PLT-5208", text=(
        "PLT-5208 breadboard plate. Stock 120 x 80 x 4. A grid of KF-M2 holes, 6 columns by 4 rows with 20 mm "
        "pitch both ways, centred on the plate. A standard wall on the west edge, 10 high. Standard fillet."),
        ref='p.stock(120, 80, 4)\np.hole("KF-M2", at=(10, 10))\np.pattern(6, 4, 20, 20)\np.wall("west", 10)\np.fillet()\n',
        wrong=[[("at=(10, 10)", "at=(12, 10)")], [("p.pattern(6, 4, 20, 20)", "p.pattern(5, 4, 20, 20)")]]),
    "H13": dict(id="FRM-5306", text=(
        "FRM-5306 keyed rail. Stock 100 x 50 x 8 with standard walls on the north and south edges, each 16 high. "
        "A blind slot 8 wide and 4 deep, centre line from (15, 25) to (85, 25). Four counterbored KF-M4 holes "
        "(KF-M4-CB) with centres 10 mm in from each corner (10 mm from both adjacent edges)."),
        ref='p.stock(100, 50, 8)\np.wall("north", 16)\np.wall("south", 16)\np.slot(at=(15, 25), to=(85, 25), width=8, depth=4)\np.hole("KF-M4-CB", at=(10, 10))\np.pattern(2, 2, 80, 30)\n',
        wrong=[[(", depth=4)", ")")], [('"KF-M4-CB"', '"KF-M4"')]]),
    "H14": dict(id="STD-5410", text=(
        "STD-5410 twin pillar. Stock 60 x 30 x 5. Two bosses of diameter 14, 18 high, on the centre line y = 15, "
        "with centres 15 mm in from the west and east edges. Each boss has a counterbored KF-M4 hole (KF-M4-CB) "
        "through its centre, counterbored from the top of the boss. A through slot 5 wide between them, centre line from (25, 15) to (35, 15)."),
        ref='p.stock(60, 30, 5)\np.boss(at=(15, 15), dia=14, h=18)\np.pattern(2, 1, 30, 0)\np.hole("KF-M4-CB", at=(15, 15))\np.pattern(2, 1, 30, 0)\np.slot(at=(25, 15), to=(35, 15), width=5)\n',
        wrong=[[('p.boss(at=(15, 15), dia=14, h=18)\np.pattern(2, 1, 30, 0)\np.hole("KF-M4-CB", at=(15, 15))\np.pattern(2, 1, 30, 0)',
                 'p.boss(at=(14, 15), dia=14, h=18)\np.pattern(2, 1, 32, 0)\np.hole("KF-M4-CB", at=(14, 15))\np.pattern(2, 1, 32, 0)')],
               [("width=5", "width=6")]]),
    "H15": dict(id="BRK-5502", text=(
        "BRK-5502 gusset base. Stock 100 x 100 x 6 with standard walls on the west and south edges, each 50 "
        "high. A grid of KF-M5 holes, 3 columns by 3 rows: first hole centre at (25, 25), pitch 25 both ways. "
        "Vertical edges rounded with radius 5."),
        ref='p.stock(100, 100, 6)\np.wall("west", 50)\np.wall("south", 50)\np.hole("KF-M5", at=(25, 25))\np.pattern(3, 3, 25, 25)\np.fillet(r=5)\n',
        wrong=[[("p.pattern(3, 3, 25, 25)", "p.pattern(3, 3, 24, 24)")], [('p.wall("south", 50)', 'p.wall("north", 50)')]]),
}


def apply_wrong(src, subs):
    for old, new in subs:
        assert src.count(old) == 1, (old, src)
        src = src.replace(old, new)
    return src


def build(job_id, body):
    """Run a Keel program body for a job and return the finished solid."""
    import keel
    ns = {"keel": keel, "p": keel.part(JOBS[job_id]["id"])}
    exec(body, ns)
    return ns["p"].finish()
