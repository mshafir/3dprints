"""Strength checks for the craft drawers' load-bearing parts, by finite
elements: Gmsh meshes a CadQuery solid, scikit-fem solves linear elasticity.

Run `uv run fea.py` from this folder for a report.

Every check is a hard pull on a drawer, or a turn of the key, applied to a
part cut out of the model where it sits in use. The results are rough: PLA
is treated as isotropic and linear, and printed parts are weaker across their
layers than along them, so each check compares the stress across the layers
with the weaker strength. Treat a failure load as an order of magnitude, and
the ranking of the parts as the useful answer.
"""

import math
import tempfile
from dataclasses import dataclass
from pathlib import Path

import gmsh
import numpy as np
from skfem import Basis, ElementTetP2, ElementVector, FacetBasis, LinearForm, MeshTet, asm, condense, solve as sksolve
from skfem.helpers import dot, sym_grad
from skfem.models.elasticity import lame_parameters, linear_elasticity, linear_stress

import craft_drawers as cd


@dataclass(frozen=True)
class Material:
    E: float = 3500.0  # MPa
    nu: float = 0.35
    along: float = 40.0  # tensile strength along the printed lines, MPa
    across: float = 20.0  # across the layers: the weak direction


PLA = Material()


def mesh(part, size):
    """Tetrahedral mesh of a CadQuery solid, `size` mm at most."""
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "part.brep")
        part.val().exportBrep(path)
        gmsh.initialize()
        try:
            gmsh.option.setNumber("General.Terminal", 0)
            gmsh.model.occ.importShapes(path)
            gmsh.model.occ.synchronize()
            gmsh.option.setNumber("Mesh.MeshSizeMax", size)
            gmsh.option.setNumber("Mesh.MeshSizeMin", size / 4)
            gmsh.model.mesh.generate(3)
            tags, coords, _ = gmsh.model.mesh.getNodes()
            _, _, conn = gmsh.model.mesh.getElements(3)
        finally:
            gmsh.finalize()
    index = {t: i for i, t in enumerate(tags)}
    p = coords.reshape(-1, 3).T
    t = np.array([index[n] for n in conn[0]]).reshape(-1, 4).T
    used = np.unique(t)  # drop nodes only on surfaces and edges
    remap = -np.ones(p.shape[1], dtype=int)
    remap[used] = np.arange(len(used))
    return MeshTet(p[:, used], remap[t])


@dataclass
class Result:
    basis: Basis
    u: np.ndarray
    stress: np.ndarray  # (3, 3, elements, points)
    points: np.ndarray  # (3, elements, points): where each stress is

    def displacement(self, region):
        """Mean displacement of the mesh nodes in `region`."""
        m = self.basis.mesh
        nodes = np.nonzero(region(m.p))[0]
        dofs = self.basis.nodal_dofs[:, nodes]
        return self.u[dofs].mean(axis=1)

    def max_stress(self, axis, region=None):
        """Largest tension along `axis` (0, 1, 2 for x, y, z)."""
        s = self.stress[axis, axis]
        if region is not None:
            s = np.where(region(self.points), s, -np.inf)
        return float(s.max())

    def max_von_mises(self, region=None):
        s = self.stress
        vm = np.sqrt(0.5 * ((s[0, 0] - s[1, 1]) ** 2 + (s[1, 1] - s[2, 2]) ** 2 + (s[2, 2] - s[0, 0]) ** 2) + 3 * (s[0, 1] ** 2 + s[1, 2] ** 2 + s[0, 2] ** 2))
        if region is not None:
            vm = np.where(region(self.points), vm, -np.inf)
        return float(vm.max())


def solve(part, size, fixed, loads, material=PLA):
    """Clamp the boundary faces whose midpoints satisfy `fixed`, and spread
    each load's total force (N) evenly over the boundary faces its selector
    picks. Lengths in mm, so stresses come out in MPa."""
    m = mesh(part, size)
    e = ElementVector(ElementTetP2())
    basis = Basis(m, e, intorder=3)
    lam, mu = lame_parameters(material.E, material.nu)
    K = asm(linear_elasticity(lam, mu), basis)
    f = np.zeros(basis.N)
    for select, force in loads:
        facets = m.facets_satisfying(select, boundaries_only=True)
        if len(facets) == 0:
            raise ValueError("a load picks no faces")
        fb = FacetBasis(m, e, facets=facets)
        area = asm(LinearForm(lambda v, w: v), FacetBasis(m, ElementTetP2(), facets=facets)).sum()
        traction = np.array(force) / area

        @LinearForm
        def load(v, w, t=traction):
            return t[0] * v[0] + t[1] * v[1] + t[2] * v[2]

        f += asm(load, fb)
    clamp = m.facets_satisfying(fixed, boundaries_only=True)
    if len(clamp) == 0:
        raise ValueError("nothing is clamped")
    u = skfem_solve(K, f, basis.get_dofs(facets=clamp).all())
    uh = basis.interpolate(u)
    stress = linear_stress(lam, mu)(sym_grad(uh))
    return Result(basis, u, np.asarray(stress), basis.mapping.F(basis.X))


def skfem_solve(K, f, D):
    return sksolve(*condense(K, f, D=D))


# --- Checks -------------------------------------------------------------------
#
# Each returns the load at which the part would break (N, or N mm for a
# torque), taking whichever is lower: the stress along the layers against
# `across`, or the largest von Mises stress against `along`. The model is
# linear, so a 1 N solve scales.

YANK = 100.0  # N: a child pulling a drawer hard, about 10 kg
EPS = 1e-3


def near(v, a):
    return np.abs(v - a) < EPS


def crop_faces(lo, hi, axes):
    """Selector for the faces of a crop box on the given axes."""
    return lambda x: np.any([near(x[a], lo[a]) | near(x[a], hi[a]) for a in axes], axis=0)


def breaking_load(r, layer_axis, region=None):
    across = r.max_stress(layer_axis, region)
    vm = r.max_von_mises(region)
    return min(PLA.across / across if across > 0 else np.inf, PLA.along / vm)


def lever(p=cd.P):
    """Rod axis to the middle of the cam's contact in its pocket."""
    x, _ = cd.rod_xy(p)
    reach = cd.drawer_box(p)[1] - (x - p.cam_r)  # how far the cam is in the pocket
    return x - (cd.drawer_box(p)[1] - reach / 2)


def stop_leaf(p=cd.P, size=0.8):
    """The drawer stop: the rail pushes the nub back. Drawers print upright,
    so the layers are across z."""
    x0, _, _, y1, h = cd.drawer_box(p)
    top = cd.drawer_z(0, p) + h
    ly0, ly1 = cd.leaf_y(p)
    lo = (x0 - p.nub_out - 1, ly0 - 6, top - p.leaf_len - 8)
    hi = (x0 + p.wall, min(ly1 + 6, y1 - p.wall), top + 1)  # above the free top edge
    part = cd.make_drawer(0, p).intersect(cd.box(lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    nf = cd.nub_front_y(p)
    nub = lambda x: near(x[1], nf) & (x[0] < x0 - 0.05)
    r = solve(part, size, crop_faces(lo, hi, (1, 2)), [(nub, (0, 1.0, 0))])
    return breaking_load(r, 2)


def leaf_press(p=cd.P, size=0.8):
    """Force to press the stop leaf in far enough to free the drawer."""
    x0, _, _, y1, h = cd.drawer_box(p)
    top = cd.drawer_z(0, p) + h
    ly0, ly1 = cd.leaf_y(p)
    lo = (x0 - p.nub_out - 1, ly0 - 6, top - p.leaf_len - 8)
    hi = (x0 + p.wall, min(ly1 + 6, y1 - p.wall), top + 1)  # above the free top edge
    part = cd.make_drawer(0, p).intersect(cd.box(lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    inside = lambda x: near(x[0], x0 + p.wall) & (x[1] > ly0) & (x[1] < ly1) & (x[2] > top - 6)
    r = solve(part, size, crop_faces(lo, hi, (1, 2)), [(inside, (1.0, 0, 0))])
    move = r.displacement(lambda x: (x[1] > ly0) & (x[1] < ly1) & (x[2] > top - 6) & (x[0] < x0 + 0.01))[0]
    return (p.nub_out + 0.2) / move


def pocket_post(p=cd.P, size=0.8):
    """The cam presses on the back of its pocket."""
    x1 = cd.drawer_box(p)[1]
    y0, y1 = cd.pocket_y(p)
    z0, z1 = cd.cam_span(0, p)
    dz = cd.drawer_z(0, p)
    lo = (x1 - 14, -p.front_t - 0.01, dz)
    hi = (x1 + 0.01, y1 + 12, dz + 45)
    part = cd.make_drawer(0, p).intersect(cd.box(*[v for pair in zip(lo, hi) for v in pair]))
    face = lambda x: near(x[1], y1) & (x[0] < x1) & (x[2] > z0 - 1) & (x[2] < z1 + 1)
    r = solve(part, size, crop_faces(lo, hi, (0, 1)), [(face, (0, 1.0, 0))])
    return breaking_load(r, 2)


def cam(p=cd.P, size=0.6):
    """A locked cam, its pocket pushing on the back of its tip. The rod prints
    lying with its cams up, so the layers are across the cam's length (x
    when locked)."""
    x, y = cd.rod_xy(p)
    z0, z1 = cd.cam_span(0, p)
    lo = (x - 15, y - 8, z0 - 10)
    hi = (x + 8, y + 8, z1 + 10)
    part = cd.make_rod(cd.LOCKED, p).intersect(cd.box(lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    x1 = cd.drawer_box(p)[1]
    back = lambda x_: (x_[0] < x1) & (x_[1] > y + 0.5) & (x_[2] > z0 + 0.05) & (x_[2] < z1 - 0.05)  # the round tip's back half
    r = solve(part, size, crop_faces(lo, hi, (2,)), [(back, (0, -1.0, 0))])
    return breaking_load(r, 0)


def lug(p=cd.P, size=0.5):
    """The lug that stops the rod past locked, as a pull on a drawer turns
    the rod: torque / radius on its side. Layers across its length (x)."""
    x, y = cd.rod_xy(p)
    zh = cd.flange_top(p)
    lo = (x - 8, y - 8, zh - p.lug_h - 6)
    hi = (x + 8, y + 8, zh + 0.5)
    part = cd.make_rod(cd.LOCKED, p).intersect(cd.box(lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    side = lambda x_: near(x_[1], y - p.lug_w / 2) & (x_[0] < x - p.flange_r)
    r = solve(part, size, crop_faces(lo, hi, (2,)), [(side, (0, 1.0, 0))])
    return breaking_load(r, 0) * (p.lug_r + p.flange_r) / 2 / lever(p)


def tooth(p=cd.P, size=0.5):
    """The badge's tooth, pushed by the lug. The badge prints top down, so
    the layers are across z."""
    x, y = cd.rod_xy(p)
    zt = cd.badge_tube_bottom(p)
    lo = (x - 9, y - 9, zt - 8)
    hi = (x + 9, y + 9, zt + 6)
    part = cd.make_badge(p).intersect(cd.box(lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    a0 = math.radians(p.tooth_a[0])
    face = lambda x_: (np.abs((x_[0] - x) * math.sin(a0) - (x_[1] - y) * math.cos(a0)) < 0.02) & (x_[2] < zt)
    push = (math.sin(a0), -math.cos(a0), 0)  # the lug pushes the tooth counter-clockwise
    r = solve(part, size, crop_faces(lo, hi, (2,)), [(face, push)])
    return breaking_load(r, 2) * (p.lug_r + p.flange_r) / 2 / lever(p)
