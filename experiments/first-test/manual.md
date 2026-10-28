# CadQuery manual (excerpt from CadQuery 2.8's own API documentation)

## Named planes (Plane.named)
Available named planes are as follows. Direction references refer to
the global directions.

=========== ======= ======= ======
Name        xDir    yDir    zDir
=========== ======= ======= ======
XY          +x      +y      +z
YZ          +y      +z      +x
ZX          +z      +x      +y
XZ          +x      +z      -y
YX          +y      +x      -z
ZY          +z      +y      -x
front       +x      +y      +z
back        -x      +y      -z
left        +z      +y      -x
right       -z      +y      +x
top         +x      -z      +y
bottom      +x      +z      -y
=========== ======= ======= ======

## Workplane(inPlane='XY', origin=(0, 0, 0), obj=None)
make a workplane from a particular plane

:param inPlane: the plane in which the workplane will be done
:param origin: the desired origin of the new workplane
:param obj: an object to use initially for the stack
    stack value.

The most common use is::

    s = Workplane("XY")

After creation, the stack contains a single point, the origin of the underlying plane, and
the *current point* is on the origin.

## Workplane.workplane(offset: float = 0.0, invert: bool = False, centerOption: Literal['CenterOfMass', 'ProjectedOrigin', 'CenterOfBoundBox'] = 'ProjectedOrigin', origin: Union[Tuple[float, float], Tuple[float, float, float], Vector, NoneType] = None) -> ~T
Creates a new 2D workplane, located relative to the first face on the stack.

:param offset:  offset for the workplane in its normal direction . Default
:param invert:  invert the normal direction from that of the face.
:param centerOption: how local origin of workplane is determined.
:param origin: origin for plane center, requires 'ProjectedOrigin' centerOption.

The first element on the stack must be a face, a set of
co-planar faces or a vertex.  If a vertex, then the parent
…

## Workplane.center(x: float, y: float) -> ~T
Shift local coordinates to the specified location.

The location is specified in terms of local coordinates.

:param x: the new x location
:param y: the new y location

The current point is set to the new center.
This method is useful to adjust the center point after it has been created automatically on
a face, but not where you'd like it to be.

In this example, we adjust the workplane center to be at the corner of a cube, instead of
the center of a face, which is the default::

…

## Workplane.moveTo(x: float = 0, y: float = 0) -> ~T
Move to the specified point, without drawing.

:param x: desired x location, in local coordinates
:param y: desired y location, in local coordinates

Not to be confused with :meth:`center`, which moves the center of the entire
workplane, this method only moves the current point ( and therefore does not affect objects
already drawn ).

See :meth:`move` to do the same thing but using relative dimensions

## Workplane.pushPoints(pntList: Iterable[Union[Tuple[float, float], Tuple[float, float, float], Vector, Location]]) -> ~T
Pushes a list of points onto the stack as vertices.
The points are in the 2D coordinate space of the workplane face

:param pntList: a list of points to push onto the stack

A common use is to provide a list of points for a subsequent operation, such as creating
circles or holes. This example creates a cube, and then drills three holes through it,
based on three points::

    s = (
        Workplane()
        .box(1, 1, 1)
        .faces(">Z")
        .workplane()
…

## Workplane.rarray(xSpacing: float, ySpacing: float, xCount: int, yCount: int, center: Union[bool, Tuple[bool, bool]] = True) -> ~T
Creates an array of points and pushes them onto the stack.
If you want to position the array at another point, create another workplane
that is shifted to the position you would like to use as a reference

:param xSpacing: spacing between points in the x direction ( must be >= 0)
:param ySpacing: spacing between points in the y direction ( must be >= 0)
:param xCount: number of points ( > 0 )
:param yCount: number of points ( > 0 )
:param center: If True, the array will be centered around the workplane center.
…

## Workplane.polarArray(radius: float, startAngle: float, angle: float, count: int, fill: bool = True, rotate: bool = True) -> ~T
Creates a polar array of points and pushes them onto the stack.
The zero degree reference angle is located along the local X-axis.

:param radius: Radius of the array.
:param startAngle: Starting angle (degrees) of array. Zero degrees is
    situated along the local X-axis.
:param angle: The angle (degrees) to fill with elements. A positive
    value will fill in the counter-clockwise direction. If fill is
    False, angle is the angle between elements.
:param count: Number of elements in array. (count >= 1)
…

## Workplane.rect(xLen: float, yLen: float, centered: Union[bool, Tuple[bool, bool]] = True, forConstruction: bool = False) -> ~T
Make a rectangle for each item on the stack.

:param xLen: length in the x direction (in workplane coordinates)
:param yLen: length in the y direction (in workplane coordinates)
:param centered: If True, the rectangle will be centered around the reference
  point. If False, the corner of the rectangle will be on the reference point and
  it will extend in the positive x and y directions. Can also use a 2-tuple to
  specify centering along each axis.
…

## Workplane.circle(radius: float, forConstruction: bool = False) -> ~T
Make a circle for each item on the stack.

:param radius: radius of the circle
:param forConstruction: should the new wires be reference geometry only?
    part geometry

A common use case is to use a for-construction rectangle to define the centers of a
hole pattern::

    s = Workplane().rect(4.0, 4.0, forConstruction=True).vertices().circle(0.25)

Creates 4 circles at the corners of a square centered on the origin. Another common case is
…

## Workplane.polygon(nSides: int, diameter: float, forConstruction: bool = False, circumscribed: bool = False) -> ~T
Make a polygon for each item on the stack.

By default, each polygon is created by inscribing it in a circle of the
specified diameter, such that the first vertex is oriented in the x direction.
Alternatively, each polygon can be created by circumscribing it around
a circle of the specified diameter, such that the midpoint of the first edge
is oriented in the x direction. Circumscribed polygons are thus rotated by
pi/nSides radians relative to the inscribed polygon. This ensures the extent
…

## Workplane.polyline(listOfXYTuple: Sequence[VectorLike], forConstruction: bool = False, includeCurrent: bool = False) -> ~T
Create a polyline from a list of points

:param listOfXYTuple: a list of points in Workplane coordinates (2D or 3D)
:param forConstruction: whether or not the edges are used for reference
    part geometry
:param includeCurrent: use current point as a starting point of the polyline

*NOTE* most commonly, the resulting wire should be closed.

## Workplane.close() -> ~T
End construction, and attempt to build a closed wire.

After 2D (or 3D) drafting with methods such as lineTo, threePointArc,
tangentArcPoint and polyline, it is necessary to convert the edges
produced by these into one or more wires.

When a set of edges is closed, CadQuery assumes it is safe to build
the group of edges into a wire. This example builds a simple triangular
prism::

    s = Workplane().lineTo(1, 0).lineTo(1, 1).close().extrude(0.2)

## Workplane.slot2D(length: float, diameter: float, angle: float = 0) -> ~T
Creates a rounded slot for each point on the stack.

:param diameter: desired diameter, or width, of slot
:param length: desired end to end length of slot
:param angle: angle of slot in degrees, with 0 being along x-axis

Can be used to create arrays of slots, such as in cooling applications::

    Workplane().box(10, 25, 1).rarray(1, 2, 1, 10).slot2D(8, 1, 0).cutThruAll()

## Workplane.box(length: float, width: float, height: float, centered: Union[bool, Tuple[bool, bool, bool]] = True, combine: Union[bool, Literal['cut', 'a', 's']] = True, clean: bool = True) -> ~T
Return a 3d box with specified dimensions for each object on the stack.

:param length: box size in X direction
:param width: box size in Y direction
:param height: box size in Z direction
:param centered: If True, the box will be centered around the reference point.
    If False, the corner of the box will be on the reference point and it will
    extend in the positive x, y and z directions. Can also use a 3-tuple to
    specify centering along each axis.
…

## Workplane.cylinder(height: float, radius: float, direct: Union[Tuple[float, float, float], Vector] = Vector: (0.0, 0.0, 1.0), angle: float = 360, centered: Union[bool, Tuple[bool, bool, bool]] = True, combine: Union[bool, Literal['cut', 'a', 's']] = True, clean: bool = True) -> ~T
Returns a cylinder with the specified radius and height for each point on the stack

:param height: The height of the cylinder
:param radius: The radius of the cylinder
:param direct: The direction axis for the creation of the cylinder
:param angle: The angle to sweep the cylinder arc through
:param centered: If True, the cylinder will be centered around the reference point. If False,
    the corner of a bounding box around the cylinder will be on the reference point and it
…

## Workplane.extrude(until: Union[float, Literal['next', 'last'], Face], combine: Union[bool, Literal['cut', 'a', 's']] = True, clean: bool = True, both: bool = False, taper: Optional[float] = None) -> ~T
Use all un-extruded wires in the parent chain to create a prismatic solid.

:param until: The distance to extrude, normal to the workplane plane. When a float is
    passed, the extrusion extends this far and a negative value is in the opposite direction
    to the normal of the plane. The string "next" extrudes until the next face orthogonal to
    the wire normal. "last" extrudes to the last face. If a object of type Face is passed then
…

## Workplane.revolve(angleDegrees: float = 360.0, axisStart: Union[Tuple[float, float], Tuple[float, float, float], Vector, NoneType] = None, axisEnd: Union[Tuple[float, float], Tuple[float, float, float], Vector, NoneType] = None, combine: Union[bool, Literal['cut', 'a', 's']] = True, clean: bool = True) -> ~T
Use all un-revolved wires in the parent chain to create a solid.

:param angleDegrees: the angle to revolve through.
:param axisStart: the start point of the axis of rotation
:param axisEnd: the end point of the axis of rotation
:param combine: True or "a" to combine the resulting solid with parent solids if found,
    "cut" or "s" to remove the resulting solid from the parent solids if found.
    False to keep the resulting solid separated from the parent solids.
…

## Workplane.cutBlind(until: Union[float, Literal['next', 'last'], Face], clean: bool = True, both: bool = False, taper: Optional[float] = None) -> ~T
Use all un-extruded wires in the parent chain to create a prismatic cut from existing solid.

Specify either a distance value, or one of "next", "last" to indicate a face to cut to.

Similar to extrude, except that a solid in the parent chain is required to remove material
from. cutBlind always removes material from a part.

:param until: The distance to cut to, normal to the workplane plane. When a negative float
    is passed the cut extends this far in the opposite direction to the normal of the plane
…

## Workplane.cutThruAll(clean: bool = True, taper: float = 0) -> ~T
Use all un-extruded wires in the parent chain to create a prismatic cut from existing solid.
Cuts through all material in both normal directions of workplane.

Similar to extrude, except that a solid in the parent chain is required to remove material
from. cutThruAll always removes material from a part.

:param clean: call :meth:`clean` afterwards to have a clean shape

see :meth:`cutBlind` to cut material to a limited depth

## Workplane.hole(diameter: float, depth: Optional[float] = None, clean: bool = True) -> ~T
Makes a hole for each item on the stack.

:param diameter: the diameter of the hole
:param depth: the depth of the hole
:param clean: call :meth:`clean` afterwards to have a clean shape

The surface of the hole is at the current workplane.

One hole is created for each item on the stack.  A very common use case is to use a
construction rectangle to define the centers of a set of holes, like so::

    s = (
        Workplane()
        .box(2, 4, 0.5)
        .faces(">Z")
        .workplane()
…

## Workplane.cboreHole(diameter: float, cboreDiameter: float, cboreDepth: float, depth: Optional[float] = None, clean: bool = True) -> ~T
Makes a counterbored hole for each item on the stack.

:param diameter: the diameter of the hole
:param cboreDiameter: the diameter of the cbore, must be greater than hole diameter
:param cboreDepth: depth of the counterbore
:param depth: the depth of the hole
:param clean: call :meth:`clean` afterwards to have a clean shape

The surface of the hole is at the current workplane plane.

One hole is created for each item on the stack.  A very common use case is to use a
…

## Workplane.cskHole(diameter: float, cskDiameter: float, cskAngle: float, depth: Optional[float] = None, clean: bool = True) -> ~T
Makes a countersunk hole for each item on the stack.

:param diameter: the diameter of the hole
:param cskDiameter: the diameter of the countersink, must be greater than hole diameter
:param cskAngle: angle of the countersink, in degrees ( 82 is common )
:param depth: the depth of the hole
:param clean: call :meth:`clean` afterwards to have a clean shape

The surface of the hole is at the current workplane.

One hole is created for each item on the stack.  A very common use case is to use a
…

## Workplane.union(toUnion: Union[ForwardRef('Workplane'), Solid, Compound, NoneType] = None, clean: bool = True, glue: bool = False, tol: Optional[float] = None) -> ~T
Unions all of the items on the stack of toUnion with the current solid.
If there is no current solid, the items in toUnion are unioned together.

:param toUnion: a solid object, or a Workplane object having a solid
:param clean: call :meth:`clean` afterwards to have a clean shape (default True)
:param glue: use a faster gluing mode for non-overlapping shapes (default False)
:param tol: tolerance value for fuzzy bool operation mode (default None)

## Workplane.cut(toCut: Union[ForwardRef('Workplane'), Solid, Compound], clean: bool = True, tol: Optional[float] = None) -> ~T
Cuts the provided solid from the current solid, IE, perform a solid subtraction.

:param toCut: a solid object, or a Workplane object having a solid
:param clean: call :meth:`clean` afterwards to have a clean shape
:param tol: tolerance value for fuzzy bool operation mode (default None)

## Workplane.intersect(toIntersect: Union[ForwardRef('Workplane'), Solid, Compound], clean: bool = True, tol: Optional[float] = None) -> ~T
Intersects the provided solid from the current solid.

:param toIntersect: a solid object, or a Workplane object having a solid
:param clean: call :meth:`clean` afterwards to have a clean shape
:param tol: tolerance value for fuzzy bool operation mode (default None)

## Workplane.translate(vec: VectorLike) -> ~T
Returns a copy of all of the items on the stack moved by the specified translation vector.

:param tupleDistance: distance to move, in global coordinates

## Workplane.rotate(axisStartPoint: VectorLike, axisEndPoint: VectorLike, angleDegrees: float) -> ~T
Returns a copy of all of the items on the stack rotated through and angle around the axis
of rotation.

:param axisStartPoint: The first point of the axis of rotation
:param axisEndPoint: The second point of the axis of rotation
:param angleDegrees: the rotation angle, in degrees

## Workplane.faces(selector: Union[str, cadquery.selectors.Selector, NoneType] = None, tag: Optional[str] = None) -> ~T
Select the faces of objects on the stack, optionally filtering the selection. If there are
multiple objects on the stack, the faces of all objects are collected and a list of all the
distinct faces is returned.

:param selector: optional Selector object, or string selector expression
    (see :class:`StringSyntaxSelector`)
:param tag: if set, search the tagged object instead of self
    the current stack, filtered by the provided selector.

…

## Workplane.edges(selector: Union[str, cadquery.selectors.Selector, NoneType] = None, tag: Optional[str] = None) -> ~T
Select the edges of objects on the stack, optionally filtering the selection. If there are
multiple objects on the stack, the edges of all objects are collected and a list of all the
distinct edges is returned.

:param selector: optional Selector object, or string selector expression
    (see :class:`StringSyntaxSelector`)
:param tag: if set, search the tagged object instead of self
    the current stack, filtered by the provided selector.

…

## Workplane.fillet(radius: float) -> ~T
Fillets a solid on the selected edges.

The edges on the stack are filleted. The solid to which the edges belong must be in the
parent chain of the selected edges.

:param radius: the radius of the fillet, must be > zero

This example will create a unit cube, with the top edges filleted::

    s = Workplane().box(1, 1, 1).faces("+Z").edges().fillet(0.1)

## Workplane.chamfer(length: float, length2: Optional[float] = None) -> ~T
Chamfers a solid on the selected edges.

The edges on the stack are chamfered. The solid to which the
edges belong must be in the parent chain of the selected
edges.

Optional parameter `length2` can be supplied with a different
value than `length` for a chamfer that is shorter on one side
longer on the other side.

:param length: the length of the chamfer, must be greater than zero
:param length2: optional parameter for asymmetrical chamfer

This example will create a unit cube, with the top edges chamfered::

…

## Workplane.val() -> Union[Vector, Location, Shape, cadquery.sketch.Sketch]
Return the first value on the stack. If no value is present, current plane origin is returned.

## Solid.makeBox(length: 'float', width: 'float', height: 'float', pnt: 'VectorLike' = Vector: (0.0, 0.0, 0.0), dir: 'VectorLike' = Vector: (0.0, 0.0, 1.0)) -> 'Solid'
makeBox(length,width,height,[pnt,dir]) -- Make a box located in pnt with the dimensions (length,width,height)
By default pnt=Vector(0,0,0) and dir=Vector(0,0,1)

## Solid.makeCylinder(radius: 'float', height: 'float', pnt: 'VectorLike' = Vector: (0.0, 0.0, 0.0), dir: 'VectorLike' = Vector: (0.0, 0.0, 1.0), angleDegrees: 'float' = 360) -> 'Solid'
makeCylinder(radius,height,[pnt,dir,angle]) --
Make a cylinder with a given radius and height
By default pnt=Vector(0,0,0),dir=Vector(0,0,1) and angle=360

## Solid.makeCone(radius1: 'float', radius2: 'float', height: 'float', pnt: 'VectorLike' = Vector: (0.0, 0.0, 0.0), dir: 'VectorLike' = Vector: (0.0, 0.0, 1.0), angleDegrees: 'float' = 360) -> 'Solid'
Make a cone with given radii and height
By default pnt=Vector(0,0,0),
dir=Vector(0,0,1) and angle=360

## Selectors (from CadQuery's selectors reference)
CadQuery selector strings allow filtering various types of object lists. Most commonly, Edges, Faces, and Vertices are
used, but all objects types can be filtered.

Object lists are created by using the following methods, which each collect a type of shape:

    * :py:meth:`cadquery.Workplane.vertices`
    * :py:meth:`cadquery.Workplane.edges`
    * :py:meth:`cadquery.Workplane.faces`
    * :py:meth:`cadquery.Workplane.shells`
    * :py:meth:`cadquery.Workplane.solids`

Each of these methods accepts either a Selector object or a string. String selectors are simply
shortcuts for using the full object equivalents. If you pass one of the string patterns in,
CadQuery will automatically use the associated selector object.


Filtering Faces
----------------

All types of string selectors work on faces.  In most cases, the selector refers to the direction
of the **normal vector** of the face.

.. warning::

    If a face is not planar, selectors are evaluated at the center of mass of the face. This can lead
    to results that are quite unexpected.

The axis used in the listing below are for illustration: any axis would work similarly in each case.

=========   =========================================  =======================================================
Selector    Selects                                    Selector Class
=========   =========================================  =======================================================
+Z          Faces with normal in +z direction          `cadquery.DirectionSelector`
|Z         Faces with normal parallel to z dir        `cadquery.ParallelDirSelector`
-X          Faces with normal in neg x direction       `cadquery.DirectionSelector`
#Z          Faces with normal orthogonal to z dir      `cadquery.PerpendicularDirSelector`
%Plane      Faces of type plane                        `cadquery.TypeSelector`
>Y          Face farthest in the positive y dir        `cadquery.DirectionMinMaxSelector`
<Y          Face farthest in the negative y dir        `cadquery.DirectionMinMaxSelector`
>Y[-2]      2nd farthest Face **normal** to the y dir  `cadquery.DirectionNthSelector`
<Y[0]       1st closest Face **normal** to the y dir   `cadquery.DirectionNthSelector`
>>Y[-2]     2nd farthest Face in the y dir             `cadquery.CenterNthSelector`
<<Y[0]      1st closest Face in the y dir              `cadquery.CenterNthSelector`
=========   =========================================  =======================================================

