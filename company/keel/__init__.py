"""Keel: Quillon Orbital Works' private part-description tool (v2.0.0).

Units are millimetres. Datum = the part's lower-left-bottom corner (0, 0, 0).
+X = east, +Y = north, +Z = up. Nothing is centred unless the call says so.
"""

import math

import cadquery as cq

__version__ = "2.0.0"

# Company material standards: material -> (standard wall, standard fillet, minimum wall).
MATERIALS = {
    "AL6061": (2.5, 1.0, 1.5),
    "TI6AL4V": (3.0, 1.5, 2.0),
    "SS316": (2.0, 0.5, 1.2),
}

STANDARD_WALL = 2.5    # AL6061 standard (kept for compatibility; per-part value may differ)
STANDARD_FILLET = 1.0  # AL6061 standard (kept for compatibility; per-part value may differ)

# Company fastener table KF: code -> (clearance dia, (counterbore dia, depth)).
# "-CB" suffix = counterbored from the local top face (see _local_top).
# "-CS" suffix = 90-degree countersink from the local top face (v2).
KF = {
    "KF-M2": (2.4, (4.4, 2.0)),
    "KF-M3": (3.4, (6.5, 3.0)),
    "KF-M4": (4.5, (8.0, 4.0)),
    "KF-M5": (5.5, (10.0, 5.0)),
    "KF-M6": (6.6, (11.0, 6.0)),
}

# Countersink diameter at the local top face, per base code (v2).
KF_CS = {
    "KF-M2": 4.3,
    "KF-M3": 6.3,
    "KF-M4": 8.4,
    "KF-M5": 10.4,
    "KF-M6": 12.4,
}

# Company standard mounts (v2): name -> (base fastener code, offsets from origin).
_MOUNT_RECT = {
    "PETREL-MOUNT-A": ("KF-M4", [(0, 0), (40, 0), (0, 30), (40, 30)]),
    "PETREL-MOUNT-B": ("KF-M5", [(0, 0), (60, 0), (0, 40), (60, 40)]),
    "HARNESS-P2": ("KF-M2", [(0, 0), (15, 0)]),
}
_MOUNT_NAMES = ("PETREL-MOUNT-A", "PETREL-MOUNT-B", "STAR-TRACKER-3", "HARNESS-P2")


def _star_tracker_offsets():
    """3 holes on a circle of diameter 30 about the origin, at 90/210/330 deg."""
    pts = []
    for deg in (90, 210, 330):
        a = math.radians(deg)
        pts.append((15 * math.cos(a), 15 * math.sin(a)))
    return pts


def _mount_holes(name, origin):
    """Expand a mount to [(base_code, (x, y)), ...] hole positions."""
    ox, oy = origin
    if name in _MOUNT_RECT:
        code, offs = _MOUNT_RECT[name]
        return [(code, (ox + dx, oy + dy)) for dx, dy in offs]
    if name == "STAR-TRACKER-3":
        return [("KF-M3", (ox + dx, oy + dy)) for dx, dy in _star_tracker_offsets()]
    raise KeelError(
        f"keel: unknown mount {name!r}; mounts are "
        "PETREL-MOUNT-A, PETREL-MOUNT-B, STAR-TRACKER-3, HARNESS-P2"
    )


def _split_code(code):
    """Split a hole code into (base, suffix) where suffix is '', '-CB' or '-CS'."""
    for suffix in ("-CB", "-CS"):
        if code.endswith(suffix):
            return code[: -len(suffix)], suffix
    return code, ""


_EDGES = ("north", "south", "east", "west")


class KeelError(Exception):
    """Company-style error raised for any misuse of Keel."""


def _positive(value, what):
    if not isinstance(value, (int, float)) or value <= 0:
        raise KeelError(f"{what} must be a positive number of millimetres, got {value!r}")
    return float(value)


def _fmt_xy(x, y):
    return f"({x:g}, {y:g})"


class part:  # noqa: N801 - company style uses lowercase, like the manual
    """A part under construction. End every program with ``solid = p.finish()``."""

    def __init__(self, number, material="AL6061", cls="GSE"):
        if material not in MATERIALS:
            raise KeelError(
                f"keel: unknown material {material!r}; materials are AL6061, TI6AL4V, SS316 "
                "(aluminium = AL6061, titanium = TI6AL4V, stainless = SS316)"
            )
        if cls not in ("GSE", "FLIGHT"):
            raise KeelError(
                f"keel: unknown part class {cls!r}; cls is 'GSE' or 'FLIGHT' "
                "('flight part' in a request means cls=\"FLIGHT\")"
            )
        self.number = number
        self.material = material
        self.cls = cls
        self._std_wall, self._std_fillet, self._min_wall = MATERIALS[material]
        self._stock = None
        self._ops = []          # recorded feature calls, in order
        self._fillet_r = None
        self._finished = False
        self._seed = None       # last recorded feature (for pattern)
        self._mirrored = False  # pattern() is forbidden after mirror()

    # -- builders ---------------------------------------------------------
    def _guard_open(self, call):
        if self._finished:
            raise KeelError(
                f"keel: {call} called after p.finish(); "
                f"part {self.number!r} is already finished"
            )

    def stock(self, L, W, T):
        """Base block x in [0,L], y in [0,W], z in [0,T]. Exactly one per part, first call."""
        self._guard_open("stock()")
        if self._stock is not None:
            raise KeelError(
                "keel: stock() called twice; a part has exactly one base block "
                f"(part {self.number!r} already has stock)"
            )
        if self._ops or self._fillet_r is not None:
            raise KeelError(
                "keel: stock() must be the first call on a part; "
                "a feature was already recorded before the base block"
            )
        L, W, T = _positive(L, "stock length"), _positive(W, "stock width"), _positive(T, "stock thickness")
        self._stock = (L, W, T)
        return self

    def _need_stock(self, call):
        if self._stock is None:
            raise KeelError(
                f"keel: {call} called before stock(); "
                "every part starts with p.stock(L, W, T)"
            )

    def _check_xy(self, x, y, call):
        L, W, _ = self._stock
        if not (0 <= x <= L and 0 <= y <= W):
            raise KeelError(
                f"keel: {call} at ({x}, {y}) lies outside the {L:g} x {W:g} stock footprint; "
                "datum is the lower-left-bottom corner (0, 0, 0)"
            )

    def _check_fastener(self, code):
        base, _suffix = _split_code(code)
        if base not in KF:
            raise KeelError(
                f"keel: unknown fastener code {code!r}; "
                "holes use company codes KF-M2, KF-M3, KF-M4, KF-M5, KF-M6 "
                "(add -CB for a counterbore or -CS for a countersink, e.g. KF-M4-CB)"
            )
        return base

    def _flight_hole_error(self, code, x, y):
        return KeelError(
            f"keel: flight parts need -CB or -CS fasteners ({code} at {_fmt_xy(x, y)}); "
            "every base hole on a FLIGHT part must be counterbored or countersunk"
        )

    def wall(self, edge, h, t=None):
        """Wall on the top face along a named edge, flush with it, full edge length."""
        self._guard_open("wall()")
        self._need_stock("wall()")
        if edge not in _EDGES:
            raise KeelError(
                f"keel: unknown edge {edge!r}; edges are named "
                "'north', 'south', 'east' or 'west'"
            )
        h = _positive(h, "wall height")
        t = self._std_wall if t is None else _positive(t, "wall thickness")
        L, W, _ = self._stock
        if t > min(L, W):
            raise KeelError(f"keel: wall thickness {t:g} does not fit the {L:g} x {W:g} stock")
        if t < self._min_wall:
            raise KeelError(
                f"keel: wall thickness {t:g} is thinner than the {self.material} "
                f"minimum wall {self._min_wall:g}; use {self._min_wall:g} or thicker"
            )
        op = ("wall", {"edge": edge, "h": h, "t": t})
        self._ops.append(op)
        self._seed = op
        return self

    def boss(self, at, dia, h):
        """Cylinder on the top face, centre at (x, y)."""
        self._guard_open("boss()")
        self._need_stock("boss()")
        (x, y) = at
        self._check_xy(x, y, "boss()")
        dia = _positive(dia, "boss diameter")
        h = _positive(h, "boss height")
        op = ("boss", {"at": (float(x), float(y)), "dia": dia, "h": h})
        self._ops.append(op)
        self._seed = op
        return self

    def hole(self, code, at):
        """Through hole (all the way down) using table KF; '-CB'/'-CS' from the local top."""
        self._guard_open("hole()")
        self._need_stock("hole()")
        self._check_fastener(code)
        _base, suffix = _split_code(code)
        (x, y) = at
        self._check_xy(x, y, f"hole({code})")
        if self.cls == "FLIGHT" and suffix == "":
            raise self._flight_hole_error(code, x, y)
        op = ("hole", {"code": code, "at": (float(x), float(y))})
        self._ops.append(op)
        self._seed = op
        return self

    def pocket(self, at, L, W, depth):
        """Rectangular pocket from the top face; (x, y) = pocket's lower-left corner."""
        self._guard_open("pocket()")
        self._need_stock("pocket()")
        (x, y) = at
        L = _positive(L, "pocket length")
        W = _positive(W, "pocket width")
        depth = _positive(depth, "pocket depth")
        SL, SW, ST = self._stock
        if not (0 <= x and 0 <= y and x + L <= SL and y + W <= SW):
            raise KeelError(
                f"keel: pocket at ({x}, {y}) size {L:g} x {W:g} does not fit "
                f"the {SL:g} x {SW:g} stock footprint"
            )
        if depth >= ST:
            raise KeelError(
                f"keel: pocket depth {depth:g} must be less than the stock thickness {ST:g}; "
                "use slot(depth='thru') for a cut all the way through"
            )
        op = ("pocket", {"at": (float(x), float(y)), "L": L, "W": W, "depth": depth})
        self._ops.append(op)
        self._seed = op
        return self

    def slot(self, at, to, width, depth="thru"):
        """Straight slot with round ends, centre line (x1,y1) -> (x2,y2)."""
        self._guard_open("slot()")
        self._need_stock("slot()")
        (x1, y1), (x2, y2) = at, to
        self._check_xy(x1, y1, "slot() start")
        self._check_xy(x2, y2, "slot() end")
        width = _positive(width, "slot width")
        if isinstance(depth, str):
            if depth != "thru":
                raise KeelError(
                    f"keel: unknown slot depth {depth!r}; use 'thru' or a depth in millimetres"
                )
        else:
            depth = _positive(depth, "slot depth")
            if depth >= self._stock[2]:
                raise KeelError(
                    f"keel: slot depth {depth:g} must be less than the stock thickness "
                    f"{self._stock[2]:g}; use depth='thru' for a cut all the way through"
                )
        op = ("slot", {"at": (float(x1), float(y1)), "to": (float(x2), float(y2)),
                       "width": width, "depth": depth})
        self._ops.append(op)
        self._seed = op
        return self

    def pattern(self, *args):
        """Repeat the LAST feature call nx x ny times with spacing dx, dy.

        Total instances = nx * ny including the seed position, at
        (x + i*dx, y + j*dy) for i in 0..nx-1, j in 0..ny-1.
        A leading string label (e.g. pattern("hole", 2, 2, ...)) is accepted
        and ignored, for compatibility with the SPEC draft form.
        A mount() seed repeats the whole mount. pattern() after mirror()
        raises KeelError: there is nothing left to repeat.
        """
        self._guard_open("pattern()")
        self._need_stock("pattern()")
        if self._mirrored:
            raise KeelError(
                "keel: pattern() after mirror(); there is nothing to repeat "
                "(mirror already copied every feature at once)"
            )
        if args and isinstance(args[0], str):
            args = args[1:]
        if len(args) != 4:
            raise KeelError(
                f"keel: pattern() takes (nx, ny, dx, dy), got {len(args)} arguments; "
                "it repeats the LAST feature call"
            )
        nx, ny, dx, dy = args
        if self._seed is None:
            raise KeelError("keel: pattern() with no previous feature; call a feature first")
        if self._seed[0] in ("wall", "wall_hole"):
            raise KeelError(
                f"keel: pattern() cannot repeat {self._seed[0]}(); "
                "only boss, hole, pocket, slot and mount can be patterned"
            )
        for name, value in (("nx", nx), ("ny", ny)):
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise KeelError(f"keel: pattern {name} must be a positive whole number, got {value!r}")
        kind, params = self._seed
        for i in range(nx):
            for j in range(ny):
                if i == 0 and j == 0:
                    continue  # the seed call itself
                moved = dict(params)
                if kind in ("boss", "hole"):
                    x, y = params["at"]
                    moved["at"] = (x + i * dx, y + j * dy)
                    self._check_xy(*moved["at"], f"pattern() copy of {kind}()")
                elif kind == "pocket":
                    x, y = params["at"]
                    moved["at"] = (x + i * dx, y + j * dy)
                    px, py = moved["at"]
                    SL, SW, _ = self._stock
                    if not (0 <= px and 0 <= py and px + params["L"] <= SL and py + params["W"] <= SW):
                        raise KeelError(
                            f"keel: pattern() copy of pocket() at ({px:g}, {py:g}) "
                            "falls outside the stock footprint"
                        )
                elif kind == "slot":
                    x1, y1 = params["at"]
                    x2, y2 = params["to"]
                    moved["at"] = (x1 + i * dx, y1 + j * dy)
                    moved["to"] = (x2 + i * dx, y2 + j * dy)
                    self._check_xy(*moved["at"], "pattern() copy of slot() start")
                    self._check_xy(*moved["to"], "pattern() copy of slot() end")
                elif kind == "mount":
                    ox, oy = params["origin"]
                    moved["origin"] = (ox + i * dx, oy + j * dy)
                    for _code, (hx, hy) in _mount_holes(params["name"], moved["origin"]):
                        self._check_xy(hx, hy, "pattern() copy of mount() hole")
                self._ops.append((kind, moved))
        self._seed = None  # a pattern ends the chain; the next pattern needs a fresh feature
        return self

    def fillet(self, edges="vertical", r=None):
        """Round the stock's 4 vertical outer edges; r defaults to the material standard."""
        self._guard_open("fillet()")
        self._need_stock("fillet()")
        if edges != "vertical":
            raise KeelError(
                f"keel: unknown fillet edges {edges!r}; Keel only rounds 'vertical' "
                "(the stock's 4 vertical outer edges)"
            )
        r = self._std_fillet if r is None else _positive(r, "fillet radius")
        if r >= min(self._stock[0], self._stock[1]) / 2:
            raise KeelError(f"keel: fillet radius {r:g} does not fit the stock footprint")
        self._fillet_r = r
        return self

    def wall_hole(self, edge, code, at):
        """Plain KF clearance hole drilled horizontally through the wall on `edge`.

        `u` = distance along the wall (from the west end for north/south walls,
        from the south end for east/west walls); `z` = hole-centre height above
        the stock top. Add the wall before its wall holes.
        """
        self._guard_open("wall_hole()")
        self._need_stock("wall_hole()")
        if edge not in _EDGES:
            raise KeelError(
                f"keel: unknown edge {edge!r}; edges are named "
                "'north', 'south', 'east' or 'west'"
            )
        self._check_fastener(code)
        _base, suffix = _split_code(code)
        if suffix:
            raise KeelError(
                f"keel: wall_hole() takes a plain KF code without -CB/-CS, got {code!r}; "
                "walls are too thin for counterbores or countersinks"
            )
        (u, z) = at
        for name, value in (("u", u), ("z", z)):
            if not isinstance(value, (int, float)):
                raise KeelError(
                    f"keel: wall_hole() {name} must be a number of millimetres, got {value!r}"
                )
        self._check_wall_hole_fit(edge, code, float(u), float(z))
        op = ("wall_hole", {"edge": edge, "code": code, "at": (float(u), float(z))})
        self._ops.append(op)
        self._seed = op
        return self

    def _walls_on(self, edge):
        return [p for kind, p in self._ops if kind == "wall" and p["edge"] == edge]

    def _check_wall_hole_fit(self, edge, code, u, z):
        walls = self._walls_on(edge)
        if not walls:
            raise KeelError(
                f"keel: wall_hole() on the {edge!r} edge with no wall; "
                f"add p.wall({edge!r}, ...) first"
            )
        clr, _cb = KF[_split_code(code)[0]]
        r = clr / 2
        h = max(w["h"] for w in walls)
        L, W, _ = self._stock
        length = L if edge in ("north", "south") else W
        if u - r < 0 or u + r > length or z - r < 0 or z + r > h:
            raise KeelError(
                f"keel: wall_hole() {code} at (u={u:g}, z={z:g}) does not fit "
                f"the {edge} wall ({length:g} long, {h:g} high, hole dia {clr:g}); "
                "the hole edge must stay inside the wall face"
            )

    def mount(self, name, origin, finish="plain"):
        """Company standard mount: a fixed group of base holes at `origin`.

        `finish` = "plain", "CB" or "CS", applied to every hole of the mount.
        Counts as one feature for pattern() and mirror(). On FLIGHT parts a
        "plain" mount raises KeelError, like a plain hole().
        """
        self._guard_open("mount()")
        self._need_stock("mount()")
        if finish not in ("plain", "CB", "CS"):
            raise KeelError(
                f"keel: unknown mount finish {finish!r}; finish is 'plain', 'CB' or 'CS'"
            )
        holes = _mount_holes(name, origin)  # also rejects unknown mount names
        (ox, oy) = origin
        for code, (hx, hy) in holes:
            eff = code if finish == "plain" else f"{code}-{finish}"
            self._check_xy(hx, hy, f"mount({name}) hole {eff}")
            if self.cls == "FLIGHT" and finish == "plain":
                raise self._flight_hole_error(code, hx, hy)
        op = {"name": name, "origin": (float(ox), float(oy)), "finish": finish}
        op = ("mount", op)
        self._ops.append(op)
        self._seed = op
        return self

    def mirror(self, axis):
        """Copy every hole, boss, pocket, slot and mount recorded so far.

        axis="ew" mirrors about the stock centre line x = L/2; axis="ns"
        about y = W/2. Originals stay; walls and wall holes are not mirrored.
        After a mirror, pattern() raises KeelError.
        """
        self._guard_open("mirror()")
        self._need_stock("mirror()")
        if axis not in ("ew", "ns"):
            raise KeelError(
                f"keel: unknown mirror axis {axis!r}; axis is 'ew' (about x = L/2) "
                "or 'ns' (about y = W/2)"
            )
        L, W, _ = self._stock
        copies = []
        for kind, p in list(self._ops):
            if kind == "hole":
                x, y = p["at"]
                at = (L - x, y) if axis == "ew" else (x, W - y)
                copies.append(("hole", {"code": p["code"], "at": at}))
            elif kind == "boss":
                x, y = p["at"]
                at = (L - x, y) if axis == "ew" else (x, W - y)
                copies.append(("boss", {"at": at, "dia": p["dia"], "h": p["h"]}))
            elif kind == "pocket":
                x, y = p["at"]
                if axis == "ew":
                    at = (L - x - p["L"], y)
                else:
                    at = (x, W - y - p["W"])
                copies.append(("pocket", {"at": at, "L": p["L"], "W": p["W"],
                                          "depth": p["depth"]}))
            elif kind == "slot":
                (x1, y1), (x2, y2) = p["at"], p["to"]
                if axis == "ew":
                    at, to = (L - x1, y1), (L - x2, y2)
                else:
                    at, to = (x1, W - y1), (x2, W - y2)
                copies.append(("slot", {"at": at, "to": to, "width": p["width"],
                                        "depth": p["depth"]}))
            elif kind == "mount":
                # Mirror the whole mount hole by hole; the mirrored set is what
                # a physical mirror of the drilled holes produces.
                for code, (hx, hy) in _mount_holes(p["name"], p["origin"]):
                    eff = code if p["finish"] == "plain" else f"{code}-{p['finish']}"
                    at = (L - hx, hy) if axis == "ew" else (hx, W - hy)
                    copies.append(("hole", {"code": eff, "at": at}))
        self._ops.extend(copies)
        self._mirrored = True
        self._seed = None
        return self

    # -- build ------------------------------------------------------------
    def _wall_box(self, op):
        L, W, T = self._stock
        edge, h, t = op["edge"], op["h"], op["t"]
        if edge == "north":
            return (0, W - t, T, L, t, h)
        if edge == "south":
            return (0, 0, T, L, t, h)
        if edge == "east":
            return (L - t, 0, T, t, W, h)
        return (0, 0, T, t, W, h)  # west

    def _wall_hole_cutter(self, op):
        """Horizontal cylinder through the tallest/thickest wall on the edge."""
        L, W, T = self._stock
        edge, code, (u, z) = op["edge"], op["code"], op["at"]
        clr, _cb = KF[_split_code(code)[0]]
        r = clr / 2
        walls = self._walls_on(edge)
        t = max(w["t"] for w in walls)
        cz = T + z
        if edge == "north":
            return cq.Solid.makeCylinder(r, t + 2.0, cq.Vector(u, W - t - 1.0, cz),
                                         cq.Vector(0, 1, 0))
        if edge == "south":
            return cq.Solid.makeCylinder(r, t + 2.0, cq.Vector(u, -1.0, cz),
                                         cq.Vector(0, 1, 0))
        if edge == "east":
            return cq.Solid.makeCylinder(r, t + 2.0, cq.Vector(L - t - 1.0, u, cz),
                                         cq.Vector(1, 0, 0))
        return cq.Solid.makeCylinder(r, t + 2.0, cq.Vector(-1.0, u, cz),
                                     cq.Vector(1, 0, 0))  # west

    def _local_top(self, x, y, additives):
        """Highest added material covering point (x, y): walls are strips, bosses discs."""
        top = self._stock[2]
        for kind, p in additives:
            if kind == "wall":
                L, W, T = self._stock
                edge, h, t = p["edge"], p["h"], p["t"]
                inside = (
                    (edge == "north" and y >= W - t)
                    or (edge == "south" and y <= t)
                    or (edge == "east" and x >= L - t)
                    or (edge == "west" and x <= t)
                )
                if inside:
                    top = max(top, T + h)
            elif kind == "boss":
                bx, by = p["at"]
                if math.hypot(x - bx, y - by) <= p["dia"] / 2:
                    top = max(top, self._stock[2] + p["h"])
        return top

    def _cut_base_hole(self, solid, code, x, y, additives):
        """Cut one base hole (through + counterbore/countersink from the local top)."""
        base, suffix = _split_code(code)
        clr, (cbd, cbdpth) = KF[base]
        top = self._local_top(x, y, additives)
        cut = cq.Solid.makeCylinder(clr / 2, top + 2.0, cq.Vector(x, y, -1.0))
        solid = solid.cut(cut)
        if suffix == "-CB":
            cb = cq.Solid.makeCylinder(cbd / 2, cbdpth + 1.0, cq.Vector(x, y, top - cbdpth))
            solid = solid.cut(cb)
        elif suffix == "-CS":
            csd = KF_CS[base]
            cone_h = (csd - clr) / 2.0  # 45-degree half-angle down to the clearance dia
            cone = cq.Solid.makeCone(clr / 2, csd / 2, cone_h,
                                     cq.Vector(x, y, top - cone_h), cq.Vector(0, 0, 1))
            solid = solid.cut(cone)
        return solid

    def _build(self):
        L, W, T = self._stock
        solid = cq.Solid.makeBox(L, W, T, pnt=cq.Vector(0, 0, 0))
        if self._fillet_r is not None:
            solid = (
                cq.Workplane(obj=solid).edges("|Z").fillet(self._fillet_r).val()
            )
        additives = []  # (kind, params) of walls/bosses applied so far
        for kind, p in self._ops:
            if kind == "wall":
                x0, y0, z0, dx, dy, dz = self._wall_box(p)
                solid = solid.fuse(
                    cq.Solid.makeBox(dx, dy, dz, pnt=cq.Vector(x0, y0, z0))
                )
                additives.append((kind, p))
            elif kind == "boss":
                x, y = p["at"]
                cyl = cq.Solid.makeCylinder(p["dia"] / 2, p["h"], cq.Vector(x, y, T))
                solid = solid.fuse(cyl)
                additives.append((kind, p))
            elif kind == "hole":
                solid = self._cut_base_hole(solid, p["code"], *p["at"], additives)
            elif kind == "mount":
                for code, (hx, hy) in _mount_holes(p["name"], p["origin"]):
                    eff = code if p["finish"] == "plain" else f"{code}-{p['finish']}"
                    solid = self._cut_base_hole(solid, eff, hx, hy, additives)
            elif kind == "wall_hole":
                solid = solid.cut(self._wall_hole_cutter(p))
            elif kind == "pocket":
                x, y = p["at"]
                cx, cy = x + p["L"] / 2, y + p["W"] / 2
                top = self._local_top(cx, cy, additives)
                box = cq.Solid.makeBox(
                    p["L"], p["W"], p["depth"] + 1.0, pnt=cq.Vector(x, y, top - p["depth"])
                )
                solid = solid.cut(box)
            elif kind == "slot":
                (x1, y1), (x2, y2) = p["at"], p["to"]
                r = p["width"] / 2
                seg = math.hypot(x2 - x1, y2 - y1)
                if p["depth"] == "thru":
                    top = max(
                        self._local_top(x1, y1, additives),
                        self._local_top(x2, y2, additives),
                        self._local_top((x1 + x2) / 2, (y1 + y2) / 2, additives),
                    )
                    z0, zlen = -1.0, top + 2.0
                else:
                    top = self._local_top((x1 + x2) / 2, (y1 + y2) / 2, additives)
                    z0, zlen = top - p["depth"], p["depth"] + 1.0
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
                bar = cq.Solid.makeBox(
                    seg + 2 * r, 2 * r, zlen, pnt=cq.Vector(mx - (seg + 2 * r) / 2, my - r, z0)
                )
                bar = bar.rotate(cq.Vector(mx, my, z0), cq.Vector(mx, my, z0 + 1), ang)
                cutter = bar.fuse(
                    cq.Solid.makeCylinder(r, zlen, cq.Vector(x1, y1, z0)),
                    cq.Solid.makeCylinder(r, zlen, cq.Vector(x2, y2, z0)),
                )
                solid = solid.cut(cutter)
        return solid.clean()

    def _check_flight_fasteners(self):
        """FLIGHT rule 2: every base hole (holes and mounts) is -CB or -CS."""
        for kind, p in self._ops:
            if kind == "hole":
                _base, suffix = _split_code(p["code"])
                if suffix == "":
                    raise self._flight_hole_error(p["code"], *p["at"])
            elif kind == "mount" and p["finish"] == "plain":
                code, (hx, hy) = _mount_holes(p["name"], p["origin"])[0]
                raise self._flight_hole_error(code, hx, hy)

    def finish(self):
        """Return the part as exactly one CadQuery solid. Must be the last call."""
        self._guard_open("finish()")
        if self._stock is None:
            raise KeelError("keel: finish() with no stock(); every part starts with p.stock(L, W, T)")
        if self.cls == "FLIGHT":
            if self._fillet_r is None:
                self._fillet_r = self._std_fillet  # auto fillet in the material standard
            self._check_flight_fasteners()
        solid = self._build()
        solids = solid.Solids()
        if len(solids) != 1:
            raise KeelError(
                f"keel: part {self.number!r} built {len(solids)} solids, not one; "
                "a Keel program compiles to exactly one solid"
            )
        if not solid.isValid():
            raise KeelError(f"keel: part {self.number!r} built an invalid solid")
        self._finished = True
        return solid


def render(p, path, projection=(1.0, 1.0, 1.0)):
    """Write an SVG preview of a finished part (CadQuery SVG export, isometric)."""
    if not isinstance(p, part):
        raise KeelError(f"keel: render() needs a keel part, got {type(p).__name__}")
    if not p._finished:
        raise KeelError(
            "keel: render() before p.finish(); finish the part first "
            "(every program ends in solid = p.finish())"
        )
    solid = p._build()
    cq.exporters.export(
        cq.Workplane(obj=solid),
        path,
        opt={
            "projectionDir": projection,
            "showHidden": False,
            "strokeColor": (30, 58, 95),
            "hiddenColor": (160, 175, 195),
            "showAxes": False,
        },
    )
    return path
