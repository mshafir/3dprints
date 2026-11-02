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


# --- The parts that take a hard pull, and the ones a hand works -------------
#
# Each must hold a 100 N yank on a drawer (fea.YANK) before PLA's strength
# across its layers, or along them, runs out.


@pytest.mark.parametrize("check", ["latch", "latch_nub", "stop_post", "pocket_post", "cam"])
def test_holds_a_hard_yank(check):
    assert getattr(fea, check)() >= fea.YANK


def test_click_is_firm_and_lasts():
    force, torque, stress = fea.click()
    assert 30.0 <= torque <= 150.0  # N mm at the key: a clear click, still easy for an adult
    assert stress <= fea.PLA.across / 1.5  # it bends every turn


def test_latch_lifts_easily():
    force, stress = fea.latch_lift()
    assert force <= 15.0
    assert stress <= fea.PLA.along / 1.5


def test_solver_matches_theory_on_a_slender_strip():
    # long and thin, like the latch's strips: an iterative solver without the
    # right setup stops short here and reports a part ten times too stiff
    L, b, t = 50.0, 4.0, 1.6
    r = fea.solve(cd.box(0, b, 0, L, 0, t), size=0.6, fixed=lambda x: x[1] < 1e-6, loads=[(lambda x: x[1] > L - 1e-6, (0, 0, 1.0))])
    tip = L**3 / (3 * fea.PLA.E * b * t**3 / 12)
    assert r.displacement(lambda x: x[1] > L - 1e-6)[2] == pytest.approx(tip, rel=0.1)
