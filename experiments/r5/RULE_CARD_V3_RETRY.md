CadQuery rule card (CadQuery 2.8). Use only these calls and arguments.
- Units mm. Final solid in `result`. One solid only: fuse every part before you cut.
- Corner boxes: `cq.Solid.makeBox(dx, dy, dz, cq.Vector(x0, y0, z0))` (corner at x0,y0,z0; no `centered` argument).
  `cq.Workplane("XY").box(dx, dy, dz)` is CENTRED by default; for "X from a to b" use
  `box(dx, dy, dz, centered=(False, False, False))` then `.translate((a, y0, z0))`.
- Cylinders on any axis: `cq.Solid.makeCylinder(radius, height, cq.Vector(x, y, z), cq.Vector(dx, dy, dz))`:
  the point is the START of the range, the direction is the tube's axis ((1,0,0) along X, (0,1,0) along Y, (0,0,1) along Z).
  Positional arguments only: there is no `start=` or `center=` keyword.
  `Workplane.cylinder()` takes no point; do not use it for placed cylinders.
- Cones / frustums: `cq.Solid.makeCone(r_bottom, r_top, height, cq.Vector(x, y, z), cq.Vector(0, 0, 1))`.
- Two kinds of objects, never mix them. A Solid (from `cq.Solid.make...`) joins with `a.fuse(b)` and cuts with
  `a.cut(b)` (b must be a Solid). A Workplane joins with `.union(x)` and cuts with `.cut(x)` (x: Workplane or Solid).
  Workplanes have no `.fuse()` and no `.solid()`: to get the Solid out of a Workplane use `wp.val()`.
- Through holes: extend the cutter 1 mm only past faces that are on the outside of the whole part. A cut that the job says stops inside the part (a slot, groove or pocket that ends at another solid) must stop exactly at the given value, with no extra length.
- Rounded rectangle window: `cq.Workplane("XY").rect(w, h).extrude(t).edges("|Z").fillet(r)` (`rect()` has no radius;
  there is no `roundedRect`).
- Slots: `.slot2D(length, diameter, angle)` gives ROUND ends (diameter = slot width); "square ends" = a rotated `rect`.
- Polygons: `cq.Workplane("XY").polyline([(x1, y1), (x2, y2), (x3, y3)]).close().extrude(t)`.
- `extrude()` has no `centered`; `Plane(origin, xDir, normal)` has no `yDir`; `workplane()` has no `inPlane`.
- Move with `.translate((dx, dy, dz))`; never leave a part at the origin when the job gives coordinates.
- Arcs: there is no `.arc()`; use `.threePointArc((xm, ym), (x2, y2))` or `.radiusArc((x2, y2), r)`.
- Revolve: `.revolve(angleDegrees, axisStart, axisEnd)` (points, no `axisDir`).
- Vectors: `cq.Vector(x, y, z)` with three numbers; tuples of two numbers are only for 2D sketch points.

