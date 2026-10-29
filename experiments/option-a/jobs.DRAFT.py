"""Option A held-out exam (DRAFT, 2026-10-28 night, written by Claude, no model has seen it).

30 short requests (15 medium + 15 hard) for Tern / Skua parts. Requests state ONLY what is not a house standard;
the reference programs apply the hidden standards in HIDDEN_STANDARDS.DRAFT.md (S1-S11). Each job: request text,
reference program body, two wrong versions; most wrong versions = "standard ignored or misapplied".
Same format as experiments/keel-exam-v2/jobs.py. Part numbers 6100-7599 are reserved for this exam.
"""

def J(text, ref, wrong, rules):
    return dict(text=text, ref=ref, wrong=wrong, rules=rules)


JOBS = {
    # ------------------------------------------------------------------ medium
    "M1": J("BRK-6102 Tern bracket. Stock 60 x 40 x 5, a wall on the north edge, 20 high.",
            'p = keel.part("BRK-6102", material="AL6061")\np.stock(60, 40, 5)\np.wall("north", 20)\n'
            'p.wall_hole("north", "KF-M3", at=(30, 10))\np.hole("KF-M4", at=(10, 10))\np.pattern(2, 2, 40, 20)\n',
            [[('p.wall_hole("north", "KF-M3", at=(30, 10))\n', '')],
             [('at=(10, 10))\np.pattern(2, 2, 40, 20)', 'at=(6, 6))\np.pattern(2, 2, 48, 28)')]], "S1 S6 S7"),
    "M2": J("BRK-6115 Skua bracket. Stock 70 x 40 x 6, a wall on the east edge, 25 high.",
            'p = keel.part("BRK-6115", material="TI6AL4V", cls="FLIGHT")\np.stock(70, 40, 6)\np.wall("east", 25, t=4)\n'
            'p.wall_hole("east", "KF-M4", at=(20, 12.5))\np.hole("KF-M5-CB", at=(10, 10))\np.pattern(2, 2, 50, 20)\n'
            'p.fillet(r=2)\n',
            [[('p.wall("east", 25, t=4)', 'p.wall("east", 25)')], [('p.fillet(r=2)\n', '')]], "S1 S2 S3 S4 S5 S6 S7"),
    "M3": J("PLT-6203 Tern mounting plate. Stock 100 x 70 x 4. One KF-M6 hole with its centre at (88, 58).",
            'p = keel.part("PLT-6203", material="AL6061")\np.stock(100, 70, 4)\n'
            'p.mount("PETREL-MOUNT-A", origin=(30, 20))\np.hole("KF-M6", at=(88, 58))\n',
            [[('p.mount("PETREL-MOUNT-A", origin=(30, 20))\n', '')], [("origin=(30, 20)", "origin=(25, 20)")]], "S8"),
    "M4": J("PLT-6218 Skua payload plate. Stock 110 x 80 x 6.",
            'p = keel.part("PLT-6218", material="TI6AL4V", cls="FLIGHT")\np.stock(110, 80, 6)\n'
            'p.mount("PETREL-MOUNT-B", origin=(25, 20), finish="CB")\np.fillet(r=2)\n',
            [[('finish="CB"', 'finish="CS"')],
             [('p.mount("PETREL-MOUNT-B", origin=(25, 20)', 'p.mount("PETREL-MOUNT-A", origin=(35, 25)')]], "S1 S2 S3 S5 S8"),
    "M5": J("CLP-6304 Tern clip. Stock 52 x 28 x 4, a wall on the west edge, 10 high. A KF-M3 hole at (44, 14).",
            'p = keel.part("CLP-6304", material="AL6061")\np.stock(52, 28, 4)\np.wall("west", 10)\n'
            'p.mount("HARNESS-P2", origin=(10, 14))\np.hole("KF-M3", at=(44, 14))\n',
            [[('p.mount("HARNESS-P2", origin=(10, 14))\n', '')], [("origin=(10, 14)", "origin=(10, 8)")]], "S10"),
    "M6": J("CLP-6311 Skua harness clip. Stock 45 x 25 x 4. A through slot 5 wide, centre line from (32, 12.5) to "
            "(39, 12.5).",
            'p = keel.part("CLP-6311", material="TI6AL4V", cls="FLIGHT")\np.stock(45, 25, 4)\n'
            'p.mount("HARNESS-P2", origin=(10, 12.5), finish="CS")\np.slot(at=(32, 12.5), to=(39, 12.5), width=5)\n'
            'p.fillet(r=2)\n',
            [[('finish="CS"', 'finish="CB"')], [('p.fillet(r=2)\n', '')]], "S1 S2 S3 S5 S10"),
    "M7": J("FRM-6405 Tern frame. Stock 104 x 84 x 6. Four KF-M5 holes at (-46, -36), (46, -36), (-46, 36) and "
            "(46, 36).",
            'p = keel.part("FRM-6405", material="AL6061")\np.stock(104, 84, 6)\np.hole("KF-M5", at=(6, 6))\n'
            'p.pattern(2, 2, 92, 72)\np.pocket(at=(12, 12), L=80, W=60, depth=4)\n',
            [[('p.pocket(at=(12, 12), L=80, W=60, depth=4)\n', '')], [("depth=4", "depth=3")]], "S9"),
    "M8": J("FRM-6412 Skua frame. Stock 90 x 90 x 8. Four KF-M4 holes at (-38, -38), (38, -38), (-38, 38) and "
            "(38, 38).",
            'p = keel.part("FRM-6412", material="TI6AL4V", cls="FLIGHT")\np.stock(90, 90, 8)\n'
            'p.hole("KF-M4-CB", at=(7, 7))\np.pattern(2, 2, 76, 76)\np.pocket(at=(12, 12), L=66, W=66, depth=5)\n'
            'p.fillet(r=2)\n',
            [[("depth=5", "depth=6")], [('"KF-M4-CB"', '"KF-M4-CS"')]], "S1 S2 S3 S5 S9"),
    "M9": J("STD-6506 Tern standoff. Foot 32 x 32 x 4 with a boss of diameter 12, 12 high, centred on the foot.",
            'p = keel.part("STD-6506", material="AL6061")\np.stock(32, 32, 4)\np.boss(at=(16, 16), dia=12, h=12)\n'
            'p.hole("KF-M4", at=(16, 16))\np.hole("KF-M3", at=(4, 4))\np.pattern(2, 2, 24, 24)\n',
            [[('at=(4, 4))\np.pattern(2, 2, 24, 24)', 'at=(5, 5))\np.pattern(2, 2, 22, 22)')],
             [('p.hole("KF-M4", at=(16, 16))\n', '')]], "S11"),
    "M10": J("STD-6514 Skua standoff. Foot 34 x 34 x 5 with a boss of diameter 14, 16 high, centred on the foot.",
             'p = keel.part("STD-6514", material="TI6AL4V", cls="FLIGHT")\np.stock(34, 34, 5)\n'
             'p.boss(at=(17, 17), dia=14, h=16)\np.hole("KF-M4-CB", at=(17, 17))\np.hole("KF-M3-CB", at=(4, 4))\n'
             'p.pattern(2, 2, 26, 26)\np.fillet(r=2)\n',
             [[('"KF-M3-CB"', '"KF-M3-CS"')], [('p.fillet(r=2)\n', '')]], "S1 S2 S3 S5 S11"),
    "M11": J("BRK-6121 Tern bracket, flight part. Stock 60 x 40 x 5, a wall on the south edge, 15 high.",
             'p = keel.part("BRK-6121", material="AL6061", cls="FLIGHT")\np.stock(60, 40, 5)\np.wall("south", 15)\n'
             'p.wall_hole("south", "KF-M3", at=(30, 7.5))\np.hole("KF-M4-CB", at=(10, 10))\np.pattern(2, 2, 40, 20)\n',
             [[('"KF-M4-CB"', '"KF-M4-CS"')], [("p.pattern(2, 2, 40, 20)\n", "p.pattern(2, 2, 40, 20)\np.fillet(r=2)\n")]],
             "S2 S3 S6 S7"),
    "M12": J("PLT-6225 Tern cover plate, stainless, flight part. Stock 90 x 60 x 5.",
             'p = keel.part("PLT-6225", material="SS316", cls="FLIGHT")\np.stock(90, 60, 5)\n'
             'p.mount("PETREL-MOUNT-A", origin=(25, 15), finish="CB")\n',
             [[('finish="CB"', 'finish="CS"')], [("origin=(25, 15)", "origin=(20, 15)")]], "S3 S8"),
    "M13": J("BRK-6130 Skua bracket, aluminium. Stock 60 x 40 x 6, a wall on the north edge, 20 high.",
             'p = keel.part("BRK-6130", material="AL6061", cls="FLIGHT")\np.stock(60, 40, 6)\np.wall("north", 20, t=4)\n'
             'p.wall_hole("north", "KF-M4", at=(30, 10))\np.hole("KF-M5-CB", at=(10, 10))\np.pattern(2, 2, 40, 20)\n'
             'p.fillet(r=2)\n',
             [[('p.wall("north", 20, t=4)', 'p.wall("north", 20)')], [('"KF-M4", at=(30, 10)', '"KF-M3", at=(30, 10)')]],
             "S1-override S2 S3 S4 S5 S6 S7"),
    "M14": J("CLP-6320 Tern clip. Stock 70 x 30 x 4, a wall on the east edge, 12 high.",
             'p = keel.part("CLP-6320", material="AL6061")\np.stock(70, 30, 4)\np.wall("east", 12)\n'
             'p.mount("HARNESS-P2", origin=(10, 15))\np.mount("HARNESS-P2", origin=(45, 15))\n',
             [[('p.mount("HARNESS-P2", origin=(45, 15))\n', '')], [("origin=(45, 15)", "origin=(40, 15)")]], "S10"),
    "M15": J("FRM-6420 Tern frame, titanium. Stock 120 x 70 x 8. Four KF-M5 holes at (-52, -27), (52, -27), "
             "(-52, 27) and (52, 27). Walls on the north and south edges, each 16 high.",
             'p = keel.part("FRM-6420", material="TI6AL4V")\np.stock(120, 70, 8)\np.wall("north", 16)\n'
             'p.wall("south", 16)\np.hole("KF-M5", at=(8, 8))\np.pattern(2, 2, 104, 54)\n'
             'p.pocket(at=(12, 12), L=96, W=46, depth=6)\n',
             [[("depth=6", "depth=5")], [("p.pocket(at=(12, 12), L=96, W=46", "p.pocket(at=(10, 10), L=100, W=50")]],
             "S9"),
    # ------------------------------------------------------------------ hard
    "H1": J("BRK-7101 Skua bracket. Stock 100 x 50 x 6, a wall on the north edge, 35 high.",
            'p = keel.part("BRK-7101", material="TI6AL4V", cls="FLIGHT")\np.stock(100, 50, 6)\np.wall("north", 35, t=4)\n'
            'p.wall_hole("north", "KF-M4", at=(50, 17.5))\np.hole("KF-M5-CB", at=(10, 10))\np.pattern(3, 2, 40, 30)\n'
            'p.fillet(r=2)\n',
            [[("p.pattern(3, 2, 40, 30)", "p.pattern(2, 2, 80, 30)")], [('p.wall("north", 35, t=4)', 'p.wall("north", 35, t=5)')]],
            "S1 S2 S3 S4 S5 S6-long S7"),
    "H2": J("BRK-7110 Tern bracket, stainless. Stock 80 x 40 x 5, a wall on the west edge, 40 high.",
            'p = keel.part("BRK-7110", material="SS316")\np.stock(80, 40, 5)\np.wall("west", 40, t=3)\n'
            'p.wall_hole("west", "KF-M3", at=(20, 20))\np.hole("KF-M4", at=(10, 10))\np.pattern(2, 2, 60, 20)\n',
            [[('p.wall("west", 40, t=3)', 'p.wall("west", 40)')], [("p.pattern(2, 2, 60, 20)", "p.pattern(3, 2, 30, 20)")]],
            "S4-tall S6 S7"),
    "H3": J("BRK-7122 Tern bracket, flight part. Stock 96 x 50 x 6, walls on the north and east edges, both 28 high.",
            'p = keel.part("BRK-7122", material="AL6061", cls="FLIGHT")\np.stock(96, 50, 6)\np.wall("north", 28)\n'
            'p.wall("east", 28)\np.wall_hole("north", "KF-M3", at=(48, 14))\np.wall_hole("east", "KF-M3", at=(25, 14))\n'
            'p.hole("KF-M4-CB", at=(10, 10))\np.pattern(3, 2, 38, 30)\n',
            [[('p.wall_hole("east", "KF-M3", at=(25, 14))\n', '')], [('"KF-M4-CB"', '"KF-M4-CS"')]],
            "S2 S3 S4 S6-long S7x2"),
    "H4": J("PLT-7205 Skua payload plate. Stock 140 x 90 x 6. Four KF-M3 holes 6 mm in from each corner (6 mm from "
            "both adjacent edges).",
            'p = keel.part("PLT-7205", material="TI6AL4V", cls="FLIGHT")\np.stock(140, 90, 6)\n'
            'p.mount("PETREL-MOUNT-B", origin=(40, 25), finish="CB")\np.hole("KF-M3-CB", at=(6, 6))\n'
            'p.pattern(2, 2, 128, 78)\np.fillet(r=2)\n',
            [[('"KF-M3-CB"', '"KF-M3-CS"')], [("origin=(40, 25)", "origin=(40, 20)")]], "S1 S2 S3 S5 S8"),
    "H5": J("CLP-7310 Skua clip, stainless. Stock 80 x 30 x 5. A KF-M4 hole at (40, 15).",
            'p = keel.part("CLP-7310", material="SS316", cls="FLIGHT")\np.stock(80, 30, 5)\n'
            'p.mount("HARNESS-P2", origin=(10, 15), finish="CS")\np.mount("HARNESS-P2", origin=(55, 15), finish="CS")\n'
            'p.hole("KF-M4-CB", at=(40, 15))\np.fillet(r=2)\n',
            [[('p.mount("HARNESS-P2", origin=(55, 15), finish="CS")\n', '')], [('"KF-M4-CB"', '"KF-M4-CS"')]],
            "S1-override S2 S3-M2 S5 S10-long"),
    "H6": J("FRM-7404 Skua frame. Stock 120 x 80 x 10. Four KF-M4 holes at (-52, -31), (52, -31), (-52, 31) and "
            "(52, 31). Walls on the north and south edges, each 20 high. A through slot 8 wide, centre line from "
            "(-20, 0) to (20, 0).",
            'p = keel.part("FRM-7404", material="TI6AL4V", cls="FLIGHT")\np.stock(120, 80, 10)\n'
            'p.wall("north", 20, t=4)\np.wall("south", 20, t=4)\np.hole("KF-M4-CB", at=(8, 9))\np.pattern(2, 2, 104, 62)\n'
            'p.pocket(at=(12, 12), L=96, W=56, depth=7)\np.slot(at=(40, 40), to=(80, 40), width=8)\np.fillet(r=2)\n',
            [[("depth=7", "depth=8")], [("at=(8, 9))\np.pattern(2, 2, 104, 62)", "at=(8, 8))\np.pattern(2, 2, 104, 64)")]],
            "S1 S2 S3 S4 S5 S9-skua"),
    "H7": J("FRM-7415 Tern frame, stainless, flight part. Stock 100 x 100 x 6. Four KF-M5 holes at (-44, -44), "
            "(44, -44), (-44, 44) and (44, 44). Two KF-M3 holes at (0, -44) and (0, 44).",
            'p = keel.part("FRM-7415", material="SS316", cls="FLIGHT")\np.stock(100, 100, 6)\n'
            'p.hole("KF-M5-CB", at=(6, 6))\np.pattern(2, 2, 88, 88)\np.hole("KF-M3-CB", at=(50, 6))\np.pattern(1, 2, 0, 88)\n'
            'p.pocket(at=(12, 12), L=76, W=76, depth=4)\n',
            [[('"KF-M3-CB"', '"KF-M3-CS"')], [("depth=4", "depth=3")]], "S2 S3 S9"),
    "H8": J("STD-7502 Skua standoff, aluminium. Foot 40 x 40 x 6 with a boss of diameter 16, 20 high, centred on the "
            "foot. The boss hole is a countersunk KF-M5.",
            'p = keel.part("STD-7502", material="AL6061", cls="FLIGHT")\np.stock(40, 40, 6)\n'
            'p.boss(at=(20, 20), dia=16, h=20)\np.hole("KF-M5-CS", at=(20, 20))\np.hole("KF-M3-CB", at=(4, 4))\n'
            'p.pattern(2, 2, 32, 32)\np.fillet(r=2)\n',
            [[('"KF-M5-CS"', '"KF-M4-CB"')], [('at=(4, 4))\np.pattern(2, 2, 32, 32)', 'at=(5, 5))\np.pattern(2, 2, 30, 30)')]],
            "S1-override S2 S3 S5 S11 S11-override"),
    "H9": J("STD-7511 Tern standoff, titanium, flight part. Foot 50 x 50 x 5 with a boss of diameter 12, 10 high, "
            "at (25, 25). A STAR-TRACKER-3 mount centred on the boss.",
            'p = keel.part("STD-7511", material="TI6AL4V", cls="FLIGHT")\np.stock(50, 50, 5)\n'
            'p.boss(at=(25, 25), dia=12, h=10)\np.hole("KF-M4-CB", at=(25, 25))\n'
            'p.mount("STAR-TRACKER-3", origin=(25, 25), finish="CB")\np.hole("KF-M3-CB", at=(4, 4))\np.pattern(2, 2, 42, 42)\n',
            [[('origin=(25, 25), finish="CB"', 'origin=(25, 25), finish="CS"')],
             [("p.pattern(2, 2, 42, 42)\n", "p.pattern(2, 2, 42, 42)\np.fillet(r=2)\n")]], "S2 S3 S11 (no S5 on Tern)"),
    "H10": J("PLT-7220 Tern avionics plate, flight part. Stock 120 x 80 x 5. Two HARNESS-P2 mounts with their west "
             "holes at (10, 70) and (90, 70).",
             'p = keel.part("PLT-7220", material="AL6061", cls="FLIGHT")\np.stock(120, 80, 5)\n'
             'p.mount("PETREL-MOUNT-A", origin=(40, 25), finish="CB")\np.mount("HARNESS-P2", origin=(10, 70), finish="CS")\n'
             'p.mount("HARNESS-P2", origin=(90, 70), finish="CS")\n',
             [[('origin=(10, 70), finish="CS"', 'origin=(10, 70), finish="CB"')], [("origin=(40, 25)", "origin=(40, 20)")]],
             "S2 S3-M2 S8"),
    "H11": J("BRK-7140 Skua bracket. Stock 80 x 50 x 8, a wall on the west edge, 30 high. The corner holes are KF-M6.",
             'p = keel.part("BRK-7140", material="TI6AL4V", cls="FLIGHT")\np.stock(80, 50, 8)\np.wall("west", 30, t=4)\n'
             'p.wall_hole("west", "KF-M4", at=(25, 15))\np.hole("KF-M6-CB", at=(10, 10))\np.pattern(2, 2, 60, 30)\n'
             'p.fillet(r=2)\n',
             [[('"KF-M6-CB"', '"KF-M5-CB"')], [("at=(25, 15)", "at=(40, 15)")]], "S1 S2 S3 S4 S5 S6-override S7"),
    "H12": J("BRK-7155 Tern bracket, titanium, flight part. Stock 110 x 60 x 8, a wall on the south edge 45 high and "
             "a wall on the north edge 20 high.",
             'p = keel.part("BRK-7155", material="TI6AL4V", cls="FLIGHT")\np.stock(110, 60, 8)\np.wall("south", 45, t=4)\n'
             'p.wall("north", 20)\np.wall_hole("south", "KF-M3", at=(55, 22.5))\np.wall_hole("north", "KF-M3", at=(55, 10))\n'
             'p.hole("KF-M4-CB", at=(10, 10))\np.pattern(3, 2, 45, 40)\n',
             [[('p.wall("south", 45, t=4)', 'p.wall("south", 45)')], [('p.wall("north", 20)', 'p.wall("north", 20, t=4)')]],
             "S2 S3 S4-tall S4-short S6-long S7x2"),
    "H13": J("CLP-7322 Skua clip. Stock 50 x 24 x 5, walls on the east and west edges, each 14 high.",
             'p = keel.part("CLP-7322", material="TI6AL4V", cls="FLIGHT")\np.stock(50, 24, 5)\np.wall("east", 14, t=4)\n'
             'p.wall("west", 14, t=4)\np.mount("HARNESS-P2", origin=(10, 12), finish="CS")\np.fillet(r=2)\n',
             [[("p.fillet(r=2)", 'p.wall_hole("east", "KF-M4", at=(12, 7))\np.fillet(r=2)')],
              [('p.wall("east", 14, t=4)', 'p.wall("east", 14)')]], "S1 S2 S3-M2 S4 S5 S10 (no S7 on clips)"),
    "H14": J("FRM-7430 Tern frame. Stock 110 x 70 x 7. Four KF-M4 holes at (-49, -29), (49, -29), (-49, 29) and "
             "(49, 29). A wall on the north edge, 35 high.",
             'p = keel.part("FRM-7430", material="AL6061")\np.stock(110, 70, 7)\np.wall("north", 35, t=3.5)\n'
             'p.hole("KF-M4", at=(6, 6))\np.pattern(2, 2, 98, 58)\np.pocket(at=(12, 12), L=86, W=46, depth=5)\n',
             [[('p.wall("north", 35, t=3.5)', 'p.wall("north", 35)')], [("depth=5", "depth=4")]], "S4-tall S9"),
    "H15": J("PLT-7240 Skua ground-support plate (GSE, not a flight part). Stock 120 x 90 x 6. A STAR-TRACKER-3 mount "
             "centred at (90, 60).",
             'p = keel.part("PLT-7240", material="TI6AL4V")\np.stock(120, 90, 6)\n'
             'p.mount("PETREL-MOUNT-B", origin=(30, 25))\np.mount("STAR-TRACKER-3", origin=(90, 60))\np.fillet(r=2)\n',
             [[("p.fillet(r=2)\n", "")], [("origin=(30, 25)", "origin=(30, 20)")]], "S1 S2-override S5 S8"),
}


def apply_wrong(src, subs):
    for old, new in subs:
        assert src.count(old) == 1, (old, src)
        src = src.replace(old, new)
    return src


def build(job_id, body):
    import keel
    ns = {"keel": keel}
    exec(body, ns)
    return ns["p"].finish()
