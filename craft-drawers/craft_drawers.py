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

LOCKED = 180  # cams point -x, into the drawers' pockets
UNLOCKED = 90  # cams point back: unlocking turns clockwise, so a pull on a
# locked drawer, which turns the cams counter-clockwise, drives each cam into a
# post in the frame right in front of it
SHAPES = ("circle", "triangle", "square", "star")  # recessed in the frame's sides


@dataclass(frozen=True)
class Params:
    # Outside
    width: float = 203.2  # 8 in
    depth: float = 184.0  # the fronts take it to 186.4; the handles stand 22 mm past
    height: float = 248.0
    side: float = 1.8
    cap: float = 2.0  # top and bottom
    back: float = 1.2
    edge_r: float = 3.0  # outside vertical edges

    bays: int = 4

    # Ledges the drawers run on: a strip on each side wall, no shelves
    ledge_t: float = 2.0  # 1.6 let the latch rail bend it: 96 N (fea.latch_nub)
    ledge_under: float = 6.0  # how far under the drawer
    ledge_left: float = 20.0  # the left ledge, under the drawer's stop latch
    head_gap: float = 1.0  # drawer top to the ledge above, so a tipped drawer stays put

    # Drawer
    gap_left: float = 2.0
    column: float = 16.0  # drawer's right wall to the frame's right inner face: the lock rod
    wall: float = 1.2
    floor: float = 1.2
    back_clr: float = 1.0
    front_t: float = 2.4
    front_gap: float = 1.0  # between neighbouring fronts
    front_r: float = 4.0

    # Bar handle, the same on every drawer: two posts and a bar a hand wraps
    # round. Everything under it is 45 degrees, so it prints upright; the bar
    # starts from a point, so only its first lines bridge.
    handle_out: float = 22.0  # front plate to the bar's front
    handle_w: float = 98.0  # outside of the posts
    post_w: float = 8.0
    bar_t: float = 6.0  # front to back
    bar_h: float = 9.0  # top to the point underneath
    handle_up: float = 10.0  # bar top above the front's middle

    # Lock: a rod in the front right corner with one cam per drawer. Locked, a
    # cam reaches into a pocket in its drawer's side; with a drawer open, the
    # drawer's wall is in the cam's way, so the key will not turn. A pull on a
    # locked drawer turns the rod, and a post in the frame in front of each
    # cam stops it.
    rod_r: float = 3.5
    rod_dx: float = 7.5  # rod axis from the drawer's right wall
    rod_y: float = 13.0
    cam_r: float = 10.5  # axis to the square tip: 3 mm into the drawer's wall
    cam_w: float = 6.0
    cam_h: float = 8.0
    cam_z: float = 5.0  # cam bottom above the drawer's underside: low, by the forks, clear of the floor boss
    pocket_clr: float = 0.4
    post_wall: float = 1.2  # behind the pocket, in a post in the drawer's corner
    lock_clr: float = 0.5
    fork_clr: float = 0.55  # round the rod's keel corners, which reach 3.7 mm

    # Rod head, under the keyhole tube in the badge
    head_r: float = 4.7
    head_len: float = 5.0
    flange_r: float = 5.3  # stops the rod lifting out of its floor socket
    flange_t: float = 1.0
    bore_r: float = 5.0
    tube_wall: float = 1.3
    tube_len: float = 16.0
    socket_depth: float = 5.0
    key_depth: float = 17.0  # badge top to the socket mouth: past a fingertip
    pin_depth: float = 6.0  # still 2.7 mm in when the rod is lifted to the tube
    boss_h: float = 6.0  # floor boss holding the rod's foot

    # Socket: three lobes round a hub, clear of the print flat
    hub_r: float = 1.5
    lobe_r: float = 0.95
    lobe_at: float = 1.9
    lobe_a: tuple = (100.0, 220.0, 340.0)  # from the cam direction
    key_clr: float = 0.25  # the socket prints on its side

    # Click: an arm in the frame, running front to back beside the rod's top,
    # presses a nub against a collar on the rod. It drops into a notch when
    # unlocked and onto the rod's print flat when locked.
    collar_r: float = 4.6
    collar_h: float = 22.0
    arm_t: float = 2.8  # 2.2 gave 14 N mm, too soft (fea.click)
    arm_len: float = 36.0
    arm_relief: float = 0.6  # recess in the side wall behind the arm, so it can bend
    arm_clr: float = 0.4  # collar to the arm
    det_press: float = 1.0
    nub_r: float = 1.0


    # Lock badge on top, over the slot the rod goes in by
    badge_t: float = 3.0
    badge_x: tuple = (-15.3, 9.7)  # from the rod's axis
    badge_y: tuple = (-14.0, 24.0)
    badge_chamfer: float = 1.0
    screws: tuple = ((-3.3, 18.5), (5.2, 18.5))  # from the rod's axis: behind the tube and the icons, clear of the top drawer
    screw_pilot: float = 2.6
    screw_clear: float = 3.4
    cbore_r: float = 3.25
    cbore_d: float = 1.8
    boss_r: float = 3.5
    boss_len: float = 10.0
    web: float = 1.6  # runs each screw boss back to the back wall

    # Drawer stop: a nub on the left ledge runs in a covered channel under the
    # drawer's floor and meets a crossbar near the back. The crossbar hangs on
    # two springy floor strips anchored ahead of it, so a pull stretches them;
    # an adult lifts the crossbar's tab to take the drawer out.
    latch_hinge_w: float = 4.0
    latch_t: float = 2.4  # the strips: thick, so the crossbar's push is near their middle and stretches more than bends them
    latch_len: float = 50.0  # the strips, crossbar to anchor
    latch_bar: float = 9.0  # the crossbar, front to back: stiff between the strips
    latch_slit: float = 0.6
    latch_back: float = 4.0  # crossbar to the inside of the back wall
    tunnel_w: float = 6.0  # the rail in it is 1 mm narrower
    tunnel_h: float = 2.4
    tunnel_roof: float = 1.0
    tunnel_wall: float = 1.2
    latch_nub_h: float = 2.0
    latch_fillet: float = 1.0  # at the rail's root, cleared by a bevel on the crossbar
    latch_lift: float = 2.5  # lifting the crossbar this far frees the drawer
    latch_tab: float = 6.0  # finger tab on the crossbar
    stop_frac: float = 2 / 3

    # Dividers
    div_t: float = 1.4
    rib: float = 3.0  # deep enough to hold a divider upright
    rib_w: float = 1.6
    div_slot: float = 1.75  # 0.18 mm each side of the divider
    div_xs: tuple = (-45.0, 0.0, 45.0)  # from the drawer's centre

    # The drawer's shape, recessed in its front left of the handle
    face_size: float = 24.0

    # Decoration and feet
    decor_depth: float = 0.6
    decor_size: float = 30.0
    bump_r: float = 6.0
    bump_d: float = 0.8
    bump_inset: float = 15.0

    # Icons and the key's pointer: V-grooves, which print on the bed face
    groove: float = 0.6  # deep, 45 degree sides

    # Key
    key_size: float = 36.0
    key_grip: float = 4.0
    key_hole_r: float = 2.5

    bed: float = 250.0  # largest part either way; the P1S bed is 256


P = Params()

# A one-drawer chest from the same code, to try the lock, stop, click, key
# and dividers before printing the full chest: narrower, shallower and one
# bay tall, with every moving part the full size.
MINI = Params(width=110.0, depth=100.0, height=65.0, bays=1, handle_w=60.0, face_size=16.0, div_xs=(-20.0, 20.0))


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
    """How far a drawer pulls out before the latch catches."""
    return p.stop_frac * drawer_box(p)[3]


def latch_x(p=P):
    """Left edges, from the drawer's left wall, of the stop latch's strips:
    left strip, channel walls and channel, right strip."""
    x0 = drawer_box(p)[0]
    s, w, tw = p.latch_slit, p.latch_hinge_w, p.tunnel_wall
    a = x0 + p.wall + s  # left strip
    b = a + w + s  # left channel wall
    c = b + tw  # channel
    d = c + p.tunnel_w  # right channel wall
    e = d + tw + s  # right strip
    return {"left": a, "wall_l": b, "chan": c, "wall_r": d, "right": e, "end": e + w}


def latch_y(p=P):
    """Along the drawer, closed: the crossbar's face, its back, and the
    strips' anchor."""
    back = drawer_box(p)[3] - p.wall - p.latch_back
    face = back - p.latch_bar
    return {"face": face, "back": back, "anchor": face - p.latch_len}


def latch_nub_y(p=P):
    """The top back edge of the ledge's rail, which meets the crossbar's face."""
    return latch_y(p)["face"] - travel_stop(p)


def screw_xy(p=P):
    x, y = rod_xy(p)
    return [(x + dx, y + dy) for dx, dy in p.screws]


def slot(p=P):
    """The opening in the top the rod goes in by, cams pointing back:
    x0, x1, y0, y1."""
    x, y = rod_xy(p)
    r = p.bore_r + p.tube_wall + 0.3
    return x - r, x + r, y - r, y + p.cam_r + 0.5


def collar_z(p=P):
    """The click's collar on the rod, just under the flange."""
    top = flange_top(p) - p.flange_t - 2.0
    return top - p.collar_h, top


def stop_post_x(p=P):
    """The posts that stop the cams past locked: between the drawers and the
    rod's keel."""
    return drawer_box(p)[1] + 0.5, rod_xy(p)[0] - rod_reach(p) - 0.6


def fork_zs(p=P):
    """Heights where the rod is held: the forks in bays 1 up, and the floor boss."""
    return [p.cap + p.boss_h] + [bay_z(i, p) + p.ledge_t / 2 for i in range(1, p.bays)]


def outside(p=P):
    """Width, depth with the handles, height with the lock badge."""
    return p.width, p.depth + p.front_t + p.handle_out, p.height + p.badge_t


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


def xz_prism(pts, y0, y1):
    """Prism of an (x, z) outline from y0 to y1."""
    return prism(pts, -y1, -y0).rotate((0, 0, 0), (1, 0, 0), 90)


def yz_prism(pts, x0, x1):
    """Prism of a (y, z) outline from x0 to x1."""
    return prism([(-z, y) for y, z in pts], x0, x1).rotate((0, 0, 0), (0, 1, 0), 90)


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
        return [((r if k % 2 == 0 else 0.5 * r) * math.cos(math.radians(90 + 36 * k)), (r if k % 2 == 0 else 0.5 * r) * math.sin(math.radians(90 + 36 * k))) for k in range(10)]
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
    """Left and right ledge for each bay. Above the bottom bay the right ledge
    has a slot round the rod, open toward the back, that the cams drop
    through pointing back."""
    xl, xr = inner_x(p)
    x0, x1 = drawer_box(p)[:2]
    y1 = p.depth - p.back
    out = []
    for i in range(p.bays):
        z = bay_z(i, p)
        out.append(box(xl - 0.1, x0 + p.ledge_left, 0, y1 + 0.1, z, z + p.ledge_t))
        right = box(x1 - p.ledge_under, xr + 0.1, 0, y1 + 0.1, z, z + p.ledge_t)
        if i > 0:
            right = right.cut(fork_notch(z, p))
        out.append(right)
    return out


def fork_notch(z, p=P):
    """Slot round the rod, open toward the back. Its front is a 45 degree
    point, so it grows from the ledge when the frame prints on its back, and
    the point's sides hold the rod against the pull of a locked drawer."""
    x, y = rod_xy(p)
    r = p.rod_r + p.fork_clr
    y1 = p.depth - p.back + 0.2
    return teardrop(r, z - 0.1, z + p.ledge_t + 0.1, x, y, toward=-1).union(box(x - r, x + r, y, y1, z - 0.1, z + p.ledge_t + 0.1))


def stop_posts(p=P):
    """A post in front of the cams: past locked, each cam's front meets its
    back corner, out by the drawer where the cam's lever on it is longest.
    Its back is 45 degrees, so it prints. Brackets just below and above each
    cam tie it to the side wall, clear of the rod, so the cam pushes on a
    short braced length."""
    xa, xb = stop_post_x(p)
    xr = inner_x(p)[1]
    ys = p.rod_y - p.cam_w / 2 - p.pocket_clr
    post = prism([(xa, 0), (xb, 0), (xb, ys - (xb - xa)), (xa, ys)], p.cap - 0.1, cam_span(p.bays - 1, p)[1] + 3.0)
    depth = rod_xy(p)[1] - p.collar_r - 1.0  # clear of the rod, its keel and collar
    out = [post]
    for i in range(p.bays):
        c0, c1 = cam_span(i, p)
        for z0, z1 in ((drawer_z(i, p) - 0.1, c0 - 0.5), (c1 + 0.5, c1 + 5.0)):  # below and above the cam
            out.append(yz_prism([(0, z0), (depth, z0), (depth - (z1 - z0), z1), (0, z1)], xa, xr + 0.1))
            # Beside the post, as deep as the post, so the edge the cam presses is braced
            out.append(yz_prism([(0, z0), (ys, z0), (ys - (z1 - z0), z1), (0, z1)], xa, xb))
        # 45 degree gusset behind the post, from the ledge up its back edge
        # under the cam: a pull on a locked drawer peaked in that corner. It
        # fills the post's whole width, its 45 degree back included: a gusset
        # only behind the post's back edge leaves a slot beside it that
        # cracks at its root. Above it, the post's back goes from square
        # back to 45 degrees over a slope rather than a step, whose corner
        # was the next weak spot.
        z0, g = drawer_z(i, p) - 0.1, min(4.0, c0 - 0.6 - drawer_z(i, p))
        zt = z0 + g + 0.1
        out.append(yz_prism([(0, z0), (ys + g, z0), (ys - 0.1, zt), (0, zt)], xa, xb))
        out.append(loft([(xa, 0), (xb, 0), (xb, ys - 0.1), (xa, ys - 0.1)], zt - 0.1, [(xa, 0), (xb, 0), (xb, ys - (xb - xa)), (xa, ys)], zt + (xb - xa)))
    return out


def unlock_stop(p=P):
    """Beside the top cam: just past unlocked, the cam's corner meets it."""
    x, y = rod_xy(p)
    xr = inner_x(p)[1]
    xa = x + p.cam_w / 2 + 2.2
    yb = y + p.cam_r + 2.5
    pts = [(xa, y - 4.0), (xr + 0.1, y - 4.0), (xr + 0.1, yb + (xr - xa)), (xa, yb)]
    z = drawer_z(p.bays - 1, p)
    return prism(pts, z - 0.1, cam_span(p.bays - 1, p)[1] + 2.0)


def click_arm(p=P):
    """A springy arm on the frame's right, front to back beside the collar,
    with a nub at its free front end. It bends sideways, so it prints
    standing up on the frame's back."""
    x, y = rod_xy(p)
    xr = inner_x(p)[1]
    xa = x + p.collar_r + p.arm_clr
    z0, z1 = collar_z(p)
    ya, yb = y - p.nub_r - 0.5, y + p.arm_len
    arm = box(xa, xa + p.arm_t, ya, yb + 0.1, z0, z1)
    base = prism([(xa, yb), (xr + 0.1, yb), (xr + 0.1, yb + 3 + (xr - xa)), (xa, yb + 3)], z0, z1)
    tip = x + p.collar_r - p.det_press  # how far in the nub reaches
    nub = teardrop(p.nub_r, z0 + 2, z1 - 2, tip + p.nub_r, y).union(box(tip + p.nub_r, xa + 0.1, y - p.nub_r, y + p.nub_r, z0 + 2, z1 - 2))
    return [arm.union(base).union(nub)]


def arm_relief(p=P):
    """A shallow recess in the side wall behind the click's arm, so a thicker
    arm still has room to bend. Its front end is 45 degrees, so it prints
    with the frame on its back."""
    x, y = rod_xy(p)
    xr = inner_x(p)[1]
    z0, z1 = collar_z(p)
    ya, yb = y - p.nub_r - 0.5, y + p.arm_len
    d = p.arm_relief
    return prism([(xr - 0.1, ya - d - 0.1), (xr + d, ya), (xr + d, yb), (xr - 0.1, yb)], z0, z1)


def latch_nubs(p=P):
    """A rail on each left ledge, from the front to the catch, running in the
    drawer's channel. Its back end is square where the crossbar meets it,
    with a 45 degree fillet below that the crossbar's bevel clears: the
    fillet stiffens the rail's root, and the square face is short enough to
    print."""
    lx = latch_x(p)
    xa, xb = lx["chan"] + 0.5, lx["wall_r"] - 0.5
    ys = latch_nub_y(p)
    h, f = p.latch_nub_h, p.latch_fillet
    out = []
    for i in range(p.bays):
        z = drawer_z(i, p)
        out.append(yz_prism([(1.0, z - 0.1), (ys + f + 0.1, z - 0.1), (ys, z + f), (ys, z + h), (1.0, z + h)], xa, xb))
    return out


def floor_boss(p=P):
    x, y = rod_xy(p)
    return teardrop(p.rod_r + 2, p.cap - 0.1, p.cap + p.boss_h, x, y)


def rod_socket(p=P):
    x, y = rod_xy(p)
    top = p.cap + p.boss_h
    return teardrop(p.rod_r + p.fork_clr, top - p.pin_depth, top + 0.1, x, y, toward=-1)


def screw_bosses(p=P):
    """Hanging from the top wall, each with a web back to the back wall: the
    frame prints on its back, and a boss alone would start in mid-air."""
    xl, xr = inner_x(p)
    top = p.height - p.cap
    room = box(xl, xr, 0, p.depth - p.back + 0.1, p.cap, top + 0.1)
    w = p.web
    return [teardrop(p.boss_r, top - p.boss_len, top + 0.1, x, y).union(box(x - w / 2, x + w / 2, y, p.depth, top - p.boss_len, top + 0.1)).intersect(room) for x, y in screw_xy(p)]


def screw_holes(p=P):
    return [teardrop(p.screw_pilot / 2, p.height - p.cap - p.boss_len - 0.1, p.height + 0.1, x, y, toward=-1) for x, y in screw_xy(p)]


def top_slot(p=P):
    x0, x1, y0, y1 = slot(p)
    return box(x0, x1, y0, y1, p.height - p.cap - 0.1, p.height + 0.1)


def decor(p=P):
    """One of each shape on each side, recessed."""
    spots = [(p.depth * u, p.height * v) for v in (0.3, 0.69) for u in (0.3, 0.7)]
    out = []
    for side, inward in ((p.width / 2, -1), (-p.width / 2, 1)):
        names = SHAPES if inward < 0 else SHAPES[::-1]
        size = min(p.decor_size, 0.35 * p.height)
        out += [shape_on_side(n, u, v, size, side, inward, p.decor_depth) for n, (u, v) in zip(names, spots)]
    return out


def bumpers(p=P):
    xs = (-p.width / 2 + p.bump_inset, p.width / 2 - p.bump_inset)
    ys = (p.bump_inset, p.depth - p.bump_inset)
    return [cyl(p.bump_r, -0.1, p.bump_d, x, y) for x in xs for y in ys]


def make_frame(p=P):
    xl, xr = inner_x(p)
    body = shell(p).cut(box(xl, xr, -1, p.depth - p.back, p.cap, p.height - p.cap))
    for part in ledges(p) + latch_nubs(p) + stop_posts(p) + [unlock_stop(p)] + click_arm(p) + screw_bosses(p) + [floor_boss(p)]:
        body = body.union(part)
    body = body.cut(arm_relief(p))  # on its own: cut_all mishandles overlapping cutters
    return cut_all(body, [top_slot(p), rod_socket(p)] + screw_holes(p) + decor(p) + bumpers(p))


def frame_print(part, p=P):
    """Turned onto its back, front up: z = 0 is the back."""
    return part.rotate((0, 0, 0), (1, 0, 0), -90).translate((0, 0, p.depth))


def bridge_zones(p=P):
    """Where the frame, printed on its back, has planned flat undersides, in
    frame coordinates: the slot's edge, the bumper pockets, and the 1 mm
    square faces on the latch rails."""
    lx = latch_x(p)
    ys = latch_nub_y(p)
    rails = [box(lx["chan"], lx["wall_r"], ys - 0.2, ys + 0.2, drawer_z(i, p) + p.latch_fillet - 0.1, drawer_z(i, p) + p.latch_nub_h + 0.1) for i in range(p.bays)]
    x0, x1, y0, y1 = slot(p)
    zones = rails + [box(x0 - 0.1, x1 + 0.1, y0 - 0.2, y0 + 0.2, p.height - p.cap - 0.1, p.height + 0.1)]
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


# --- Drawers ------------------------------------------------------------------


def front_plate(i, p=P):
    """Covers the frame's edges round the opening. Its bottom is level with
    the drawer's underside, so it prints on the bed with the drawer."""
    z0 = drawer_z(i, p)
    z1 = bay_z(i, p) + pitch(p) - p.front_gap / 2
    w = p.width - p.front_gap
    plate = box(-w / 2, w / 2, -p.front_t, 0, z0, z1)
    plate = plate.edges("|Y and >Z").fillet(p.front_r)
    return plate.edges("|Y and <Z").chamfer(1.0)


def front_mid(i, p=P):
    return (drawer_z(i, p) + bay_z(i, p) + pitch(p) - p.front_gap / 2) / 2


def handle(i, p=P):
    """Bar handle on the front of drawer i."""
    y0 = -p.front_t + 0.1
    yb, yf = -p.front_t - p.handle_out + p.bar_t, -p.front_t - p.handle_out
    zt = front_mid(i, p) + p.handle_up
    shoulder = zt - p.bar_h + p.bar_t / 2  # where the bar's 45 degree underside starts
    bar = yz_prism([(yb, zt), (yb, shoulder), ((yb + yf) / 2, zt - p.bar_h), (yf, shoulder), (yf, zt)], -p.handle_w / 2, p.handle_w / 2)
    post = [(y0, zt), (yf, zt), (yf, shoulder), (y0, shoulder - (y0 - yf))]
    x = p.handle_w / 2
    return bar.union(yz_prism(post, -x, -x + p.post_w)).union(yz_prism(post, x - p.post_w, x))


def handle_grip(i, p=P):
    """The space a hand takes behind the bar: x0, x1, z0, z1, and the bar's
    back face."""
    x = p.handle_w / 2 - p.post_w
    zt = front_mid(i, p) + p.handle_up
    yb = -p.front_t - p.handle_out + p.bar_t
    return -x, x, zt - p.bar_h, zt, yb


def cam_outline(angle, p=P, n=24):
    """Points round a cam's square-tipped outline, seen from above, at `angle`."""
    x, y = rod_xy(p)
    h, t = p.cam_w / 2, p.cam_r
    pts = [(t * k / n, s * h) for k in range(n + 1) for s in (-1, 1)] + [(t, h * k / n) for k in range(-n, n + 1)]
    return [(x + px * math.cos(math.radians(angle)) - py * math.sin(math.radians(angle)), y + px * math.sin(math.radians(angle)) + py * math.cos(math.radians(angle))) for px, py in pts]


def pocket_y(p=P):
    """Front and back of the pocket: room for the cam to swing in from
    unlocked, and no more, so a locked drawer is caught after a few mm."""
    x1 = drawer_box(p)[1]
    inside = [py for a in range(UNLOCKED, LOCKED + 1) for px, py in cam_outline(a, p) if px <= x1 + p.pocket_clr]
    return min(inside) - p.pocket_clr, max(inside) + p.pocket_clr


def pocket(i, p=P):
    """The pocket the cam reaches into, with a 45 degree roof so it prints."""
    x, _ = rod_xy(p)
    x1 = drawer_box(p)[1]
    y0, y1 = pocket_y(p)
    z0, z1 = cam_span(i, p)
    z0, z1 = z0 - p.pocket_clr, z1 + p.pocket_clr
    pts = [(y0, z0), (y1, z0), (y1, z1), ((y0 + y1) / 2, z1 + (y1 - y0) / 2), (y0, z1)]
    return yz_prism(pts, x - p.cam_r - p.pocket_clr, x1 + 0.1)


def pocket_post(i, p=P):
    """Solid corner post inside the drawer that the pocket is cut into."""
    x, _ = rod_xy(p)
    x1 = drawer_box(p)[1]
    y1 = pocket_y(p)[1]
    z0, z1 = cam_span(i, p)
    top = z1 + p.pocket_clr + (y1 - pocket_y(p)[0]) / 2 + p.post_wall
    return box(x - p.cam_r - p.pocket_clr - p.post_wall, x1 - 0.1, -0.1, y1 + p.post_wall, drawer_z(i, p) + 0.1, top)


def face_shape(i, p=P):
    """The drawer's shape, recessed 0.6 mm into its front left of the handle,
    with 45 degree sides."""
    cx = (-(p.width - p.front_gap) / 2 - p.handle_w / 2) / 2
    cz = front_mid(i, p)
    y_out = -p.front_t
    pts = shape_pts(SHAPES[i], p.face_size)

    def wire(y, d):
        if pts is None:
            return cq.Wire.makeCircle(p.face_size / 2 + d, cq.Vector(cx, y, cz), cq.Vector(0, 1, 0))
        return cq.Wire.makePolygon([cq.Vector(cx + u, y, cz + v) for u, v in grow(pts, d)], close=True)

    return cq.Workplane(obj=cq.Solid.makeLoft([wire(y_out - 0.1, 0.1), wire(y_out + p.decor_depth, -p.decor_depth)], True))


def latch_strip(i, p=P):
    """Raised strip along the drawer's left floor: the channel's walls and
    roof, and the latch's two floor strips and crossbar, cut free by slits."""
    lx, ly = latch_x(p), latch_y(p)
    x0, _, y0, y1, _ = drawer_box(p)
    z = drawer_z(i, p)
    top = z + p.tunnel_h + p.tunnel_roof
    channel = box(lx["wall_l"], lx["right"] - p.latch_slit, -p.front_t, y1, z, top)
    bar = prism(crossbar_plan(p), z, top)
    strips = [box(a, b, ly["anchor"] - 2, ly["face"] + 0.1, z, z + p.latch_t) for a, b in ((lx["left"] - p.latch_slit - 1, lx["wall_l"]), (lx["right"] - p.latch_slit, lx["end"] + p.latch_slit + 1))]
    for st in strips:
        channel = channel.union(st)
    tab = box(lx["chan"], lx["wall_r"], ly["face"], ly["face"] + 2.0, top - 0.1, top + p.latch_tab)  # at the front, over the strips' ends
    return channel.union(bar).union(tab)


def crossbar_plan(p=P):
    """The crossbar seen from above. Its face is square across the channel,
    so the ledge nub pushes it straight back along the strips."""
    lx, ly = latch_x(p), latch_y(p)
    f, b = ly["face"], ly["back"]
    return [(lx["left"], f), (lx["end"], f), (lx["end"], b), (lx["left"], b)]


def latch_cuts(i, p=P):
    """The channel under the drawer, and the slits that free the latch."""
    lx, ly = latch_x(p), latch_y(p)
    x0, _, _, y1, _ = drawer_box(p)
    z = drawer_z(i, p)
    s = p.latch_slit
    top = z + p.tunnel_h + p.tunnel_roof + p.latch_tab + 1
    chan = box(lx["chan"], lx["wall_r"], -p.front_t - 0.1, y1 + 0.1, z - 0.1, z + p.tunnel_h).cut(prism(crossbar_plan(p), z - 0.2, z + p.tunnel_h + 0.1))
    a, f, b = ly["anchor"], ly["face"], ly["back"]
    cuts = [
        box(lx["left"] - s, lx["left"], a, b + s, z - 0.1, top),  # outside the left strip
        box(lx["end"], lx["end"] + s, a, b + s, z - 0.1, top),  # outside the right strip
        box(lx["left"] - s, lx["end"] + s, b, b + s, z - 0.1, top),  # behind the crossbar
        box(lx["wall_l"] - s, lx["wall_l"], a, f, z - 0.1, top),  # strip to channel wall, left
        box(lx["right"] - s, lx["right"], a, f, z - 0.1, top),  # and right
        box(lx["wall_l"] - s, lx["right"], f - s, f, z - 0.1, top),  # the channel ahead, from the crossbar
    ]
    # Bevel under the crossbar's face, clearing the rail's root fillet
    bev = p.latch_fillet + 0.3
    cuts.append(yz_prism([(f - 0.1, z - 0.1), (f + bev + 0.1, z - 0.1), (f - 0.1, z + bev + 0.1)], lx["chan"], lx["wall_r"]))
    # Round ends on the slits at the strips' anchor, so they don't crack there
    cuts += [cyl(0.7, z - 0.1, top, x + s / 2, a) for x in (lx["left"] - s, lx["wall_l"] - s, lx["right"] - s, lx["end"])]
    # Ramp under the crossbar's back, so the nub lifts it as the drawer goes in
    rise = p.tunnel_h + 0.2
    ramp = yz_prism([(b + s + 0.1 - rise, z - 0.1), (b + s + 0.1, z - 0.1), (b + s + 0.1, z - 0.1 + rise)], lx["chan"], lx["wall_r"])
    return chan, cuts, ramp


def latch_leaf(i, p=P):
    """The latch's moving part, for lifting it clear: crossbar, tab and strips."""
    lx, ly = latch_x(p), latch_y(p)
    z = drawer_z(i, p)
    top = z + p.tunnel_h + p.tunnel_roof + p.latch_tab + 1
    return prism(crossbar_plan(p), z - 0.1, top).union(box(lx["left"], lx["wall_l"] - p.latch_slit, ly["anchor"], ly["face"], z - 0.1, top)).union(
        box(lx["right"], lx["end"], ly["anchor"], ly["face"], z - 0.1, top))


def div_ribs(i, p=P):
    x0, x1, _, y1, h = drawer_box(p)
    cx = (x0 + x1) / 2
    z0, z1 = drawer_z(i, p) + p.floor - 0.1, drawer_z(i, p) + h
    out = []
    for dx in p.div_xs:
        for s in (-1, 1):
            xa = cx + dx + s * p.div_slot / 2
            xb = xa + s * p.rib_w
            xa, xb = sorted((xa, xb))
            out.append(box(xa, xb, -0.1, p.rib, z0, z1))
            out.append(box(xa, xb, y1 - p.wall - p.rib, y1 - p.wall + 0.1, z0, z1))
    return out


def make_drawer(i, p=P, pressed=False):
    """Drawer i, closed. `pressed` lifts its stop latch clear of the ledge's
    nub, as an adult does to take the drawer out."""
    x0, x1, y0, y1, h = drawer_box(p)
    z = drawer_z(i, p)
    d = box(x0, x1, y0, y1, z, z + h).cut(box(x0 + p.wall, x1 - p.wall, y0 - 0.1, y1 - p.wall, z + p.floor, z + h + 0.1))
    for part in [front_plate(i, p), handle(i, p), pocket_post(i, p), latch_strip(i, p)] + div_ribs(i, p):
        d = d.union(part)
    chan, slits, ramp = latch_cuts(i, p)
    d = d.cut(chan).cut(ramp)
    for slit in slits:  # they meet at the corners, so one at a time
        d = d.cut(slit)
    d = d.cut(pocket(i, p)).cut(face_shape(i, p))
    if pressed:
        leaf = d.intersect(latch_leaf(i, p))
        d = d.cut(latch_leaf(i, p)).union(leaf.translate((0, 0, p.latch_lift)))
    return d


def drawer_bridges(i, p=P):
    """Where a drawer, printed upright, has planned flat undersides: the
    channel's roof, the pocket's floor-level edges."""
    lx = latch_x(p)
    z = drawer_z(i, p)
    return [box(lx["chan"] - 0.2, lx["wall_r"] + 0.2, -p.front_t - 0.2, drawer_box(p)[3] + 0.2, z + p.tunnel_h - 0.2, z + p.tunnel_h + 0.2)]


def drawer_at(i, t, p=P, pressed=False):
    """Drawer i pulled out by t."""
    return make_drawer(i, p, pressed).translate((0, -t, 0))


def drawer_print(part, i, p=P):
    """Upright, the floor and the front plate's bottom on the bed."""
    return part.translate((0, 0, -drawer_z(i, p)))


def make_divider(p=P):
    """Drops into a pair of slots, front to back, splitting the drawer."""
    _, _, _, y1, h = drawer_box(p)
    d = box(-p.div_t / 2, p.div_t / 2, 0.3, y1 - p.wall - 0.3, 0, h - p.floor - 6)
    return d.edges("|X and >Z").fillet(3.0)


def divider_in(i, slot, p=P):
    x0, x1 = drawer_box(p)[:2]
    return make_divider(p).translate(((x0 + x1) / 2 + p.div_xs[slot], 0, drawer_z(i, p) + p.floor + 0.2))


def divider_print(part, p=P):
    return part.rotate((0, 0, 0), (0, 1, 0), 90).translate((0, 0, p.div_t / 2))


# --- Lock ---------------------------------------------------------------------


def mouth_z(p=P):
    """Top of the rod head, where the socket opens."""
    return p.height + p.badge_t - p.key_depth


def rod_flat(p=P):
    """The rod prints lying on a flat on the side away from its cams, as far
    out as the head can be cut without an underside flatter than 45 degrees."""
    return p.head_r * math.sqrt(0.5)


def rod_body(r, z0, z1, p=P):
    """Round rod, with a 45 degree keel out to the flat on the side away from
    the cams (-x, before turning). The keel fits inside the forks and the
    floor socket at every angle the rod turns through."""
    f = rod_flat(p)
    k = r * math.sqrt(0.5)
    keel = [(-k, k), (-f, r * math.sqrt(2) - f), (-f, f - r * math.sqrt(2)), (-k, -k), (0, 0)]
    return cyl(r, z0, z1).union(prism(keel, z0, z1))


def socket(p=P, grow_by=0.0):
    """Three lobes round a hub, at `lobe_a` from the cam direction."""
    z0, z1 = mouth_z(p) - p.socket_depth, mouth_z(p) + 0.1
    s = cyl(p.hub_r + grow_by, z0, z1)
    for a in p.lobe_a:
        c = p.lobe_at * math.cos(math.radians(a)), p.lobe_at * math.sin(math.radians(a))
        s = s.union(cyl(p.lobe_r + grow_by, z0, z1, *c))
    return s


def notch_angles(p=P):
    """Notch directions on the collar, from the cam direction, where the
    arm's nub (fixed at +x) sits when unlocked. Locked, it sits on the rod's
    print flat, which is the other notch."""
    return [(0 - UNLOCKED) % 360]


def make_rod(angle, p=P):
    """The lock rod in place, cams pointing at `angle`."""
    z0 = p.cap + p.boss_h - p.pin_depth + 0.3
    zm = mouth_z(p)
    zh = zm - p.head_len
    rod = rod_body(p.rod_r, z0, zh - p.flange_t, p)
    rod = rod.union(cyl(p.flange_r, zh - p.flange_t, zh)).union(cyl(p.head_r, zh, zm))
    c0, c1 = collar_z(p)
    rod = rod.union(cyl(p.collar_r, c0, c1))
    for i in range(p.bays):
        a0, a1 = cam_span(i, p)
        rod = rod.union(box(0, p.cam_r, -p.cam_w / 2, p.cam_w / 2, a0, a1))
    notches = [turn(prism(collar_notch(p), c0 - 0.1, c1 + 0.1), a) for a in notch_angles(p)]
    f = rod_flat(p)
    rod = cut_all(rod, [socket(p)] + notches).cut(box(-20, -f, -20, 20, 0, p.height + 10))
    return turn(rod, angle).translate((*rod_xy(p), 0))


def collar_notch(p=P):
    """A 90 degree V cut into the collar along +x, deep enough to cradle the
    nub clear of its sides. A V's sides are 45 degrees, so it prints on the
    rod's side."""
    apex = p.collar_r - p.det_press - p.nub_r * (math.sqrt(2) - 1) - 0.2
    far = p.collar_r + 2.0
    return [(apex, 0), (far, far - apex), (far, apex - far)]


def flange_top(p=P):
    return mouth_z(p) - p.head_len


def rod_reach(p=P):
    """Farthest the rod's body reaches from its axis: the keel's corners."""
    f = rod_flat(p)
    return math.hypot(f, p.rod_r * math.sqrt(2) - f)


def socket_wall(p=P):
    """Thinnest wall round the socket: to the head's rim or its flat."""
    walls = [p.head_r - p.lobe_at - p.lobe_r]
    for a in p.lobe_a:
        lx = p.lobe_at * math.cos(math.radians(a))
        walls.append(lx - p.lobe_r + rod_flat(p))
    return min(walls)


def rod_print(part, angle=LOCKED, p=P):
    """Lying on its flat, cams up."""
    x, y = rod_xy(p)
    local = turn(part.translate((-x, -y, 0)), -angle)
    return local.rotate((0, 0, 0), (0, 1, 0), -90).translate((0, 0, rod_flat(p)))


def rod_bridges(angle=LOCKED, p=P):
    """The socket, a hole in the rod's end only 2 to 3 mm across: its roof
    bridges when the rod prints lying down."""
    return turn(socket(p, 0.2), angle).translate((*rod_xy(p), 0))


def groove(a, b, top, p=P):
    """V-groove from a to b in a face at height `top`, opening upward."""
    (ax, ay), (bx, by) = a, b
    length = math.hypot(bx - ax, by - ay)
    w = p.groove + 0.1
    v = yz_prism([(-w, top + 0.1), (w, top + 0.1), (0, top - p.groove)], -p.groove, length + p.groove)
    return turn(v, math.degrees(math.atan2(by - ay, bx - ax))).translate((ax, ay, 0))


def padlock(cx, cy, top, closed, p=P, flip=False):
    """Padlock outline as grooves, 5 x 4 body, shackle toward +y. `flip`
    mirrors it for a face seen from below."""
    pts = [(-2.5, -2.5), (2.5, -2.5), (2.5, 1.5), (-2.5, 1.5)]
    segs = list(zip(pts, pts[1:] + pts[:1]))
    lift = 0.0 if closed else 1.5
    segs += [((-1.5, 1.5 + lift), (-1.5, 4.0 + lift)), ((-1.5, 4.0 + lift), (1.5, 4.0 + lift)), ((1.5, 4.0 + lift), (1.5, 1.5 + (0 if closed else 2.5)))]
    s = -1 if flip else 1
    return [groove((cx + s * ax, cy + ay), (cx + s * bx, cy + by), top, p) for (ax, ay), (bx, by) in segs]


def badge_tube_bottom(p=P):
    return mouth_z(p) - 2.0


def make_badge(p=P):
    """The lock badge in place on top: plate and keyhole tube."""
    x, y = rod_xy(p)
    top = p.height + p.badge_t
    bx0, bx1 = x + p.badge_x[0], x + p.badge_x[1]
    by0, by1 = y + p.badge_y[0], y + p.badge_y[1]
    plate = box(bx0, bx1, by0, by1, p.height, top).edges("|Z").fillet(3.0).faces(">Z").edges().chamfer(p.badge_chamfer)
    ro = p.bore_r + p.tube_wall
    zt = badge_tube_bottom(p)
    b = plate.union(cyl(ro, zt, p.height + 0.1, x, y))
    holes = [cyl(p.bore_r, zt - 0.1, top + 0.1, x, y)]
    for sx, sy in screw_xy(p):
        holes += [cyl(p.screw_clear / 2, p.height - 0.1, top + 0.1, sx, sy).union(cyl(p.cbore_r, top - p.cbore_d, top + 0.1, sx, sy))]
    b = cut_all(b, holes)
    r = 9.5
    icons = padlock(x - r, y, top, True, p) + padlock(x, y + r - 2.0, top, False, p)
    for g in icons:
        b = b.cut(g)
    return b


def badge_bridges(p=P):
    """The counterbores' floors, rings round the screw holes: bridges when
    the badge prints top down."""
    top = p.height + p.badge_t
    return [cyl(p.cbore_r + 0.2, top - p.cbore_d - 0.1, top - p.cbore_d + 0.1, sx, sy) for sx, sy in screw_xy(p)]


def badge_print(part, p=P):
    """Top face down, tube up."""
    return part.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, p.height + p.badge_t))


def covers(part, x0, x1, y0, y1, z, holes=()):
    """True when the part's section at height z covers the rectangle, apart
    from the `holes`."""
    slab = cut_all(box(x0, x1, y0, y1, z - 0.05, z + 0.05), list(holes)).cut(part)
    return slab.val().Volume() < 0.01


def make_key(angle, p=P):
    """The key in place, seated in the socket, its pointer at `angle`."""
    zm = mouth_z(p)
    top = p.height + p.badge_t + 1.0
    tip = socket(p, -p.key_clr).cut(box(-10, 10, -10, 10, zm - 20, zm - p.socket_depth + 0.2)).cut(box(-10, 10, -10, 10, zm + 0.1, zm + 10))
    shaft = cyl(p.bore_r - 0.4, zm + 0.1, top + 0.1).union(cyl(p.hub_r - p.key_clr, zm - 0.1, zm + 0.2))
    star = [(u, v) for u, v in (turn_pt(pt, -90) for pt in shape_pts("star", p.key_size))]
    grip = prism(star, top, top + p.key_grip)
    hc = 9.0 * math.cos(math.radians(180)), 9.0 * math.sin(math.radians(180))
    key = tip.union(shaft).union(grip).cut(cyl(p.key_hole_r, top - 0.1, top + p.key_grip + 0.1, *hc))
    for g in [groove((4.0, 0.0), (13.0, 0.0), top + p.key_grip, p), groove((13.0, 0.0), (10.0, 2.5), top + p.key_grip, p), groove((13.0, 0.0), (10.0, -2.5), top + p.key_grip, p)]:
        key = key.cut(g)
    return turn(key, angle).translate((*rod_xy(p), 0))


def turn_pt(pt, deg):
    a = math.radians(deg)
    return pt[0] * math.cos(a) - pt[1] * math.sin(a), pt[0] * math.sin(a) + pt[1] * math.cos(a)


def key_print(part, p=P):
    """Grip down, pointer groove on the bed face."""
    return part.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, p.height + p.badge_t + 1.0 + p.key_grip))


def hex_key(af, angle, p=P):
    """A hex key `af` across flats, standing in the socket at the rod axis."""
    r = af / math.sqrt(3)
    pts = [turn_pt((r, 0), 60 * k + angle) for k in range(6)]
    zm = mouth_z(p)
    return prism(pts, zm - p.socket_depth + 0.1, zm + 10).translate((*rod_xy(p), 0))


# --- Whole chest --------------------------------------------------------------


def tip_margin(load=300.0, drawer=3, p=P):
    """Moment (g mm) about the frame's front bottom edge with one drawer at
    its stop and `load` grams at its centre. Positive: it stays standing."""
    def m(part, t=0.0):
        c = cq.Shape.centerOfMass(part.val())
        return grams(part), c.y - t

    items = [m(make_frame(p))]
    items += [m(make_drawer(i, p)) for i in range(p.bays) if i != drawer]
    t = travel_stop(p)
    items.append(m(make_drawer(drawer, p).translate((0, -t, 0)), 0.0))
    items.append((load, drawer_box(p)[3] / 2 - t))
    return sum(g * y for g, y in items)


def on_back(part):
    """Turned onto its back like the frame, resting on the bed."""
    t = part.rotate((0, 0, 0), (1, 0, 0), -90)
    return t.translate((0, 0, -t.val().BoundingBox().zmin))


def fit_test_parts(p=P):
    """Small prints to check the keyhole, detent and key before the frame: the
    frame's top corner round the slot, and the top of the rod."""
    x0, x1, y0, y1 = slot(p)
    x, _ = rod_xy(p)
    corner = make_frame(p).intersect(box(x - 21.3, p.width / 2 + 1, -1, 36.0, p.height - 28.0, p.height + 1))
    rod = make_rod(LOCKED, p).intersect(box(-200, 200, -200, 200, p.height - 28.0, p.height))
    return {"test_corner": on_back(corner), "test_rod": rod_print(rod, LOCKED, p)}


def mini_parts(m=MINI):
    """The mini chest's parts, turned to print."""
    rod = make_rod(LOCKED, m)
    return {
        "mini_frame": frame_print(make_frame(m), m),
        "mini_drawer": drawer_print(make_drawer(0, m), 0, m),
        "mini_divider": divider_print(make_divider(m), m),
        "mini_rod": rod_print(rod, LOCKED, m),
        "mini_badge": badge_print(make_badge(m), m),
        "mini_key": key_print(make_key(LOCKED, m), m),
    }


def main(out=Path(__file__).parent / "out", p=P):
    out.mkdir(exist_ok=True)
    frame = make_frame(p)
    drawers = [make_drawer(i, p) for i in range(p.bays)]
    rod, badge, key = make_rod(LOCKED, p), make_badge(p), make_key(LOCKED, p)
    asm = cq.Assembly()
    asm.add(frame, name="frame", color=cq.Color("white"))
    for i, (d, c) in enumerate(zip(drawers, ("red", "yellow", "blue", "green"))):
        asm.add(d, name=f"drawer_{i}", color=cq.Color(c))
    for name, part in (("rod", rod), ("badge", badge), ("key", key)):
        asm.add(part, name=name, color=cq.Color("gray80"))
    asm.export(str(out / "assembly.step"))
    parts = {"frame": frame_print(frame, p)}
    parts |= {f"drawer_{i}": drawer_print(d, i, p) for i, d in enumerate(drawers)}
    parts |= {"divider": divider_print(make_divider(p), p), "rod": rod_print(rod, LOCKED, p), "badge": badge_print(badge, p), "key": key_print(key, p)}
    parts |= fit_test_parts(p)
    parts |= mini_parts()
    for name, part in parts.items():
        bb = part.val().BoundingBox()
        cq.exporters.export(part, str(out / f"{name}.step"))
        cq.exporters.export(part, str(out / f"{name}.stl"), tolerance=0.01, angularTolerance=0.1)
        print(f"{name:12s} {bb.xlen:6.1f} x {bb.ylen:6.1f} x {bb.zlen:5.1f} mm  {grams(part):6.1f} g")
    w, d, h = outside(p)
    total = grams(frame) + sum(grams(x) for x in drawers)
    print(f"chest {w:.1f} x {d:.1f} x {h:.1f} mm, frame and drawers {total:.0f} g")


if __name__ == "__main__":
    main()
