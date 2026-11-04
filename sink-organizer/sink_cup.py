"""Simplified sink organizer: one wide fluted cup, no baseplate.

Run `uv run sink_cup.py` from this folder to write STEP and STL files to
out/, prefixed `cup_`.

A 6 x 3 cell fluted sleeve stands on a removable drip tray that sits flat on
the counter, with the same wall style and click as the grid organizer
(sink_organizer.py, whose builders this reuses). Separators slide down rails
on the front and back walls at five evenly spaced places and hang down to a
third of the cup's height, leaving the bottom open end to end. The cords of electric toothbrush chargers leave
through a slot in the back wall at the right.

Parts are modelled z up, centred on the origin in x and y; z = 0 is the
counter. The back of the counter is +y and the right is +x.
"""

import math
from dataclasses import dataclass, replace
from pathlib import Path

import cadquery as cq

import sink_organizer as so
from sink_organizer import box, crest_prism, gable, groove, rprism, seat_cone, spigot_off, valley

NX, NY = 6, 3


@dataclass(frozen=True)
class CupParams:
    floor_t: float = 2.4  # tray floor
    rim_z: float = 100.0  # top of the sleeve above the counter
    bottom_chamfer: float = 0.4  # round the tray's bed edge, against elephant's foot
    # Wall: thicker than the grid cups above the latches. Over the top the
    # whole wall, flutes and inside face alike, curves inward on an arc that
    # ends at 45 degrees, so the inside overhang still prints. The flutes run
    # through the curve to the rim.
    wall_t: float = 3.0  # at the bottom of the flutes
    thick_z: float = 24.0  # where the wall steps up from p.wall, above the latches
    roll_in: float = 5.0  # how far the top curves in
    roll_steps: int = 12
    # Separators and the rails they slide down
    stops: tuple = tuple(k / 6 for k in range(1, 6))  # along the inside length:
    # five places, of which any can be left empty
    sep_t: float = 2.0
    sep_clr: float = 0.3  # per side, in the channel between the rails
    sep_end_clr: float = 0.5  # from each end of a separator to the channel
    sep_top: float = 0.5  # separator top below the rim
    sep_lead: float = 1.0  # chamfer on the corners, to start it into the rails
    stop_z: float = 38.0  # the separators rest here, 62% of the way down.
    # Lower and the rails run into the top of the cord slot
    rail_w: float = 2.0
    rail_d: float = 2.5  # how far the rails stand out from the rim's inside face
    rail_top: float = 1.0  # rails end this far below the rim
    cord_margin: float = 2.0  # keeps the cord slot on the flat of the back wall
    # Sections (0 = left) with a cord opening each, for one charger's cord.
    # Empty: one wide slot at the back right for all the cords.
    cords: tuple = ()
    cord_one_w: float = 8.0  # width of a one-cord opening
    name: str = "cup"  # prefix of the part names and files


C = CupParams()

# The grid organizer's heights, dropped so the tray floor is floor_t thick and
# sits on the counter. Everything that stacks on the floor (seat, latches,
# vents, cord slot) moves down with it. Flutes are close set like the
# reference cup's, and as deep as a round flute at that pitch can be.
_drop = so.P.floor_z - C.floor_t
P = replace(
    so.P,
    floor_z=C.floor_t,
    seat_z=so.P.seat_z - _drop,
    pad_z=so.P.pad_z - _drop,
    top_latch_z=so.P.top_latch_z - _drop,
    vent_z=so.P.vent_z - _drop,
    cord_z=so.P.cord_z - _drop,
    rib_d=1.8,
    rib_pitch=4.0,
)


def inner(c=C, p=P):
    """Inside size of the sleeve between the latches and the curve at the top."""
    w, d = valley(NX, NY, p)
    return w - 2 * c.wall_t, d - 2 * c.wall_t


def roll_curve(c=C):
    """(height, [(dz, inset)]) of the curve at the top: an arc from upright to
    45 degrees that moves roll_in inward."""
    a = math.radians(45)
    r = c.roll_in / (1 - math.cos(a))
    pts = [(r * math.sin(a * i / c.roll_steps), r * (1 - math.cos(a * i / c.roll_steps))) for i in range(c.roll_steps + 1)]
    return r * math.sin(a), pts


def stop_xs(c=C, p=P):
    """x of each separator, which divide the inside length evenly."""
    iw, _ = inner(c, p)
    return [-iw / 2 + f * iw for f in c.stops]


def cord_x(c=C, p=P):
    """Centre of the cord slot: in the middle of the right-hand section, or
    as near as the flat of the back wall allows."""
    iw, _ = inner(c, p)
    flat = valley(NX, NY, p)[0] / 2 - so.corner(NX, NY, p)
    return min((iw / 2 + stop_xs(c, p)[-1]) / 2, flat - p.cord_w / 2 - c.cord_margin)


def cords(c=C, p=P):
    """[(x, width)] of each cord opening in the back wall: the one wide slot,
    or one per listed section, in its middle or as near as the flat of the
    back wall allows."""
    if not c.cords:
        return [(cord_x(c, p), p.cord_w)]
    iw, _ = inner(c, p)
    flat = valley(NX, NY, p)[0] / 2 - so.corner(NX, NY, p) - c.cord_one_w / 2 - c.cord_margin
    edges = [-iw / 2, *stop_xs(c, p), iw / 2]
    return [(max(-flat, min(flat, (edges[i] + edges[i + 1]) / 2)), c.cord_one_w) for i in c.cords]


def cord_slots(c=C, p=P):
    """[(sleeve cutter, tray cutter)] for each cord opening in the back wall,
    as in the grid organizer's electric cup."""
    _, d = valley(NX, NY, p)
    y_out = d / 2 + p.rib_d + 1
    out = []
    for x, cw in cords(c, p):
        top = gable(cw, p.pad_z - 1, p.cord_z, d / 2 - spigot_off(p) - p.wall - 1, y_out, x)
        tray = box(x - cw / 2, x + cw / 2, d / 2 - p.wall - 1, y_out, p.floor_z, p.seat_z + 1)
        out.append((top, tray))
    return out


def make_tray(c=C, p=P):
    """Drip tray: a smooth, flat-bottomed dish the sleeve rests on and clicks
    into. It drains out through the cord slot."""
    w, d = valley(NX, NY, p)
    rim = so.base_line(p)
    outer = crest_prism(NX, NY, 0, rim, p).faces("<Z").edges().chamfer(c.bottom_chamfer)
    cavity = rprism(w - 2 * p.wall, d - 2 * p.wall, so.corner(NX, NY, p) - p.wall, p.floor_z, rim + 1)
    tray = outer.cut(cavity).cut(seat_cone(NX, NY, p.seat_z, 8, p))
    g = groove(w / 2 - p.wall, p.top_latch_z, p.top_latch_proud, p.top_latch_w / 2 + 1.5, p)
    tray = tray.cut(g).cut(g.rotate((0, 0, 0), (0, 0, 1), 180))
    for _, cut in cord_slots(c, p):
        tray = tray.cut(cut)
    return tray


def reeded_wire(w, d, r, n, depth, z):
    """Closed ring of n round flutes on a rounded rectangle, at height z."""
    step = (2 * (w + d) - 8 * r + 2 * math.pi * r) / n
    grooves = [cq.Vector(*so.outline_point(w, d, r, k * step)[0], z) for k in range(n)]
    edges = []
    for k in range(n):
        (x, y), (ax, ay) = so.outline_point(w, d, r, (k + 0.5) * step)
        crest = cq.Vector(x + ax * depth, y + ay * depth, z)
        edges.append(cq.Edge.makeThreePointArc(grooves[k], crest, grooves[(k + 1) % n]))
    return cq.Wire.assembleEdges(edges)


def fluted(z0, c=C, p=P):
    """Outer form of the sleeve from z0 to the rim: straight flutes, then the
    curve at the top with the same flutes carried round it."""
    w, d = valley(NX, NY, p)
    r = so.corner(NX, NY, p)
    n, _ = so.rib_step(NX, NY, p)
    h, curve = roll_curve(c)
    zs = c.rim_z - h
    straight = cq.Solid.extrudeLinear(cq.Face.makeFromWires(reeded_wire(w, d, r, n, p.rib_d, z0)), cq.Vector(0, 0, zs - z0))
    wires = [reeded_wire(w - 2 * i, d - 2 * i, r - i, n, p.rib_d, zs + dz) for dz, i in curve]
    top = cq.Solid.makeLoft(wires, True)
    return cq.Workplane(obj=straight).union(cq.Workplane(obj=top))


def inside(c=C, p=P, grow=0.0):
    """The space inside the wall above the seat, `grow` larger all round: the
    grid cups' thin wall up to thick_z, a 45 degree step in to wall_t, then
    the curve at the top, parallel to the outside."""
    w, d = valley(NX, NY, p)
    r = so.corner(NX, NY, p)
    h, curve = roll_curve(c)
    zs = c.rim_z - h
    t0, t1 = p.wall - grow, c.wall_t - grow
    # Faces meet exactly: an overlap leaves a flat sliver where the step
    # narrows, an overhang
    out = rprism(w - 2 * t0, d - 2 * t0, r - t0, p.pad_z - 1, c.thick_z)
    out = out.union(so.flare(w - 2 * t0, d - 2 * t0, r - t0, c.thick_z, t1 - t0, t0 - t1))
    out = out.union(rprism(w - 2 * t1, d - 2 * t1, r - t1, c.thick_z + t1 - t0, zs + 0.01))
    sections = [so._rrect(w - 2 * (t1 + i), d - 2 * (t1 + i), r - t1 - i).moved(cq.Location(cq.Vector(0, 0, zs + dz))) for dz, i in curve]
    out = out.union(cq.Workplane("XY").placeSketch(*sections).loft(ruled=True))
    top = w - 2 * (t1 + c.roll_in), d - 2 * (t1 + c.roll_in), r - t1 - c.roll_in
    return out.union(rprism(*top, c.rim_z - 0.01, c.rim_z + 1))


def channel_back(c=C, p=P):
    """y of the back of the rail channels: the inside face at the rim, so a
    separator passes the narrowed opening."""
    return inner(c, p)[1] / 2 - c.roll_in


def rails(x, c=C, p=P):
    """A pair of rails standing out from the back (+y) wall either side of x,
    with a stop across their foot. Below the stop the block tapers into the
    wall at 45 degrees, so it prints without support. The channel between the
    rails is in line with the inside face at the rim, so the rails stand out
    further below the curve."""
    face = inner(c, p)[1] / 2
    back = channel_back(c, p)
    front = back - c.rail_d
    deep = face - front
    gap = c.sep_t + 2 * c.sep_clr
    hw = gap / 2 + c.rail_w
    zt = c.rim_z - c.rail_top
    # Profile in (y, z), extruded across x, chamfered at the top as a lead-in
    lead = 1.0
    pts = [(face + 1, c.stop_z - deep - 1), (face + 1, zt), (front + lead, zt)]
    pts += [(front, zt - lead), (front, c.stop_z), (face, c.stop_z - deep)]
    block = cq.Workplane("YZ").polyline(pts).close().extrude(hw, both=True).translate((x, 0, 0))
    block = block.intersect(inside(c, p, grow=0.5))
    return block.cut(box(x - gap / 2, x + gap / 2, front - 1, back, c.stop_z, zt + 1))


def make_sleeve(c=C, p=P):
    """Open fluted sleeve on the tray, built like the grid organizer's cup
    tops (seat, spigot, a snap leaf at each end, vents along the back wall)
    with a thicker wall, deeper flutes and a curved top. The cord slot is at
    the back right, and rails for the separators on the front and back walls."""
    w, d = valley(NX, NY, p)
    so_ = spigot_off(p)
    r = so.corner(NX, NY, p)
    tall = c.rim_z - p.seat_z + so_ + 5
    shape = seat_cone(NX, NY, p.seat_z, tall, p)
    shape = shape.union(rprism(w - 2 * so_, d - 2 * so_, r - so_, p.pad_z, p.seat_z - so_ + 0.05))
    outer = fluted(p.pad_z, c, p).intersect(shape)

    iw, idp = so.top_inner(NX, NY, p)
    ir = r - so_ - p.wall
    zf = p.pad_z - 1
    za = p.seat_z - so_ - p.wall + p.wall * math.sqrt(2)  # keeps the sloped wall full thickness
    spigot = rprism(iw, idp, ir, zf, za + 0.05).union(so.flare(iw, idp, ir, za, tall, tall))
    sleeve = outer.cut(inside(c, p).intersect(spigot))
    top_w, top_d = inner(c, p)
    sleeve = so.round_rim(sleeve, c.rim_z, p.rim_r, top_w - 2 * c.roll_in, top_d - 2 * c.roll_in)

    for turn in (0, 180):
        add, cuts = so.top_latch(w / 2 - so_, p)
        sleeve = sleeve.union(add.rotate((0, 0, 0), (0, 0, 1), turn))
        for cut in cuts:
            sleeve = sleeve.cut(cut.rotate((0, 0, 0), (0, 0, 1), turn))

    vents = [
        gable(p.vent_w, p.vent_z, p.vent_z + p.vent_h, d / 2 - p.wall - 1, d / 2 + p.rib_d + 1, u)
        for u in so.vent_positions(NX, NY, 0, p)
        if all(abs(u - x) >= cw / 2 + p.vent_w for x, cw in cords(c, p))
    ]
    sleeve = so.cut_all(sleeve, vents)
    for cut, _ in cord_slots(c, p):
        sleeve = sleeve.cut(cut)
    for x in stop_xs(c, p):
        rail = rails(x, c, p)
        sleeve = sleeve.union(rail).union(rail.mirror("XZ"))
    return sleeve


def make_separator(c=C, p=P):
    """Plain plate that slides down a pair of rails and rests on their stops,
    shown in place at the first stop."""
    y = channel_back(c, p) - c.sep_end_clr
    plate = box(-c.sep_t / 2, c.sep_t / 2, -y, y, c.stop_z, c.rim_z - c.sep_top)
    return plate.edges("|X").chamfer(c.sep_lead).translate((stop_xs(c, p)[0], 0, 0))


def tray_overhangs(c=C, p=P):
    """(z0, z1) of the tray's latch-groove holding face, the one short
    overhang allowed on purpose."""
    zt = p.top_latch_z
    return [(zt + 0.1, zt + 0.15 + p.top_latch_proud * so.hold_rise(p))]


def make_parts(c=C, p=P):
    """Part name -> solid, in assembled position."""
    n = c.name
    return {f"{n}_tray": make_tray(c, p), f"{n}_sleeve": make_sleeve(c, p), f"{n}_separator": make_separator(c, p)}


def assembled(parts, c=C, p=P):
    """Name -> solid for the whole cup, with a separator in every place."""
    n = c.name
    out = {f"{n}_tray": parts[f"{n}_tray"], f"{n}_sleeve": parts[f"{n}_sleeve"]}
    x0 = stop_xs(c, p)[0]
    for i, x in enumerate(stop_xs(c, p)):
        out[f"{n}_separator_{i + 1}"] = parts[f"{n}_separator"].translate((x - x0, 0, 0))
    return out


def print_pose(name, part):
    """Separators print lying flat; the rest stand as modelled."""
    if name.endswith("_separator"):
        part = part.rotate((0, 0, 0), (0, 1, 0), 90)
    return so.on_bed(part)


def main(out=Path(__file__).parent / "out", c=C):
    out.mkdir(exist_ok=True)
    parts = make_parts(c)
    for name, part in assembled(parts, c).items():
        cq.exporters.export(part, str(out / f"assembled.{name}.stl"), tolerance=0.02, angularTolerance=0.2)
    for name, part in parts.items():
        part = print_pose(name, part)
        bb = part.val().BoundingBox()
        cq.exporters.export(part, str(out / f"{name}.step"))
        cq.exporters.export(part, str(out / f"{name}.stl"), tolerance=0.01, angularTolerance=0.1)
        print(f"{name:20s} {bb.xlen:6.1f} x {bb.ylen:6.1f} x {bb.zlen:5.1f} mm")


if __name__ == "__main__":
    main()
