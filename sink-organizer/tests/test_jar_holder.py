import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import jar_holder as jh  # noqa: E402
import sink_organizer as so  # noqa: E402

J = jh.J
EPS = 0.01  # mm^3, boolean noise floor


def overlap(a, b):
    return a.intersect(b).val().Volume()


def probe(x, y, z, size=0.5):
    h = size / 2
    return so.box(x - h, x + h, y - h, y + h, z - h, z + h)


def filled(part, x, y, z, size=0.5):
    return overlap(part, probe(x, y, z, size)) == pytest.approx(size**3, rel=1e-3)


@pytest.fixture(scope="module")
def parts():
    return jh.make_parts()


@pytest.fixture(scope="module")
def holder(parts):
    return parts["jar_holder"]


@pytest.fixture(scope="module")
def ring(parts):
    return parts["jar_test_ring"]


def test_parts_are_single_valid_solids(parts):
    for name, part in parts.items():
        assert len(part.solids().vals()) == 1, name
        assert part.val().isValid(), name


def test_no_unsupported_overhangs(parts):
    for name, part in parts.items():
        assert so.overhang_area(part) < 1.0, name


def test_parts_fit_the_bed(parts):
    for name, part in parts.items():
        bb = part.val().BoundingBox()
        assert bb.xlen < 250 and bb.ylen < 250 and bb.zlen < 250, name


def test_holder_stands_on_the_counter_and_is_low(holder):
    bb = holder.val().BoundingBox()
    assert bb.zmin == pytest.approx(0, abs=0.05)
    assert bb.zmax == pytest.approx(J.floor_t + J.depth, abs=0.05)
    assert bb.zmax < 30


def test_jars_drop_in_with_clearance(holder):
    for x in jh.jar_xs():
        assert overlap(holder, jh.jar_stand_in(x)) < EPS
        # Not oversized: the wall starts right at the pocket's radius
        wider = so.cyl(jh.pocket_r() + 0.3, J.floor_t + J.floor_r + 0.5, J.floor_t + 10, x)
        assert overlap(holder, wider) > EPS
    assert 0.5 <= J.jar_clr <= 1.5


def test_jars_sit_an_inch_deep_on_a_closed_floor(holder):
    for x in jh.jar_xs():
        assert filled(holder, x, 0, J.floor_t / 2)  # floor under the middle
        assert filled(holder, x, 0, J.floor_t - 0.3)
        assert not filled(holder, x, 0, J.floor_t + 0.3)
        # Wall beside the jar up to just below the lead-in
        wall_x = x + jh.pocket_r() + 0.5
        assert filled(holder, wall_x, 0, J.floor_t + J.depth - J.lead - 0.5)
    assert J.depth == pytest.approx(25.4, abs=1.0)


def test_lid_bands_clear_each_other(holder):
    a, b = (jh.jar_stand_in(x) for x in jh.jar_xs())
    assert overlap(a, b) < EPS
    assert jh.spacing() - J.lid_d >= J.lid_gap - 1e-9


def test_flat_top_between_the_pockets(holder):
    z = J.floor_t + J.depth - 0.25
    assert filled(holder, 0, 0, z)  # the ridge between the openings
    ridge = jh.spacing() - 2 * (jh.pocket_r() + J.lead)
    assert ridge >= 1.5


def test_pocket_has_a_lead_in(holder):
    x = jh.jar_xs()[1]
    z = J.floor_t + J.depth - 0.25
    assert not filled(holder, x + jh.pocket_r() + 0.5, 0, z)  # cut away by the chamfer
    assert filled(holder, x + jh.pocket_r() + J.lead + J.land / 2, 0, J.floor_t + J.depth - 0.15, size=0.2)  # the flat beyond it


def test_flutes_run_round_the_outside(holder):
    r = jh.outline_r()
    x = jh.jar_xs()[1]
    z = 5.0
    # Round the far end, the outside reaches past the bottom of the flutes
    # at the crests and not between them
    n = jh.flute_count(2 * r + jh.spacing(), 2 * r, r)
    assert n % 4 == 0
    hits = sum(filled(holder, x + r + J.rib_d / 2, y, z, size=0.3) for y in (-3, -2, -1, 0, 1, 2, 3))
    assert 0 < hits < 7


def test_holder_fits_seven_inches_of_counter(holder):
    bb = holder.val().BoundingBox()
    assert bb.xlen <= 7 * 25.4


def test_test_ring_is_the_holders_pocket_without_a_floor(ring):
    bb = ring.val().BoundingBox()
    assert bb.zmin == pytest.approx(0, abs=0.05)
    assert bb.zmax == pytest.approx(J.test_depth, abs=0.05)
    jar = so.cyl(J.jar_d / 2, -1, 50)
    assert overlap(ring, jar) < EPS  # drops right through: no floor
    assert overlap(ring, so.cyl(jh.pocket_r() + 0.3, 1, 5)) > EPS
    assert filled(ring, jh.pocket_r() + 0.5, 0, 3)
    assert not filled(ring, jh.pocket_r() + 0.5, 0, J.test_depth - 0.25)  # lead-in
    assert bb.xlen == pytest.approx(2 * (jh.pocket_r() + J.lead + J.test_wall), abs=0.05)  # plain, no flutes


def test_test_ring_uses_little_plastic(ring, holder):
    assert ring.val().Volume() < 0.12 * holder.val().Volume()
