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
      "version": "1.0.0",
      "manual": "../manual.md",
      "blurb": "Our private part-description tool. A short Python recipe compiles to exactly one solid; the Gauge station checks it.",
      "status": "live"
    },
    "kf": [
      {
        "code": "KF-M2",
        "hole": "2.4",
        "counterbore": "4.4 x 2.0"
      },
      {
        "code": "KF-M3",
        "hole": "3.4",
        "counterbore": "6.5 x 3.0"
      },
      {
        "code": "KF-M4",
        "hole": "4.5",
        "counterbore": "8.0 x 4.0"
      },
      {
        "code": "KF-M5",
        "hole": "5.5",
        "counterbore": "10.0 x 5.0"
      },
      {
        "code": "KF-M6",
        "hole": "6.6",
        "counterbore": "11.0 x 6.0"
      }
    ],
    "rules": [
      "Units are millimetres; datum is the lower-left-bottom corner.",
      "Holes use KF codes, never raw diameters.",
      "Standard wall 2.5 mm; standard fillet 1.0 mm."
    ],
    "gauge": {
      "name": "Gauge",
      "blurb": "The automatic checking station: bounding box, volume, area, centre of mass and overlap mismatch within 0.2%.",
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
      "status": "Gauge PASS"
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
      "status": "Gauge PASS"
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
      "status": "Gauge PASS"
    },
    {
      "id": "FRM-0310",
      "title": "Panel frame with centre pocket",
      "file": "frm_0310.py",
      "svg": "parts/frm_0310.svg",
      "code": "\"\"\"FRM-0310 panel frame with a central pocket and side walls.\"\"\"\nimport sys\nimport os\n\nsys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n\nimport keel\n\np = keel.part(\"FRM-0310\", material=\"AL6061\")\np.stock(100, 80, 6)\np.pocket(at=(10, 10), L=80, W=60, depth=4)\np.wall(\"north\", 12)\np.wall(\"south\", 12)\np.hole(\"KF-M5\", at=(5, 5))\np.pattern(2, 2, 90, 70)\nsolid = p.finish()\n",
      "size": "100 x 80 x 18 mm",
      "volume": "34228.3 mm^3",
      "request": "Frame blank 100 x 80 x 6, pocket 80 x 60 x 4 deep starting at (10, 10), north and south walls 12 high, four KF-M5 corner holes 5 mm in from the corners.",
      "status": "Gauge PASS"
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
      "status": "AI draft"
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
      "status": "Gauge PASS"
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
      "status": "open"
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
      "status": "Gauge PASS"
    }
  ],
  "requests": [
    {
      "id": "BRK-0101",
      "title": "Petrel-2 L-bracket, north wall",
      "request": "Base plate 60 x 40 x 4 with a standard north wall 25 high, four KF-M4 clearance holes 6 mm in from each corner of the base, standard fillet on the vertical edges.",
      "status": "Gauge PASS"
    },
    {
      "id": "PLT-0230",
      "title": "Avionics mounting plate, KF-M3 grid",
      "request": "Plate 80 x 60 x 3 with a 4 x 3 grid of KF-M3 holes starting at (10, 10), 20 mm pitch both ways, standard fillet.",
      "status": "Gauge PASS"
    },
    {
      "id": "STD-0044",
      "title": "Harness standoff with centre boss",
      "request": "30 x 30 x 4 foot with a dia-12 boss 10 high in the centre, KF-M4 through the middle of the boss, four KF-M3 corner holes at 5 mm insets.",
      "status": "Gauge PASS"
    },
    {
      "id": "FRM-0310",
      "title": "Panel frame with centre pocket",
      "request": "Frame blank 100 x 80 x 6, pocket 80 x 60 x 4 deep starting at (10, 10), north and south walls 12 high, four KF-M5 corner holes 5 mm in from the corners.",
      "status": "Gauge PASS"
    },
    {
      "id": "CLP-0012",
      "title": "Harness clip with cable slot",
      "request": "Clip 50 x 30 x 4 with a 5 mm wide through slot down the middle from x = 10 to x = 40, west wall 10 high, two KF-M3 holes near the east edge.",
      "status": "AI draft"
    },
    {
      "id": "BRK-0155",
      "title": "Corner bracket, two walls",
      "request": "Corner bracket 50 x 50 x 5 with north and east walls 20 high, two KF-M5 base holes along the south edge, standard fillet.",
      "status": "Gauge PASS"
    },
    {
      "id": "PLT-0277",
      "title": "Cover plate, counterbored",
      "request": "Cover 70 x 50 x 4 with four counterbored KF-M4-CB holes 8 mm in from the corners and a shallow 30 x 20 x 2 pocket in the middle, standard fillet.",
      "status": "open"
    },
    {
      "id": "FRM-0320",
      "title": "Rail frame with long slot",
      "request": "Rail 120 x 40 x 5 with a 6 mm wide through slot from (15, 20) to (105, 20), east and west end walls 15 high, four KF-M4 corner holes 6 mm in from the corners.",
      "status": "Gauge PASS"
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
