# Nimbus Devices mechanical design standard NDS-1 (excerpt)

All Nimbus parts follow these rules unless a request says otherwise. Units are millimetres, Z is up.
An "inside space" height or depth is always measured from the top of the floor to the rim (inside, not overall).

1. **Placement.** A part's base (plate, floor or block bottom) lies on Z = 0 and is centred on the origin in X and Y,
   with its longest base side along X. Features "on top" point to +Z.
2. **Material.** Parts are plastic unless the request says aluminium.
3. **Clearance holes** for screws (through holes, normal fit): M3 → 3.4, M4 → 4.5, M5 → 5.5, M6 → 6.6 diameter.
4. **Counterbores** for socket-head screws, cut from the top face: M3 → diameter 6.5, depth 3.5; M4 → 8, depth 4.5;
   M5 → 10, depth 5.5; M6 → 11, depth 6.5. The clearance hole continues through the rest of the part. Screws not called socket-head get a plain
   clearance hole only (no counterbore).
5. **Corner holes.** When a part is fixed by four screws "at the corners", each hole centre is inset from both
   adjacent outer edges by twice the screw size (M4 → 8 from each edge).
6. **Walls.** Enclosures, housings and lids have walls, floors and plates of thickness 2.5 (plastic) or 4 (aluminium).
7. **Fit around a contained or passing-through part** (any part given by its outside size: circuit board, pipe,
   module, cable gland, motor body, shaft housing): leave a clearance of 0.5 on every side (so each
   inside size or bore diameter is 1.0 larger than the part).
8. **Screw bosses** (plastic, thread-forming screws): a boss is a cylinder of outer diameter 2.5 × screw size, with a
   pilot hole of diameter 0.8 × screw size along its axis, open at the top and as deep as the boss is tall (it does
   not enter the floor). Bosses stand on the floor (or plate) and a stated boss height is measured from that surface.
   **Lid-screw bosses** stand one in each of the four inner corners of an enclosure:
   each boss touches both inner walls and reaches the top rim.
9. **Mounting slots** (adjustable fixing): an obround slot through the part, width = the screw's clearance hole
   (rule 3), overall length = width + 10, long side along X unless the request says otherwise.
10. **Lids** sit on the enclosure rim: a plate with the same outside X/Y size as the enclosure, thickness per rule 6,
    with a rectangular lip ring under it that goes into the enclosure opening. The lip's outside is the enclosure's
    inside minus 0.3 on every side (0.6 smaller in X and in Y); its walls have the rule-6 thickness and it is 4 tall. A lid is modelled upside
    down: the plate on Z = 0 to its thickness, the lip on top of it (rule 1).

## Further rules (NDS-1 sections 11-40)

**Materials and thickness**
11. **Steel** parts (only when the request says steel): walls, floors and plates 2.0 thick; corner holes (rule 5) are
    inset 1.5 × screw size instead of 2 ×.
12. **Sheet-metal** parts (only when the request says sheet metal): thickness 1.5, inside bend radius 1.5, and no
    counterbores; use countersinks (rule 16) instead.
13. **Aluminium enclosures and housings whose inside is deeper than 60** have walls and floor 5 thick instead of 4.
    Shallower ones keep rule 6.
14. **Plastic plates thinner than 3** never get counterbores; their socket-head screws get a plain clearance hole.
15. A **lid** is made of the same material as the enclosure it closes, unless the request names its material.

**Other fasteners**
16. **Countersunk screws** (only when the request says countersunk): 90° countersink from the top face, top
    diameter M3 → 6.3, M4 → 8.4, M5 → 10.4, M6 → 12.4; the clearance hole (rule 3) continues below.
17. **Tapped holes** (only when the request says tapped or threaded): drill diameter M3 → 2.5, M4 → 3.3, M5 → 4.2,
    M6 → 5.0, and no clearance hole.
18. **Heat-set inserts** (only when the request says insert): the boss pilot (rule 8) is replaced by a hole of
    M3 → 4.0, M4 → 5.6, M5 → 6.4, as deep as the boss is tall.
19. **Captive nuts** (only when the request says captive nut): a hexagonal pocket from the bottom face, across flats
    M3 → 5.7, M4 → 7.1, M5 → 8.1, depth equal to the nut height (M3 2.4, M4 3.2, M5 4.0).
20. **Press-fit pins** (only when the request says press-fit): hole diameter = pin diameter − 0.05.
21. **Washers** are not modelled; never add washer seats unless the request asks for them.

**Features made only on request**
22. **Ventilation slots** (only when the request asks for ventilation): a row of 2 × 15 slots on the long walls, 4
    apart, centred at half the inside height.
23. **Stiffening ribs** (only when the request asks for ribs): 0.6 × wall thickness, from the floor to 2 below the rim.
24. **Feet** (only when the request says with feet): four cylinders of diameter 8, 2 tall, under the floor, inset 6
    from both outer edges; the part then stands on the feet, so Z = 0 is the bottom of the feet.
25. **Edge fillets and chamfers** are not modelled unless the request gives their size.
26. **Draft** (only for parts the request calls injection-moulded): 1° on walls; otherwise walls are vertical.
27. **Engraved text or part numbers** are not modelled unless the request asks for them.
28. **Cable entries** (only when the request asks for a cable entry in a wall): a round hole in the shorter wall,
    diameter = cable diameter + 1, centred at half the inside height.
29. **Snap-fit hooks** and **hinges** are not modelled unless the request asks for them.
30. **Light pipes and display windows** (only when requested): a rectangular through-cut in the lid with 0.2
    clearance per side.

**Exceptions and limits**
31. **Bosses taller than 40** get four triangular gussets; bosses of 40 or less have none.
32. **Mounting slots longer than 30** have a 1 wide relief groove around them; shorter slots have none.
33. **Lids for enclosures whose inside is smaller than 20 in X or in Y** have a 3 tall lip instead of 4 (rule 10).
34. **Counterbores deeper than 90% of the material they are cut into** are not allowed; use a plain clearance hole
    instead (only then). A counterbore of 90% or less is made as rule 4 says.
35. **Corner holes in parts whose shorter side is less than 8 × screw size** (M4 → 32) move to the centre line;
    other parts keep rule 5.
36. **Plastic parts for outdoor use** (only when the request says outdoor): walls 3.5 instead of 2.5.
37. **Enclosures for batteries** (only when the request says battery): clearance 1.0 per side instead of rule 7's 0.5.

**Drawing and model conventions**
38. A model is one solid; separate parts (screws, boards, pipes, motors, modules) are never modelled, only the space
    they need.
39. Hole and boss positions given in a request are measured from the part's centre (rule 1), not from an edge,
    unless the request says "from the edge".
40. Where a request and this standard disagree, the request wins.
