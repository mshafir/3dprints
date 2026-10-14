import math
import sys
from itertools import combinations
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sink_organizer as so  # noqa: E402

P = so.P
EPS = 0.01  # mm^3, boolean noise floor


def overlap(a, b):
    return a.intersect(b).val().Volume()


def turned(part, deg):
    return part.rotate((0, 0, 0), (0, 0, 1), deg)


@pytest.fixture(scope="module")
def plate():
    return so.make_baseplate()


@pytest.fixture(scope="module")
def modules():
    return so.make_modules()


@pytest.fixture(scope="module")
def parts(plate, modules):
    out = {"baseplate": plate}
    for items in modules.values():
        out.update(items)
    out.update(so.fit_test_parts())
    return out


@pytest.fixture(scope="module")
def placed(modules):
    return so.placed(modules)


def pair(modules, name):
    (_, top), (_, tray) = modules[name]
    return top, tray


# --- Every part -------------------------------------------------------------


def test_parts_are_single_valid_solids(parts):
    for name, part in parts.items():
        assert part.solids().size() == 1, name
        assert part.val().isValid(), name


def test_no_unsupported_overhangs(parts):
    for name, part in parts.items():
        assert so.overhang_area(part) < 0.5, name


def test_parts_fit_the_bed(parts):
    for name, part in parts.items():
        bb = part.val().BoundingBox()
        assert max(bb.xlen, bb.ylen) <= 256 and bb.zlen <= 256, name


# --- Grid -----------------------------------------------------------------------


def test_baseplate_is_7_by_5_inches(plate):
    # Measured over the vertices: the bounding box is loose once the shape
    # has been meshed by an earlier test.
    pts = [v.toTuple() for v in plate.vertices().vals()]
    size = [max(c) - min(c) for c in zip(*pts)]
    assert size == pytest.approx([177.8, 127.0, P.plate_h], abs=0.01)


def test_layout_fills_every_cell_once():
    cells = [
        (ix + i, iy + j)
        for _, ix, iy, nx, ny, _ in so.LAYOUT
        for i in range(nx)
        for j in range(ny)
    ]
    assert len(cells) == len(set(cells)) == P.nx * P.ny
    assert set(cells) == {(i, j) for i in range(P.nx) for j in range(P.ny)}


def test_modules_seat_in_the_plate(plate, placed):
    for _, name, part in placed:
        assert overlap(part, plate) < EPS, name


def test_modules_stay_inside_their_cells(placed):
    boxes = {}
    for module, _, part in placed:
        boxes.setdefault(module, []).append(part.val().BoundingBox())
    for a, b in combinations(boxes, 2):
        for ba in boxes[a]:
            for bb in boxes[b]:
                apart_x = max(ba.xmin - bb.xmax, bb.xmin - ba.xmax)
                apart_y = max(ba.ymin - bb.ymax, bb.ymin - ba.ymax)
                assert max(apart_x, apart_y) >= P.gap - 0.01, (a, b)


def test_feet_rest_on_the_socket_ledge_with_side_clearance(plate):
    tray = so.make_open_tray(1, 1, 20.0, base=False)
    x, y = so.module_origin(3, 3, 1, 1)
    seated = tray.translate((x, y, 0))
    assert seated.val().distance(plate.val()) < 1e-3
    assert overlap(seated, plate) < EPS
    assert overlap(seated.translate((0, 0, -0.2)), plate) > EPS
    assert overlap(seated.translate((P.foot_clr - 0.05, 0, 0)), plate) < EPS
    assert overlap(seated.translate((P.foot_clr + 0.1, 0, 0)), plate) > EPS


def test_modules_seat_when_turned(plate, modules):
    _, soap = pair(modules, "soap")
    x, y = so.module_origin(0, 0, 4, 3)
    assert overlap(turned(soap, 180).translate((x, y, 0)), plate) < EPS
    _, tray = pair(modules, "brush")
    x, y = so.module_origin(3, 1, 2, 4)
    assert overlap(turned(tray, 90).translate((x, y, 0)), plate) < EPS


def test_feet_snap_into_the_plate(plate, modules):
    """Seated, the latch ridges sit clear in their grooves. Lifting brings the
    ridges up against the top of the grooves: a snap, not a lock."""
    assert P.foot_latch_proud - P.foot_clr >= 0.8  # grip per latch
    for name, cell, size in (("brush", (0, 3), (4, 2)), ("electric", (4, 2), (3, 3))):
        part = modules[name][-1][1]
        x, y = so.module_origin(*cell, *size)
        seated = part.translate((x, y, 0))
        assert overlap(seated, plate) < EPS
        assert overlap(seated.translate((0, 0, 0.2)), plate) < EPS
        caught = [overlap(seated.translate((0, 0, lift)), plate) for lift in (1.0, 2.0, 3.0)]
        assert all(v > 4.0 for v in caught), (name, caught)  # four ridges, each 10 mm wide
        assert overlap(seated.translate((0, 0, P.socket_d + 1)), plate) < EPS
    # Pushed in by the grip, the ridge clears the socket wall
    assert P.foot_latch_back >= P.foot_latch_proud - P.foot_clr + 0.4


def test_foot_latches_face_full_width_bars():
    assert so.foot_latch_cells(4, 2) == [(0, 0, 1), (0, 1, 1), (3, 0, -1), (3, 1, -1)]
    assert sorted(so.foot_latch_cells(1, 1)) == [(0, 0, -1), (0, 0, 1)]
    # The web left between the grooves cut into both faces of a bar
    assert P.bar - 2 * P.foot_latch_proud >= 1.2


def test_foot_latch_leaf_is_free_to_bend(modules):
    _, tray = pair(modules, "brush")
    cx = -1.5 * P.pitch  # corner foot at i = 0 of a 4 x 2 module, latch on its +x face
    cy = -0.5 * P.pitch
    a = cx + (P.pitch - P.bar) / 2 - P.foot_clr
    hw, s, t = P.foot_latch_w / 2, P.latch_slit, P.foot_latch_t
    root = P.foot_latch_z + P.foot_latch_len

    def probe(x, y, z, size=0.2):
        return so.box(x - size / 2, x + size / 2, y - size / 2, y + size / 2, z - size / 2, z + size / 2)

    free = [
        probe(a - t - P.foot_latch_back / 2, cy, so.foot_z() + 0.5),  # behind the leaf
        probe(a - t - P.foot_latch_back / 2, cy, root - 1),
        probe(a + P.latch_gap / 2, cy, root - 1),  # between the leaf and the body, above the plate
        probe(a - t / 2, cy + hw + s / 2, so.foot_z() + 0.5),  # the slit at each end
        probe(a - t / 2, cy - hw - s / 2, root - 1),
    ]
    for cell in free:
        assert overlap(tray, cell) < 1e-6
    for z in (so.foot_z() + 0.5, P.plate_h, root - 1, root + 1.5):
        assert overlap(tray, probe(a - t / 2, cy, z)) == pytest.approx(0.2**3, rel=1e-3)
    # The pockets stop short of the floor, so the tray still holds water
    assert overlap(tray, probe(a - t - P.foot_latch_back / 2, cy, P.floor_z - 0.3)) == pytest.approx(0.2**3, rel=1e-3)
    assert root + P.foot_latch_back / 2 <= P.floor_z - 0.8
    # Bending strain when the ridge rides over the socket wall, as a fraction
    grip = P.foot_latch_proud - P.foot_clr
    assert 1.5 * t * grip / P.foot_latch_len**2 < 0.016


def test_feet_engage_deep_straight_sockets(plate):
    assert P.socket_d >= 5.0
    foot = so.feet(1, 1)
    slice_lo = foot.intersect(so.box(-50, 50, -50, 50, so.foot_z() + P.foot_chamfer + 0.1, so.foot_z() + P.foot_chamfer + 0.2))
    slice_hi = foot.intersect(so.box(-50, 50, -50, 50, P.plate_h - 0.2, P.plate_h - 0.1))
    assert slice_lo.val().Volume() == pytest.approx(slice_hi.val().Volume(), rel=1e-6)


# --- Two-part modules -------------------------------------------------------------


@pytest.mark.parametrize("name", ["brush", "paste", "electric"])
def test_top_sits_on_tray_pads_and_lifts_off(modules, name):
    top, tray = pair(modules, name)
    assert overlap(top, tray) < EPS
    assert top.val().distance(tray.val()) < 1e-3
    assert overlap(top.translate((0, 0, -0.2)), tray) > EPS
    assert overlap(top.translate((0, 0, 0.2)), tray) < EPS
    for lift in (12, 20):
        assert overlap(top.translate((0, 0, lift)), tray) < EPS
    assert overlap(turned(top, 180), tray) < EPS


@pytest.mark.parametrize("name", ["brush", "electric"])
def test_tray_locates_the_top_sideways(modules, name):
    top, tray = pair(modules, name)
    for dx, dy in ((1, 0), (0, 1)):
        assert overlap(top.translate((0.2 * dx, 0.2 * dy, 0)), tray) < EPS
        assert overlap(top.translate((0.6 * dx, 0.6 * dy, 0)), tray) > EPS


def test_cup_top_snaps_onto_its_tray(modules):
    top, tray = pair(modules, "brush")
    assert P.top_latch_proud - P.spigot_clr >= 1.0  # grip per latch
    caught = [overlap(top.translate((0, 0, lift)), tray) for lift in (1.5, 2.5)]
    assert all(v > 8.0 for v in caught), caught  # two ridges, each 16 mm wide
    assert overlap(top.translate((0, 0, 6.0)), tray) < EPS  # then it is past the catch
    # Pushed in by the grip, the ridge clears the tray wall: it is a snap, not a lock
    assert P.top_latch_back >= P.top_latch_proud - P.spigot_clr + 0.4


def test_cup_latch_leaf_is_free_to_bend(modules):
    top, _ = pair(modules, "brush")
    a = so.valley(4, 2)[0] / 2 - so.spigot_off()
    hw, s, t = P.top_latch_w / 2, P.latch_slit, P.top_latch_t
    root = P.pad_z + P.top_latch_len

    def probe(x, y, z, size=0.2):
        return so.box(x - size / 2, x + size / 2, y - size / 2, y + size / 2, z - size / 2, z + size / 2)

    free = [
        probe(a - t - P.top_latch_back / 2, 0, P.pad_z + 0.5),  # through the floor behind the leaf
        probe(a - t - P.top_latch_back / 2, 0, P.pad_z + 5),
        probe(a + P.latch_gap / 2, 0, root - 1),  # between the leaf and the cup wall
        probe(a - t / 2, hw + s / 2, P.pad_z + 0.5),  # the slit at each end
        probe(a - t / 2, -hw - s / 2, root - 1),
    ]
    for cell in free:
        assert overlap(top, cell) < 1e-6
    solid = [probe(a - t / 2, 0, z) for z in (P.pad_z + 0.5, P.pad_z + 6, root - 1, root + 1.5)]
    for cell in solid:
        assert overlap(top, cell) == pytest.approx(0.2**3, rel=1e-3)
    assert root - P.top_latch_z >= 10.0  # bending length
    # Bending strain when the ridge rides over the tray wall, as a fraction
    grip = P.top_latch_proud - P.spigot_clr
    assert 1.5 * t * grip / (root - P.top_latch_z) ** 2 < 0.015


def test_top_floor_stands_clear_of_the_tray_floor(modules):
    top, _ = pair(modules, "brush")
    assert top.val().BoundingBox().zmin - P.floor_z >= 2.0


def test_cup_floor_drains_and_walls_are_vented(modules):
    top, _ = pair(modules, "brush")
    holes = so.drain_holes(4, 2)
    assert len(holes) >= 12
    x, y = holes[0]
    plug = so.cyl(P.hole_d / 2 - 0.1, P.pad_z, P.pad_z + P.top_floor, x, y)
    assert overlap(top, plug) < EPS
    solid = so.make_top(4, 2, P.brush_z, holes=False, vents=False)
    lost = solid.val().Volume() - top.val().Volume()
    drained = len(holes) * math.pi * (P.hole_d / 2) ** 2 * P.top_floor
    assert lost > drained + 100  # the rest is vent openings


def test_cups_are_tall_enough(modules):
    brush, _ = pair(modules, "brush")
    paste, _ = pair(modules, "paste")
    assert brush.val().BoundingBox().zmax - P.plate_h == pytest.approx(100, abs=0.1)
    assert paste.val().BoundingBox().zmax - P.plate_h == pytest.approx(90, abs=0.1)


# --- Things the modules hold --------------------------------------------------------


@pytest.fixture(scope="module")
def jar_holder():
    """Not in this version's layout, but kept buildable for the next one."""
    return so.make_jar_holder()


def test_two_jars_fit_at_the_same_depth(jar_holder):
    holder = jar_holder
    assert holder.solids().size() == 1 and holder.val().isValid()
    assert P.jar_step == 0
    assert so.jar_spacing() == pytest.approx(88.8, abs=0.05)
    low, high = so.jar_blocks(band_d=so.jar_spacing() - 1.0)
    for jar in (low, high):
        assert overlap(holder, jar) < EPS
        assert jar.val().distance(holder.val()) < 1e-3  # stands on its pocket floor
    assert overlap(low, high) < EPS
    assert low.val().distance(high.val()) >= 0.9


def test_jar_holder_is_watertight(jar_holder):
    holder = jar_holder
    x, r = so.jar_pockets()
    for cx, z in ((-x, P.floor_z), (x, P.floor_z + P.jar_step)):
        # Solid from above the foot-latch pockets up to the pocket floor
        sealed = P.foot_latch_z + P.foot_latch_len + P.foot_latch_back / 2 + 0.05
        under = so.cyl(r - 0.5, sealed, z - 0.05, cx)
        assert overlap(holder, under) == pytest.approx(under.val().Volume(), rel=1e-4)
    w, _ = so.valley(7, 4)
    assert w / 2 - (x + r) >= 1.2 - 1e-6


def test_chargers_fit_with_their_cords(modules):
    top, tray = pair(modules, "electric")
    blocks = so.charger_blocks()
    assert len(blocks) == P.chargers
    for block, cx in zip(blocks, so.charger_xs()):
        assert overlap(block, top) < EPS
        assert overlap(block, tray) < EPS
        assert block.val().distance(tray.val()) < 1e-3  # stands on the tray floor
        for sy in (-1, 1):
            cord = (
                so.cyl(2.5, 20, 60)
                .rotate((0, 0, 0), (1, 0, 0), -90 * sy)
                .translate((cx, 0, P.floor_z + 2.6))
            )
            assert overlap(cord, top) < EPS
            assert overlap(cord, tray) < EPS


def test_collar_drops_over_chargers_already_in_the_tray(modules):
    top, _ = pair(modules, "electric")
    for block in so.charger_blocks():
        for lift in (5, 15, 30):
            assert overlap(top.translate((0, 0, lift)), block) < EPS


def test_bar_soap_rests_on_the_grate(modules):
    grate, tray = pair(modules, "soap")
    assert overlap(grate, tray) < EPS
    assert grate.val().distance(tray.val()) < 1e-3
    assert overlap(grate.translate((0, 0, 10)), tray) < EPS
    top = so.base_line() + P.grate_proud
    bar = so.box(-47.5, 47.5, -32, 32, top, top + 25)
    assert overlap(bar, tray) < EPS
    assert overlap(bar, grate) < EPS
    assert grate.val().BoundingBox().zmax > tray.val().BoundingBox().zmax


def test_fit_test_cup_exercises_both_latches(parts):
    tray, top, small = parts["test_cup_tray_2x2"], parts["test_cup_top_2x2"], parts["test_plate_2x2"]
    assert overlap(tray, small) < EPS
    assert overlap(tray.translate((0, 0, 2.0)), small) > 4.0
    assert overlap(top, tray) < EPS
    assert overlap(top.translate((0, 0, 2.5)), tray) > 8.0


def test_small_latch_test_uses_little_plastic(parts):
    plate, stub = parts["test_plate_1x1"], parts["test_module_1x1"]
    assert overlap(stub, plate) < EPS
    assert stub.val().distance(plate.val()) < 1e-3
    assert overlap(stub.translate((0, 0, 2.0)), plate) > 2.0  # two ridges catch
    grams = (plate.val().Volume() + stub.val().Volume()) * 1.24e-3
    assert grams < 12
