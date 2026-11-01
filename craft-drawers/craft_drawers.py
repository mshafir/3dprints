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


def leaf_y(p=P):
    """Front and back of the stop leaf in the drawer's left wall."""
    y1 = drawer_box(p)[3] - p.wall - p.leaf_back
    return y1 - p.leaf_w, y1


def nub_front_y(p=P):
    """The nub's flat front face, drawer closed."""
    return leaf_y(p)[0] + 1.0


def nub_z(i, p=P):
    top = drawer_z(i, p) + drawer_box(p)[4] - p.nub_top
    return top - p.nub_h, top


def stop_y(p=P):
    """Back end of the stop rail."""
    return nub_front_y(p) - travel_stop(p)


def slot(p=P):
    """The opening in the top the rod goes in by: x0, x1, y0, y1."""
    x, y = rod_xy(p)
    r = p.bore_r + p.tube_wall + 0.3
    return drawer_box(p)[1], x + r, y - r, y + r


def fork_zs(p=P):
    """Heights where the rod is held: the forks in bays 1 up, and the floor boss."""
    return [p.cap + p.boss_h] + [bay_z(i, p) + p.ledge_t / 2 for i in range(1, p.bays)]


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


def grow(pts, d):
    """A polygon with every edge moved outward by d (inward if d < 0)."""
    if sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1])) < 0:
        pts = pts[::-1]  # counter-clockwise, so the right of each edge is outside
    lines = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        length = math.hypot(x1 - x0, y1 - y0)
        nx, ny = (y1 - y0) / length, -(x1 - x0) / length
        lines.append(((x0 + nx * d, y0 + ny * d), (x1 - x0, y1 - y0)))
    out = []
    for ((ax, ay), (adx, ady)), ((bx, by), (bdx, bdy)) in zip(lines[-1:] + lines[:-1], lines):
        t = ((bx - ax) * bdy - (by - ay) * bdx) / (adx * bdy - ady * bdx)
        out.append((ax + adx * t, ay + ady * t))
    return out


def teardrop(r, z0, z1, x=0.0, y=0.0, toward=1):
    """Upright cylinder with a 45 degree point toward +y (toward=1) or -y, so
    it prints lying on the frame's back: a boss points +y, a hole -y."""
    k = r / math.sqrt(2)
    tip = [(x - k, y + toward * k), (x, y + toward * r * math.sqrt(2)), (x + k, y + toward * k), (x, y)]
    return cyl(r, z0, z1, x, y).union(prism(tip, z0, z1))


def shape_on_side(name, u, v, size, x_out, inward, depth, extra=0.1):
    """A shape recessed into a side wall with 45 degree walls: (u, v) is its
    centre in (y, z), x_out the wall's outside, inward -1 on the right side
    and +1 on the left."""
    x_in = x_out + inward * depth
    x_far = x_out - inward * extra
    pts = shape_pts(name, size)
    if pts is None:
        r = size / 2
        lo, hi = sorted([(x_in, r - depth), (x_far, r + extra)])
        return cq.Workplane(obj=cq.Solid.makeCone(lo[1], hi[1], hi[0] - lo[0], cq.Vector(lo[0], u, v), cq.Vector(1, 0, 0)))
    a = [(u + py, v + pz) for py, pz in grow(pts, -depth)]
    b = [(u + py, v + pz) for py, pz in grow(pts, extra)]
    wa = cq.Workplane("YZ").workplane(offset=x_in).polyline(a).close()
    return wa.workplane(offset=x_far - x_in).polyline(b).close().loft(ruled=True)


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


# --- Frame --------------------------------------------------------------------


def shell(p=P):
    """The outside box: front edges rounded, back edges chamfered so they
    print on the bed."""
    s = box(-p.width / 2, p.width / 2, 0, p.depth, 0, p.height)
    s = s.edges("|Z and <Y").fillet(p.edge_r)
    return s.edges("|Z and >Y").chamfer(p.edge_r / 2)


def ledges(p=P):
    xl, xr = inner_x(p)
    x0, x1 = drawer_box(p)[:2]
    y1 = p.depth - p.back
    out = []
    for i in range(p.bays):
        z = bay_z(i, p)
        out.append(box(xl - 0.1, x0 + p.ledge_under, 0, y1 + 0.1, z, z + p.ledge_t))
        right = box(x1 - p.ledge_under, xr + 0.1, 0, y1 + 0.1, z, z + p.ledge_t)
        if i > 0:
            right = right.cut(fork_notch(z, p))
        out.append(right)
    return out


def fork_notch(z, p=P):
    """Notch round the rod in a right ledge, open toward the drawers. The
    front arm bears on the rod; past the rod its edge runs off forward at 45
    degrees so it prints."""
    x, y = rod_xy(p)
    r = p.rod_r + p.fork_clr
    xe = drawer_box(p)[1] - p.ledge_under - 1
    flat = x - p.rod_r + 1.0  # the arm stays square across the rod's front
    pts = [(x + r, y - r), (x + r, y + r), (xe, y + r), (xe, y - r - (flat - xe)), (flat, y - r)]
    return prism(pts, z - 0.1, z + p.ledge_t + 0.1)


def floor_boss(p=P):
    x, y = rod_xy(p)
    return teardrop(p.rod_r + 2, p.cap - 0.1, p.cap + p.boss_h, x, y)


def rod_socket(p=P):
    x, y = rod_xy(p)
    top = p.cap + p.boss_h
    return teardrop(p.rod_r + p.fork_clr, top - p.pin_depth, top + 0.1, x, y, toward=-1)


def rails(p=P):
    """Stop rails on the left inner face: ramped at the front, square at the back."""
    xl = inner_x(p)[0]
    y0, y1 = 0.5, stop_y(p)
    pts = [(xl - 0.1, y0), (xl, y0), (xl + p.rail_out, y0 + p.rail_out), (xl + p.rail_out, y1), (xl - 0.1, y1)]
    return [prism(pts, *nub_z(i, p)) for i in range(p.bays)]


def screw_bosses(p=P):
    xl, xr = inner_x(p)
    top = p.height - p.cap
    room = box(xl, xr, 0, p.depth - p.back, p.cap, top + 0.1)
    return [teardrop(p.boss_r, top - p.boss_len, top + 0.1, x, y).intersect(room) for x, y in p.screws]


def screw_holes(p=P):
    return [teardrop(p.screw_pilot / 2, p.height - p.cap - p.boss_len - 0.1, p.height + 0.1, x, y, toward=-1) for x, y in p.screws]


def top_slot(p=P):
    x0, x1, y0, y1 = slot(p)
    return box(x0, x1, y0, y1, p.height - p.cap - 0.1, p.height + 0.1)


def decor(p=P):
    """One of each shape on each side, recessed."""
    spots = [(55.0, 75.0), (130.0, 75.0), (55.0, 170.0), (130.0, 170.0)]
    out = []
    for side, inward in ((p.width / 2, -1), (-p.width / 2, 1)):
        names = SHAPES if inward < 0 else SHAPES[::-1]
        out += [shape_on_side(n, u, v, p.decor_size, side, inward, p.decor_depth) for n, (u, v) in zip(names, spots)]
    return out


def bumpers(p=P):
    xs = (-p.width / 2 + p.bump_inset, p.width / 2 - p.bump_inset)
    ys = (p.bump_inset, p.depth - p.bump_inset)
    return [cyl(p.bump_r, -0.1, p.bump_d, x, y) for x in xs for y in ys]


def make_frame(p=P):
    xl, xr = inner_x(p)
    body = shell(p).cut(box(xl, xr, -1, p.depth - p.back, p.cap, p.height - p.cap))
    for part in ledges(p) + rails(p) + screw_bosses(p) + [floor_boss(p)]:
        body = body.union(part)
    return cut_all(body, [top_slot(p), rod_socket(p)] + screw_holes(p) + decor(p) + bumpers(p))


def frame_print(part, p=P):
    """Turned onto its back, front up: z = 0 is the back."""
    return part.rotate((0, 0, 0), (1, 0, 0), -90).translate((0, 0, p.depth))


def bridge_zones(p=P):
    """Where the frame, printed on its back, has planned flat undersides, in
    frame coordinates: the rails' square back ends, the fork arms across the
    rod, the slot's edge and the bumper pockets."""
    xl = inner_x(p)[0]
    x, y = rod_xy(p)
    zones = [box(xl - 0.1, xl + p.rail_out + 0.1, stop_y(p) - 0.2, stop_y(p) + 0.2, *nub_z(i, p)) for i in range(p.bays)]
    zones += [box(x - p.rod_r, x + p.rod_r + 1, y - p.rod_r - 0.6, y - p.rod_r, bay_z(i, p) - 0.1, bay_z(i, p) + p.ledge_t + 0.1) for i in range(1, p.bays)]
    x0, x1, y0, y1 = slot(p)
    zones.append(box(x0 - 0.1, x1 + 0.1, y0 - 0.2, y0 + 0.2, p.height - p.cap - 0.1, p.height + 0.1))
    zones += [cyl(p.bump_r + 0.2, -0.1, p.bump_d + 0.1, *c.val().Center().toTuple()[:2]) for c in bumpers(p)]
    return zones


def outside_openings(frame, p=P):
    """Outer faces with a hole through them, probing a thin slab just inside
    each face, deeper than the decoration and bumper recesses; the top's
    badge slot and screw holes, under the badge, are allowed for. Names in the order front, back, left, right,
    bottom, top."""
    w, d, h = p.width / 2, p.depth, p.height
    a, b, m = 0.9, 1.15, p.edge_r + 1
    slabs = {
        "front": box(-w + m, w - m, a, b, m, h - m),
        "back": box(-w + m, w - m, d - b, d - a, m, h - m),
        "left": box(-w + a, -w + b, m, d - m, m, h - m),
        "right": box(w - b, w - a, m, d - m, m, h - m),
        "bottom": box(-w + m, w - m, m, d - m, a, b),
        "top": cut_all(box(-w + m, w - m, m, d - m, h - b, h - a), [top_slot(p)] + screw_holes(p)),
    }
    return [n for n, s in slabs.items() if s.cut(frame).val().Volume() > 0.01]
