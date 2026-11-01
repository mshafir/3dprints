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
