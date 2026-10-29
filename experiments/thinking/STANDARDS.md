# Nimbus Devices mechanical design standard NDS-1 (excerpt)

All Nimbus parts follow these rules unless a request says otherwise. Units are millimetres, Z is up.

1. **Placement.** A part's base (plate, floor or block bottom) lies on Z = 0 and is centred on the origin in X and Y,
   with its longest base side along X. Features "on top" point to +Z.
2. **Material.** Parts are plastic unless the request says aluminium.
3. **Clearance holes** for screws (through holes, normal fit): M3 → 3.4, M4 → 4.5, M5 → 5.5, M6 → 6.6 diameter.
4. **Counterbores** for socket-head screws, cut from the top face: M3 → diameter 6.5, depth 3.5; M4 → 8, depth 4.5;
   M5 → 10, depth 5.5; M6 → 11, depth 6.5. The clearance hole continues through the rest of the part.
5. **Corner holes.** When a part is fixed by four screws "at the corners", each hole centre is inset from both
   adjacent outer edges by twice the screw size (M4 → 8 from each edge).
6. **Walls.** Enclosures, housings and lids have walls, floors and plates of thickness 2.5 (plastic) or 4 (aluminium).
7. **Fit around a contained part** (circuit board, pipe, module): leave a clearance of 0.5 on every side.
8. **Screw bosses** (plastic, thread-forming screws): a boss is a cylinder of outer diameter 2.5 × screw size, with a
   pilot hole of diameter 0.8 × screw size along its axis, open at the top and as deep as the boss is tall (it does
   not enter the floor). Bosses stand on the floor. **Lid-screw bosses** stand in the inner corners of an enclosure:
   each boss touches both inner walls and reaches the top rim.
9. **Mounting slots** (adjustable fixing): an obround slot through the part, width = the screw's clearance hole
   (rule 3), overall length = width + 10, long side along X unless the request says otherwise.
10. **Lids** sit on the enclosure rim: a plate with the same outside X/Y size as the enclosure, thickness per rule 6,
    with a rectangular lip ring under it that goes into the enclosure opening. The lip's outside is the enclosure's
    inside minus 0.3 on every side; its walls have the rule-6 thickness and it is 4 tall. A lid is modelled upside
    down: the plate on Z = 0 to its thickness, the lip on top of it (rule 1).
