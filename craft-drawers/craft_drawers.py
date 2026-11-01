"""Four-drawer craft chest for an 8 in deep shelf, with a printed key that
turns one rod to lock every drawer.

Run `uv run craft_drawers.py` from this folder to write STEP and STL files to
out/.

Every part is modelled where it sits in use: x across (0 at the centre, +x on
the lock side, the right seen from the front), y from the frame's front face
into the frame, z up from the bottom. Drawers are built closed and the rod at
a given angle: the direction its cams point, counter-clockwise from +x seen
from above. The print functions turn each part onto the bed.
"""

import math
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq

LOCKED = 180  # cams point -x, at the drawers' tabs
UNLOCKED = 270  # cams point forward, clear of the tabs
SHAPES = ("circle", "triangle", "square", "star")  # pulls, bottom drawer up


@dataclass(frozen=True)
class Params:
    # Outside
    width: float = 203.2  # 8 in
    depth: float = 184.0  # the pulls take it to 200.4 on an 8 in shelf
    height: float = 248.0
    side: float = 1.8
    cap: float = 2.0  # top and bottom
    back: float = 1.2
    edge_r: float = 3.0  # outside vertical edges

    bays: int = 4

    # Ledges the drawers run on: a strip on each side wall, no shelves
    ledge_t: float = 1.6
    ledge_under: float = 6.0  # how far under the drawer
    head_gap: float = 1.0  # drawer top to the ledge above, so a tipped drawer stays put

    # Drawer
    gap_left: float = 2.0  # room for the stop rail
    column: float = 16.0  # drawer's right wall to the frame's right inner face: the lock rod
    wall: float = 1.2
    floor: float = 1.2
    back_clr: float = 1.0
    front_t: float = 2.4
    front_gap: float = 1.0  # between neighbouring fronts
    front_r: float = 4.0

    # Pulls
    pull_size: float = 34.0
    pull_proud: float = 14.0

    # Lock: a rod behind the front post, with one cam per drawer. Locked, a
    # cam stands in a notch in its drawer's fin, ahead of the tab behind it.
    rod_r: float = 3.5
    rod_dx: float = 9.0  # rod axis from the drawer's right wall
    rod_y: float = 13.0
    stile: float = 2.0  # front post ahead of the rod
    cam_r: float = 8.5  # axis to tip
    cam_w: float = 6.0
    cam_h: float = 5.0
    cam_z: float = 24.5  # cam bottom above the drawer's underside
    fin_reach: float = 4.0
    fin_z: float = 20.0  # fin bottom above the drawer's underside; 45 degree chamfer to fin_z + 4
    fin_h: float = 10.0
    lock_clr: float = 0.5
    fork_clr: float = 0.3

    # Rod head, under the keyhole tube in the badge
    head_r: float = 4.7
    head_len: float = 5.0
    flange_r: float = 5.5  # stops the rod lifting out of its floor socket
    flange_t: float = 1.0
    bore_r: float = 5.0
    tube_wall: float = 1.3
    tube_len: float = 16.0
    socket_depth: float = 5.0
    key_depth: float = 17.0  # badge top to the socket mouth: past a fingertip
    pin_depth: float = 4.0
    boss_h: float = 4.0  # floor boss holding the rod's foot

    # Socket: three lobes round a hub
    hub_r: float = 1.5
    lobe_r: float = 1.0
    lobe_at: float = 2.2
    key_clr: float = 0.15

    # Detent: a leaf in the tube wall presses a nub into notches in the head
    det_press: float = 0.7
    nub_r: float = 1.0
    notch_r: float = 1.1
    det_w: float = 4.0

    # Lock badge on top, over the slot the rod goes in by
    badge_t: float = 3.0
    badge_x: tuple = (76.0, 101.0)
    badge_y: tuple = (-1.0, 33.0)
    badge_chamfer: float = 1.0
    screws: tuple = ((88.0, 3.0), (95.0, 27.5))
    screw_pilot: float = 2.6
    screw_clear: float = 3.4
    cbore_r: float = 3.25
    cbore_d: float = 1.8
    boss_r: float = 3.5
    boss_len: float = 10.0

    # Drawer stop: a leaf in the drawer's left wall carries a nub that meets
    # the back end of a rail on the frame's left wall
    leaf_w: float = 10.0
    leaf_slit: float = 0.6
    leaf_back: float = 4.0  # leaf's back edge ahead of the inside of the drawer's back wall
    nub_out: float = 1.2
    nub_h: float = 6.0
    nub_top: float = 4.0  # nub top below the wall top
    rail_out: float = 1.5
    stop_frac: float = 2 / 3

    # Dividers
    div_t: float = 1.4
    rib: float = 1.0
    rib_w: float = 1.2
    div_slot: float = 1.8
    div_xs: tuple = (-45.0, 0.0, 45.0)  # from the drawer's centre

    # Decoration and feet
    decor_depth: float = 0.6
    decor_size: float = 30.0
    bump_r: float = 6.0
    bump_d: float = 0.8
    bump_inset: float = 15.0

    bed: float = 250.0  # largest part either way; the P1S bed is 256


P = Params()


# --- Sizes --------------------------------------------------------------------


def pitch(p=P):
    return (p.height - 2 * p.cap) / p.bays


def bay_z(i, p=P):
    """Floor of bay i, where its ledges sit."""
    return p.cap + i * pitch(p)


def inner_x(p=P):
    """The side walls' inner faces."""
    return -p.width / 2 + p.side, p.width / 2 - p.side


def drawer_box(p=P):
    """The closed drawer's box without its front plate: x0, x1, y0, y1, height."""
    xl, xr = inner_x(p)
    x0 = xl + p.gap_left
    x1 = xr - p.column
    return x0, x1, 0.0, p.depth - p.back - p.back_clr, pitch(p) - p.ledge_t - p.head_gap


def drawer_z(i, p=P):
    """Underside of drawer i."""
    return bay_z(i, p) + p.ledge_t


def inside(p=P):
    """A drawer's inside: width, length, depth."""
    x0, x1, y0, y1, h = drawer_box(p)
    return x1 - x0 - 2 * p.wall, y1 - y0 - p.wall, h - p.floor


def rod_xy(p=P):
    return drawer_box(p)[1] + p.rod_dx, p.rod_y


def cam_span(i, p=P):
    z0 = drawer_z(i, p) + p.cam_z
    return z0, z0 + p.cam_h


def travel_stop(p=P):
    """How far a drawer pulls out before its nub meets the rail."""
    return p.stop_frac * drawer_box(p)[3]


def outside(p=P):
    """Width, depth with the pulls, height with the lock badge."""
    return p.width, p.depth + p.front_t + p.pull_proud, p.height + p.badge_t


# --- Solid-building helpers ---------------------------------------------------


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl(r, z0, z1, x=0.0, y=0.0):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(r).extrude(z1 - z0)


def rprism(w, d, r, z0, z1):
    """Rounded-rectangle prism centred on the z axis."""
    s = cq.Workplane("XY").workplane(offset=z0).rect(w, d).extrude(z1 - z0)
    return s.edges("|Z").fillet(r) if r > 0 else s


def loft(pts0, z0, pts1, z1):
    """Ruled solid from polygon pts0 at z0 to polygon pts1 at z1."""
    w = cq.Workplane("XY").workplane(offset=z0).polyline(pts0).close()
    return w.workplane(offset=z1 - z0).polyline(pts1).close().loft(ruled=True)


def prism(pts, z0, z1):
    return loft(pts, z0, pts, z1)


def combo(*parts):
    return cq.Workplane(obj=cq.Compound.makeCompound([s for p in parts for s in p.solids().vals()]))


def cut_all(part, cutters):
    """Cut many solids in one boolean. They must not overlap one another."""
    return part.cut(combo(*cutters)) if cutters else part


def turn(part, deg, x=0.0, y=0.0):
    return part.rotate((x, y, 0), (x, y, 1), deg)


def shape_pts(name, size):
    """Outline of a pull or decoration shape, centred on 0, about `size`
    across; None for the circle."""
    if name == "circle":
        return None
    if name == "square":
        h = size * 0.44
        return [(-h, -h), (h, -h), (h, h), (-h, h)]
    if name == "triangle":
        r = size * 0.58  # circumradius; the side is about `size`
        return [(r * math.cos(math.radians(90 + 120 * k)), r * math.sin(math.radians(90 + 120 * k)) - r * 0.25) for k in range(3)]
    if name == "star":
        r = size / 2
        return [((r if k % 2 == 0 else 0.42 * r) * math.cos(math.radians(90 + 36 * k)), (r if k % 2 == 0 else 0.42 * r) * math.sin(math.radians(90 + 36 * k))) for k in range(10)]
    raise ValueError(name)


def overhang_area(part, max_deg=48.0, allow=()):
    """Area (mm^2) of downward faces flatter than `max_deg` from vertical,
    ignoring the face on the bed and any inside the `allow` solids, which are
    planned bridges. The margin over 45 degrees absorbs meshing error on the
    45 degree faces."""
    verts, tris = part.val().tessellate(0.02, 0.1)
    zmin = min(v.z for v in verts)
    limit = -math.sin(math.radians(max_deg))
    total = 0.0
    for i, j, k in tris:
        a, b, c = verts[i], verts[j], verts[k]
        n = (b - a).cross(c - a)
        if n.Length < 1e-12:
            continue
        if n.z / n.Length < limit and (a.z + b.z + c.z) / 3 > zmin + 0.05:
            m = (a + b + c) * (1 / 3)
            if any(s.val().isInside(m, 0.01) for s in allow):
                continue
            total += n.Length / 2
    return total


def grams(part):
    """Solid PLA weight; the print is lighter where infill replaces solid."""
    return part.val().Volume() / 1000 * 1.24
