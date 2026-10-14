# Sink organizer — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A parametric CadQuery script that generates print-ready STEP and STL files for a 7 x 8 in baseplate and six modules, with automated fit checks.

**Architecture:** One module, `sink_organizer.py`, holding a frozen `Params` dataclass, shared builders (socket plate, feet, ribbed shell, drip tray, perforated floor), one `make_*` function per part, a `LAYOUT` table placing modules on the grid, and a `main()` that exports. Every part is modelled z up in print orientation with its footprint centred on the origin. `tests/test_sink_organizer.py` checks geometry by boolean intersection and distance.

**Tech Stack:** Python 3.12 in the repo-root `.venv`, CadQuery 2.8, pytest.

**Spec:** `sink-organizer/docs/superpowers/specs/2026-10-12-sink-organizer-design.md`

## Global Constraints

- Grid pitch 25.4 mm, 7 x 8 cells, baseplate 177.8 x 203.2 mm.
- Module footprint (cells x 25.4) - 0.5 mm; foot-to-socket clearance 0.25 mm per side.
- PLA, 0.4 mm nozzle, 0.2 mm layers, no supports: no unsupported downward face flatter than 45 degrees.
- Walls at least 1.6 mm. No hardware.
- Every part fits the 256 x 256 mm bed.

## Review Focus

- Printer tolerance differs from the assumed clearances: each clearance is one named `Params` field, and the test plate, test foot and charger ring cover every fit.
- Module placed rotated 90 or 180 degrees, or elsewhere on the grid: feet are per-cell and symmetric, so it must still seat.
- Top put on its tray the other way round: tops and trays are symmetric under 180 degrees.
- Standing water: perforated floors sit above the tray floor on pads; the baseplate is open under every cell.
- Charger larger than published: recess dimensions are parameters and the test ring is printed first.

## File structure

- `sink-organizer/sink_organizer.py` — parameters, builders, parts, layout, export.
- `sink-organizer/tests/test_sink_organizer.py` — geometry tests.
- `sink-organizer/out/` — generated STEP and STL (ignored by git).

## Key dimensions (all `Params` fields)

| Item | Value |
|---|---|
| Pitch | 25.4 |
| Baseplate height | 4.0; socket depth 2.4 with 45 degree walls; through-hole under each cell |
| Foot | 2.4 tall, 45 degree chamfer, 0.25 clearance per side |
| Module gap | 0.5 total per footprint |
| Wall | 1.6 at the rib valleys; ribs add 1.2, pitch about 6.35 (four per cell) |
| Rib fade | over the top 14 mm, into a 6 mm smooth band; rim rounded 0.8 |
| Drip tray | 8 tall, pads 3 tall, top-to-tray lip clearance 0.3 |
| Drain holes | 4 mm; vent slots 4 wide x 6 tall |
| Charger recess | 52 x 42 oval, 0.6 clearance, 2 off; cord slot 8 wide |
| Bottle pocket | 80 square |

## Tasks

### Task 1: Grid, baseplate and feet

**Files:** create `sink_organizer.py`, `tests/test_sink_organizer.py`.

**Produces:** `Params`, `footprint(p, nx, ny) -> (w, d)`, `make_baseplate(p, nx=7, ny=8)`, `feet(p, nx, ny)`, `cell_origin(p, ix, iy, nx, ny)`.

- [ ] Tests: baseplate bounding box is 177.8 x 203.2 x 4.0; single valid solid; a 1 x 1 and a 4 x 3 foot block placed at any grid position do not intersect the plate and sit within 0.2 to 0.4 mm of the socket walls; the same block rotated 90 degrees still seats.
- [ ] Run tests, see them fail.
- [ ] Implement, run tests, see them pass.

### Task 2: Ribbed shell and one-piece modules

**Produces:** `ribbed_shell(p, nx, ny, height)` (outer solid with ribs, fade and rounded rim), `make_bottle_tray(p)`, `make_spare_tray(p)`, `overhang_area(shape)`.

- [ ] Tests: each is a single valid solid inside its footprint; bottle pocket holds an 76.2 mm square prism with clearance; `overhang_area` under 0.5 mm^2; rib count is four per cell on each side.
- [ ] Run, fail, implement, pass.

### Task 3: Two-part wet modules

**Produces:** `make_tray(p, nx, ny)`, `make_top(p, nx, ny, height)`, `make_brush_cup(p)`, `make_paste_cup(p)` each returning `(top, tray)`.

- [ ] Tests: top seated on tray does not intersect it; top floor is at least 2 mm above the tray floor; top lifts straight up without collision; top rotated 180 degrees still seats; drain-hole and vent-slot open area is non-zero; overhang check.
- [ ] Run, fail, implement, pass.

### Task 4: Electric holder and bar soap dish

**Produces:** `make_electric(p)` returning `(top, tray)`, `make_soap_dish(p)` returning `(grate, tray)`.

- [ ] Tests: two 52 x 42 x 20 charger blocks sit in the tray recesses without intersecting tray or top; a cord path of 5 mm diameter runs from each recess out through a slot on either long side; a 95 x 64 x 25 bar rests on the grate inside the dish; grate lifts out; overhang check.
- [ ] Run, fail, implement, pass.

### Task 5: Layout, test pieces and export

**Produces:** `LAYOUT`, `assembly(p)`, `test_parts(p)` (2 x 2 plate, 1 x 1 foot block, charger ring), `main()`.

- [ ] Tests: the default layout covers all 56 cells exactly once; no two placed modules intersect; no module intersects the plate; every part fits 256 x 256.
- [ ] Run, fail, implement, pass.
- [ ] Run `../.venv/bin/python sink_organizer.py`; confirm each STL is written and non-empty.
- [ ] Render preview images of the assembly and check them by eye.
