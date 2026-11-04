import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sink_cup as sc  # noqa: E402
import sink_cup4 as s4  # noqa: E402
import sink_organizer as so  # noqa: E402

P, C = sc.P, s4.C4
EPS = 0.01  # mm^3, boolean noise floor


def overlap(a, b):
    return a.intersect(b).val().Volume()


def probe(x, y, z, size=1.0):
    h = size / 2
    return so.box(x - h, x + h, y - h, y + h, z - h, z + h)


@pytest.fixture(scope="module")
def parts():
    return s4.make_parts()


@pytest.fixture(scope="module")
def tray(parts):
    return parts["cup4_tray"]


@pytest.fixture(scope="module")
def sleeve(parts):
    return parts["cup4_sleeve"]


@pytest.fixture(scope="module")
def separators(parts):
    return [p for name, p in sc.assembled(parts, C).items() if name.startswith("cup4_separator_")]


def test_parts_are_single_valid_solids(parts):
    assert set(parts) == {"cup4_tray", "cup4_sleeve", "cup4_separator"}
    for name, part in parts.items():
        assert part.solids().size() == 1, name
        assert part.val().isValid(), name


def test_no_unsupported_overhangs(parts):
    for name, part in parts.items():
        part = sc.print_pose(name, part)
        allow = sc.tray_overhangs(C) if name == "cup4_tray" else ()
        assert so.overhang_area(part, allow=allow) < 0.5, name


def test_sleeve_sits_on_the_tray_and_snaps_on(tray, sleeve):
    assert overlap(sleeve, tray) < EPS
    assert sleeve.val().distance(tray.val()) < 1e-3
    assert all(overlap(sleeve.translate((0, 0, lift)), tray) > 8.0 for lift in (1.5, 2.5))


def test_three_separators_divide_the_length_in_four(separators):
    assert len(separators) == 3
    iw, _ = sc.inner(C)
    xs = sorted(s.val().Center().x for s in separators)
    edges = [-iw / 2, *xs, iw / 2]
    gaps = [b - a for a, b in zip(edges, edges[1:])]
    assert gaps == pytest.approx([iw / 4] * 4, abs=0.01)


def test_separators_slide_in_and_rest_on_the_stops(sleeve, separators):
    for s in separators:
        assert overlap(s, sleeve) < EPS
        assert overlap(s.translate((0, 0, -0.2)), sleeve) > EPS
        for lift in (10, 30, C.rim_z):
            assert overlap(s.translate((0, 0, lift)), sleeve) < EPS
        assert overlap(s.translate((C.sep_clr + 0.1, 0, 0)), sleeve) > EPS


def test_a_cord_opening_behind_each_section(tray, sleeve):
    _, d = so.valley(sc.NX, sc.NY, P)
    iw, _ = sc.inner(C)
    edges = [-iw / 2, *sc.stop_xs(C), iw / 2]
    xs = [x for x, _ in sc.cords(C)]
    assert len(xs) == 4
    for i, x in zip(C.cords, xs):
        assert edges[i] + C.cord_one_w / 2 < x < edges[i + 1] - C.cord_one_w / 2  # inside its section
    z = P.floor_z + 3
    for x in xs:
        for part in (tray, sleeve):
            assert overlap(part, probe(x, d / 2 - 0.5, z)) < 1e-6
        # The sleeve lowers over a cord already in place
        cord = so.cyl(2.0, 0, 60).rotate((0, 0, 0), (1, 0, 0), -90).translate((x, 0, P.floor_z + 2.2))
        for lift in (0, 5, 20, 40):
            assert overlap(sleeve.translate((0, 0, lift)), cord) < EPS
        assert overlap(tray, cord) < EPS
    assert list(C.cords) == list(range(len(edges) - 1))  # every section
    # The front stays closed, and the back between the openings
    assert overlap(tray, probe(xs[0], -d / 2 + 0.5, z)) == pytest.approx(1.0, rel=1e-3)
    between = (xs[1] + xs[2]) / 2
    assert overlap(tray, probe(between, d / 2 - 0.5, z)) == pytest.approx(1.0, rel=1e-3)


def test_rails_end_above_the_cord_openings():
    deep = sc.inner(C)[1] / 2 - sc.channel_back(C) + C.rail_d
    assert C.stop_z - deep - 1 > P.cord_z + C.cord_one_w / 2 + 1
    rail_hw = C.sep_t / 2 + C.sep_clr + C.rail_w
    for x, cw in sc.cords(C):
        assert all(abs(x - s) >= cw / 2 + rail_hw for s in sc.stop_xs(C))
