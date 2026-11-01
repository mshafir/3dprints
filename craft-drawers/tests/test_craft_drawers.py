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
    assert d - P.handle_out <= 203.2  # only the handles stand past an 8 in shelf
    assert P.handle_out <= 25.0
    assert P.height <= P.bed


def test_inside_holds_a_pencil():
    w, l, h = cd.inside()
    assert l >= 180.0 and w >= 175.0 and h >= 50.0


def test_lock_geometry_numbers():
    x, y = cd.rod_xy()
    x1 = cd.drawer_box()[1]
    assert x1 - (x - P.cam_r) >= 2.5  # locked, the cam reaches well into the drawer's pocket
    assert x - P.cam_w / 2 - x1 >= 1.5  # unlocked, it points back, clear of the drawer


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


def test_handles_all_the_same():
    vols = [cd.handle(i).val().Volume() for i in range(P.bays)]
    assert max(vols) - min(vols) < 0.01


def test_each_front_has_its_shape_left_of_the_handle(drawers):
    post = -P.handle_w / 2
    for i, d in enumerate(drawers):
        cut = cd.face_shape(i)
        assert overlap(d, cut) < EPS  # recessed
        assert overlap(cd.front_plate(i), cut) > EPS  # into the front
        bb = cut.val().BoundingBox()
        assert bb.xmax < post - 3 and bb.xmin > -P.width / 2 + 3


def test_divider_ribs_hold():
    assert P.rib >= 3.0 and P.div_slot - P.div_t <= 0.4


def test_handle_fits_a_hand(drawers):
    # four fingers, 16 mm across and 70 mm wide, slide in behind the bar
    x0, x1, z0, z1, y_back = cd.handle_grip(0)
    assert x1 - x0 >= 70.0 and z1 - z0 >= 8.0
    fingers = cd.box(-35, 35, -P.front_t - 15.9, -P.front_t - 0.1, z0, z1)
    assert overlap(drawers[0], fingers) < EPS


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
        assert overlap(rod_locked, cd.drawer_at(i, 6.0)) > EPS  # opens about 5 mm, then held


@pytest.mark.parametrize("t", [1, 2, 5, 40, 120])
def test_open_drawer_blocks_locking(t):
    d = cd.drawer_at(2, t)
    assert any(overlap(cd.make_rod(a), d) > EPS for a in range(cd.UNLOCKED, cd.LOCKED + 1, 15))


def test_unlocked_frees_every_drawer(frame, rod_unlocked):
    assert overlap(frame, rod_unlocked) < EPS
    for i in range(P.bays):
        for t in (0, 60, 120):
            assert overlap(rod_unlocked, cd.drawer_at(i, t)) < EPS


def test_turn_is_clear_with_drawers_shut(frame, drawers):
    for a in range(cd.UNLOCKED, cd.LOCKED + 1, 10):
        rod = cd.make_rod(a)
        assert overlap(frame, rod) < EPS
        assert all(overlap(rod, d) < EPS for d in drawers)


def test_reinserting_while_locked_stops_short(rod_locked, rod_unlocked):
    # pushed back in while locked, the drawer's back meets the cam 10 mm short
    assert overlap(rod_locked, cd.drawer_at(0, 170.0)) > EPS
    assert overlap(rod_unlocked, cd.drawer_at(0, 170.0)) < EPS


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
    assert overlap(badge, cd.make_rod((cd.LOCKED + cd.UNLOCKED) // 2)) > EPS


def test_rod_cannot_lift_out_of_its_socket(badge, rod_locked):
    lift = P.pin_depth - 0.5
    assert overlap(badge, rod_locked.translate((0, 0, lift))) > EPS


def test_key_fits_and_drives(rod_locked):
    assert overlap(rod_locked, cd.make_key(cd.LOCKED)) < EPS
    assert overlap(rod_locked, cd.make_key(cd.LOCKED + 15)) > EPS  # past the clearance's backlash


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
        (cd.badge_print(badge), [cd.badge_print(z) for z in cd.badge_bridges()]),
        (cd.key_print(cd.make_key(cd.LOCKED)), []),
    ]
    for part, allow in parts:
        assert len(part.solids().vals()) == 1
        assert max(size(part)) <= P.bed
        assert cd.overhang_area(part, allow=allow) < 5.0


# --- Whole chest ------------------------------------------------------------


def test_weight_budget(frame, drawers):
    total = cd.grams(frame) + sum(cd.grams(d) for d in drawers)
    assert total < 1150


def test_does_not_tip_with_top_drawer_out():
    # top drawer at its stop holding 300 g at its centre: the moment about the
    # frame's front bottom edge stays on the frame's side
    assert cd.tip_margin(load=300.0, drawer=3) > 0


def test_tips_only_with_an_absurd_load():
    # the check can fail: a 5 kg load in the open top drawer tips it
    assert cd.tip_margin(load=5000.0, drawer=3) < 0


def test_fit_test_parts_fit():
    for part in cd.fit_test_parts().values():
        assert len(part.solids().vals()) >= 1
        assert max(size(part)) <= P.bed



# --- Review fixes -----------------------------------------------------------


def test_pulling_a_locked_drawer_cannot_turn_the_rod(frame, badge):
    # a pull on the tab turns the cam counter-clockwise, away from unlocked,
    # into a hard stop just past locked
    assert (cd.UNLOCKED - cd.LOCKED) % 360 > 180  # unlocking turns clockwise
    for a in (cd.LOCKED + 10, cd.LOCKED + 20, cd.LOCKED + 30):
        rod = cd.make_rod(a)
        assert overlap(badge, rod) + overlap(frame, rod) > EPS


def test_detent_leaf_is_cut_free(badge):
    x, y = cd.rod_xy()
    zone = cd.box(x - 8, x + 8, y - 8, y + 8, 239.9, 240.1)
    assert len(badge.intersect(zone).solids().vals()) >= 2


def test_rod_turns_with_clearance_in_forks():
    assert cd.rod_reach() + 0.3 <= P.rod_r + P.fork_clr


def test_key_clearance_for_a_sideways_socket():
    assert P.key_clr >= 0.25


def test_socket_walls():
    assert cd.socket_wall() >= 0.9


def test_stop_holds_with_drawer_pushed_sideways(frame):
    play = cd.side_play()
    assert play <= 0.6
    assert overlap(frame, cd.drawer_at(1, cd.travel_stop() + 1.0).translate((play, 0, 0))) > EPS


def test_stop_leaf_is_short_and_wide():
    assert P.leaf_len <= 30.0 and P.leaf_w >= 20.0


def test_top_drawer_clear_of_screw_bosses():
    x1 = cd.drawer_box()[1]
    assert min(x for x, y in P.screws) - P.boss_r - x1 >= 0.5


def test_rod_stays_in_floor_socket_at_full_lift():
    lift = cd.badge_tube_bottom() - cd.flange_top() + 0.3  # it rests 0.3 lower than modelled
    assert P.pin_depth - lift >= 2.0



# --- Locking, as a pull would test it ---------------------------------------


def test_no_fin_on_the_drawer_side():
    # the drawer's own wall blocks the turn; nothing stands proud of it
    x1 = cd.drawer_box()[1]
    beside = cd.box(x1 + 0.05, x1 + 10, 0, cd.drawer_box()[3], 0, P.height)
    assert overlap(cd.make_drawer(1), beside) < EPS


def test_locked_drawer_is_caught_within_8_mm(rod_locked):
    for i in range(P.bays):
        assert overlap(rod_locked, cd.drawer_at(i, 8.0)) > EPS


@pytest.mark.parametrize("a", [0, 5, 10, 15, 20])
def test_locked_drawer_stays_caught_as_the_rod_twists(a):
    # a pull turns the rod counter-clockwise into its stop (about 10 degrees)
    # and the rod twists a little more along its length under a hard yank
    rod = cd.make_rod(cd.LOCKED + a)
    for t in (8.0, 15.0, 40.0):
        assert overlap(rod, cd.drawer_at(0, t)) > EPS


def test_stop_halts_the_rod_before_the_cam_lets_go(badge):
    assert overlap(badge, cd.make_rod(cd.LOCKED + 12)) > EPS


def test_back_stop_catch_is_deep():
    assert cd.stop_catch() >= 2.5
    assert cd.stop_catch() - cd.side_play() >= 2.0
