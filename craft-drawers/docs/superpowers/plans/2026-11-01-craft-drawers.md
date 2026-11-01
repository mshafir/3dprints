# Craft drawers — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A parametric CadQuery script that generates print-ready STEP and STL
files for a four-drawer craft chest, 8 in wide, with a key-operated lock rod
that holds all four drawers, plus geometry tests and a multi-colour Bambu
Studio project.

**Architecture:** One module, `craft_drawers/craft_drawers.py`, in the repo's
usual shape: a frozen `Params`, size helpers, solid helpers copied from
`frame/frame.py`, one builder per part, print-orientation functions, and
`main()` to export. Every part is modelled where it sits in use; the tests
check fits there and print checks on the turned parts. `make_3mf.py` follows
`pill-case/make_3mf.py` (several filaments).

**Tech Stack:** Python 3.12 via uv, CadQuery 2.8, pytest, Bambu Studio 2.8 CLI.

**Spec:** `craft-drawers/docs/superpowers/specs/2026-11-01-craft-drawers-design.md`
(read Revision 1 first: it moves the rod to the front and the cover to the top)

## Global Constraints

- P1S, 0.4 mm nozzle, PLA, 0.2 mm layers, no supports: no downward face
  flatter than 45 degrees except the planned bridges listed by `bridge_zones()`.
- Every part within 250 x 250 x 250 mm in its print orientation (`P.bed`).
- Outside 203.2 mm wide; depth including pulls at most 203.2 mm.
- Hardware: two M3 screws for the lock badge, optional stick-on bumpers.
- Inside each drawer a 180 x 8 x 8 mm pencil lies front to back.
- Frame outside closed: only the front opening, the badge slot (covered) and
  the keyhole (closed below by the rod head).
- Plastic target about 1 kg for frame plus four drawers.

## Coordinates and key numbers

Use coordinates: x across (0 at the centre, +x is the lock side, the right
seen from the front), y front to back (y = 0 is the frame's front face, +y
goes into the frame), z up (z = 0 is the bottom). Every builder returns the
part in place, with the drawers closed and the rod at a given angle. Rod angle
is the direction the cams point, in degrees counter-clockwise from +x seen
from above: `LOCKED = 180` (cams point -x, at the drawers) and
`UNLOCKED = 270` (cams point -y, forward).

`Params` (all mm), with the derived values the plan relies on:

| Group | Fields |
|---|---|
| Outside | `width 203.2`, `depth 184.0`, `height 248.0`, `side 1.8`, `cap 2.0` (top and bottom), `back 1.2`, `edge_r 3.0` (outside vertical edges) |
| Bays | `bays 4`; pitch = (height - 2 cap) / 4 = 61.0; bay i floor `z_i = cap + i * pitch` |
| Ledges | `ledge_t 1.6`, `ledge_under 6.0` (how far under the drawer), `head_gap 1.0` (drawer top to the next ledge) |
| Drawer | `gap_left 2.0`, `column 16.0` (drawer's right wall to the frame's right inner face), `wall 1.2`, `floor 1.2`, `back_clr 1.0`, `front_t 2.4`, `front_gap 1.0`, `front_r 4.0` |
| Pulls | `pull_size 34.0`, `pull_proud 14.0`; shapes `("circle", "triangle", "square", "star")` for drawers 0 to 3, bottom up |
| Lock | `rod_r 3.5`, `rod_dx 9.0` (rod axis from the drawer's right wall), `rod_y 13.0`, `stile 2.0` (front post), `cam_r 8.5`, `cam_w 6.0`, `cam_h 5.0`, `cam_z 24.5` (cam bottom above drawer floor underside), `fin_reach 4.0`, `fin_z 20.0`, `fin_h 10.0`, `lock_clr 0.5`, `fork_clr 0.3` |
| Head | `head_r 4.7`, `head_len 5.0`, `flange_r 5.5`, `flange_t 1.0`, `bore_r 5.0`, `tube_wall 1.3`, `tube_len 16.0`, `socket_depth 5.0`, `key_depth 17.0` (badge top to socket mouth), `pin_depth 4.0`, `boss_h 4.0` (floor boss) |
| Socket | `hub_r 1.5`, `lobe_r 1.0`, `lobe_at 2.2`, `key_clr 0.15` |
| Detent | as in `frame.py`: `det_press 0.7`, `nub_r 1.0`, `notch_r 1.1`; leaf 4.0 wide, the length of the tube below the top wall |
| Badge | `badge_t 3.0`, x from 76.0 to 101.0, y from -1.0 to 33.0, 45 degree 1.0 chamfer on top; screws at (88.0, 3.0) and (95.0, 27.5); `screw_pilot 2.6`, `screw_clear 3.4`, `cbore_r 3.25`, `cbore_d 1.8`, `boss_r 3.5`, `boss_len 10.0` |
| Stop | `leaf_w 10.0`, `leaf_slit 0.6`, `leaf_back 4.0` (leaf's back edge ahead of the inside of the drawer's back wall), `nub_out 1.2`, `nub_h 6.0`, `nub_top 4.0` (nub top below the wall top), `rail_out 1.5`, `stop_frac 2/3` |
| Dividers | `div_t 1.4`, `rib 1.0`, `rib_w 1.2`, slot 1.8 wide at x offsets (-45, 0, 45) from the drawer's centre |
| Decor | `decor_depth 0.6`, `decor_size 30.0`; bumper recesses `bump_r 6.0`, `bump_d 0.8`, inset 15.0 |
| Print | `bed 250.0` |

Derived (implement as functions in Task 1; tests use these names):

- inside width 199.6; drawer box x from -97.8 to 83.8 (183.6 wide); drawer box
  y from 0 to `depth - back - back_clr` = 181.8, inside length 180.6.
- drawer height `pitch - ledge_t - head_gap` = 58.4, from `z_i + ledge_t`.
- front plate y from -2.4 to 0, 202.2 x 60.0, centred on the bay. Pulls make
  the total depth 2.4 + 14 + 184 = 200.4.
- rod axis x = 83.8 + 9.0 = 92.8, y = 13.0. Locked cam tip x = 84.3, 0.5 mm
  clear of the drawer wall, overlapping the fin (to 87.8) by 3.5 mm. Unlocked
  cam spans x 89.8 to 95.8, 2.0 mm clear of the fin. Unlocked cam tip
  y = 4.5, 2.5 mm behind the stile.
- fin notch: the fin is absent for y < `rod_y + cam_w / 2 + lock_clr` = 16.5.
  Behind that, the fin (the tab) runs to the drawer's back.
- cam z for drawer i: `z_i + ledge_t + cam_z` to `+ cam_h`. The fin's vertical
  tip face covers `fin_z + 4` to `fin_z + fin_h` above the drawer underside,
  and its underside is a 45 degree chamfer.
- travel to the stop = `stop_frac` x 181.8 = 121.2.
- rod z from `cap + boss_h - pin_depth` + 0.3 to the socket mouth at
  `height + badge_t - key_depth` = 234.0. The head runs from 229.0 to 234.0,
  and the flange from 228.0 to 229.0. The tube runs from z 232.0 to 248.0
  (the badge underside).

## Review Focus

1. **Key turned with a drawer ajar by 1 to 5 mm.** The rod must stop, not
   slip past the tab's corner. Task 4 adds a test at t = 1, 2, 5 (at 0.5 mm the tab only just touches the cam, which is the lock clearance).
2. **A child yanks a locked drawer hard.** The cam load bends the rod between
   supports. A fork (a notched ledge) must be within half a pitch of every
   cam, and the stile must sit directly ahead of the rod. Task 4 adds the test.
3. **A pencil pushed down the keyhole.** The bore is 10 mm, so a pencil fits.
   It must stop on the rod head and not pass into the frame. Task 4 adds the
   test.
4. **Rod dropped in at the wrong angle, or upside down.** It must not go in
   at any angle but the insertion angle (LOCKED), and the head end does not
   fit through a fork. Task 4 adds the test.
5. **A drawer pushed back in while the rod is locked.** The tab meets the cam
   and the drawer stops about 16 mm short of closed. That is expected: unlock,
   push it shut, lock again. Task 4 adds a test that confirms the stop and
   that nothing overlaps at the unlocked angle.

---

### Task 1: Scaffold, sizes and helpers

**Files:**
- Create: `craft-drawers/craft_drawers.py`
- Create: `craft-drawers/tests/test_craft_drawers.py`

**Interfaces:**
- Produces: `Params`, `P`, `LOCKED`, `UNLOCKED`, `SHAPES`;
  `pitch(p) -> float`, `bay_z(i, p) -> float`,
  `drawer_box(p) -> (x0, x1, y0, y1, h)` (closed, without the front plate),
  `drawer_z(i, p) -> float` (drawer underside), `inside(p) -> (w, l, h)`,
  `rod_xy(p) -> (x, y)`, `cam_span(i, p) -> (z0, z1)`,
  `travel_stop(p) -> float`, `outside(p) -> (w, d_with_pulls, h_with_badge)`;
  helpers `box, cyl, rprism, prism, combo, cut_all, turn, overhang_area, grams`
  copied unchanged from `frame/frame.py`; `shape_pts(name, size) -> list[(x, y)] | None`
  (None for the circle), a polygon centred on 0. The star has 5 points, inner
  radius 0.42 x outer.

- [ ] **Step 1: Write the failing tests**

```python
def test_outside_fits_shelf_and_bed():
    w, d, h = cd.outside()
    assert w == pytest.approx(203.2)
    assert d <= 203.2
    assert P.height <= P.bed

def test_inside_holds_a_pencil():
    w, l, h = cd.inside()
    assert l >= 180.0 and w >= 178.0 and h >= 50.0

def test_lock_geometry_numbers():
    x, y = cd.rod_xy()
    x1 = cd.drawer_box()[1]
    assert x - P.cam_r - x1 == pytest.approx(P.lock_clr)       # locked cam tip clear of the wall
    assert x - P.cam_w / 2 - (x1 + P.fin_reach) >= 1.5          # unlocked cam clear of the fin
    assert y - P.cam_r - P.stile >= 1.5                         # unlocked cam clear of the stile

def test_travel_stop():
    assert cd.travel_stop() == pytest.approx(cd.drawer_box()[3] * 2 / 3)
```

- [ ] **Step 2: Run them and see them fail**

Run: `cd craft-drawers && uv run pytest tests -q`
Expected: FAIL. `craft_drawers` cannot be imported.

- [ ] **Step 3: Implement the Params, sizes and helpers listed above.**
  The module docstring states the coordinates and the run command, in the
  style of `frame.py`.

- [ ] **Step 4: Run the tests and see them pass**

Run: `cd craft-drawers && uv run pytest tests -q`
Expected: 4 passed.

- [ ] **Step 5: Commit** with message `Craft drawers: sizes and helpers`

### Task 2: Frame

**Files:** Modify `craft_drawers.py` and the test file.

**Interfaces:**
- Consumes: Task 1.
- Produces: `make_frame(p) -> Workplane`; `frame_print(part, p)` (turned onto
  its back: rotate so +y becomes -z, back face at z = 0);
  `bridge_zones(p) -> list[Workplane]` (frame coordinates, in the frame's own
  print orientation once turned); `badge_slot(p) -> (x0, x1, y0, y1)`.

The frame is a box with rounded vertical edges (`edge_r`), open at the front.
It has:

- **Ledges.** One left and one right ledge for each bay, `ledge_t` tall, at
  `z_i`, from y = 0 to `depth - back`. The left ledge runs from the wall to
  `ledge_under` under the drawer. The right ledge spans the whole column plus
  `ledge_under`.
- **Forks.** Each right ledge for bays 1 to 3 has a notch round the rod,
  open toward -x. The notch runs from `rod_x + rod_r + fork_clr` out to the
  ledge's left edge, and spans `rod_y ± (rod_r + fork_clr)`. Bay 0 has no
  ledge notch, because the floor boss holds the rod.
- **Floor boss.** It sits on the floor at the rod axis, radius `rod_r + 2`,
  `boss_h` tall, with a blind hole of radius `rod_r + fork_clr` and depth
  `pin_depth`.
- **Stile.** A front post, `stile` thick (y 0 to 2), across the column from
  the drawer's right wall line to the right inner face, full inside height.
- **Stop rails.** One on the left inner face for each bay, `rail_out` proud,
  `nub_h` tall, at the nub's height, from y = 0.5 to the stop y (the nub's
  closed front y minus `travel_stop`). Its front end has a 45 degree ramp in
  plan. Its back end is square and is a planned overhang in `bridge_zones`.
- **Top slot.** x from `drawer_x1` to `rod_x + bore_r + tube_wall + 0.3`, y
  `rod_y ± (bore_r + tube_wall + 0.3)`, through the top wall. Two screw
  bosses hang from the top wall, `boss_r`, `boss_len` long, each with a
  `screw_pilot` hole. They are clipped to the frame's inside and merged with
  the stile or side wall where they touch.
- **Decor.** Four recessed shapes per side, one of each, `decor_size`,
  `decor_depth` deep, with 45 degree walls. Four bumper recesses under the
  base.

- [ ] **Step 1: Write the failing tests**

```python
@pytest.fixture(scope="module")
def frame(): return cd.make_frame()

def test_frame_fits_bed_on_its_back(frame):
    assert max(size(cd.frame_print(frame))) <= P.bed

def test_frame_outside_closed(frame):
    # only the front opening, the slot and nothing else: the frame's bounding
    # box minus the frame, minus the front opening's prism and the slot's prism, has
    # no part that touches the outside of the box
    assert cd.outside_openings(frame) == ["front", "slot"]

def test_frame_prints_without_supports(frame):
    assert cd.overhang_area(cd.frame_print(frame), allow=[cd.frame_print(z) for z in cd.bridge_zones()]) < 5.0

def test_fork_near_every_cam(frame):
    for i in range(P.bays):
        z0, z1 = cd.cam_span(i)
        assert min(abs((z0 + z1) / 2 - zf) for zf in cd.fork_zs()) <= cd.pitch() / 2 + 1
```

  `outside_openings(frame) -> list[str]` is a test helper in the module. It
  probes with thin slabs just inside each outer face and reports a face whose
  slab is not fully inside the frame. The left and right decor recesses are
  shallower than the slab offset, so they don't count. `fork_zs(p) -> list[float]`
  returns the fork mid-heights plus the floor boss top.

- [ ] **Step 2: Run and see them fail**: `uv run pytest tests -q -k frame or fork`
- [ ] **Step 3: Implement `make_frame`, `frame_print`, `bridge_zones`, `badge_slot`, `outside_openings`, `fork_zs`.**
- [ ] **Step 4: Run and see them pass.**
- [ ] **Step 5: Commit** with message `Craft drawers: frame`

### Task 3: Drawers and dividers

**Files:** Modify `craft_drawers.py` and the test file.

**Interfaces:**
- Consumes: Tasks 1 and 2.
- Produces: `make_drawer(i, p, pressed=False) -> Workplane` (closed, in bay
  i; `pressed=True` builds the stop leaf bent in by `nub_out + 0.2`);
  `drawer_at(i, t, p, pressed=False)` (moved by -t in y);
  `drawer_print(part, i, p)` (upright, floor on the bed);
  `make_divider(p)`, `divider_print(part, p)`; `nub_front_y(p) -> float`.

The drawer is an open box (`wall`, `floor`) with:

- **Front plate.** `front_t` thick, with the plate's corners rounded
  `front_r`.
- **Pull.** The shape from `SHAPES[i]`, extruded `pull_proud` forward, with
  its underside cut back at 45 degrees from the plate so it prints upright.
- **Fin.** On the outside of the right wall, from y = 16.5 to the back. Its
  profile is a 45 degree chamfer from the wall at `fin_z` out to `fin_reach`
  at `fin_z + 4`, then vertical to `fin_z + fin_h`.
- **Stop leaf.** In the left wall, `leaf_w` wide, its back edge `leaf_back`
  ahead of the back wall's inside, cut free by two vertical `leaf_slit` slits
  from the floor top to the wall top, so it springs from the floor. The nub
  stands on the leaf's outside, `nub_out` proud, `nub_h` tall, its top
  `nub_top` below the wall top. Its front face is flat, its back face has a
  45 degree ramp in plan, and its underside has a 45 degree chamfer.
- **Divider ribs.** On the inside of the front and back walls, a pair of ribs
  per slot.
- **Divider.** `div_t` thick, inside length minus 2 x (`rib` + 0.3) long,
  inside height minus 6 tall, with rounded top corners. Printed flat.

- [ ] **Step 1: Write the failing tests**

```python
@pytest.fixture(scope="module")
def drawers(): return [cd.make_drawer(i) for i in range(P.bays)]

def test_pencil_fits(drawers):
    x0, x1, y0, y1, h = cd.drawer_box()
    pencil = cd.box(-4, 4, P.wall + P.rib + 0.5, P.wall + P.rib + 180.5, 0, 8).translate((0, 0, cd.drawer_z(0) + P.floor + 0.1))
    assert overlap(drawers[0], pencil) < EPS

def test_drawers_fit_closed(frame, drawers):
    for d in drawers:
        assert overlap(frame, d) < EPS
    for a, b in zip(drawers, drawers[1:]):
        assert overlap(a, b) < EPS

@pytest.mark.parametrize("t", [10, 40, 80, 120])
def test_drawer_slides_to_stop(frame, drawers, t):
    assert overlap(frame, cd.drawer_at(1, t)) < EPS

def test_stop_holds_and_releases(frame):
    t = cd.travel_stop() + 1.0
    assert overlap(frame, cd.drawer_at(1, t)) > EPS
    for t in (cd.travel_stop() + 1, 150, 175):
        assert overlap(frame, cd.drawer_at(1, t, pressed=True)) < EPS

def test_pull_shapes_differ():
    assert len(set(cd.SHAPES)) == P.bays == 4

def test_divider_fits(drawers):
    assert overlap(drawers[0], cd.divider_in(0, slot=1)) < EPS

def test_drawer_and_divider_print(drawers):
    for i, d in enumerate(drawers):
        part = cd.drawer_print(d, i)
        assert max(size(part)) <= P.bed
        assert cd.overhang_area(part) < 5.0
    assert cd.overhang_area(cd.divider_print(cd.make_divider())) < 1.0
```

  `divider_in(i, slot, p)` places a divider in drawer i's slot (0 to 2).
- [ ] **Step 2: Run and see them fail.**
- [ ] **Step 3: Implement.** If insertion is blocked anywhere other than the
  ramped rail, the nub's ramp or the rail's front ramp is wrong.
  `test_drawer_slides_to_stop` covers withdrawal only. Insertion runs the same
  path, with the nub pressed over the rail's length.
- [ ] **Step 4: Run and see them pass.**
- [ ] **Step 5: Commit** with message `Craft drawers: drawers, pulls, stop and dividers`

### Task 4: Lock rod, badge and key

**Files:** Modify `craft_drawers.py` and the test file.

**Interfaces:**
- Consumes: Tasks 1 to 3.
- Produces: `make_rod(angle, p) -> Workplane` (in place, cams pointing at
  `angle`); `make_badge(p)` (badge, tube and detent leaf, in place on top);
  `make_key(angle, p)` (in place with its tip seated in the socket);
  `rod_print`, `badge_print`, `key_print`; `socket_pts(p, grow=0.0)` (the
  tri-lobe outline, made with `hub_r`, `lobe_r` and `lobe_at`).

The parts are:

- **Rod.** A cylinder `rod_r`. Its bottom pin sits in the floor boss, and it
  has one cam per drawer at `cam_span(i)`: a slab `cam_w` wide reaching
  `cam_r` from the axis, with the outer end rounded. At the top are the
  flange and the head. The head has a tri-lobe socket `socket_depth` deep and
  two vertical detent notches (`notch_r`, deep enough that the nub rests in them untouched, about `det_press + 0.1`) at the angles that face the nub
  when locked and unlocked. The nub is on the tube's -y side, so the notches
  are at +90 degrees and 0 degrees from the cam direction. A flat on the side
  opposite the cams (truncated at 0.7 x radius along the whole rod and head)
  makes it print lying cams-up with no overhang. The flat is clear of both
  notches.
- **Badge.** A rounded plate with chamfered edges. It has the bore, the
  counterbored screw holes, and the tube with an `bore_r` bore and
  `tube_wall` wall, which ends 2 mm into the head's height. The leaf is cut
  by two vertical slits in the tube wall at -y, free at the bottom, and the
  nub (`nub_r`) reaches `det_press` past the head's radius. Locked and
  unlocked icons are recessed 0.6 mm beside the bore: a closed padlock at the
  key-pointer direction for LOCKED, an open padlock for UNLOCKED. It prints
  top face down.
- **Key.** A grip disc 4 mm thick in a fun shape (`star`, 36 mm across) with
  a 5 mm keyring hole and a raised pointer arrow on top aligned with the cam
  direction. The shaft has radius `bore_r - 0.4`, and the tip is the socket
  outline grown by `-key_clr` and `socket_depth - 0.2` long. The shaft is
  long enough that the tip seats with the grip resting 1 mm above the badge.
  It prints grip down. `make_3mf` prints two.

- [ ] **Step 1: Write the failing tests**

```python
def test_locked_holds_every_drawer(frame, drawers):
    rod = cd.make_rod(cd.LOCKED)
    assert overlap(frame, rod) < EPS
    for i in range(P.bays):
        assert overlap(rod, drawers[i]) < EPS
        assert overlap(rod, cd.drawer_at(i, 1.0)) > EPS

@pytest.mark.parametrize("t", [1, 2, 5, 40, 120])
def test_open_drawer_blocks_locking(t):
    assert overlap(cd.make_rod(cd.LOCKED), cd.drawer_at(2, t)) > EPS

def test_unlocked_frees_every_drawer(frame):
    rod = cd.make_rod(cd.UNLOCKED)
    assert overlap(frame, rod) < EPS
    for i in range(P.bays):
        for t in (0, 60, 120):
            assert overlap(rod, cd.drawer_at(i, t)) < EPS

def test_turn_is_clear_with_drawers_shut(frame, drawers):
    for a in range(180, 271, 10):
        rod = cd.make_rod(a)
        assert overlap(frame, rod) < EPS
        assert all(overlap(rod, d) < EPS for d in drawers)

def test_reinserting_while_locked_stops_short():
    rod = cd.make_rod(cd.LOCKED)
    assert overlap(rod, cd.drawer_at(0, 17.0)) > EPS     # tab meets the cam
    assert overlap(cd.make_rod(cd.UNLOCKED), cd.drawer_at(0, 17.0)) < EPS

def test_rod_drops_in_only_at_insertion_angle(frame):
    for dz in range(0, 260, 10):
        assert overlap(frame, cd.make_rod(cd.LOCKED).translate((0, 0, dz))) < EPS
    dz = cd.pitch() - P.cam_z - P.cam_h / 2 - P.ledge_t / 2      # cams level with the forks above
    assert overlap(frame, cd.make_rod(cd.UNLOCKED).translate((0, 0, dz))) > EPS

def test_badge_covers_slot_and_seats(frame):
    badge, rod = cd.make_badge(), cd.make_rod(cd.LOCKED)
    assert overlap(frame, badge) < EPS and overlap(badge, rod) < EPS   # nub rests in a notch
    x0, x1, y0, y1 = cd.badge_slot()
    assert cd.covers(badge, x0, x1, y0, y1, z=P.height + 0.5)

def test_detent_presses_between_positions():
    badge = cd.make_badge()
    assert overlap(badge, cd.make_rod(cd.UNLOCKED)) < EPS
    assert overlap(badge, cd.make_rod(225)) > EPS

def test_key_fits_and_drives():
    rod = cd.make_rod(cd.LOCKED)
    assert overlap(rod, cd.make_key(cd.LOCKED)) < EPS
    assert overlap(rod, cd.make_key(cd.LOCKED + 5)) > EPS

def test_keyhole_depth_and_seal():
    assert P.key_depth >= 15.0 and 2 * P.bore_r < 17.0            # no fingertip, no coin
    pencil = cd.cyl(3.6, 200, 260, *cd.rod_xy())
    assert overlap(pencil, cd.make_rod(cd.LOCKED)) > EPS          # stops on the head

@pytest.mark.parametrize("af", [2.5, 3.0, 4.0, 5.0, 6.0])
def test_hex_keys_do_not_drive(af):
    rod = cd.make_rod(cd.LOCKED)
    hits = [overlap(rod, cd.hex_key(af, a)) > EPS for a in range(0, 60, 5)]
    assert all(hits) or not any(hits)

def test_lock_parts_print():
    for part in (cd.rod_print(cd.make_rod(cd.LOCKED)), cd.badge_print(cd.make_badge()), cd.key_print(cd.make_key(cd.LOCKED))):
        assert max(size(part)) <= P.bed
        assert cd.overhang_area(part) < 5.0
```

  These are module helpers. `hex_key(af, angle, p)` is a hex prism, with
  across-flats size `af`, placed at the rod axis and reaching to the socket
  floor. `covers(part, x0, x1, y0, y1, z)` is True when the part's section
  at height z covers that rectangle.
- [ ] **Step 2: Run and see them fail.**
- [ ] **Step 3: Implement.** The hex test decides whether a hex can sit in
  the socket at only some angles. If one does, enlarge the lobes or shrink the
  hub until every hex either doesn't fit or turns freely.
- [ ] **Step 4: Run and see them pass.**
- [ ] **Step 5: Commit** with message `Craft drawers: lock rod, badge and key`

### Task 5: Exports, fit test, weight and stability

**Files:** Modify `craft_drawers.py` and the test file.

**Interfaces:**
- Consumes: Tasks 1 to 4.
- Produces: `fit_test_parts(p) -> dict[str, Workplane]` (`test_corner`, the
  frame cropped to x 70 to 101.6, y 0 to 36, z 220 to 248, on its back;
  `test_rod`, the rod cropped to z 215 and above, printed lying), the badge
  and a key are reused; `tip_margin(p) -> float`; `main(out)`.

- [ ] **Step 1: Write the failing tests**

```python
def test_weight_budget(frame, drawers):
    total = cd.grams(frame) + sum(cd.grams(d) for d in drawers)
    assert total < 1150

def test_does_not_tip_with_top_drawer_out():
    # top drawer at its stop holding 300 g at its centre: moment about the
    # frame's front bottom edge stays positive
    assert cd.tip_margin(load=300.0, drawer=3) > 0

def test_fit_test_parts_fit():
    for part in cd.fit_test_parts().values():
        assert max(size(part)) <= P.bed
```

- [ ] **Step 2: Run and see them fail.**
- [ ] **Step 3: Implement `tip_margin`, `fit_test_parts` and `main`.**
  `tip_margin` takes the frame's and the closed drawers' centres of mass
  (from `Volume` and `Center`), plus the open drawer and its load at its
  centre, all as weights. It returns the moment, in g·mm, about the frame's
  front bottom edge (y = 0, z = 0). `main` writes an `assembly.step` (locked,
  coloured), then each print part as STEP and STL, and prints the size and
  weight per part plus the total, like `frame.main`. The STL names are
  `frame`, `drawer_0` to `drawer_3`, `divider`, `rod`, `badge`, `key`,
  `test_corner`, `test_rod`.
- [ ] **Step 4: Run all tests and `uv run craft_drawers.py`.** Expect every
  test to pass, and the exports in `out/` with a total under 1150 g.
- [ ] **Step 5: Commit** with message `Craft drawers: exports, weight and stability`

### Task 6: Bambu Studio project and README

**Files:**
- Create: `craft-drawers/make_3mf.py`
- Modify: `README.md` (projects table: `craft-drawers/`, "Four-drawer craft chest for an 8 in shelf with a printed key that locks every drawer", "Designed; not yet printed")

**Interfaces:**
- Consumes: the STL names from Task 5.

Copy `pill-case/make_3mf.py` and adapt it. The process name is
`0.20mm Craft Drawers`, and the overrides are:

- `wall_loops` 2, `sparse_infill_density` 10%, `sparse_infill_pattern` gyroid
- `enable_support` 0, `brim_type` no_brim, `enable_prime_tower` 0
- `wall_generator` arachne

The filaments are:

| Slot | Colour | Parts |
|---|---|---|
| WHITE | `#FFFFFF` | frame |
| RED | `#E53935` | drawer 0 |
| YELLOW | `#FDD835` | drawer 1 |
| BLUE | `#1E88E5` | drawer 2 |
| GREEN | `#43A047` | drawer 3 |

All five use Bambu PLA Basic. The plates are:

1. "Fit test": `test_corner`, `test_rod`, `badge`, `key` (white)
2. "Frame"
3. "Drawer 1 (circle)" through "Drawer 4 (star)", one per plate
4. "Lock": `rod`, `badge`, and two `key` (white)
5. "Dividers": four `divider` (white)

Keep `check` and `report` as in `frame/make_3mf.py`, so the weight per plate
is printed.

- [ ] **Step 1: Run** `uv run craft_drawers.py && uv run make_3mf.py`.
  Expect `craft_drawers.3mf: 9 plates [...]`, the weight per plate, and the
  sum of the frame and drawer plates at about 1 kg.
- [ ] **Step 2: Add the README row.** Also add the folder's run notes if the
  README lists per-project commands.
- [ ] **Step 3: Commit** with message `Craft drawers: Bambu Studio project and README`
