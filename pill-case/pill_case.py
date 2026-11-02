"""Four-week click-dial pill case for a 0.4 mm nozzle FDM printer.

Run `uv run pill_case.py` from this folder to write STEP and STL files to out/.
All parts are modelled assembled, z up, which is also their print orientation.
Angles are degrees, anticlockwise seen from above; pocket 0 (week 1 Sunday) is
at +Y and the days run clockwise.
"""

import math
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq


@dataclass(frozen=True)
class Params:
    # tablet
    pill_d: float = 7.5  # tablets stand on edge in the pockets
    pill_t: float = 3.0

    # pockets
    n: int = 28
    floor: float = 1.2
    pk_depth: float = 8.7
    pk_w: float = 3.7  # straight slot, so a tablet can only stand facing sideways, edge to the centre
    pk_rin: float = 31.0
    pk_rout: float = 39.2
    pk_fillet: float = 0.5
    wall: float = 1.6
    # vertical ribs round the base, to tell it from a smooth case by feel
    ribs: int = 40
    rib_h: float = 0.7
    rib_w: float = 1.8

    # hub sprocket (day detent) and post
    sp_r: float = 14.0
    notch: float = 1.5  # V-notch depth
    detent_angle: float = 41.0  # flank angle from radial; steeper holds harder, below ~32 it jams
    detent_clr: float = 0.15  # nub flanks sit this far (radially) inside the notch
    post_r: float = 6.0
    lug_out: float = 2.5
    lug_hw: float = 3.2
    lug_flat: float = 1.0
    lug_undercut: float = 10.0  # degrees; makes the dial hooks pull tighter under load

    # lid
    lid_t: float = 1.2  # over the pockets; keep thin for clarity
    lid_thick: float = 3.4  # hub zone, rim and rail height
    lid_overhang: float = 0.8  # rim past the base wall, for grip
    rim_w: float = 1.9
    thick_r: float = 20.5
    bore_clr: float = 0.15
    arm_t: float = 2.9
    arm_slot: float = 1.2
    arm_sweep: float = 80.0  # degrees of arc per flex arm
    nub: float = 1.3  # nub height; sits `notch - nub` clear of the notch root
    scallops: int = 56

    # door: printed in place inside a slot through the lid, so it is captive.
    # The slot is also the window, and its ends are the open and closed stops.
    door_hw: float = 3.4
    door_len: float = 11.2
    door_t: float = 3.0
    door_y0: float = 28.5  # inner end when closed
    door_travel: float = 9.0
    edge_z: float = 1.9  # top of the vertical part of the door edge
    lip: float = 0.9  # overhang above and ledge below that hold the door in
    track_clr: float = 0.3  # print-in-place gap
    rail_w: float = 2.1
    ridge_h: float = 2.0

    # door latch: a flex arm in each rail, inboard of the pockets, with a nub
    # that sits behind the door when closed and in a door notch when open
    door_arm: float = 1.0
    door_slot: float = 0.9
    door_arm_y0: float = 20.0
    door_arm_y1: float = 29.7
    door_nub: float = 0.5

    # dial cap and bayonet
    dial_gap: float = 0.2  # axial play between lid and dial
    dial_r: float = 29.0
    dial_t: float = 4.2
    dial_bore_clr: float = 0.25
    seat_gap: float = 0.15  # dial lift before the lugs catch
    key_clr: float = 0.3
    bayonet_twist: float = 60.0
    latch_gap: float = 0.6  # slot between the dial and the latch arm
    latch_t: float = 1.3  # dial latch arm thickness
    latch_slot: float = 2.4  # room behind the arm to flex over the lug
    latch_nub: float = 1.8  # how far the latch hook overlaps the lug
    latch_root: float = 45.0  # degrees anticlockwise of the lug where the arm is rooted
    latch_ramp: float = 18.0  # degrees the hook's lead-in ramp spans
    latch_nose: float = 5.0  # degrees of blunt tip on the hook, so it is not a sliver

    # finger pockets: an opening inside each latch arm, partway along it, to
    # push the arm out with a fingertip or nail and free the hook
    access_wall_r: float = 10.3  # outer face of the dial wall around the lug seat
    latch_ri: float = 13.8  # inner face of the latch arm
    access_a0: float = -12.0  # pocket span, degrees from the lug
    access_a1: float = 16.0
    text_h: float = 0.6
    day_size: float = 4.0
    week_size: float = 5.0
    week_r: float = 20.5

    @property
    def pitch(self):
        return 360.0 / self.n

    @property
    def H(self):
        return self.floor + self.pk_depth

    @property
    def R(self):
        return self.pk_rout + self.wall

    @property
    def lid_R(self):
        return self.R + self.lid_overhang

    @property
    def bore_r(self):
        return self.sp_r + self.bore_clr

    @property
    def z_lid(self):  # top of the thin lid zone
        return self.H + self.lid_t

    @property
    def z_rail(self):  # top of rails, rim and hub zone
        return self.H + self.lid_thick

    @property
    def z_dial(self):
        return self.z_rail + self.dial_gap

    @property
    def z_top(self):
        return self.z_dial + self.dial_t

    @property
    def lug_r(self):
        return self.post_r + self.lug_out

    @property
    def latch_ro(self):
        return self.latch_ri + self.latch_t


P = Params()
DAYS = "SMTWTFS"


# --- helpers ---------------------------------------------------------------


def cyl(r, z0, z1):
    return cq.Workplane("XY").workplane(offset=z0).circle(r).extrude(z1 - z0)


def tube(r_in, r_out, z0, z1):
    return (
        cq.Workplane("XY").workplane(offset=z0).circle(r_out).circle(r_in).extrude(z1 - z0)
    )


def box(x0, x1, y0, y1, z0, z1):
    return (
        cq.Workplane("XY")
        .box(x1 - x0, y1 - y0, z1 - z0, centered=False)
        .translate((x0, y0, z0))
    )


def rot(wp, deg):
    return wp.rotate((0, 0, 0), (0, 0, 1), deg)


def ring(pts_rz):
    """Solid of revolution about Z from an (r, z) profile."""
    solid = cq.Workplane("XY").polyline(pts_rz).close().revolve(360, (0, 0, 0), (0, 1, 0))
    return solid.rotate((0, 0, 0), (1, 0, 0), 90)


def prism_y(pts_xz, y0, y1):
    """(x, z) profile extruded along Y."""
    solid = cq.Workplane("XY").polyline(pts_xz).close().extrude(y1 - y0)
    return solid.rotate((0, 0, 0), (1, 0, 0), 90).translate((0, y1, 0))


def prism_x(pts_yz, x0, x1):
    """(y, z) profile extruded along X."""
    solid = cq.Workplane("XY").polyline(pts_yz).close().extrude(x1 - x0)
    return solid.rotate((0, 0, 0), (1, 1, 1), 120).translate((x0, 0, 0))


def wedge(a0, a1, z0, z1, r=100.0):
    steps = max(2, int(abs(a1 - a0) / 10) + 2)
    pts = [(0.0, 0.0)]
    for i in range(steps):
        a = math.radians(a0 + (a1 - a0) * i / (steps - 1))
        pts.append((r * math.cos(a), r * math.sin(a)))
    return cq.Workplane("XY").workplane(offset=z0).polyline(pts).close().extrude(z1 - z0)


def polar(r, deg):
    return (r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg)))


def plate(pts_xy, z0, z1):
    """(x, y) outline extruded along Z."""
    return cq.Workplane("XY").workplane(offset=z0).polyline(pts_xy).close().extrude(z1 - z0)


def vees(r, depth, half_angle, z0, z1, count, start, shift=0.0):
    """`count` rhombus prisms on a circle, pointed along the radius: the inner
    tip `depth` inside r, flanks `half_angle` from the radius. `shift` moves
    each one outward, keeping its tip at r - depth."""
    d = depth + shift
    w = d * math.tan(math.radians(half_angle))
    c = r + shift
    one = plate([(c - d, 0), (c, w), (c + d, 0), (c, -w)], z0, z1)
    out = rot(one, start)
    for i in range(1, count):
        out = out.union(rot(one, start + i * 360.0 / count))
    return out


def line_at_r(a, b, r):
    """Point at radius r on the line through a and b, on b's far side of a."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    qa = dx * dx + dy * dy
    qb = 2 * (a[0] * dx + a[1] * dy)
    qc = a[0] ** 2 + a[1] ** 2 - r * r
    t = (-qb + math.sqrt(qb * qb - 4 * qa * qc)) / (2 * qa)
    return (a[0] + t * dx, a[1] + t * dy)


def lug_edge(p=P):
    """Half-angle of a bayonet lug at its outer radius."""
    return math.degrees(math.asin(p.lug_hw / p.lug_r))


def lug_side(p=P, gap=0.0):
    """Two points (inner, outer) on the clockwise side of the lug at angle 0.
    The side leans in toward the lug's root, so a hook against it is pulled
    toward the post instead of being cammed outward. `gap` is in degrees."""
    r_in = p.post_r - 0.5
    lean = math.degrees(math.tan(math.radians(p.lug_undercut)) * (p.lug_r - r_in) / r_in)
    return polar(r_in, -lug_edge(p) + lean - gap), polar(p.lug_r, -lug_edge(p) - gap)


def door_nub_y(p=P):
    """Y of the centre of the rail nubs: just inboard of the closed door."""
    return p.door_y0 - 0.3


def nub_outline(x_root, x_tip, yc, grow=0.0):
    """Plan outline of a latch nub or its notch: flat tip with 45 degree ramps."""
    half = 0.2 + grow
    run = abs(x_root - x_tip)
    return [(x_root, yc - half - run), (x_tip, yc - half), (x_tip, yc + half), (x_root, yc + half + run)]


def latch_free(p=P):
    """Angle of the free end of the latch arm for the lug at 0."""
    return -lug_edge(p) - p.latch_ramp - 1.5


def finger_push(p=P):
    """How far a finger in the pocket must push the arm out to free the hook.
    The arm swings out further beyond the push, like a cantilever loaded at x
    of its length L: hook/push = 1 + 1.5 (L - x) / x."""
    r = (p.latch_ri + p.latch_ro) / 2
    L = math.radians(p.latch_root - latch_free(p)) * r
    x = math.radians(p.latch_root - (p.access_a0 + p.access_a1) / 2) * r
    return (p.latch_nub + 0.3) / (1 + 1.5 * (L - x) / x)


def combo(*parts):
    """Several separate solids as one object, for print-in-place export."""
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound([q.val() for q in parts])])


def pocket_angle(k, p=P):
    return 90.0 - k * p.pitch


# --- parts -----------------------------------------------------------------


def make_base(p=P):
    body = cyl(p.R, 0, p.H).edges("<Z").chamfer(0.5)
    slot = (
        box(p.pk_rin, p.pk_rout, -p.pk_w / 2, p.pk_w / 2, 0, p.pk_depth + 1)
        .edges("<Z")
        .fillet(p.pk_fillet)
        .translate((0, 0, p.floor))
    )
    for k in range(p.n):
        body = body.cut(rot(slot, pocket_angle(k, p)))

    # Triangular ribs, their foot cut back at 50 degrees to match the chamfer
    rib = plate([(p.R - 0.3, -p.rib_w / 2), (p.R + p.rib_h, 0), (p.R - 0.3, p.rib_w / 2)], 0, p.H)
    ribs = rib
    for k in range(1, p.ribs):
        ribs = ribs.union(rot(rib, k * 360 / p.ribs))
    foot = ring([(0, 0), (p.R - 0.5, 0), (p.R + p.rib_h, 0.5 + 1.2 * (p.rib_h + 0.5)), (p.R + p.rib_h, p.H), (0, p.H)])
    body = body.union(ribs.intersect(foot))

    sprocket = cyl(p.sp_r, p.H, p.z_dial).cut(
        vees(p.sp_r, p.notch, p.detent_angle, p.H, p.z_dial, p.n, 90)
    )
    post = cyl(p.post_r, p.z_dial, p.z_top)
    z_lug = p.z_top - p.lug_flat - p.lug_out
    lugs = ring(
        [
            (p.post_r - 1, z_lug),
            (p.post_r, z_lug),
            (p.lug_r, z_lug + p.lug_out),
            (p.lug_r, p.z_top),
            (p.post_r - 1, p.z_top),
        ]
    )
    inner, outer = lug_side(p)
    far = line_at_r(inner, outer, p.lug_r + 2)
    wing = plate([inner, far, (far[0], -far[1]), (inner[0], -inner[1])], 0, p.z_top + 1)
    lugs = lugs.intersect(wing.union(rot(wing, 180)))
    return body.union(sprocket).union(post).union(lugs)


def make_lid(p=P):
    z0, zt, zk = p.H, p.z_lid, p.z_rail
    tw = p.door_hw + p.track_clr
    s0 = p.door_y0 - p.door_travel - p.track_clr
    s1 = p.door_y0 + p.door_len + p.track_clr
    zc = (z0 - 1, zk + 1)

    # Rim with a rounded top and a chamfered bottom edge so nothing is sharp.
    rim_ri = p.lid_R - p.rim_w
    rim = (
        ring([(rim_ri, z0), (p.lid_R - 0.4, z0), (p.lid_R, z0 + 0.4), (p.lid_R, zk), (rim_ri, zk)])
        .edges(">Z")
        .fillet(0.7)
    )
    lid = tube(p.bore_r, rim_ri + 0.1, z0, zt).union(tube(p.bore_r, p.thick_r, z0, zk)).union(rim)

    def rails(width, y0, y1):
        r = box(tw - p.lip, tw + width, y0, y1, z0, zk).edges("|Y and >Z").chamfer(0.4)
        return r.union(r.mirror("YZ"))

    # Wide where the latch arms are cut (all inboard of the pockets), narrow
    # over the pocket ring to keep the view of the neighbouring pockets.
    split = p.door_arm_y1 + 0.8
    wide = p.door_arm + p.door_slot + 1.2
    lid = lid.union(
        rails(wide, s0 - 1.7, split)
        .union(rails(p.rail_w, split, p.lid_R + 5))
        .intersect(cyl(rim_ri + 0.2, 0, zk + 1))
    )

    # The slot the door lives in. It goes right through the lid and is closed
    # at both ends. It is narrower at the bottom and at the top than in the
    # middle, so the door can neither drop out nor lift out.
    e = z0 + p.edge_z + 0.1  # lip sits a little high so the sloped gap is not pinched
    half = [
        (tw - p.lip, zc[0]),
        (tw - p.lip, z0),
        (tw, z0 + p.lip),
        (tw, e),
        (tw - p.lip, e + p.lip),
        (tw - p.lip, zc[1]),
    ]
    track = prism_y(half + [(-x, z) for x, z in reversed(half)], s0, s1)
    lid = lid.cut(track)

    back = box(tw + p.door_arm, tw + p.door_arm + p.door_slot, p.door_arm_y0, p.door_arm_y1 + 0.6, *zc)
    end = box(tw - p.lip - 0.1, tw + p.door_arm + p.door_slot, p.door_arm_y1, p.door_arm_y1 + 0.6, *zc)
    nub = plate(nub_outline(tw + 0.2, p.door_hw - p.door_nub, door_nub_y(p)), z0, e - 0.2)
    for cut_a, cut_b, add in (
        (back, end, nub),
        (back.mirror("YZ"), end.mirror("YZ"), nub.mirror("YZ")),
    ):
        lid = lid.cut(cut_a).cut(cut_b).union(add)

    # Two flex arms cut from the hub zone, each with a nub riding the sprocket.
    # They are mirror images, both running away from the door so they can be
    # long; the nubs are at 0 and 180 degrees.
    arm_ro = p.bore_r + p.arm_t
    nub = vees(p.bore_r, p.nub, p.detent_angle, z0, zk, 1, 0, shift=p.detent_clr)
    arc = tube(arm_ro, arm_ro + p.arm_slot, z0 - 1, zk + 1).intersect(
        wedge(-p.arm_sweep, 8.9, z0 - 1, zk + 1)
    )
    end = rot(box(p.bore_r - 1, arm_ro + p.arm_slot, -0.5, 0.5, z0 - 1, zk + 1), 7)
    lid = lid.union(nub).cut(arc).cut(end)
    lid = lid.union(nub.mirror("YZ")).cut(arc.mirror("YZ")).cut(end.mirror("YZ"))

    grip = (
        cq.Workplane("XY")
        .workplane(offset=z0 - 1)
        .polarArray(p.lid_R + 1.6, 0, 360, p.scallops)
        .circle(2.0)
        .extrude(zk - z0 + 2)
    )
    return lid.cut(grip)


def make_door(p=P):
    """Door in its closed position, which is also how it is printed."""
    z0, y0, y1 = p.H, p.door_y0, p.door_y0 + p.door_len
    hw, top_hw = p.door_hw, p.door_hw - p.lip
    e, z_top = z0 + p.edge_z, z0 + p.door_t
    half = [
        (hw - p.lip - 0.1, z0),
        (hw, z0 + p.lip + 0.1),
        (hw, e),
        (top_hw, e + p.lip),
        (top_hw, z_top),
    ]
    door = prism_y(half + [(-x, z) for x, z in reversed(half)], y0, y1)
    ridge = (
        box(-top_hw + 0.2, top_hw - 0.2, y1 - 1.4, y1, z_top - 0.1, z_top + p.ridge_h)
        .edges("not <Z")
        .fillet(0.5)
    )

    # Inner corners are ramped to ride over the rail nubs; the notches catch
    # the nubs when the door is open.
    c = p.door_nub + p.track_clr
    corner = plate([(hw - c - 0.1, y0 - 0.1), (hw + 0.1, y0 + c + 0.1), (hw + 0.1, y0 - 0.1)], z0 - 1, z_top + 1)
    notch = plate(
        nub_outline(hw + 0.1, hw - p.door_nub - 0.25, door_nub_y(p) + p.door_travel, grow=0.25),
        z0 - 1,
        z_top + 1,
    )
    door = door.union(ridge)
    for cut in (corner, notch, corner.mirror("YZ"), notch.mirror("YZ")):
        door = door.cut(cut)
    return door


def make_labels(p=P):
    """Raised weekday letters at the rim and week numbers further in."""
    def label(s, size, r, angle):
        t = cq.Workplane("XY").text(s, size, p.text_h + 0.1, kind="bold")
        return rot(t.translate((0, r, p.z_top - 0.1)), angle - 90)

    out = None
    for k in range(p.n):
        lab = label(DAYS[k % 7], p.day_size, p.dial_r - 3.7, pocket_angle(k, p))
        out = lab if out is None else out.union(lab)
    for w in range(4):
        out = out.union(label(str(w + 1), p.week_size, p.week_r, pocket_angle(7 * w + 3, p)))
    return out


def make_dial(p=P, text=True):
    zd0, zd1 = p.z_dial, p.z_top
    bore = p.post_r + p.dial_bore_clr
    pocket_r = p.lug_r + p.key_clr
    key_hw = p.lug_hw + p.key_clr
    # Angle at which a lug's corner meets the end stop, plus a little slack.
    stop = lug_edge(p) + 0.5

    dial = cyl(p.dial_r, zd0, zd1).faces(">Z").edges().chamfer(0.6).faces("<Z").edges().chamfer(0.4)
    dial = dial.cut(cyl(bore, zd0 - 1, zd1 + 1))
    z_seat = zd1 - p.lug_flat - p.lug_out - p.seat_gap + (bore - p.post_r)
    seat = ring(
        [
            (bore - 0.2, z_seat),
            (bore, z_seat),
            (pocket_r, z_seat + pocket_r - bore),
            (pocket_r, zd1 + 1),
            (bore - 0.2, zd1 + 1),
        ]
    )
    edge = lug_edge(p)
    key_r = pocket_r + 0.2  # keyway radius
    arm_ri, arm_ro = p.latch_ri, p.latch_ro
    zc = (zd0 - 1, zd1 + 1)
    for a in (0, 180):
        key = box(0, key_r + 1, -key_hw, key_hw, *zc).intersect(cyl(key_r, *zc))
        dial = dial.cut(rot(key, a - p.bayonet_twist))
        sweep = wedge(a - p.bayonet_twist - stop, a + stop, zd0, zd1 + 1)
        dial = dial.cut(seat.intersect(sweep))

        # Latch: a flex arm rooted anticlockwise of the locked lug and running
        # clockwise over it, with a hook at its free end that drops in behind
        # the lug once the dial is twisted home. Trying to untwist pulls on
        # the arm rather than pushing it, so it cannot bow out of the way, and
        # the hook and lug faces lean the same way (see lug_side), so the pull
        # draws the hook in tighter. To open, push both arms outward with a
        # finger in the pockets inside them, and twist.
        tip = a - edge + 5.5  # clear of the leaning lug side
        free, root = a + latch_free(p), a + p.latch_root
        b0, b1 = a + p.access_a0, a + p.access_a1
        relief = tube(bore - 0.1, arm_ri, *zc).intersect(wedge(a - p.bayonet_twist, tip, *zc))
        gap = tube(arm_ri - p.latch_gap, arm_ri, *zc)
        gap = gap.intersect(wedge(free - 4, b0, *zc)).union(gap.intersect(wedge(b1, root, *zc)))
        back = tube(arm_ro, arm_ro + p.latch_slot, *zc).intersect(wedge(free - 4, root, *zc))
        end = tube(arm_ri - p.latch_gap, arm_ro + p.latch_slot, *zc).intersect(wedge(free - 4, free, *zc))
        hole = tube(p.access_wall_r, arm_ri, *zc).intersect(wedge(b0, b1, *zc))

        inner, outer = lug_side(p, gap=0.6)
        f_in = line_at_r(inner, outer, p.lug_r - p.latch_nub)
        nose = polar(p.lug_r - p.latch_nub, math.degrees(math.atan2(f_in[1], f_in[0])) - p.latch_nose)
        hook = rot(
            plate(
                [
                    line_at_r(inner, outer, arm_ri + 0.3),
                    f_in,
                    nose,
                    polar(arm_ri, -edge - p.latch_ramp),
                    polar(arm_ri + 0.3, -edge - p.latch_ramp),
                ],
                zd0,
                zd1,
            ),
            a,
        )
        dial = dial.cut(relief).cut(gap).cut(back).cut(end).cut(hole).union(hook)

    for w in range(4):
        groove = box(p.dial_r - 9, p.dial_r + 1, -0.4, 0.4, zd1 - 0.4, zd1 + 1)
        dial = dial.cut(rot(groove, 90 + p.pitch / 2 - 7 * w * p.pitch))

    if text:
        dial = dial.union(make_labels(p))
    return dial


# --- placement of the moving parts -------------------------------------------


def lid_at(lid, days, p=P):
    """Lid turned clockwise by `days` pockets."""
    return rot(lid, -days * p.pitch)


def door_at(door, shift):
    """Door slid `shift` mm toward the centre (0 closed, door_travel open)."""
    return door.translate((0, -shift, 0))


def dial_at(dial, turn, lift):
    """Dial turned `turn` degrees anticlockwise from locked and raised `lift` mm."""
    return rot(dial, turn).translate((0, 0, lift))


# --- checks and export -------------------------------------------------------


def overhang_area(part, max_deg=46.0):
    """Area (mm^2) of downward faces flatter than `max_deg` from vertical,
    ignoring the face on the bed."""
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
            total += n.Length / 2
    return total


def make_pocket_test(p=P, widths=(3.7, 4.0, 4.3)):
    """A strip of tablet pockets at full depth in a few slot widths, each
    width engraved beside its slot. The middle one is the real pocket."""
    gap, label_w = 3.0, 5.0
    pitch = max(widths) + gap
    y_end = len(widths) * pitch / 2
    x0, x1 = -p.wall - label_w, p.pk_rout - p.pk_rin + p.wall
    block = box(x0, x1, -y_end, y_end, 0, p.H).edges("|Z").fillet(1.0)
    for i, w in enumerate(widths):
        y = (i - (len(widths) - 1) / 2) * pitch
        slot = box(0, p.pk_rout - p.pk_rin, y - w / 2, y + w / 2, p.floor, p.H + 1)
        block = block.cut(slot.edges("<Z").fillet(p.pk_fillet))
        txt = (
            cq.Workplane("XY")
            .text(f"{w:.1f}", 2.6, 0.7, kind="bold")
            .rotate((0, 0, 0), (0, 0, 1), -90)
            .translate((-p.wall - label_w / 2, y, p.H - 0.6))
        )
        block = block.cut(txt)
    return block


def fit_test_parts(p=P):
    """Small pieces covering every sliding or snapping fit."""
    base, lid, door, dial = make_base(p), make_lid(p), make_door(p), make_dial(p)
    return {
        "test_hub_base": base.intersect(cyl(p.thick_r - 2, p.H - 2, 50)),
        "test_hub_lid": lid.intersect(cyl(p.thick_r, 0, 50)),
        # wide enough to include the latch arms and the dial around them
        "test_hub_dial": make_dial(p, text=False).intersect(cyl(p.latch_ro + p.latch_slot + 2.5, 0, 50)),
        "test_door": combo(lid.intersect(box(-11, 11, 17.6, 50, 0, 50)), door),
        "test_pocket": make_pocket_test(p),
    }


def on_bed(part):
    return part.translate((0, 0, -part.val().BoundingBox().zmin))


def colour_bands(part, cuts):
    """Slice a part standing on the bed into horizontal bands at `cuts`."""
    edges = [-1.0] + list(cuts) + [1000.0]
    return [part.intersect(box(-500, 500, -500, 500, lo, hi)) for lo, hi in zip(edges, edges[1:])]


def colour_cuts(p=P):
    """Heights above the bed where a part changes colour: the dial's raised
    letters start at its top face."""
    return {"dial": [p.dial_t]}


def main(out=Path(__file__).parent / "out"):
    out.mkdir(exist_ok=True)
    base, lid, door, dial = make_base(), make_lid(), make_door(), make_dial()
    asm = cq.Assembly()
    for name, part, color in (
        ("base", base, "gray20"),
        ("lid", lid, "lightblue"),
        ("door", door, "lightblue"),
        ("dial", dial, "gray20"),
    ):
        asm.add(part, name=name, color=cq.Color(color))
    asm.export(str(out / "assembly.step"))

    parts = {"base": base, "lid_with_door": combo(lid, door), "dial": dial}
    parts.update(fit_test_parts())
    for name, part in parts.items():
        part = on_bed(part)
        cq.exporters.export(part, str(out / f"{name}.step"))
        cq.exporters.export(part, str(out / f"{name}.stl"), tolerance=0.01, angularTolerance=0.1)
        # The same part in bands, left in place, for printing in more than one colour
        if name in colour_cuts():
            for i, band in enumerate(colour_bands(part, colour_cuts()[name])):
                cq.exporters.export(band, str(out / f"{name}.band{i}.stl"), tolerance=0.01, angularTolerance=0.1)
        bb = part.val().BoundingBox()
        print(f"{name:14s} {bb.xlen:6.1f} x {bb.ylen:6.1f} x {bb.zlen:5.1f} mm")


if __name__ == "__main__":
    main()
