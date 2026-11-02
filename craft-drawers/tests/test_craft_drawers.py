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


def test_latch_stops_at_travel():
    assert cd.latch_y()["face"] - cd.latch_nub_y() == pytest.approx(cd.travel_stop())


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
        assert cd.overhang_area(part, allow=[cd.drawer_print(z, i) for z in cd.drawer_bridges(i)]) < 5.0
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
    # clear everywhere but the click, which presses on the collar mid-turn
    z0, z1 = cd.collar_z()
    no_click = frame.cut(cd.box(-200, 200, -10, 300, z0, z1))
    for a in range(cd.UNLOCKED, cd.LOCKED + 1, 10):
        rod = cd.make_rod(a)
        assert overlap(no_click, rod) < EPS
        assert all(overlap(rod, d) < EPS for d in drawers)


def test_reinserting_while_locked_stops_short(rod_locked, rod_unlocked):
    # pushed back in while locked, the drawer's back meets the cam 10 mm short
    assert overlap(rod_locked, cd.drawer_at(0, 170.0)) > EPS
    assert overlap(rod_unlocked, cd.drawer_at(0, 170.0)) < EPS


def test_rod_drops_in_only_at_insertion_angle(frame, rod_locked, rod_unlocked):
    # in with the cams pointing back, through the forks' slots
    for dz in range(0, 260, 10):
        assert overlap(frame, rod_unlocked.translate((0, 0, dz))) < EPS
    dz = cd.pitch() - P.cam_z - P.cam_h / 2 - P.ledge_t / 2  # cams level with the forks above
    assert overlap(frame, rod_locked.translate((0, 0, dz))) > EPS


def test_rod_goes_in_with_the_drawers_in_place(drawers, rod_unlocked):
    for dz in range(0, 260, 10):
        rod = rod_unlocked.translate((0, 0, dz))
        assert all(overlap(rod, d) < EPS for d in drawers)


def test_badge_covers_slot_and_seats(frame, badge, rod_locked):
    assert overlap(frame, badge) < EPS
    assert overlap(badge, rod_locked) < EPS  # the nub rests in a notch
    bore = cd.cyl(P.bore_r, 0, 300, *cd.rod_xy())  # the keyhole: sealed by the rod head
    assert cd.covers(badge, *cd.slot(), z=P.height + 0.5, holes=[bore])


def test_click_presses_between_positions(frame, rod_locked, rod_unlocked):
    # the frame's arm rests in the collar's notch unlocked, on its flat locked,
    # and is pushed back in between
    assert overlap(frame, rod_unlocked) < EPS and overlap(frame, rod_locked) < EPS
    assert overlap(frame, cd.make_rod((cd.LOCKED + cd.UNLOCKED) // 2)) > EPS


def test_hard_stop_just_past_unlocked(frame):
    assert overlap(frame, cd.make_rod(cd.UNLOCKED - 15)) > EPS


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


def test_pulling_a_locked_drawer_cannot_turn_the_rod(frame):
    # a pull on the pocket turns the cam counter-clockwise, away from
    # unlocked, into a post in the frame right in front of every cam
    assert (cd.UNLOCKED - cd.LOCKED) % 360 > 180  # unlocking turns clockwise
    for a in (cd.LOCKED + 8, cd.LOCKED + 20):
        rod = cd.make_rod(a)
        for i in range(P.bays):
            z0, z1 = cd.cam_span(i)
            assert overlap(frame.intersect(cd.box(-200, 200, -10, 300, z0, z1)), rod) > EPS


def test_rod_turns_with_clearance_in_forks():
    assert cd.rod_reach() + 0.3 <= P.rod_r + P.fork_clr


def test_key_clearance_for_a_sideways_socket():
    assert P.key_clr >= 0.25


def test_socket_walls():
    assert cd.socket_wall() >= 0.9


@pytest.mark.parametrize("dx", [-0.5, 0.5])
def test_stop_holds_with_drawer_pushed_sideways(frame, dx):
    # the nub runs in a channel under the drawer, so the drawer can't dodge it
    assert overlap(frame, cd.drawer_at(1, cd.travel_stop() + 1.0).translate((dx, 0, 0))) > EPS


def test_top_drawer_clear_of_screw_bosses():
    x1 = cd.drawer_box()[1]
    assert min(x for x, y in cd.screw_xy()) - P.boss_r - x1 >= 0.5


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


@pytest.mark.parametrize("a", [0, 4, 8])
def test_locked_drawer_stays_caught_as_the_rod_turns_to_its_stop(a):
    # a pull turns the rod counter-clockwise until each cam meets its post,
    # about 6 degrees past locked
    rod = cd.make_rod(cd.LOCKED + a)
    for t in (8.0, 15.0, 40.0):
        assert overlap(rod, cd.drawer_at(0, t)) > EPS


def test_stop_halts_the_rod_before_the_cam_lets_go(frame):
    assert overlap(frame, cd.make_rod(cd.LOCKED + 8)) > EPS


def test_back_stop_catch_is_deep():
    assert P.latch_nub_h >= 2.0 and P.latch_lift > P.latch_nub_h


# --- Mini chest: one drawer, to try the mechanism before the full print -------

M = cd.MINI


@pytest.fixture(scope="module")
def mini():
    return {
        "frame": cd.make_frame(M),
        "drawer": cd.make_drawer(0, M),
        "locked": cd.make_rod(cd.LOCKED, M),
        "unlocked": cd.make_rod(cd.UNLOCKED, M),
        "badge": cd.make_badge(M),
    }


def test_mini_is_small_and_cheap(mini):
    w, d, h = cd.outside(M)
    assert w <= 120 and d <= 130 and h <= 75
    total = cd.grams(mini["frame"]) + cd.grams(mini["drawer"]) + cd.grams(mini["locked"]) + cd.grams(mini["badge"])
    assert total < 250


def test_mini_keeps_the_mechanism_sizes():
    # everything that moves, catches or clicks is the full chest's
    for name in ("rod_r", "rod_dx", "rod_y", "cam_r", "cam_w", "cam_h", "cam_z", "pocket_clr", "head_r", "bore_r", "key_depth",
                 "collar_r", "collar_h", "arm_t", "arm_len", "det_press", "nub_r", "latch_hinge_w", "latch_len",
                 "latch_nub_h", "latch_lift", "gap_left", "rib", "rib_w", "div_slot", "div_t", "handle_out", "bar_t", "bar_h",
                 "front_t", "wall"):
        assert getattr(M, name) == getattr(P, name), name
    assert cd.pitch(M) == cd.pitch(P)


def test_mini_parts_are_single_solids(mini):
    for part in mini.values():
        assert len(part.solids().vals()) == 1 and part.val().isValid()


def test_mini_frame_closed_and_printable(mini):
    assert cd.outside_openings(mini["frame"], M) == ["front"]
    allow = [cd.frame_print(z, M) for z in cd.bridge_zones(M)]
    assert cd.overhang_area(cd.frame_print(mini["frame"], M), allow=allow) < 5.0


def test_mini_drawer_runs_and_stops(mini):
    f = mini["frame"]
    assert overlap(f, mini["drawer"]) < EPS
    for t in (10, cd.travel_stop(M) - 1):
        assert overlap(f, cd.drawer_at(0, t, M)) < EPS
    assert overlap(f, cd.drawer_at(0, cd.travel_stop(M) + 1, M)) > EPS
    assert overlap(f, cd.drawer_at(0, cd.travel_stop(M) + 1, M).translate((0.5, 0, 0))) > EPS
    assert overlap(f, cd.drawer_at(0, cd.travel_stop(M) + 1, M, pressed=True)) < EPS


def test_mini_lock_holds_and_frees(mini):
    locked, unlocked = mini["locked"], mini["unlocked"]
    assert overlap(mini["frame"], locked) < EPS and overlap(mini["frame"], unlocked) < EPS
    assert overlap(locked, mini["drawer"]) < EPS
    for a in (0, 4, 8):  # out to the post
        assert overlap(cd.make_rod(cd.LOCKED + a, M), cd.drawer_at(0, 8.0, M)) > EPS
    for t in (0, 30, cd.travel_stop(M) - 1):
        assert overlap(unlocked, cd.drawer_at(0, t, M)) < EPS


def test_mini_open_drawer_blocks_the_key():
    for t in (1, 5, 30):
        d = cd.drawer_at(0, t, M)
        assert any(overlap(cd.make_rod(a, M), d) > EPS for a in range(cd.UNLOCKED, cd.LOCKED + 1, 15))


def test_mini_turn_clear_and_stopped(mini):
    z0, z1 = cd.collar_z(M)
    no_click = mini["frame"].cut(cd.box(-200, 200, -10, 300, z0, z1))
    for a in range(cd.UNLOCKED, cd.LOCKED + 1, 15):
        rod = cd.make_rod(a, M)
        assert overlap(no_click, rod) < EPS and overlap(mini["drawer"], rod) < EPS
    assert overlap(mini["frame"], cd.make_rod(cd.LOCKED + 8, M)) > EPS
    assert overlap(mini["frame"], cd.make_rod(cd.UNLOCKED - 15, M)) > EPS
    assert overlap(mini["frame"], cd.make_rod(135, M)) > EPS  # the click


def test_mini_badge_key_and_rod_fit(mini):
    badge, locked = mini["badge"], mini["locked"]
    assert overlap(mini["frame"], badge) < EPS and overlap(badge, locked) < EPS
    assert overlap(badge, mini["unlocked"]) < EPS
    bore = cd.cyl(M.bore_r, 0, 300, *cd.rod_xy(M))
    assert cd.covers(badge, *cd.slot(M), z=M.height + 0.5, holes=[bore])
    assert overlap(locked, cd.make_key(cd.LOCKED, M)) < EPS and overlap(badge, cd.make_key(cd.LOCKED, M)) < EPS
    for dz in range(0, 80, 10):
        assert overlap(mini["frame"], mini["unlocked"].translate((0, 0, dz))) < EPS


def test_mini_divider_and_front(mini):
    for slot in range(len(M.div_xs)):
        assert overlap(mini["drawer"], cd.divider_in(0, slot, M)) < EPS
    assert overlap(mini["drawer"], cd.face_shape(0, M)) < EPS
    bb = cd.face_shape(0, M).val().BoundingBox()
    assert bb.xmax < -M.handle_w / 2 - 3 and bb.xmin > -M.width / 2 + 3


def test_mini_parts_print(mini):
    parts = cd.mini_parts()
    for name, part in parts.items():
        assert max(size(part)) <= P.bed, name
    assert cd.overhang_area(parts["mini_drawer"], allow=[cd.drawer_print(z, 0, M) for z in cd.drawer_bridges(0, M)]) < 5.0
    assert cd.overhang_area(parts["mini_divider"]) < 1.0


def test_screw_bosses_grow_from_the_back_wall():
    # printed on its back, a boss that hangs off the top wall alone starts in
    # mid-air (Bambu Studio: "floating cantilever"); a web runs it back to the
    # back wall, which is on the bed
    for p in (P, M):
        for b in cd.screw_bosses(p):
            assert b.val().BoundingBox().ymax >= p.depth - p.back


def test_forks_hold_the_rod_forward_with_a_45_degree_face(rod_locked):
    # the fork's front arm meets the rod on a 45 degree face, so it grows from
    # the ledge when the frame prints on its back, and still takes the pull
    forks = cd.combo(*[cd.ledges()[2 * i + 1] for i in range(1, P.bays)])
    assert overlap(forks, rod_locked) < EPS
    assert overlap(forks, rod_locked.translate((0, -1.0, 0))) > EPS
    assert len(cd.bridge_zones()) == P.bays + 1 + 4  # rail faces, the slot, the bumpers: no fork arms
