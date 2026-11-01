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
