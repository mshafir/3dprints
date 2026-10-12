import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pill_case as pc  # noqa: E402

P = pc.P
EPS = 0.01  # mm^3, boolean noise floor


@pytest.fixture(scope="module")
def base():
    return pc.make_base()


@pytest.fixture(scope="module")
def lid():
    return pc.make_lid()


@pytest.fixture(scope="module")
def door():
    return pc.make_door()


@pytest.fixture(scope="module")
def dial():
    return pc.make_dial()


def overlap(a, b):
    return a.val().intersect(b.val()).Volume()


@pytest.mark.parametrize("name", ["base", "lid", "door", "dial"])
def test_part_is_single_valid_solid(name, request):
    part = request.getfixturevalue(name)
    assert part.val().isValid()
    assert len(part.solids().vals()) == 1


def tablet_on_edge(k, z_top=None):
    """A tablet standing on its edge in pocket k; with z_top, swept up to there."""
    r_mid = (P.pk_rin + P.pk_rout) / 2
    zc = P.floor + P.pill_d / 2 + 0.05
    disc = (
        pc.cyl(P.pill_d / 2, -P.pill_t / 2, P.pill_t / 2)
        .rotate((0, 0, 0), (1, 0, 0), 90)
        .translate((r_mid, 0, zc))
    )
    if z_top is not None:
        disc = disc.union(
            pc.box(r_mid - P.pill_d / 2, r_mid + P.pill_d / 2, -P.pill_t / 2, P.pill_t / 2, zc, z_top)
        )
    return pc.rot(disc, pc.pocket_angle(k))


def test_tablet_fits_in_pocket(base, lid, door):
    tablet = tablet_on_edge(0)
    assert overlap(base, tablet) < EPS
    assert overlap(lid, tablet) < EPS
    assert overlap(door, tablet) < EPS


def test_lid_clears_base_on_each_day(base, lid):
    assert overlap(base, lid) < EPS
    assert overlap(base, pc.lid_at(lid, 1)) < EPS
    assert overlap(base, pc.lid_at(lid, 13)) < EPS


def test_lid_detent_engages_between_days(base, lid):
    assert overlap(base, pc.lid_at(lid, 0.5)) > 0.05


def test_window_sits_over_pocket(base, lid, dial):
    path = tablet_on_edge(5, z_top=P.H + 20)
    assert overlap(pc.lid_at(lid, 5), path) < EPS
    assert overlap(dial, path) < EPS
    assert overlap(lid, path) > 1.0  # lid at home covers pocket 5


def test_slot_never_opens_a_neighbouring_pocket(lid):
    for k in (1, 27):
        assert overlap(lid, tablet_on_edge(k, z_top=P.H + 0.5)) > 0.5


@pytest.mark.parametrize("shift", [0.0, P.door_travel])
def test_door_clears_everything_closed_and_open(base, lid, dial, door, shift):
    d = pc.door_at(door, shift)
    assert overlap(lid, d) < EPS
    assert overlap(dial, d) < EPS
    assert overlap(base, d) < EPS


def test_door_covers_window_when_closed_only(door):
    path = tablet_on_edge(0, z_top=P.H + 20)
    assert overlap(door, path) > 1.0
    assert overlap(pc.door_at(door, P.door_travel), path) < EPS


@pytest.mark.parametrize("shift", [4.5, -1.0, P.door_travel + 1.0])
def test_door_latch_and_stops(lid, door, shift):
    assert overlap(lid, pc.door_at(door, shift)) > 0.01


def test_door_is_captive(lid, dial, door):
    assert overlap(lid, door.translate((0, 0, 1.5))) > 0.05
    assert overlap(lid, door.translate((0, 0, -1.5))) > 0.05
    assert overlap(lid, pc.door_at(door, P.door_travel).translate((0, 0, -1.5))) > 0.05
    assert overlap(dial, pc.door_at(door, P.door_travel).translate((0, 0, 1.5))) > 0.05


def test_door_prints_free_of_lid(lid, door):
    assert lid.val().distance(door.val()) >= 0.25


def test_dial_locked_clear_and_retained(base, lid, dial):
    assert overlap(base, dial) < EPS
    assert overlap(lid, dial) < EPS
    assert overlap(base, pc.dial_at(dial, 0, 0.6)) > 0.05


def test_dial_releases_after_twist(base, dial):
    assert overlap(base, pc.dial_at(dial, P.bayonet_twist, 0)) < EPS
    assert overlap(base, pc.dial_at(dial, P.bayonet_twist, 5.0)) < EPS


def test_dial_latch_resists_untwisting(base, dial):
    assert overlap(base, pc.dial_at(dial, 10.0, 0)) > 0.05


def test_dial_hook_is_pulled_in_by_untwisting():
    # The lug's side must lean so its outward normal points toward the post.
    (ix, iy), (ox, oy) = pc.lug_side()
    ux, uy = ox - ix, oy - iy
    nx, ny = uy, -ux  # normal on the clockwise (hook) side
    assert ny < 0
    assert nx * ox + ny * oy < 0


def test_dial_hard_stop(base, dial):
    assert overlap(base, pc.dial_at(dial, -5.0, 0)) > 0.05


def test_dial_text_adds_volume(dial):
    plain = pc.make_dial(text=False)
    assert dial.val().Volume() - plain.val().Volume() > 20


@pytest.mark.parametrize(
    "name,limit", [("base", 0.5), ("lid", 0.5), ("dial", 0.5), ("door", 0.5)]
)
def test_no_unsupported_overhangs(name, limit, request):
    assert pc.overhang_area(request.getfixturevalue(name)) < limit


def test_overall_size(base, lid, door, dial):
    asm = base.union(lid).union(door).union(dial)
    bb = asm.val().BoundingBox()
    assert bb.xlen <= 84 and bb.ylen <= 84
    assert bb.zlen <= 17.5
