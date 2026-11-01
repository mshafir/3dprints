import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import craft_drawers as cd  # noqa: E402

P = cd.P
EPS = 0.01  # mm^3, boolean noise floor


def overlap(a, b):
    return a.intersect(b).val().Volume()


def size(part):
    """Measured over the vertices: the bounding box is loose once the shape
    has been meshed by an earlier test."""
    pts = [v.toTuple() for v in part.vertices().vals()]
    return [max(c) - min(c) for c in zip(*pts)]


# --- Sizes ------------------------------------------------------------------


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
    assert x - P.cam_r - x1 == pytest.approx(P.lock_clr)  # locked cam tip clear of the wall
    assert x - P.cam_w / 2 - (x1 + P.fin_reach) >= 1.5  # unlocked cam clear of the fin
    assert y - P.cam_r - P.stile >= 1.5  # unlocked cam clear of the stile


def test_travel_stop():
    assert cd.travel_stop() == pytest.approx(cd.drawer_box()[3] * 2 / 3)


# --- Frame ------------------------------------------------------------------


@pytest.fixture(scope="module")
def frame():
    return cd.make_frame()


def test_frame_is_one_solid(frame):
    assert len(frame.solids().vals()) == 1 and frame.val().isValid()


def test_frame_fits_bed_on_its_back(frame):
    assert max(size(cd.frame_print(frame))) <= P.bed


def test_frame_outside_closed(frame):
    # every outer face is closed except the front opening; the top only has
    # the badge slot
    assert cd.outside_openings(frame) == ["front"]


def test_frame_prints_without_supports(frame):
    allow = [cd.frame_print(z) for z in cd.bridge_zones()]
    assert cd.overhang_area(cd.frame_print(frame), allow=allow) < 5.0


def test_fork_near_every_cam():
    for i in range(P.bays):
        z0, z1 = cd.cam_span(i)
        assert min(abs((z0 + z1) / 2 - zf) for zf in cd.fork_zs()) <= cd.pitch() / 2 + 1


def test_rail_stops_at_travel():
    assert cd.nub_front_y() - cd.stop_y() == pytest.approx(cd.travel_stop())


# --- Drawers ----------------------------------------------------------------


@pytest.fixture(scope="module")
def drawers():
    return [cd.make_drawer(i) for i in range(P.bays)]


def test_drawers_are_single_solids(drawers):
    for d in drawers:
        assert len(d.solids().vals()) == 1 and d.val().isValid()


def test_pencil_fits(drawers):
    # lying between two divider slots, so the ribs are not in the way
    x0, x1 = cd.drawer_box()[:2]
    cx = (x0 + x1) / 2 + (P.div_xs[0] + P.div_xs[1]) / 2
    pencil = cd.box(cx - 4, cx + 4, 0.3, 180.3, 0, 8).translate((0, 0, cd.drawer_z(0) + P.floor + 0.1))
    assert overlap(drawers[0], pencil) < EPS


def test_drawers_fit_closed(frame, drawers):
    for d in drawers:
        assert overlap(frame, d) < EPS
    for a, b in zip(drawers, drawers[1:]):
        assert overlap(a, b) < EPS


@pytest.mark.parametrize("t", [10, 40, 80, 120])
def test_drawer_slides_to_stop(frame, t):
    assert overlap(frame, cd.drawer_at(1, t)) < EPS


def test_stop_holds_and_releases(frame):
    assert overlap(frame, cd.drawer_at(1, cd.travel_stop() + 1.0)) > EPS
    for t in (cd.travel_stop() + 1, 150, 175):
        assert overlap(frame, cd.drawer_at(1, t, pressed=True)) < EPS


def test_pull_shapes_differ():
    assert len(set(cd.SHAPES)) == P.bays == 4


def test_divider_fits(drawers):
    for slot in range(len(P.div_xs)):
        assert overlap(drawers[0], cd.divider_in(0, slot)) < EPS


def test_drawer_and_divider_print(drawers):
    for i, d in enumerate(drawers):
        part = cd.drawer_print(d, i)
        assert max(size(part)) <= P.bed
        assert cd.overhang_area(part) < 5.0
    assert cd.overhang_area(cd.divider_print(cd.make_divider())) < 1.0


# --- Lock -------------------------------------------------------------------


@pytest.fixture(scope="module")
def rod_locked():
    return cd.make_rod(cd.LOCKED)


@pytest.fixture(scope="module")
def rod_unlocked():
    return cd.make_rod(cd.UNLOCKED)


@pytest.fixture(scope="module")
def badge():
    return cd.make_badge()


def test_locked_holds_every_drawer(frame, drawers, rod_locked):
    assert overlap(frame, rod_locked) < EPS
    for i in range(P.bays):
        assert overlap(rod_locked, drawers[i]) < EPS
        assert overlap(rod_locked, cd.drawer_at(i, 1.0)) > EPS


@pytest.mark.parametrize("t", [1, 2, 5, 40, 120])
def test_open_drawer_blocks_locking(rod_locked, t):
    assert overlap(rod_locked, cd.drawer_at(2, t)) > EPS


def test_unlocked_frees_every_drawer(frame, rod_unlocked):
    assert overlap(frame, rod_unlocked) < EPS
    for i in range(P.bays):
        for t in (0, 60, 120):
            assert overlap(rod_unlocked, cd.drawer_at(i, t)) < EPS


def test_turn_is_clear_with_drawers_shut(frame, drawers):
    for a in range(180, 271, 10):
        rod = cd.make_rod(a)
        assert overlap(frame, rod) < EPS
        assert all(overlap(rod, d) < EPS for d in drawers)


def test_reinserting_while_locked_stops_short(rod_locked, rod_unlocked):
    assert overlap(rod_locked, cd.drawer_at(0, 17.0)) > EPS  # tab meets the cam
    assert overlap(rod_unlocked, cd.drawer_at(0, 17.0)) < EPS


def test_rod_drops_in_only_at_insertion_angle(frame, rod_locked, rod_unlocked):
    for dz in range(0, 260, 10):
        assert overlap(frame, rod_locked.translate((0, 0, dz))) < EPS
    dz = cd.pitch() - P.cam_z - P.cam_h / 2 - P.ledge_t / 2  # cams level with the forks above
    assert overlap(frame, rod_unlocked.translate((0, 0, dz))) > EPS


def test_badge_covers_slot_and_seats(frame, badge, rod_locked):
    assert overlap(frame, badge) < EPS
    assert overlap(badge, rod_locked) < EPS  # the nub rests in a notch
    bore = cd.cyl(P.bore_r, 0, 300, *cd.rod_xy())  # the keyhole: sealed by the rod head
    assert cd.covers(badge, *cd.slot(), z=P.height + 0.5, holes=[bore])


def test_detent_presses_between_positions(badge, rod_unlocked):
    assert overlap(badge, rod_unlocked) < EPS
    assert overlap(badge, cd.make_rod(225)) > EPS


def test_rod_cannot_lift_out_of_its_socket(badge, rod_locked):
    lift = P.pin_depth - 0.5
    assert overlap(badge, rod_locked.translate((0, 0, lift))) > EPS


def test_key_fits_and_drives(rod_locked):
    assert overlap(rod_locked, cd.make_key(cd.LOCKED)) < EPS
    assert overlap(rod_locked, cd.make_key(cd.LOCKED + 5)) > EPS


def test_key_clears_badge(badge):
    assert overlap(badge, cd.make_key(cd.LOCKED)) < EPS


def test_keyhole_depth_and_seal(rod_locked):
    assert P.key_depth >= 15.0 and 2 * P.bore_r < 17.0  # no fingertip, no coin
    pencil = cd.cyl(3.6, 200, 260, *cd.rod_xy())
    assert overlap(pencil, rod_locked) > EPS  # stops on the head


@pytest.mark.parametrize("af", [2.5, 3.0, 4.0, 5.0, 6.0])
def test_hex_keys_do_not_drive(rod_locked, af):
    hits = [overlap(rod_locked, cd.hex_key(af, a)) > EPS for a in range(0, 60, 5)]
    assert all(hits) or not any(hits)


def test_lock_parts_print(rod_locked, badge):
    parts = [
        (cd.rod_print(rod_locked), [cd.rod_print(cd.rod_bridges())]),
        (cd.badge_print(badge), []),
        (cd.key_print(cd.make_key(cd.LOCKED)), []),
    ]
    for part, allow in parts:
        assert len(part.solids().vals()) == 1
        assert max(size(part)) <= P.bed
        assert cd.overhang_area(part, allow=allow) < 5.0
