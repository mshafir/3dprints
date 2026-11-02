import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sink_cup as sc  # noqa: E402
import sink_organizer as so  # noqa: E402

P, C = sc.P, sc.C
EPS = 0.01  # mm^3, boolean noise floor


def overlap(a, b):
    return a.intersect(b).val().Volume()


def probe(x, y, z, size=1.0):
    h = size / 2
    return so.box(x - h, x + h, y - h, y + h, z - h, z + h)


@pytest.fixture(scope="module")
def parts():
    return sc.make_parts()


@pytest.fixture(scope="module")
def tray(parts):
    return parts["cup_tray"]


@pytest.fixture(scope="module")
def sleeve(parts):
    return parts["cup_sleeve"]


@pytest.fixture(scope="module")
def separators(parts):
    return [p for name, p in sc.assembled(parts).items() if name.startswith("cup_separator_")]


def test_parts_are_single_valid_solids(parts):
    for name, part in parts.items():
        assert part.solids().size() == 1, name
        assert part.val().isValid(), name


def test_no_unsupported_overhangs(parts):
    for name, part in parts.items():
        part = sc.print_pose(name, part)
        allow = sc.tray_overhangs() if name == "cup_tray" else ()
        assert so.overhang_area(part, allow=allow) < 0.5, name


def test_parts_fit_the_bed(parts):
    for name, part in parts.items():
        bb = sc.print_pose(name, part).val().BoundingBox()
        assert max(bb.xlen, bb.ylen) <= 256 and bb.zlen <= 256, name


def test_cup_is_6_by_3_cells_and_stands_on_the_counter(tray, sleeve):
    assert (sc.NX, sc.NY) == (6, 3)
    bb = tray.val().BoundingBox()
    assert bb.zmin == pytest.approx(0, abs=1e-6)
    assert bb.xlen == pytest.approx(sc.NX * P.pitch - P.gap, abs=0.01)
    assert bb.ylen == pytest.approx(3 * P.pitch - P.gap, abs=0.01)
    assert sleeve.val().BoundingBox().zmax == pytest.approx(C.rim_z, abs=0.01)


def test_tray_holds_water_up_to_its_floor(tray):
    iw, idp = sc.inner()
    assert overlap(tray, so.box(-iw / 2 + 5, iw / 2 - 5, -idp / 2 + 5, idp / 2 - 5, 0, P.floor_z)) == pytest.approx(
        (iw - 10) * (idp - 10) * P.floor_z, rel=1e-3
    )


def test_sleeve_sits_on_the_tray_and_lifts_off(tray, sleeve):
    assert overlap(sleeve, tray) < EPS
    assert sleeve.val().distance(tray.val()) < 1e-3
    assert overlap(sleeve.translate((0, 0, -0.2)), tray) > EPS
    for lift in (12, 20):
        assert overlap(sleeve.translate((0, 0, lift)), tray) < EPS


def test_sleeve_snaps_onto_the_tray(tray, sleeve):
    caught = [overlap(sleeve.translate((0, 0, lift)), tray) for lift in (1.5, 2.5)]
    assert all(v > 8.0 for v in caught), caught
    assert overlap(sleeve.translate((0, 0, 6.0)), tray) < EPS


def test_separators_divide_the_length_in_six(separators):
    iw, _ = sc.inner()
    xs = sorted(s.val().Center().x for s in separators)
    edges = [-iw / 2, *xs, iw / 2]
    gaps = [b - a for a, b in zip(edges, edges[1:])]
    assert gaps == pytest.approx([iw / 6] * 6, abs=0.01)


def test_separators_slide_in_and_rest_on_the_stops(sleeve, separators):
    for s in separators:
        assert overlap(s, sleeve) < EPS
        assert overlap(s.translate((0, 0, -0.2)), sleeve) > EPS  # resting on the stops
        for lift in (10, 30, C.rim_z):
            assert overlap(s.translate((0, 0, lift)), sleeve) < EPS  # free all the way out
        # Held front to back and side to side by the rails
        assert overlap(s.translate((C.sep_clr + 0.1, 0, 0)), sleeve) > EPS
        assert overlap(s.translate((0, C.sep_end_clr + 0.1, 0)), sleeve) > EPS


def test_separators_reach_two_thirds_of_the_way_down(separators):
    for s in separators:
        bb = s.val().BoundingBox()
        assert 0.6 <= (C.rim_z - bb.zmin) / C.rim_z <= 0.75
        assert bb.zmax < C.rim_z
    # The rails and their stops end above the peaked top of the cord slot
    deep = sc.inner()[1] / 2 - sc.channel_back() + C.rail_d
    assert C.stop_z - deep - 1 > P.cord_z + P.cord_w / 2 + 1


def test_cord_slot_is_at_the_back_right(tray, sleeve):
    _, d = so.valley(sc.NX, sc.NY, P)
    x = sc.cord_x()
    assert x > sc.stop_xs()[-1]  # in the right-hand section
    z = P.floor_z + 3
    for part in (tray, sleeve):
        assert overlap(part, probe(x, d / 2 - 0.5, z)) < 1e-6
    assert overlap(tray, probe(-x, d / 2 - 0.5, z)) == pytest.approx(1.0, rel=1e-3)  # back left solid
    assert overlap(tray, probe(x, -d / 2 + 0.5, z)) == pytest.approx(1.0, rel=1e-3)  # front solid
    # The sleeve lowers over a cord already in place
    cord = so.cyl(2.5, 0, 60).rotate((0, 0, 0), (1, 0, 0), -90).translate((x, 0, P.floor_z + 2.6))
    for lift in (0, 5, 20, 40):
        assert overlap(sleeve.translate((0, 0, lift)), cord) < EPS
    assert overlap(tray, cord) < EPS


def test_vents_in_the_back_wall_only(sleeve):
    _, d = so.valley(sc.NX, sc.NY, P)
    z = P.vent_z + 1
    assert overlap(sleeve, probe(0, d / 2 - 1, z)) < 1e-6
    assert overlap(sleeve, probe(0, -d / 2 + 1, z)) == pytest.approx(1.0, rel=1e-3)


def test_flutes_are_deep_and_run_round_the_curve_to_the_rim(sleeve):
    _, d = so.valley(sc.NX, sc.NY, P)
    h, _ = sc.roll_curve()
    _, step = so.rib_step(sc.NX, sc.NY, P)
    g, c = -2 * step, -1.5 * step  # a groove clear of the rails, and the next crest
    assert P.rib_d >= 1.8 and P.rib_pitch <= 4.0 and h >= 10
    # Halfway up the back: the groove, and the crest rib_d proud of it
    assert overlap(sleeve, so.box(g - 0.02, g + 0.02, d / 2 + 0.4, d / 2 + 0.6, 59.9, 60.1)) < 1e-6
    assert overlap(sleeve, probe(c, d / 2 + P.rib_d - 0.3, 60, 0.2)) > 0
    # At the rim the outside has moved in by roll_in, and the flutes are still
    # there: as many, so a little narrower
    n, _ = so.rib_step(sc.NX, sc.NY, P)
    g, c = g * (1 - 2 * math.pi * C.roll_in / (n * step)), c * (1 - 2 * math.pi * C.roll_in / (n * step))
    z, y = C.rim_z - 0.3, d / 2 - C.roll_in
    assert overlap(sleeve, probe(c, d / 2 + 0.5, z, 0.2)) < 1e-6
    assert overlap(sleeve, so.box(g - 0.02, g + 0.02, y + 0.9, y + 1.1, z - 0.1, z + 0.1)) < 1e-6  # not quite fully in, 0.3 below the rim
    assert overlap(sleeve, probe(c, y + P.rib_d - 0.5, z, 0.2)) > 0


def test_wall_is_thick_above_the_latches(sleeve):
    _, d = so.valley(sc.NX, sc.NY, P)
    # Solid from the bottom of a groove inward for wall_t, then open
    x = -2 * so.rib_step(sc.NX, sc.NY, P)[1]  # a groove clear of the rails
    assert overlap(sleeve, so.box(x - 0.1, x + 0.1, d / 2 - C.wall_t + 0.05, d / 2 - 0.05, 59.9, 60.1)) == pytest.approx(
        0.2 * 0.2 * (C.wall_t - 0.1), rel=1e-3
    )
    assert overlap(sleeve, probe(-30, d / 2 - C.wall_t - 0.3, 60, 0.2)) < 1e-6
