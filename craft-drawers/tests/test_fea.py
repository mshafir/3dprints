import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import craft_drawers as cd  # noqa: E402
import fea  # noqa: E402


def test_solver_matches_a_textbook_cantilever():
    # a strip like the stop leaf: 1.2 thick, 20 wide, 30 long, clamped at
    # z = 0, 1 N sideways at the free end
    L, b, h, F = 30.0, 20.0, 1.2, 1.0
    beam = cd.box(0, h, 0, b, 0, L)
    r = fea.solve(beam, size=1.0, fixed=lambda x: x[2] < 1e-6, loads=[(lambda x: x[2] > L - 1e-6, (F, 0, 0))])
    inertia = b * h**3 / 12
    tip = F * L**3 / (3 * fea.PLA.E * inertia)
    root = F * L * (h / 2) / inertia
    assert r.displacement(lambda x: x[2] > L - 1e-6)[0] == pytest.approx(tip, rel=0.1)
    assert r.max_stress(axis=2, region=lambda x: x[2] < 3.0) == pytest.approx(root, rel=0.2)
