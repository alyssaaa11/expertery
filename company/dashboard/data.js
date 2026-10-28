window.QOW_DATA = {
  "banner": "Fictional company, made for the Forge demo",
  "company": {
    "name": "Quillon Orbital Works",
    "portal": "Engineering Portal",
    "badge": "QX-2 controlled: on-prem only",
    "about": "We build structural parts for small satellites: brackets, mounting plates, panel frames, standoffs and harness clips for our smallsat bus Petrel (programmes Petrel-1 and Petrel-2).",
    "programmes": [
      "Petrel-1",
      "Petrel-2"
    ],
    "teams": [
      {
        "name": "Structures",
        "blurb": "Primary structure and brackets."
      },
      {
        "name": "Avionics Integration",
        "blurb": "Plates, harness and clips."
      },
      {
        "name": "Quality",
        "blurb": "Runs the Gauge checking station."
      }
    ]
  },
  "tools": {
    "keel": {
      "name": "Keel",
      "version": "2.1.0",
      "manual": "../manual.md",
      "blurb": "Our private part-description tool. A short Python recipe compiles to exactly one solid; the Gauge station checks it.",
      "status": "live"
    },
    "kf": [
      {
        "code": "KF-M2",
        "hole": "2.4",
        "counterbore": "4.4 x 2.0",
        "countersink": "4.3"
      },
      {
        "code": "KF-M3",
        "hole": "3.4",
        "counterbore": "6.5 x 3.0",
        "countersink": "6.3"
      },
      {
        "code": "KF-M4",
        "hole": "4.5",
        "counterbore": "8.0 x 4.0",
        "countersink": "8.4"
      },
      {
        "code": "KF-M5",
        "hole": "5.5",
        "counterbore": "10.0 x 5.0",
        "countersink": "10.4"
      },
      {
        "code": "KF-M6",
        "hole": "6.6",
        "counterbore": "11.0 x 6.0",
        "countersink": "12.4"
      }
    ],
    "rules": [
      "Units are millimetres; datum is the lower-left-bottom corner (FRM requests use the frame centre).",
      "Holes use KF codes, never raw diameters.",
      "Standards depend on material: AL6061 wall 2.5 / fillet 1.0, TI6AL4V 3.0 / 1.5, SS316 2.0 / 0.5.",
      "FLIGHT parts: auto standard fillet; every base hole -CB or -CS."
    ],
    "materials": [
      {
        "code": "AL6061",
        "name": "aluminium",
        "wall": "2.5",
        "fillet": "1.0",
        "min_wall": "1.5"
      },
      {
        "code": "TI6AL4V",
        "name": "titanium",
        "wall": "3.0",
        "fillet": "1.5",
        "min_wall": "2.0"
      },
      {
        "code": "SS316",
        "name": "stainless",
        "wall": "2.0",
        "fillet": "0.5",
        "min_wall": "1.2"
      }
    ],
    "classes": [
      {
        "cls": "GSE",
        "blurb": "Ground support equipment (default). No extra rules."
      },
      {
        "cls": "FLIGHT",
        "blurb": "Flies on the satellite. finish() applies the material's standard fillet automatically; every base hole must be -CB or -CS."
      }
    ],
    "mounts": [
      {
        "name": "PETREL-MOUNT-A",
        "fastener": "KF-M4",
        "holes": "(0,0), (40,0), (0,30), (40,30)",
        "origin": "south-west hole"
      },
      {
        "name": "PETREL-MOUNT-B",
        "fastener": "KF-M5",
        "holes": "(0,0), (60,0), (0,40), (60,40)",
        "origin": "south-west hole"
      },
      {
        "name": "STAR-TRACKER-3",
        "fastener": "KF-M3",
        "holes": "3 holes on a dia-30 circle at 90, 210, 330 deg",
        "origin": "circle centre"
      },
      {
        "name": "HARNESS-P2",
        "fastener": "KF-M2",
        "holes": "(0,0), (15,0)",
        "origin": "west hole"
      }
    ],
    "gauge": {
      "name": "Gauge",
      "blurb": "The automatic checking station: bounding box, volume, area, centre of mass and overlap mismatch within 0.01%.",
      "status": "live"
    },
    "assistant": {
      "name": "Forge assistant",
      "blurb": "On-prem AI design assistant. Runs on one in-house GPU.",
      "status": "not trained yet"
    }
  },
  "parts": [
    {
      "id": "BRK-0101",
      "title": "Petrel-2 L-bracket, north wall",
      "file": "brk_0101.py",
      "svg": "parts/brk_0101.svg",
      "code": "\"\"\"BRK-0101 L-bracket. Run with the project venv from company/ (or repo root).\"\"\"\nimport sys\nimport os\n\nsys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n\nimport keel\n\np = keel.part(\"BRK-0101\", material=\"AL6061\")\np.stock(60, 40, 4)\np.wall(\"north\", 25)\np.hole(\"KF-M4\", at=(6, 6))\np.pattern(2, 2, 48, 28)\np.fillet()\nsolid = p.finish()\n",
      "size": "60 x 40 x 29 mm",
      "volume": "13092.1 mm^3",
      "request": "Base plate 60 x 40 x 4 with a standard north wall 25 high, four KF-M4 clearance holes 6 mm in from each corner of the base, standard fillet on the vertical edges.",
      "status": "Gauge PASS (sample data)"
    },
    {
      "id": "PLT-0230",
      "title": "Avionics mounting plate, KF-M3 grid",
      "file": "plt_0230.py",
      "svg": "parts/plt_0230.svg",
      "code": "\"\"\"PLT-0230 mounting plate with a KF-M3 hole pattern.\"\"\"\nimport sys\nimport os\n\nsys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n\nimport keel\n\np = keel.part(\"PLT-0230\", material=\"AL6061\")\np.stock(80, 60, 3)\np.hole(\"KF-M3\", at=(10, 10))\np.pattern(4, 3, 20, 20)\np.fillet()\nsolid = p.finish()\n",
      "size": "80 x 60 x 3 mm",
      "volume": "14070.6 mm^3",
      "request": "Plate 80 x 60 x 3 with a 4 x 3 grid of KF-M3 holes starting at (10, 10), 20 mm pitch both ways, standard fillet.",
      "status": "Gauge PASS (sample data)"
    },
    {
      "id": "STD-0044",
      "title": "Harness standoff with centre boss",
      "file": "std_0044.py",
      "svg": "parts/std_0044.svg",
      "code": "\"\"\"STD-0044 standoff with a central boss.\"\"\"\nimport sys\nimport os\n\nsys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n\nimport keel\n\np = keel.part(\"STD-0044\", material=\"AL6061\")\np.stock(30, 30, 4)\np.boss(at=(15, 15), dia=12, h=10)\np.hole(\"KF-M4\", at=(15, 15))\np.hole(\"KF-M3\", at=(5, 5))\np.pattern(2, 2, 20, 20)\nsolid = p.finish()\n",
      "size": "30 x 30 x 14 mm",
      "volume": "4363.05 mm^3",
      "request": "30 x 30 x 4 foot with a dia-12 boss 10 high in the centre, KF-M4 through the middle of the boss, four KF-M3 corner holes at 5 mm insets.",
      "status": "Gauge PASS (sample data)"
    },
    {
      "id": "FRM-0310",
      "title": "Panel frame with centre pocket",
      "file": "frm_0310.py",
      "svg": "parts/frm_0310.svg",
      "code": "\"\"\"FRM-0310 panel frame with a central pocket and side walls.\"\"\"\nimport sys\nimport os\n\nsys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n\nimport keel\n\np = keel.part(\"FRM-0310\", material=\"AL6061\")\np.stock(100, 80, 6)\np.pocket(at=(10, 10), L=80, W=60, depth=4)\np.wall(\"north\", 12)\np.wall(\"south\", 12)\np.hole(\"KF-M5\", at=(5, 5))\np.pattern(2, 2, 90, 70)\nsolid = p.finish()\n",
      "size": "100 x 80 x 18 mm",
      "volume": "34229.8 mm^3",
      "request": "Frame blank 100 x 80 x 6, pocket 80 x 60 x 4 deep starting at (10, 10), north and south walls 12 high, four KF-M5 corner holes 5 mm in from the corners.",
      "status": "Gauge PASS (sample data)"
    },
    {
      "id": "CLP-0012",
      "title": "Harness clip with cable slot",
      "file": "clp_0012.py",
      "svg": "parts/clp_0012.svg",
      "code": "\"\"\"CLP-0012 harness clip with a through slot.\"\"\"\nimport sys\nimport os\n\nsys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n\nimport keel\n\np = keel.part(\"CLP-0012\", material=\"AL6061\")\np.stock(50, 30, 4)\np.slot(at=(10, 15), to=(40, 15), width=5)\np.wall(\"west\", 10)\np.hole(\"KF-M3\", at=(45, 8))\np.pattern(1, 2, 0, 14)\nsolid = p.finish()\n",
      "size": "50 x 30 x 14 mm",
      "volume": "5977.37 mm^3",
      "request": "Clip 50 x 30 x 4 with a 5 mm wide through slot down the middle from x = 10 to x = 40, west wall 10 high, two KF-M3 holes near the east edge.",
      "status": "AI draft (sample data)"
    },
    {
      "id": "BRK-0155",
      "title": "Corner bracket, two walls",
      "file": "brk_0155.py",
      "svg": "parts/brk_0155.svg",
      "code": "\"\"\"BRK-0155 corner bracket with two walls.\"\"\"\nimport sys\nimport os\n\nsys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n\nimport keel\n\np = keel.part(\"BRK-0155\", material=\"AL6061\")\np.stock(50, 50, 5)\np.wall(\"north\", 20)\np.wall(\"east\", 20)\np.hole(\"KF-M5\", at=(8, 8))\np.pattern(2, 1, 34, 0)\np.fillet()\nsolid = p.finish()\n",
      "size": "50 x 50 x 25 mm",
      "volume": "17133.1 mm^3",
      "request": "Corner bracket 50 x 50 x 5 with north and east walls 20 high, two KF-M5 base holes along the south edge, standard fillet.",
      "status": "Gauge PASS (sample data)"
    },
    {
      "id": "PLT-0277",
      "title": "Cover plate, counterbored",
      "file": "plt_0277.py",
      "svg": "parts/plt_0277.svg",
      "code": "\"\"\"PLT-0277 cover plate with counterbored holes and a shallow pocket.\"\"\"\nimport sys\nimport os\n\nsys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n\nimport keel\n\np = keel.part(\"PLT-0277\", material=\"AL6061\")\np.stock(70, 50, 4)\np.hole(\"KF-M4-CB\", at=(8, 8))\np.pattern(2, 2, 54, 34)\np.pocket(at=(20, 15), L=30, W=20, depth=2)\np.fillet()\nsolid = p.finish()\n",
      "size": "70 x 50 x 4 mm",
      "volume": "11992.3 mm^3",
      "request": "Cover 70 x 50 x 4 with four counterbored KF-M4-CB holes 8 mm in from the corners and a shallow 30 x 20 x 2 pocket in the middle, standard fillet.",
      "status": "open (sample data)"
    },
    {
      "id": "FRM-0320",
      "title": "Rail frame with long slot",
      "file": "frm_0320.py",
      "svg": "parts/frm_0320.svg",
      "code": "\"\"\"FRM-0320 rail frame with a central slot and end walls.\"\"\"\nimport sys\nimport os\n\nsys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n\nimport keel\n\np = keel.part(\"FRM-0320\", material=\"AL6061\")\np.stock(120, 40, 5)\np.slot(at=(15, 20), to=(105, 20), width=6)\np.wall(\"east\", 15)\np.wall(\"west\", 15)\np.hole(\"KF-M4\", at=(6, 6))\np.pattern(2, 2, 108, 28)\nsolid = p.finish()\n",
      "size": "120 x 40 x 20 mm",
      "volume": "23801.9 mm^3",
      "request": "Rail 120 x 40 x 5 with a 6 mm wide through slot from (15, 20) to (105, 20), east and west end walls 15 high, four KF-M4 corner holes 6 mm in from the corners.",
      "status": "Gauge PASS (sample data)"
    },
    {
      "id": "BRK-0142",
      "title": "Flight titanium bracket, wall hole",
      "file": "brk_0142.py",
      "svg": "parts/brk_0142.svg",
      "code": "\"\"\"BRK-0142 flight bracket in titanium with a wall hole. Run with the project venv from company/ (or repo root).\"\"\"\nimport sys\nimport os\n\nsys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n\nimport keel\n\np = keel.part(\"BRK-0142\", material=\"TI6AL4V\", cls=\"FLIGHT\")\np.stock(60, 40, 4)\np.wall(\"north\", 25)\np.hole(\"KF-M4-CB\", at=(6, 6))\np.pattern(2, 2, 48, 28)\np.wall_hole(\"north\", \"KF-M3\", at=(30, 12))\nsolid = p.finish()\n",
      "size": "60 x 40 x 29 mm",
      "volume": "13260.8 mm^3",
      "request": "Flight bracket in titanium (TI6AL4V), base 60 x 40 x 4, standard north wall 25 high, four counterbored KF-M4-CB holes 6 mm in from the base corners, one KF-M3 wall hole in the north wall at u = 30, z = 12 above the stock top. Auto standard fillet.",
      "status": "Gauge PASS (sample data)"
    },
    {
      "id": "FRM-1031",
      "title": "Frame dimensioned from the centre, mirrored",
      "file": "frm_1031.py",
      "svg": "parts/frm_1031.svg",
      "code": "\"\"\"FRM-1031 frame dimensioned from the centre, west pair mirrored. Run with the project venv from company/ (or repo root).\"\"\"\nimport sys\nimport os\n\nsys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n\nimport keel\n\n# Request gives holes at (+-45, +-35) from the frame centre; Keel uses the\n# corner datum, so x = 100/2 + xr, y = 80/2 + yr. West pair mirrored about x = 50.\np = keel.part(\"FRM-1031\", material=\"AL6061\")\np.stock(100, 80, 6)\np.wall(\"north\", 12)\np.wall(\"south\", 12)\np.hole(\"KF-M5\", at=(5, 5))\np.hole(\"KF-M5\", at=(5, 75))\np.mirror(\"ew\")\np.pocket(at=(10, 10), L=80, W=60, depth=4)\nsolid = p.finish()\n",
      "size": "100 x 80 x 18 mm",
      "volume": "34229.8 mm^3",
      "request": "Frame blank 100 x 80 x 6, pocket 80 x 60 x 4 deep from (10, 10), north and south walls 12 high, four KF-M5 holes at (+-45, +-35) from the frame centre: convert with x = 50 + xr, y = 40 + yr, west pair mirrored about x = 50.",
      "status": "Gauge PASS (sample data)"
    },
    {
      "id": "PLT-1042",
      "title": "Plate with countersunk PETREL-MOUNT-A",
      "file": "plt_1042.py",
      "svg": "parts/plt_1042.svg",
      "code": "\"\"\"PLT-1042 plate with a countersunk PETREL-MOUNT-A. Run with the project venv from company/ (or repo root).\"\"\"\nimport sys\nimport os\n\nsys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n\nimport keel\n\np = keel.part(\"PLT-1042\", material=\"AL6061\")\np.stock(80, 60, 4)\np.mount(\"PETREL-MOUNT-A\", origin=(10, 10), finish=\"CS\")\np.fillet()\nsolid = p.finish()\n",
      "size": "80 x 60 x 4 mm",
      "volume": "18803.5 mm^3",
      "request": "Plate 80 x 60 x 4 with a countersunk PETREL-MOUNT-A (KF-M4, origin at (10, 10), finish CS), standard fillet on the vertical edges.",
      "status": "AI draft (sample data)"
    },
    {
      "id": "STD-1063",
      "title": "Stainless tracker plate, STAR-TRACKER-3",
      "file": "std_1063.py",
      "svg": "parts/std_1063.svg",
      "code": "\"\"\"STD-1063 stainless tracker plate with STAR-TRACKER-3. Run with the project venv from company/ (or repo root).\"\"\"\nimport sys\nimport os\n\nsys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n\nimport keel\n\np = keel.part(\"STD-1063\", material=\"SS316\")\np.stock(60, 60, 5)\np.mount(\"STAR-TRACKER-3\", origin=(30, 30))\np.fillet()\nsolid = p.finish()\n",
      "size": "60 x 60 x 5 mm",
      "volume": "17862.7 mm^3",
      "request": "Stainless (SS316) tracker plate 60 x 60 x 5 with a STAR-TRACKER-3 mount (KF-M3) centred at (30, 30), standard fillet.",
      "status": "open (sample data)"
    }
  ],
  "requests": [
    {
      "id": "BRK-0101",
      "title": "Petrel-2 L-bracket, north wall",
      "request": "Base plate 60 x 40 x 4 with a standard north wall 25 high, four KF-M4 clearance holes 6 mm in from each corner of the base, standard fillet on the vertical edges.",
      "status": "Gauge PASS (sample data)"
    },
    {
      "id": "PLT-0230",
      "title": "Avionics mounting plate, KF-M3 grid",
      "request": "Plate 80 x 60 x 3 with a 4 x 3 grid of KF-M3 holes starting at (10, 10), 20 mm pitch both ways, standard fillet.",
      "status": "Gauge PASS (sample data)"
    },
    {
      "id": "STD-0044",
      "title": "Harness standoff with centre boss",
      "request": "30 x 30 x 4 foot with a dia-12 boss 10 high in the centre, KF-M4 through the middle of the boss, four KF-M3 corner holes at 5 mm insets.",
      "status": "Gauge PASS (sample data)"
    },
    {
      "id": "FRM-0310",
      "title": "Panel frame with centre pocket",
      "request": "Frame blank 100 x 80 x 6, pocket 80 x 60 x 4 deep starting at (10, 10), north and south walls 12 high, four KF-M5 corner holes 5 mm in from the corners.",
      "status": "Gauge PASS (sample data)"
    },
    {
      "id": "CLP-0012",
      "title": "Harness clip with cable slot",
      "request": "Clip 50 x 30 x 4 with a 5 mm wide through slot down the middle from x = 10 to x = 40, west wall 10 high, two KF-M3 holes near the east edge.",
      "status": "AI draft (sample data)"
    },
    {
      "id": "BRK-0155",
      "title": "Corner bracket, two walls",
      "request": "Corner bracket 50 x 50 x 5 with north and east walls 20 high, two KF-M5 base holes along the south edge, standard fillet.",
      "status": "Gauge PASS (sample data)"
    },
    {
      "id": "PLT-0277",
      "title": "Cover plate, counterbored",
      "request": "Cover 70 x 50 x 4 with four counterbored KF-M4-CB holes 8 mm in from the corners and a shallow 30 x 20 x 2 pocket in the middle, standard fillet.",
      "status": "open (sample data)"
    },
    {
      "id": "FRM-0320",
      "title": "Rail frame with long slot",
      "request": "Rail 120 x 40 x 5 with a 6 mm wide through slot from (15, 20) to (105, 20), east and west end walls 15 high, four KF-M4 corner holes 6 mm in from the corners.",
      "status": "Gauge PASS (sample data)"
    },
    {
      "id": "BRK-0142",
      "title": "Flight titanium bracket, wall hole",
      "request": "Flight bracket in titanium (TI6AL4V), base 60 x 40 x 4, standard north wall 25 high, four counterbored KF-M4-CB holes 6 mm in from the base corners, one KF-M3 wall hole in the north wall at u = 30, z = 12 above the stock top. Auto standard fillet.",
      "status": "Gauge PASS (sample data)"
    },
    {
      "id": "FRM-1031",
      "title": "Frame dimensioned from the centre, mirrored",
      "request": "Frame blank 100 x 80 x 6, pocket 80 x 60 x 4 deep from (10, 10), north and south walls 12 high, four KF-M5 holes at (+-45, +-35) from the frame centre: convert with x = 50 + xr, y = 40 + yr, west pair mirrored about x = 50.",
      "status": "Gauge PASS (sample data)"
    },
    {
      "id": "PLT-1042",
      "title": "Plate with countersunk PETREL-MOUNT-A",
      "request": "Plate 80 x 60 x 4 with a countersunk PETREL-MOUNT-A (KF-M4, origin at (10, 10), finish CS), standard fillet on the vertical edges.",
      "status": "AI draft (sample data)"
    },
    {
      "id": "STD-1063",
      "title": "Stainless tracker plate, STAR-TRACKER-3",
      "request": "Stainless (SS316) tracker plate 60 x 60 x 5 with a STAR-TRACKER-3 mount (KF-M3) centred at (30, 30), standard fillet.",
      "status": "open (sample data)"
    }
  ],
  "assistant_panel": {
    "runs_on": "1 in-house GPU, on-prem (designs never leave the building)",
    "scoreboard_models": [
      "Glimmer + manual",
      "Forge-trained Glimmer",
      "teacher Spark Open"
    ],
    "scoreboard": null,
    "training": {
      "status": "not started",
      "cost": "not measured yet"
    }
  }
};
