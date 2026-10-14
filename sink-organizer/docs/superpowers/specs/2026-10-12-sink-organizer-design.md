# Sink organizer design

## Revision 3 (2026-10-13)

This note supersedes Revision 2 and the body below where they differ.

- First printed version leaves out the mason jar holder. `make_jar_holder`
  stays in the script and is still tested, but it is not in the layout, the
  exports or the Studio project.
- Grid is 7 x 5 cells (177.8 x 127.0 mm).

```
            back
+-------------------+------------+
|     brush cup     |            |
|       4 x 2       | electric   |
+-------------------+   3 x 3    |
|     bar soap      +------------+
|       4 x 3       | toothpaste |
|                   |   3 x 2    |
+-------------------+------------+
            front
```

- Cup-top latch redesigned after the printed test did not catch. The old
  ridge stood 0.6 mm proud, a 0.3 mm grip, on a 5 mm tab. The new one stands
  1.3 mm proud, a 1.0 mm grip, 16 mm wide, on a leaf 1.0 mm thick that runs
  from the cup floor up the inside of the cup wall and joins it 13 mm up.
  The extra length is what lets it bend a full millimetre (about 1.2%
  strain). The tray groove is deepened to match.
- Foot latch redesigned for the same reason, after the user reported the
  baseplate click was just as weak. Ridge 1.0 mm proud (0.8 mm grip), 10 mm
  wide, on a leaf 0.8 mm thick that runs 8 mm up inside the module's base in
  closed pockets, so trays stay watertight. To make room, module floors moved
  up 2.2 mm (floor at 12.5 mm) and the cup-top spigot is 2.2 mm shorter; rim
  heights are unchanged.
- Baseplate bars widened from 2.4 to 3.4 mm so a 1.4 mm web is left between
  the deeper grooves; sockets are 22.0 mm and feet 21.6 mm. Latches face the
  full-width bars inside a module's footprint, not the half bar at the
  plate's edge.
- New `test_plate_1x1` and a shorter `test_module_1x1`: about 7 g and 13
  minutes to check the baseplate click.
- Colours: grey baseplate, trays and lips; white ribbed sections. Parts are
  exported in bands so the Studio project shows the colours directly.

## Revision 2 (2026-10-13)

This note supersedes the grid, module table and layout below where they differ.

- Grid extended to 7 x 9 cells (177.8 x 228.6 mm).
- Baseplate 7 mm tall. Sockets are straight-walled and 5.4 mm deep with 0.2 mm
  clearance per side, with a latch groove right round each socket.
- Snap latches hold everything together against a sideways push at the top:
  each corner foot of a module has a flexible tab that clicks into the socket
  groove (0.2 mm grip), and each cup top has two tabs that click into its tray
  (0.3 mm grip). Geometry checks showed deep sockets alone do not stop a
  narrow cup tipping out. Latch forces are estimates until printed.
- The cup seat moved up, so the smooth base is about 15 mm tall.
- The soap bottle tray is replaced by a holder for two wide-mouth mason jars,
  7 x 4 cells, solid with no drain holes, sitting directly on the grid. Jar
  size assumed: 83 mm glass. Both pockets are the same depth (30 mm) at the
  user's request. The centres are 88.8 mm apart, the most a 7 in plate
  allows, so lids wider than that touch. `Params.jar_step` raises one pocket
  if that turns out to matter.
- One charger instead of two: the electric holder is 3 x 3 (a charger is
  too wide for two cells). `Params.chargers = 2` still builds the 4 x 3
  version.
- Brush cup is 4 x 2 (about 91 x 40 mm inside) and toothpaste cup 3 x 2
  (about 65 x 40 mm inside). Bar soap dish is 4 x 3. No spare tray.

```
            back
+-------------------+------------+
|     brush cup     |            |
|       4 x 2       | electric   |
+-------------------+   3 x 3    |
|     bar soap      +------------+
|       4 x 3       | toothpaste |
|                   |   3 x 2    |
+-------------------+------------+
|       two mason jars  7 x 4    |
|                                |
+--------------------------------+
            front
```

## Goals

- Cover a 7 x 8 in (177.8 x 203.2 mm) area of the counter with one baseplate.
- Hold manual toothbrushes, an Oral-B electric toothbrush on its charger, a
  3 x 3 in soap bottle, a bar of soap and a tube of toothpaste.
- Keep the layout flexible: any module fits anywhere on the grid.
- Vertical ribs with a smooth taper at the top as the shared look.
- Toothbrush and toothpaste modules split into a top and a base for cleaning,
  with openings so water drains and dries.

## Grid

- Pitch 25.4 mm, 7 x 8 cells. Chosen over the standard 42 mm Gridfinity pitch
  because it fills the area exactly and gives finer module sizes. Published
  Gridfinity bins do not fit.
- Baseplate: 177.8 x 203.2 mm, about 4 mm tall, one piece. Each cell is a
  chamfered socket (45 degree walls), open through to the counter so water
  cannot pool in the plate.
- Module foot: one chamfered foot per cell, matching the socket with 0.25 mm
  clearance per side.
- Module footprint: (cells x 25.4) - 0.5 mm in each direction, corners rounded.

## Shared style

Revised after the user supplied a reference photo of a reeded toothbrush caddy.

- Fine reeding: touching round ribs at about 3 mm pitch and 0.8 mm deep,
  running right round the corners.
- Corner radius 12 mm, reduced automatically on modules narrower than two
  cells.
- A smooth lip 7 mm tall at rib-crest level, with a 1.2 mm rounded rim. The
  grooves close under the lip at 45 degrees.
- A smooth base about 11 mm tall: the drip tray on two-part modules, and a
  matching smooth band on one-piece modules, so one line runs across the set.
- Walls 2.0 mm in the grooves and 2.8 mm at the ribs and lip.
- Vents are a row of small openings just above the tray, in every other
  groove.
- No face flatter than 45 degrees, so every part prints upright without
  supports.

## Two-part wet modules

Used for the brush cup, electric holder and toothpaste cup.

- Base: a shallow drip tray that carries the feet.
- Top: a ribbed sleeve with a perforated floor, resting on raised pads in the
  tray so the floor sits above any collected water.
- Vent slots between the ribs at the bottom edge of the top.
- The top locates on the tray by a loose lip (0.3 mm clearance) and lifts
  straight off; there is no latch.

## Modules

| Module | Cells | Height | Parts | Notes |
|---|---|---|---|---|
| Brush cup | 3 x 2 | about 100 mm | top + tray | Open cup, about 70 x 45 mm inside |
| Electric holder | 4 x 3 | about 45 mm collar | top + tray | Two Oral-B chargers, about 52 x 42 mm each, side by side along the 4-cell side. They stand on the tray floor and are located by two openings in the collar's floor. A cord slot per charger on both long sides. |
| Toothpaste cup | 3 x 2 | about 90 mm | top + tray | Tube stands cap-down |
| Soap bottle tray | 4 x 4 | about 30 mm | one piece | About 80 mm square pocket for a 76.2 mm bottle |
| Bar soap dish | 3 x 4 | about 25 mm | grate + tray | Lift-out slatted grate; about 72 x 98 mm inside |
| Spare tray | 4 x 1 | about 20 mm | one piece | Floss, razor |

As built, the electric holder has no pegs for spare brush heads: two chargers
leave about 6 mm of floor at each end, which is not enough. Its tray drains
through the cord slots instead of holding water, so the chargers do not stand
in a puddle.

The soap bottle tray has solid walls (about 9 mm) around its 80 mm pocket;
print it with sparse infill.

The electric holder was widened from 3 x 3 to 4 x 3 to take two chargers
(two 42 mm widths do not fit the 70 mm inside a 3 x 3). The brush cup gave up
one row to make room.

Default layout (fills all 56 cells). The top of the diagram is the back of
the counter: the tall brush cup stands behind the toothpaste cup, and the
charger cords leave over the back edge.

```
+----------------+------------+
|  electric x2   | brush cup  |
|     4 x 3      |   3 x 2    |
|                +------------+
+----------------+ toothpaste |
|  spare  4 x 1  |   3 x 2    |
+----------------+------------+
|  soap bottle   |  bar soap  |
|     4 x 4      |   3 x 4    |
|                |            |
+----------------+------------+
```

## Code layout

- `sink-organizer/sink_organizer.py`: CadQuery script with a `Params`
  dataclass, shared builders (baseplate, foot, ribbed shell, drip tray) and one
  function per module. Writes STEP and STL files to `sink-organizer/out/`.
- `sink-organizer/tests/test_sink_organizer.py`: pytest geometry checks.
- Uses the existing `.venv` at the repo root.

## Checks

- Every part is a single valid solid.
- Every module seats in the baseplate with no interference and clearance of
  at least 0.2 mm.
- The default layout fills the plate with no module overlapping another.
- Tops seat on their trays with no interference.
- The bottle pocket, charger recess and bar soap dish are at least as large
  as the items they hold.
- No unsupported overhang flatter than 45 degrees.
- Every part fits the 256 x 256 mm bed.

## Unverified until printed

- The Oral-B charger recess is taken from published dimensions. A small test
  ring is exported so it can be checked before printing the full holder.
- Socket and foot clearance; a 2 x 2 test plate and a 1 x 1 test foot are
  exported for the same reason.
