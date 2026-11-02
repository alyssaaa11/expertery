"""No-reference self-check for a visitor's job (verifier S1).

A visitor's job has no reference part, so the page verdict is conservative:
PASS only when the part built with exactly 1 solid AND the job states an
overall size (parsed ONLY by the patterns below) matching the measured
bounding-box extents within 0.5% per axis. BUILT when it built with 1 solid
but no overall size could be parsed ("size not checked"). CHECK FAILED
otherwise. When unsure, return BUILT, never PASS.

Overall size is parsed ONLY from these explicit patterns (axis order is not
guaranteed, so sorted extents are compared to sorted stated numbers):

1. OVERALL:  "overall size|dimensions A x B x C mm"
2. BOXNOUN:  "A x B x C mm box|plate|block"
3. BASE_WALL: "base A x B x C mm" plus "wall ... N mm tall" elsewhere in the
   job; the wall sits on the base, so the stated size is A x B x (C + N).
   ("adding height only when the job says so": without the wall phrase a
   bare "base ..." is NOT an overall size.)

"x" stands for any of: x X * xU+00D7 or the word "by"; numbers may be
decimal; matching is case-insensitive.
"""

import re

TOL = 0.005  # 0.5% per axis

_NUM = r"(\d+(?:\.\d+)?)"
_SEP = "(?:\u00d7|x|X|\\*|by)"  # \u00d7 is the multiplication sign
_TRIPLE = _NUM + r"\s*" + _SEP + r"\s*" + _NUM + r"\s*" + _SEP + r"\s*" + _NUM

PATTERNS = (
    ("OVERALL",
     re.compile(r"overall\s+(?:size|dimensions?)\s*(?:is|:)?\s*"
                + _TRIPLE + r"\s*mm\b", re.IGNORECASE)),
    ("BOXNOUN",
     re.compile(_TRIPLE + r"\s*mm\s*(?:box|plate|block)\b",
                re.IGNORECASE)),
    ("BASE",
     re.compile(r"base\s+" + _TRIPLE + r"\s*mm\b", re.IGNORECASE)),
)
WALL_TALL_RE = re.compile(r"wall[^.\n]{0,80}?" + _NUM + r"\s*mm\s*tall\b",
                           re.IGNORECASE)


def pattern_names():
    """Names of the documented overall-size patterns."""
    return [name for name, _ in PATTERNS] + ["BASE_WALL"]


def parse_overall_size(job_text):
    """(pattern_name, (a, b, c)) or (None, None) when nothing parsed.

    BASE_WALL only matches when the job ALSO states the wall height; a
    bare "base ..." yields (None, None).
    """
    text = job_text or ""
    for name, rx in PATTERNS:
        m = rx.search(text)
        if not m:
            continue
        if name == "BASE":
            w = WALL_TALL_RE.search(text)
            if not w:
                continue  # a bare base is not an overall size
            try:
                dims = (float(m.group(1)), float(m.group(2)),
                        float(m.group(3)) + float(w.group(1)))
            except (TypeError, ValueError):
                continue
            return "BASE_WALL", dims
        try:
            dims = (float(m.group(1)), float(m.group(2)),
                    float(m.group(3)))
        except (TypeError, ValueError):
            continue
        return name, dims
    return None, None


def measure_extents(measurements):
    """[x, y, z] extents from a box or recorded measurement dict, or None."""
    if not isinstance(measurements, dict):
        return None
    for key in ("bbox_mm", "extents_mm"):
        vals = measurements.get(key)
        if isinstance(vals, (list, tuple)) and len(vals) == 3:
            try:
                return [float(v) for v in vals]
            except (TypeError, ValueError):
                return None
    bbox = measurements.get("bbox")
    if isinstance(bbox, (list, tuple)) and len(bbox) == 6:
        try:
            lo = [float(bbox[0]), float(bbox[1]), float(bbox[2])]
            hi = [float(bbox[3]), float(bbox[4]), float(bbox[5])]
        except (TypeError, ValueError):
            return None
        return [hi[i] - lo[i] for i in range(3)]
    return None


def _fmt(dims):
    return " \u00d7 ".join(
        ("%g" % v) for v in dims) + " mm"


def self_check(job_text, measurements):
    """(verdict, reasons). Verdict is PASS, BUILT or CHECK FAILED."""
    if not isinstance(measurements, dict) or not measurements:
        return "CHECK FAILED", ["the part did not build"]
    try:
        solids = measurements.get("solids")
        n_solids = None if solids is None else int(solids)
    except (TypeError, ValueError):
        n_solids = None
    if n_solids is None:
        return "CHECK FAILED", ["could not count the solids"]
    if n_solids != 1:
        return ("CHECK FAILED",
                ["built %d solids, expected 1" % (n_solids,)])
    extents = measure_extents(measurements)
    if extents is None:
        return "CHECK FAILED", ["no size measurements"]
    _name, stated = parse_overall_size(job_text)
    if stated is None:
        return "BUILT", ["size not checked: no overall size stated"]
    lo = sorted(extents)
    hi = sorted(stated)
    for m, s in zip(lo, hi):
        if s == 0:
            ok = (m == 0)
        else:
            ok = abs(m - s) <= TOL * abs(s) + 1e-9  # float hygiene
        if not ok:
            return ("CHECK FAILED",
                    ["overall size %s does not match measured %s"
                     % (_fmt(hi), _fmt(lo))])
    return ("PASS",
            ["built", "1 solid",
             "%s matches your numbers" % (_fmt(hi),)])
