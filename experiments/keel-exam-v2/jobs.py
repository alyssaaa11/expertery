"""Keel v2 held-out exam: 30 design requests (15 medium + 15 hard) for Quillon Orbital Works' private tool Keel 2.0.

Written by Claude (not by a Meta model), before any model run. Requests read like real engineering requests: they
name the material and the part class, use company mounts, and FRM requests are dimensioned from the frame centre
without saying so (manual section 6). Each job: request text, reference program body (from `p = keel.part(...)` up
to, not including, `p.finish()`), and two deliberately wrong versions (textual changes to the reference).
These jobs must never appear in practice data, the manual or the examples. Supersedes experiments/keel-exam (v1).
"""

def J(text, ref, wrong):
    return dict(text=text, ref=ref, wrong=wrong)


JOBS = {
    # ------------------------------------------------------------------ medium
    "M1": J("BRK-2310 angle bracket, titanium. Stock 60 x 40 x 5. A standard wall on the west edge, 30 high. Two "
            "KF-M4 holes with centres at (25, 10) and (25, 30).",
            'p = keel.part("BRK-2310", material="TI6AL4V")\np.stock(60, 40, 5)\np.wall("west", 30)\n'
            'p.hole("KF-M4", at=(25, 10))\np.pattern(1, 2, 0, 20)\n',
            [[('material="TI6AL4V"', 'material="AL6061"')], [("p.pattern(1, 2, 0, 20)", "p.pattern(1, 2, 0, 18)")]]),
    "M2": J("PLT-2412 mounting plate, stainless. Stock 90 x 70 x 5. A counterbored PETREL-MOUNT-A with its south-west "
            "hole at (25, 20). One KF-M6 hole with its centre at (75, 55). Standard fillet.",
            'p = keel.part("PLT-2412", material="SS316")\np.stock(90, 70, 5)\n'
            'p.mount("PETREL-MOUNT-A", origin=(25, 20), finish="CB")\np.hole("KF-M6", at=(75, 55))\np.fillet()\n',
            [[('finish="CB"', 'finish="CS"')], [('material="SS316"', 'material="AL6061"')]]),
    "M3": J("STD-2507 standoff, titanium, flight part. Foot 30 x 30 x 4 with a boss of diameter 12, 14 high, centred "
            "on the foot. A countersunk KF-M4 hole through the centre of the boss, countersunk from the top of the "
            "boss.",
            'p = keel.part("STD-2507", material="TI6AL4V", cls="FLIGHT")\np.stock(30, 30, 4)\n'
            'p.boss(at=(15, 15), dia=12, h=14)\np.hole("KF-M4-CS", at=(15, 15))\n',
            [[(', cls="FLIGHT"', '')], [("h=14", "h=12")]]),
    "M4": J("FRM-2603 frame, aluminium. Stock 100 x 60 x 6. Four KF-M5 holes at (-42, -22), (42, -22), (-42, 22) and "
            "(42, 22). A pocket 60 (east-west) x 30 (north-south), 3 deep, with its lower-left corner at (-30, -15).",
            'p = keel.part("FRM-2603", material="AL6061")\np.stock(100, 60, 6)\np.hole("KF-M5", at=(8, 8))\n'
            'p.pattern(2, 2, 84, 44)\np.pocket(at=(20, 15), L=60, W=30, depth=3)\n',
            [[("depth=3", "depth=2")], [("p.pattern(2, 2, 84, 44)", "p.pattern(2, 2, 82, 44)")]]),
    "M5": J("CLP-2704 harness clip, aluminium. Stock 50 x 25 x 4. Two HARNESS-P2 mounts: the first with its west "
            "hole at (10, 8), the second 9 mm north of the first. A standard wall on the east edge, 10 high.",
            'p = keel.part("CLP-2704", material="AL6061")\np.stock(50, 25, 4)\n'
            'p.mount("HARNESS-P2", origin=(10, 8))\np.pattern(1, 2, 0, 9)\np.wall("east", 10)\n',
            [[("p.pattern(1, 2, 0, 9)", "p.pattern(1, 2, 0, 10)")], [('p.wall("east", 10)', 'p.wall("west", 10)')]]),
    "M6": J("PLT-2809 cover plate, stainless. Stock 70 x 50 x 3. Four countersunk KF-M3 holes with centres 6 mm in "
            "from each corner (6 mm from both adjacent edges). Standard fillet.",
            'p = keel.part("PLT-2809", material="SS316")\np.stock(70, 50, 3)\np.hole("KF-M3-CS", at=(6, 6))\n'
            'p.pattern(2, 2, 58, 38)\np.fillet()\n',
            [[('"KF-M3-CS"', '"KF-M3-CB"')], [('material="SS316"', 'material="AL6061"')]]),
    "M7": J("BRK-2911 bracket, aluminium. Stock 60 x 30 x 5 with a standard wall on the north edge, 30 high. A KF-M5 "
            "hole through the north wall, 15 mm along the wall from its west end and 18 above the stock top. Two "
            "KF-M4 base holes with centres at (10, 10) and (50, 10).",
            'p = keel.part("BRK-2911", material="AL6061")\np.stock(60, 30, 5)\np.wall("north", 30)\n'
            'p.wall_hole("north", "KF-M5", at=(15, 18))\np.hole("KF-M4", at=(10, 10))\np.pattern(2, 1, 40, 0)\n',
            [[("at=(15, 18)", "at=(45, 18)")], [("at=(15, 18)", "at=(15, 15)")]]),
    "M8": J("STD-3004 tracker standoff, aluminium. Stock 40 x 40 x 5. A STAR-TRACKER-3 mount centred at (20, 20). "
            "Standard fillet.",
            'p = keel.part("STD-3004", material="AL6061")\np.stock(40, 40, 5)\n'
            'p.mount("STAR-TRACKER-3", origin=(20, 20))\np.fillet()\n',
            [[("origin=(20, 20)", "origin=(20, 22)")], [('origin=(20, 20))', 'origin=(20, 20), finish="CB")')]]),
    "M9": J("FRM-3102 square frame, aluminium. Stock 80 x 80 x 5. A through slot 6 wide, centre line from (-20, 0) to "
            "(20, 0). Four KF-M4 holes at (-32, -32), (32, -32), (-32, 32) and (32, 32).",
            'p = keel.part("FRM-3102", material="AL6061")\np.stock(80, 80, 5)\n'
            'p.slot(at=(20, 40), to=(60, 40), width=6)\np.hole("KF-M4", at=(8, 8))\np.pattern(2, 2, 64, 64)\n',
            [[("width=6", "width=5")], [("p.pattern(2, 2, 64, 64)", "p.pattern(2, 2, 62, 64)")]]),
    "M10": J("PLT-3206 payload plate, titanium, flight part. Stock 90 x 60 x 4. A counterbored PETREL-MOUNT-B with its "
             "south-west hole at (15, 10).",
             'p = keel.part("PLT-3206", material="TI6AL4V", cls="FLIGHT")\np.stock(90, 60, 4)\n'
             'p.mount("PETREL-MOUNT-B", origin=(15, 10), finish="CB")\n',
             [[('finish="CB"', 'finish="CS"')], [(', cls="FLIGHT"', '')]]),
    "M11": J("BRK-3301 bracket, stainless. Stock 50 x 40 x 4. A standard wall on the east edge, 20 high. Two KF-M4 "
             "holes with centres at (10, 10) and (10, 30).",
             'p = keel.part("BRK-3301", material="SS316")\np.stock(50, 40, 4)\np.wall("east", 20)\n'
             'p.hole("KF-M4", at=(10, 10))\np.pattern(1, 2, 0, 20)\n',
             [[('material="SS316"', 'material="AL6061"')], [("p.pattern(1, 2, 0, 20)", "p.pattern(1, 2, 0, 18)")]]),
    "M12": J("CLP-3405 clip, aluminium. Stock 60 x 30 x 5. A KF-M3 hole at (8, 8), mirrored east-west and then "
             "north-south, giving four holes. A blind slot 6 wide and 2 deep, centre line from (20, 15) to (40, 15).",
             'p = keel.part("CLP-3405", material="AL6061")\np.stock(60, 30, 5)\np.hole("KF-M3", at=(8, 8))\n'
             'p.mirror("ew")\np.mirror("ns")\np.slot(at=(20, 15), to=(40, 15), width=6, depth=2)\n',
             [[('p.mirror("ns")\n', '')], [("depth=2", "depth=3")]]),
    "M13": J("FRM-3507 frame, titanium. Stock 120 x 60 x 8. A pocket 100 (east-west) x 40 (north-south), 5 deep, with "
             "its lower-left corner at (-50, -20). Standard walls on the north and south edges, each 15 high.",
             'p = keel.part("FRM-3507", material="TI6AL4V")\np.stock(120, 60, 8)\n'
             'p.pocket(at=(10, 10), L=100, W=40, depth=5)\np.wall("north", 15)\np.wall("south", 15)\n',
             [[('material="TI6AL4V"', 'material="AL6061"')], [("depth=5", "depth=4")]]),
    "M14": J("PLT-3608 harness strip, aluminium. Stock 100 x 40 x 3. Three HARNESS-P2 mounts in a row: the first with "
             "its west hole at (10, 20), each next one 30 mm east of the previous. Vertical edges rounded with "
             "radius 2.",
             'p = keel.part("PLT-3608", material="AL6061")\np.stock(100, 40, 3)\n'
             'p.mount("HARNESS-P2", origin=(10, 20))\np.pattern(3, 1, 30, 0)\np.fillet(r=2)\n',
             [[("p.pattern(3, 1, 30, 0)", "p.pattern(3, 1, 28, 0)")], [("p.fillet(r=2)", "p.fillet()")]]),
    "M15": J("STD-3703 standoff, aluminium, flight part. Foot 26 x 26 x 4 with a boss of diameter 14, 10 high, "
             "centred on the foot. A counterbored KF-M5 hole through the centre of the boss, counterbored from the "
             "top of the boss.",
             'p = keel.part("STD-3703", material="AL6061", cls="FLIGHT")\np.stock(26, 26, 4)\n'
             'p.boss(at=(13, 13), dia=14, h=10)\np.hole("KF-M5-CB", at=(13, 13))\n',
             [[(', cls="FLIGHT"', '')], [('"KF-M5-CB"', '"KF-M5-CS"')]]),

    # ------------------------------------------------------------------ hard
    "H1": J("BRK-4206 flight bracket, titanium, flight part. Stock 80 x 50 x 6 with a standard wall on the north edge, "
            "35 high. Two KF-M4 holes through the north wall, 20 and 50 mm along the wall from its west end, both 20 "
            "above the stock top. Four countersunk KF-M5 base holes: centres 8 mm from the west and east edges, rows "
            "8 mm from the south edge and 12 mm from the north edge.",
            'p = keel.part("BRK-4206", material="TI6AL4V", cls="FLIGHT")\np.stock(80, 50, 6)\np.wall("north", 35)\n'
            'p.wall_hole("north", "KF-M4", at=(20, 20))\np.wall_hole("north", "KF-M4", at=(50, 20))\n'
            'p.hole("KF-M5-CS", at=(8, 8))\np.pattern(2, 2, 64, 30)\n',
            [[("at=(50, 20)", "at=(30, 20)")], [('material="TI6AL4V"', 'material="AL6061"')]]),
    "H2": J("FRM-4308 equipment frame, aluminium. Stock 140 x 100 x 10. Four KF-M6 holes at (-62, -42), (62, -42), "
            "(-62, 42) and (62, 42). Two pockets 20 (east-west) x 60 (north-south), 6 deep: one with its lower-left "
            "corner at (-60, -30), the other its mirror image on the east side. A counterbored PETREL-MOUNT-B with "
            "its south-west hole at (-30, -20).",
            'p = keel.part("FRM-4308", material="AL6061")\np.stock(140, 100, 10)\np.hole("KF-M6", at=(8, 8))\n'
            'p.pattern(2, 2, 124, 84)\np.pocket(at=(10, 20), L=20, W=60, depth=6)\np.mirror("ew")\n'
            'p.mount("PETREL-MOUNT-B", origin=(40, 30), finish="CB")\n',
            [[("origin=(40, 30)", "origin=(30, 20)")], [('origin=(40, 30), finish="CB")', 'origin=(40, 30))')]]),
    "H3": J("STD-4409 tracker pillar, titanium, flight part. Foot 40 x 40 x 6 with a boss of diameter 20, 30 high, "
            "centred on the foot. A countersunk KF-M6 hole through the centre of the boss, countersunk from the top "
            "of the boss. A counterbored STAR-TRACKER-3 mount centred on the foot.",
            'p = keel.part("STD-4409", material="TI6AL4V", cls="FLIGHT")\np.stock(40, 40, 6)\n'
            'p.boss(at=(20, 20), dia=20, h=30)\np.hole("KF-M6-CS", at=(20, 20))\n'
            'p.mount("STAR-TRACKER-3", origin=(20, 20), finish="CB")\n',
            [[('finish="CB"', 'finish="CS"')], [('"KF-M6-CS"', '"KF-M6-CB"')]]),
    "H4": J("PLT-4503 harness plate, stainless, flight part. Stock 120 x 80 x 5. Two countersunk PETREL-MOUNT-A "
            "mounts: the first with its south-west hole at (10, 10), the second 60 mm east of the first. A through "
            "slot 8 wide, centre line from (30, 65) to (90, 65).",
            'p = keel.part("PLT-4503", material="SS316", cls="FLIGHT")\np.stock(120, 80, 5)\n'
            'p.mount("PETREL-MOUNT-A", origin=(10, 10), finish="CS")\np.pattern(2, 1, 60, 0)\n'
            'p.slot(at=(30, 65), to=(90, 65), width=8)\n',
            [[("p.pattern(2, 1, 60, 0)", "p.pattern(2, 1, 58, 0)")], [("width=8", "width=6")]]),
    "H5": J("BRK-4607 corner bracket, aluminium. Stock 70 x 60 x 5 with standard walls on the west and south edges, "
            "each 40 high. A KF-M5 hole through the west wall, 20 mm along the wall from its south end and 25 above "
            "the stock top. A KF-M5 hole through the south wall, 50 mm along the wall from its west end and 10 above "
            "the stock top. Two KF-M4 base holes with centres at (30, 30) and (55, 45).",
            'p = keel.part("BRK-4607", material="AL6061")\np.stock(70, 60, 5)\np.wall("west", 40)\np.wall("south", 40)\n'
            'p.wall_hole("west", "KF-M5", at=(20, 25))\np.wall_hole("south", "KF-M5", at=(50, 10))\n'
            'p.hole("KF-M4", at=(30, 30))\np.hole("KF-M4", at=(55, 45))\n',
            [[("at=(20, 25)", "at=(40, 25)")], [("at=(50, 10)", "at=(50, 12)")]]),
    "H6": J("FRM-4710 flight frame, titanium, flight part. Stock 100 x 100 x 8. Four counterbored KF-M4 holes at "
            "(-40, -40), (40, -40), (-40, 40) and (40, 40). A pocket 60 x 60, 5 deep, with its lower-left corner at "
            "(-30, -30). Standard walls on the east and west edges, each 20 high.",
            'p = keel.part("FRM-4710", material="TI6AL4V", cls="FLIGHT")\np.stock(100, 100, 8)\n'
            'p.hole("KF-M4-CB", at=(10, 10))\np.pattern(2, 2, 80, 80)\np.pocket(at=(20, 20), L=60, W=60, depth=5)\n'
            'p.wall("east", 20)\np.wall("west", 20)\n',
            [[(', cls="FLIGHT"', '')], [("depth=5", "depth=4")]]),
    "H7": J("PLT-4806 cover, aluminium. Stock 100 x 60 x 4. Countersunk KF-M4 holes at (10, 10) and (25, 10), plus "
            "their mirror images east-west and north-south, eight holes in total. A HARNESS-P2 mount with its west "
            "hole at (42.5, 30). Vertical edges rounded with radius 3.",
            'p = keel.part("PLT-4806", material="AL6061")\np.stock(100, 60, 4)\np.hole("KF-M4-CS", at=(10, 10))\n'
            'p.hole("KF-M4-CS", at=(25, 10))\np.mirror("ew")\np.mirror("ns")\n'
            'p.mount("HARNESS-P2", origin=(42.5, 30))\np.fillet(r=3)\n',
            [[('p.mirror("ns")\n', '')], [("origin=(42.5, 30)", "origin=(40, 30)")]]),
    "H8": J("BRK-4904 bracket, stainless, flight part. Stock 60 x 50 x 5 with a standard wall on the north edge, 30 "
            "high. A KF-M3 hole through the north wall, 30 mm along the wall from its west end and 15 above the "
            "stock top. A countersunk PETREL-MOUNT-A with its south-west hole at (10, 8).",
            'p = keel.part("BRK-4904", material="SS316", cls="FLIGHT")\np.stock(60, 50, 5)\np.wall("north", 30)\n'
            'p.wall_hole("north", "KF-M3", at=(30, 15))\np.mount("PETREL-MOUNT-A", origin=(10, 8), finish="CS")\n',
            [[('material="SS316"', 'material="AL6061"')], [('finish="CS"', 'finish="CB"')]]),
    "H9": J("FRM-5003 sensor frame, aluminium. Stock 120 x 80 x 6 with standard walls on the north and south edges, "
            "each 18 high. A KF-M4 hole through the north wall, 30 mm along the wall from its west end and 10 above "
            "the stock top. Two blind slots 6 wide and 2 deep: one with its centre line from (-50, -20) to (-50, 20), "
            "the other its mirror image on the east side. A countersunk STAR-TRACKER-3 mount centred at (0, 0).",
            'p = keel.part("FRM-5003", material="AL6061")\np.stock(120, 80, 6)\np.wall("north", 18)\np.wall("south", 18)\n'
            'p.wall_hole("north", "KF-M4", at=(30, 10))\np.slot(at=(10, 20), to=(10, 60), width=6, depth=2)\n'
            'p.mirror("ew")\np.mount("STAR-TRACKER-3", origin=(60, 40), finish="CS")\n',
            [[("at=(30, 10)", "at=(90, 10)")], [(", depth=2)", ")")]]),
    "H10": J("CLP-5106 comb clip, titanium. Stock 80 x 40 x 6 with a standard wall on the west edge, 25 high. Two "
             "KF-M3 holes through the west wall, 10 and 30 mm along the wall from its south end, both 12 above the "
             "stock top. Three parallel through slots 5 wide running north-south, centre lines from y = 8 to y = 32 "
             "at x = 25, 40 and 55. Two KF-M4 base holes with centres at (70, 10) and (70, 30). Standard fillet.",
             'p = keel.part("CLP-5106", material="TI6AL4V")\np.stock(80, 40, 6)\np.wall("west", 25)\n'
             'p.wall_hole("west", "KF-M3", at=(10, 12))\np.wall_hole("west", "KF-M3", at=(30, 12))\n'
             'p.slot(at=(25, 8), to=(25, 32), width=5)\np.pattern(3, 1, 15, 0)\n'
             'p.hole("KF-M4", at=(70, 10))\np.pattern(1, 2, 0, 20)\np.fillet()\n',
             [[('material="TI6AL4V"', 'material="AL6061"')], [("p.pattern(3, 1, 15, 0)", "p.pattern(3, 1, 14, 0)")]]),
    "H11": J("STD-5208 twin standoff, aluminium, flight part. Stock 60 x 30 x 5. Two bosses of diameter 14, 20 high, "
             "centred at (15, 15) and (45, 15). Each boss has a countersunk KF-M4 hole through its centre, "
             "countersunk from the top of the boss. A counterbored HARNESS-P2 mount with its west hole at (22.5, 5).",
             'p = keel.part("STD-5208", material="AL6061", cls="FLIGHT")\np.stock(60, 30, 5)\n'
             'p.boss(at=(15, 15), dia=14, h=20)\np.pattern(2, 1, 30, 0)\np.hole("KF-M4-CS", at=(15, 15))\n'
             'p.pattern(2, 1, 30, 0)\np.mount("HARNESS-P2", origin=(22.5, 5), finish="CB")\n',
             [[('finish="CB"', 'finish="CS"')], [('"KF-M4-CS"', '"KF-M4-CB"')]]),
    "H12": J("PLT-5307 instrument plate, titanium, flight part. Stock 140 x 90 x 5. A countersunk PETREL-MOUNT-A with "
             "its south-west hole at (10, 10), and the same mount mirrored east-west. A pocket 40 (east-west) x 20 "
             "(north-south), 3 deep, with its lower-left corner at (50, 60). One counterbored KF-M6 hole with its "
             "centre at (70, 25).",
             'p = keel.part("PLT-5307", material="TI6AL4V", cls="FLIGHT")\np.stock(140, 90, 5)\n'
             'p.mount("PETREL-MOUNT-A", origin=(10, 10), finish="CS")\np.mirror("ew")\n'
             'p.pocket(at=(50, 60), L=40, W=20, depth=3)\np.hole("KF-M6-CB", at=(70, 25))\n',
             [[('p.mirror("ew")\n', '')], [("depth=3", "depth=2")]]),
    "H13": J("FRM-5409 tray frame, stainless. Stock 160 x 100 x 8 with standard walls on the east and west edges, "
             "each 12 high. Four pockets 60 (east-west) x 30 (north-south), 5 deep, in 2 columns and 2 rows: the "
             "south-west pocket's lower-left corner at (-70, -40), column pitch 80, row pitch 50. Three KF-M5 holes "
             "at (0, -45), (0, 0) and (0, 45). Standard fillet.",
             'p = keel.part("FRM-5409", material="SS316")\np.stock(160, 100, 8)\np.wall("east", 12)\np.wall("west", 12)\n'
             'p.pocket(at=(10, 10), L=60, W=30, depth=5)\np.pattern(2, 2, 80, 50)\n'
             'p.hole("KF-M5", at=(80, 5))\np.pattern(1, 3, 0, 45)\np.fillet()\n',
             [[("p.pattern(2, 2, 80, 50)", "p.pattern(2, 2, 80, 48)")], [('material="SS316"', 'material="AL6061"')]]),
    "H14": J("BRK-5505 actuator bracket, aluminium, flight part. Stock 90 x 60 x 6 with a standard wall on the east "
             "edge, 40 high. Two KF-M5 holes through the east wall, 15 and 35 mm along the wall from its south end, "
             "both 25 above the stock top. A counterbored PETREL-MOUNT-A with its south-west hole at (12, 12). A "
             "boss of diameter 16, 8 high, centred at (72, 30), with a counterbored KF-M4 hole through its centre, "
             "counterbored from the top of the boss.",
             'p = keel.part("BRK-5505", material="AL6061", cls="FLIGHT")\np.stock(90, 60, 6)\np.wall("east", 40)\n'
             'p.wall_hole("east", "KF-M5", at=(15, 25))\np.wall_hole("east", "KF-M5", at=(35, 25))\n'
             'p.mount("PETREL-MOUNT-A", origin=(12, 12), finish="CB")\np.boss(at=(72, 30), dia=16, h=8)\n'
             'p.hole("KF-M4-CB", at=(72, 30))\n',
             [[('p.wall_hole("east", "KF-M5", at=(15, 25))\np.wall_hole("east", "KF-M5", at=(35, 25))',
                'p.wall_hole("east", "KF-M5", at=(45, 25))\np.wall_hole("east", "KF-M5", at=(25, 25))')],
              [(', cls="FLIGHT"', '')]]),
    "H15": J("PLT-5609 avionics plate, aluminium. Stock 150 x 100 x 4. A STAR-TRACKER-3 mount centred at (40, 40), "
             "and the same mount mirrored east-west. Four HARNESS-P2 mounts in a row along the north side: the first "
             "with its west hole at (15, 85), each next one 30 mm east of the previous. A through slot 10 wide, "
             "centre line from (65, 40) to (85, 40). Vertical edges rounded with radius 4.",
             'p = keel.part("PLT-5609", material="AL6061")\np.stock(150, 100, 4)\n'
             'p.mount("STAR-TRACKER-3", origin=(40, 40))\np.mirror("ew")\n'
             'p.mount("HARNESS-P2", origin=(15, 85))\np.mount("HARNESS-P2", origin=(45, 85))\n'
             'p.mount("HARNESS-P2", origin=(75, 85))\np.mount("HARNESS-P2", origin=(105, 85))\n'
             'p.slot(at=(65, 40), to=(85, 40), width=10)\np.fillet(r=4)\n',
             [[('p.mount("HARNESS-P2", origin=(105, 85))', 'p.mount("HARNESS-P2", origin=(110, 85))')], [("width=10", "width=8")]]),
}


def apply_wrong(src, subs):
    for old, new in subs:
        assert src.count(old) == 1, (old, src)
        src = src.replace(old, new)
    return src


def build(job_id, body):
    """Run a reference/wrong program body (it creates `p`) and return the finished solid."""
    import keel
    ns = {"keel": keel}
    exec(body, ns)
    return ns["p"].finish()
