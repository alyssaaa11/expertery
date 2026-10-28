"""Build dashboard data for file:// viewing.

Reads the company files, rebuilds every example part, writes:
  company/dashboard/data.js    (window.QOW_DATA = {...}, loaded via <script>)
  company/dashboard/parts/*.svg (isometric SVG previews via keel.render)

No network, no server: index.html loads data.js with a <script> tag because
Chrome blocks fetch() of local files.

The Forge assistant scoreboard reads company/assistant_results.json only if it
exists; until the held-out exam exists there is no such file, so the
scoreboard is "not measured yet" (never invented numbers).
"""

import importlib.util
import json
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COMPANY = os.path.dirname(HERE)
sys.path.insert(0, COMPANY)

import keel  # noqa: E402

_CHECKS = os.path.join(COMPANY, "..", "experiments", "first-test", "checks.py")
_spec = importlib.util.spec_from_file_location("qow_checks", os.path.abspath(_CHECKS))
checks = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(checks)

EXAMPLES = os.path.join(COMPANY, "examples")
PARTS_DIR = os.path.join(HERE, "parts")
RESULTS_FILE = os.path.join(COMPANY, "assistant_results.json")


def svg_name(part_file):
    return os.path.join(PARTS_DIR, os.path.splitext(part_file)[0] + ".svg")


def main():
    os.makedirs(PARTS_DIR, exist_ok=True)
    with open(os.path.join(EXAMPLES, "requests.json")) as f:
        requests = json.load(f)

    parts = []
    for req in requests:
        path = os.path.join(EXAMPLES, req["part"])
        with open(path) as f:
            code = f.read()
        ns = runpy.run_path(path)
        p_solid = ns["solid"]
        m = checks.measure(p_solid)
        # Rebuild a part object for render: re-execute and keep the part via a hook.
        # Example files only expose `solid`, so render through a fresh Workplane export.
        import cadquery as cq

        cq.exporters.export(
            cq.Workplane(obj=p_solid),
            svg_name(req["part"]),
            opt={
                "projectionDir": (-1.0, -1.0, 1.0),
                "showHidden": False,
                "strokeColor": (27, 58, 95),
                "hiddenColor": (160, 175, 195),
                "showAxes": False,
            },
        )
        bb = m["bbox"]
        parts.append(
            {
                "id": req["id"],
                "title": req["title"],
                "file": req["part"],
                "svg": "parts/" + os.path.splitext(req["part"])[0] + ".svg",
                "code": code,
                "size": f"{bb[3] - bb[0]:g} x {bb[4] - bb[1]:g} x {bb[5] - bb[2]:g} mm",
                "volume": f"{m['volume']:g} mm^3",
                "request": req["request"],
                "status": req["status"],
            }
        )

    kf = [
        {"code": code, "hole": str(d[0]), "counterbore": f"{d[1][0]} x {d[1][1]}"}
        for code, d in keel.KF.items()
    ]

    scoreboard = None
    training = {"status": "not started", "cost": "not measured yet"}
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE) as f:
            doc = json.load(f)
        scoreboard = doc.get("scoreboard")
        training = doc.get("training", training)

    data = {
        "banner": "Fictional company, made for the Forge demo",
        "company": {
            "name": "Quillon Orbital Works",
            "portal": "Engineering Portal",
            "badge": "QX-2 controlled: on-prem only",
            "about": (
                "We build structural parts for small satellites: brackets, mounting "
                "plates, panel frames, standoffs and harness clips for our "
                "smallsat bus Petrel (programmes Petrel-1 and Petrel-2)."
            ),
            "programmes": ["Petrel-1", "Petrel-2"],
            "teams": [
                {"name": "Structures", "blurb": "Primary structure and brackets."},
                {"name": "Avionics Integration", "blurb": "Plates, harness and clips."},
                {"name": "Quality", "blurb": "Runs the Gauge checking station."},
            ],
        },
        "tools": {
            "keel": {
                "name": "Keel",
                "version": keel.__version__,
                "manual": "../manual.md",
                "blurb": (
                    "Our private part-description tool. A short Python recipe "
                    "compiles to exactly one solid; the Gauge station checks it."
                ),
                "status": "live",
            },
            "kf": kf,
            "rules": [
                "Units are millimetres; datum is the lower-left-bottom corner.",
                "Holes use KF codes, never raw diameters.",
                "Standard wall 2.5 mm; standard fillet 1.0 mm.",
            ],
            "gauge": {
                "name": "Gauge",
                "blurb": (
                    "The automatic checking station: bounding box, volume, area, "
                    "centre of mass and overlap mismatch within 0.2%."
                ),
                "status": "live",
            },
            "assistant": {
                "name": "Forge assistant",
                "blurb": "On-prem AI design assistant. Runs on one in-house GPU.",
                "status": "not trained yet",
            },
        },
        "parts": parts,
        "requests": [
            {"id": r["id"], "title": r["title"], "request": r["request"], "status": r["status"]}
            for r in requests
        ],
        "assistant_panel": {
            "runs_on": "1 in-house GPU, on-prem (designs never leave the building)",
            "scoreboard_models": ["Glimmer + manual", "Forge-trained Glimmer", "teacher Spark Open"],
            "scoreboard": scoreboard,
            "training": training,
        },
    }

    with open(os.path.join(HERE, "data.js"), "w") as f:
        f.write("window.QOW_DATA = ")
        json.dump(data, f, indent=2)
        f.write(";\n")
    print(f"wrote data.js ({len(parts)} parts) and {len(parts)} SVGs")


if __name__ == "__main__":
    main()
