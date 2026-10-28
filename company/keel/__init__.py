"""Keel: Quillon Orbital Works' private part-description tool.

Units are millimetres. Datum = the part's lower-left-bottom corner (0, 0, 0).
+X = east, +Y = north, +Z = up. Nothing is centred unless the call says so.
"""

import math

import cadquery as cq

__version__ = "1.0.0"

STANDARD_WALL = 2.5
STANDARD_FILLET = 1.0

# Company fastener table KF: code -> (clearance dia, (counterbore dia, depth)).
# "-CB" suffix = counterbored from the top face.
KF = {
    "KF-M2": (2.4, (4.4, 2.0)),
    "KF-M3": (3.4, (6.5, 3.0)),
    "KF-M4": (4.5, (8.0, 4.0)),
    "KF-M5": (5.5, (10.0, 5.0)),
    "KF-M6": (6.6, (11.0, 6.0)),
}

_EDGES = ("north", "south", "east", "west")


class KeelError(Exception):
    """Company-style error raised for any misuse of Keel."""


def _positive(value, what):
    if not isinstance(value, (int, float)) or value <= 0:
        raise KeelError(f"{what} must be a positive number of millimetres, got {value!r}")
    return float(value)


class part:  # noqa: N801 - company style uses lowercase, like the manual
    """A part under construction. End every program with ``solid = p.finish()``."""

    def __init__(self, number, material="AL6061"):
        self.number = number
        self.material = material  # metadata only; never changes the shape
        self._stock = None
        self._ops = []          # recorded feature calls, in order
        self._fillet_r = None
        self._finished = False
        self._seed = None       # last recorded feature (for pattern)

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
        t = STANDARD_WALL if t is None else _positive(t, "wall thickness")
        L, W, _ = self._stock
        if t > min(L, W):
            raise KeelError(f"keel: wall thickness {t:g} does not fit the {L:g} x {W:g} stock")
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
        """Through hole (all the way down) using table KF; '-CB' adds the counterbore."""
        self._guard_open("hole()")
        self._need_stock("hole()")
        base = code[:-3] if code.endswith("-CB") else code
        if base not in KF:
            raise KeelError(
                f"keel: unknown fastener code {code!r}; "
                "holes use company codes KF-M2, KF-M3, KF-M4, KF-M5, KF-M6 "
                "(add -CB for a counterbore, e.g. KF-M4-CB)"
            )
        (x, y) = at
        self._check_xy(x, y, f"hole({code})")
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
        """
        self._guard_open("pattern()")
        self._need_stock("pattern()")
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
        if self._seed[0] in ("wall",):
            raise KeelError(
                f"keel: pattern() cannot repeat {self._seed[0]}(); "
                "only boss, hole, pocket and slot can be patterned"
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
                self._ops.append((kind, moved))
        self._seed = None  # a pattern ends the chain; the next pattern needs a fresh feature
        return self

    def fillet(self, edges="vertical", r=None):
        """Round the stock's 4 vertical outer edges; r defaults to the standard 1.0."""
        self._guard_open("fillet()")
        self._need_stock("fillet()")
        if edges != "vertical":
            raise KeelError(
                f"keel: unknown fillet edges {edges!r}; Keel only rounds 'vertical' "
                "(the stock's 4 vertical outer edges)"
            )
        r = STANDARD_FILLET if r is None else _positive(r, "fillet radius")
        if r >= min(self._stock[0], self._stock[1]) / 2:
            raise KeelError(f"keel: fillet radius {r:g} does not fit the stock footprint")
        self._fillet_r = r
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
                clr, (cbd, cbdpth) = KF[p["code"][:-3] if p["code"].endswith("-CB") else p["code"]]
                x, y = p["at"]
                top = self._local_top(x, y, additives)
                cut = cq.Solid.makeCylinder(clr / 2, top + 2.0, cq.Vector(x, y, -1.0))
                solid = solid.cut(cut)
                if p["code"].endswith("-CB"):
                    cb = cq.Solid.makeCylinder(cbd / 2, cbdpth + 1.0, cq.Vector(x, y, top - cbdpth))
                    solid = solid.cut(cb)
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

    def finish(self):
        """Return the part as exactly one CadQuery solid. Must be the last call."""
        self._guard_open("finish()")
        if self._stock is None:
            raise KeelError("keel: finish() with no stock(); every part starts with p.stock(L, W, T)")
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
