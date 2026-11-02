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
import pyamg
import scipy.sparse.linalg as spla
from skfem import Basis, ElementTetP2, ElementVector, FacetBasis, LinearForm, MeshTet, asm, condense
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


# Stresses this close to where a load is pressed on are left out: a force
# spread over a small patch makes a local peak in a linear model that a real
# contact, which spreads and beds in, does not have (Saint-Venant).
NEAR_LOAD = 1.5  # mm


@dataclass
class Result:
    basis: Basis
    u: np.ndarray
    stress: np.ndarray  # (3, 3, elements, points)
    points: np.ndarray  # (3, elements, points): where each stress is
    loaded: np.ndarray  # (3, n): midpoints of the loaded faces

    def away(self, region=None):
        """Mask of stress points outside `region`'s complement and clear of the loads."""
        pts = self.points.reshape(3, -1)
        keep = np.ones(pts.shape[1], dtype=bool)
        for c in np.array_split(self.loaded, max(1, self.loaded.shape[1] // 200), axis=1):
            d = np.min(np.linalg.norm(pts[:, :, None] - c[:, None, :], axis=0), axis=1)
            keep &= d > NEAR_LOAD
        keep = keep.reshape(self.points.shape[1:])
        if region is not None:
            keep &= region(self.points)
        return keep

    def displacement(self, region):
        """Mean displacement of the mesh nodes in `region`."""
        m = self.basis.mesh
        nodes = np.nonzero(region(m.p))[0]
        dofs = self.basis.nodal_dofs[:, nodes]
        return self.u[dofs].mean(axis=1)

    def max_stress(self, axis, region=None):
        """Largest tension along `axis` (0, 1, 2 for x, y, z)."""
        return float(np.where(self.away(region), self.stress[axis, axis], -np.inf).max())

    def max_von_mises(self, region=None):
        s = self.stress
        vm = np.sqrt(0.5 * ((s[0, 0] - s[1, 1]) ** 2 + (s[1, 1] - s[2, 2]) ** 2 + (s[2, 2] - s[0, 0]) ** 2) + 3 * (s[0, 1] ** 2 + s[1, 2] ** 2 + s[0, 2] ** 2))
        return float(np.where(self.away(region), vm, -np.inf).max())


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
    loaded = []
    for select, force in loads:
        facets = m.facets_satisfying(select, boundaries_only=True)
        loaded.append(m.p[:, m.facets[:, facets]].mean(axis=1))
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
    u = skfem_solve(K, f, basis.get_dofs(facets=clamp).all(), rigid_modes(basis))
    uh = basis.interpolate(u)
    stress = linear_stress(lam, mu)(sym_grad(uh))
    return Result(basis, u, np.asarray(stress), basis.mapping.F(basis.X), np.hstack(loaded))


def rigid_modes(basis):
    """The six rigid-body motions at every degree of freedom: smoothed
    aggregation multigrid needs them to work on elasticity at all."""
    comp = np.zeros(basis.N, dtype=int)
    for c in range(3):
        comp[basis.nodal_dofs[c]] = c
        comp[basis.edge_dofs[c]] = c
    x, y, z = basis.doflocs
    B = np.zeros((basis.N, 6))
    for c in range(3):
        B[comp == c, c] = 1.0
    rot = [((0, -y), (1, x)), ((1, -z), (2, y)), ((2, -x), (0, z))]
    for k, pairs in enumerate(rot):
        for c, v in pairs:
            B[comp == c, 3 + k] = v[comp == c]
    return B


def skfem_solve(K, f, D, B):
    """Conjugate gradients with an algebraic multigrid preconditioner: a
    direct solve takes tens of minutes on the larger crops. If it has not
    converged, solve directly rather than return a wrong answer."""
    A, b, x, I = condense(K, f, D=D)
    A = A.tocsr()
    ml = pyamg.smoothed_aggregation_solver(A, B=B[I], max_coarse=500)
    residuals = []
    xi = ml.solve(b, tol=1e-10, accel="cg", maxiter=2000, residuals=residuals)
    if residuals[-1] > 1e-8 * residuals[0]:
        xi = spla.spsolve(A.tocsc(), b)
    out = np.zeros(K.shape[0])
    out[I] = xi
    return out


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


def drawer_crop(lo, hi, p=cd.P):
    return cd.make_drawer(0, p).intersect(cd.box(lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))


def latch_region(p=cd.P):
    lx, ly = cd.latch_x(p), cd.latch_y(p)
    z = cd.drawer_z(0, p)
    lo = (lx["left"] - 2.0, ly["anchor"] - 8, z)
    hi = (lx["end"] + 2.0, ly["back"] + 0.4, z + p.tunnel_h + p.tunnel_roof + p.latch_tab + 1)
    return lx, ly, z, lo, hi


def latch(p=cd.P, size=0.6):
    """The drawer stop: the ledge's nub, at the corner of its slanted back,
    pushes the crossbar back. Drawers print upright, so their layers are
    across z."""
    lx, ly, z, lo, hi = latch_region(p)
    part = drawer_crop(lo, hi, p)
    face = lambda x: near(x[1], ly["face"]) & (x[0] > lx["chan"]) & (x[0] < lx["wall_r"]) & (x[2] > z + p.latch_fillet + 0.3) & (x[2] < z + p.latch_nub_h)
    r = solve(part, size, crop_faces(lo, hi, (0, 1)), [(face, (0, 1.0, 0))])
    return breaking_load(r, 2)


def latch_lift(p=cd.P, size=0.6):
    """Lifting the crossbar by its tab to take a drawer out: the force it
    takes, and the strips' stress (along their printed lines) when lifted."""
    lx, ly, z, lo, hi = latch_region(p)
    part = drawer_crop(lo, hi, p)
    top = z + p.tunnel_h + p.tunnel_roof + p.latch_tab
    tab = lambda x: near(x[2], top)
    r = solve(part, size, crop_faces(lo, hi, (0, 1)), [(tab, (0, 0, 1.0))])
    rise = r.displacement(lambda x: (x[1] > ly["face"]) & (x[1] < ly["back"]) & (x[0] > lx["left"]) & (x[0] < lx["end"]))[2]
    force = p.latch_lift / rise
    return force, r.max_von_mises() * force


def frame_crop(lo, hi, p=cd.P):
    return cd.make_frame(p).intersect(cd.box(lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))


def latch_nub(p=cd.P, size=0.5):
    """The rail on the ledge, pushed forward along its top back edge by the
    crossbar. The frame prints on its back, so its layers are across y."""
    lx = cd.latch_x(p)
    xa, xb = lx["chan"] + 0.5, lx["wall_r"] - 0.5
    ys = cd.latch_nub_y(p)
    z = cd.drawer_z(1, p)
    lo = (lx["left"] - 6, ys - 15, z - p.ledge_t - 0.5)
    hi = (lx["end"] + 4, ys + 10, z + p.latch_nub_h + 1)
    part = frame_crop(lo, hi, p)
    edge = lambda x: near(x[1], ys) & (x[2] > z + p.latch_fillet + 0.3) & (x[0] > xa) & (x[0] < xb)  # the square face above the crossbar's bevel
    r = solve(part, size, crop_faces(lo, hi, (0, 1)), [(edge, (0, -1.0, 0))])
    return breaking_load(r, 1)


def stop_post(p=cd.P, size=0.6):
    """The post in front of a cam: past locked, the cam's front presses its
    back corner, by the drawer. The cam turns about the rod, so the post
    takes the pull times the cam's lever over its own."""
    xa, xb = cd.stop_post_x(p)
    x, y = cd.rod_xy(p)
    ys = p.rod_y - p.cam_w / 2 - p.pocket_clr
    z0, z1 = cd.cam_span(1, p)
    lo = (xa - 1, -0.5, cd.bay_z(1, p) - 4)
    hi = (cd.inner_x(p)[1] + 0.5, 30, cd.bay_z(2, p) + 4)
    part = frame_crop(lo, hi, p)
    corner = lambda x_: (x_[0] > xa - 0.01) & (x_[0] < xa + 0.8) & (x_[1] > ys - 0.8) & (x_[2] > z0) & (x_[2] < z1)
    r = solve(part, size, crop_faces(lo, hi, (0, 2)), [(corner, (0, -1.0, 0))])
    return breaking_load(r, 1) * (x - xa) / lever(p)


def pocket_post(p=cd.P, size=0.8):
    """The cam presses on the back of its pocket."""
    x1 = cd.drawer_box(p)[1]
    y0, y1 = cd.pocket_y(p)
    z0, z1 = cd.cam_span(0, p)
    dz = cd.drawer_z(0, p)
    lo = (x1 - 14, -p.front_t - 0.01, dz)
    hi = (x1 + 0.01, y1 + 12, dz + 30)
    part = drawer_crop(lo, hi, p)
    face = lambda x: near(x[1], y1) & (x[0] < x1) & (x[2] > z0 - 1) & (x[2] < z1 + 1)
    r = solve(part, size, crop_faces(lo, hi, (0, 1)), [(face, (0, 1.0, 0))])
    return breaking_load(r, 2)


def cam(p=cd.P, size=0.6):
    """A locked cam: its pocket pushes the back of its tip forward, and its
    front rests on the post. The rod prints lying with its cams up, so its
    layers are across the cam's length (x when locked)."""
    x, y = cd.rod_xy(p)
    z0, z1 = cd.cam_span(1, p)
    lo = (x - p.cam_r - 1, y - 8, z0 - 10)
    hi = (x + 8, y + 8, z1 + 10)
    part = cd.make_rod(cd.LOCKED, p).intersect(cd.box(lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    x1 = cd.drawer_box(p)[1]
    xa, xb = cd.stop_post_x(p)
    back = lambda x_: near(x_[1], y + p.cam_w / 2) & (x_[0] < x1)
    post = lambda x_: near(x_[1], y - p.cam_w / 2) & (x_[0] > xb - 1.0) & (x_[0] < xb)
    held = lambda x_: crop_faces(lo, hi, (2,))(x_) | post(x_)
    r = solve(part, size, held, [(back, (0, -1.0, 0))])
    return breaking_load(r, 0)


def click(p=cd.P, size=0.5):
    """The key's click: the collar pushes the nub on the frame's arm aside.
    Returns the arm's force at full press (N), the torque to turn the key
    past it (N mm), and the arm's stress across the frame's layers (y) at
    full press (MPa)."""
    x, y = cd.rod_xy(p)
    xr = cd.inner_x(p)[1]
    z0, z1 = cd.collar_z(p)
    lo = (x + 1.0, y - 4, z0 - 1)
    hi = (xr + 0.5, y + p.arm_len + 10, z1 + 1)
    part = frame_crop(lo, hi, p)
    tip = x + p.collar_r - p.det_press
    nub = lambda x_: (x_[0] < tip + 0.3) & (np.abs(x_[1] - y) < p.nub_r)
    r = solve(part, size, lambda x_: near(x_[0], hi[0]) | near(x_[1], hi[1]), [(nub, (1.0, 0, 0))])
    move = r.displacement(lambda x_: (x_[0] < tip + 0.3) & (np.abs(x_[1] - y) < p.nub_r))[0]
    force = p.det_press / move
    # Climbing the V-notch's 45 degree side, the turning force at the
    # collar's rim about equals the arm's force
    return force, force * p.collar_r, r.max_stress(1) * force


STRENGTH = ("latch", "latch_nub", "stop_post", "pocket_post", "cam")


def main(names=(), p=cd.P):
    """Report every check, or only the ones named (one at a time uses less
    memory): `uv run fea.py latch click`."""
    names = names or STRENGTH + ("click", "latch_lift")
    for name in names:
        if name in STRENGTH:
            print(f"{name:12s} breaks at a {globals()[name](p):.0f} N pull (needs {YANK:.0f})", flush=True)
        elif name == "click":
            force, torque, stress = click(p)
            print(f"click        {force:.1f} N, {torque:.0f} N mm to turn the key past it, {stress:.1f} MPa across layers", flush=True)
        elif name == "latch_lift":
            force, stress = latch_lift(p)
            print(f"latch_lift   {force:.1f} N to lift it free, {stress:.1f} MPa in its strips", flush=True)
        else:
            raise SystemExit(f"no check {name!r}")


if __name__ == "__main__":
    import sys

    main(tuple(sys.argv[1:]))
