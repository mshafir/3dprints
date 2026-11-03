"""Gridfinity-style sink-top organizer on a 1 inch grid: baseplate and modules.

Run `uv run sink_organizer.py` from this folder to write STEP and
STL files to out/.

Every part is modelled z up, which is also its print orientation, centred on
the origin in x and y. z = 0 is the underside of the baseplate, so modules are
modelled at the height they sit at when placed on the plate. Module sizes are
given in grid cells as (nx, ny).
"""

import math
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq


@dataclass(frozen=True)
class Params:
    # Grid
    pitch: float = 25.4
    nx: int = 7
    ny: int = 3

    # Baseplate: each cell is a straight-walled socket over a drain hole. The
    # depth and the straight walls are what stop a module tipping: a foot
    # cannot rotate out of its socket, it has to be lifted straight up.
    plate_h: float = 7.0
    socket_d: float = 5.4
    bar: float = 3.4  # width of the lattice bars between sockets; wide enough
    # to leave a web between the latch grooves cut into both faces
    lead_in: float = 0.5  # chamfer round the top of each socket
    drain: float = 15.8  # through-hole side; the ledge around it carries the foot
    plate_r: float = 1.0

    # Module foot and body
    foot_clr: float = 0.2  # horizontal, per side
    foot_chamfer: float = 0.8
    gap: float = 0.5  # total, between a module and its cell block
    floor_z: float = 12.5  # top of a module's floor; the foot latches end below it

    # Snap latches: a flexible leaf with a ridge that clicks into a groove. The
    # ridge sits clear of the groove when seated, so the leaf is only loaded
    # while the part is being pushed in or pulled out. The ridge leads in at
    # 45 degrees; its holding face is steeper, so the part snaps in and takes
    # a firm pull to come out. A 45 degree holding face, as first printed,
    # rolled straight back out.
    latch_slit: float = 0.6
    latch_gap: float = 0.5  # between a leaf and the wall beside it
    latch_hold: float = 60.0  # holding face, degrees from vertical; 90 would lock
    # The foot latch is a leaf in the side of a corner foot. It is free at the
    # bed and runs up inside the module's base, which gives it room to bend.
    foot_latch_t: float = 1.2  # three lines of a 0.4 mm nozzle
    foot_latch_w: float = 10.0
    foot_latch_proud: float = 0.8  # ridge height; less foot_clr is the grip. Chosen
    # from three printed variants: 0.6 mm grip at 60 degrees felt best
    foot_latch_z: float = 2.8
    foot_latch_len: float = 8.0  # from the ridge to where the leaf joins the body
    foot_latch_back: float = 1.4  # room behind the leaf to bend into
    # The cup-top latch is a long leaf: it starts at the cup floor, runs up the
    # inside of the cup wall and joins it well above the tray, which gives it
    # the length to bend a full millimetre.
    top_latch_t: float = 1.2
    top_latch_w: float = 16.0
    top_latch_proud: float = 1.3  # less spigot_clr is the grip
    top_latch_z: float = 16.8
    top_latch_len: float = 16.0  # from the cup floor to where the leaf joins the wall. Was 13:
    # the cup clicked in too hard to trust over repeated use (about 1.45% root strain);
    # 16 roughly halves the push and the strain (about 0.9%). The tray is unaffected.
    top_latch_back: float = 1.6  # room behind the leaf to bend into
    wall: float = 2.0  # at the bottom of the grooves
    corner_r: float = 12.0  # reduced automatically on narrow modules

    # Fluting: deep, touching round ribs that run right round the corners and
    # all the way up, where they roll over into a rounded rim
    rib_d: float = 1.5
    rib_pitch: float = 4.0  # target; adjusted so a whole number fits the perimeter
    roll_r: float = 2.5  # how far the outside curves in at the rim; the ribs fade into it
    roll_h: float = 8.0  # height over which it curves in
    rim_r: float = 0.6  # rounds the inside of the rim
    min_ribs: float = 7.0  # a tray this little taller than the smooth base stays smooth

    # Two-part modules: a top with a perforated floor on a drip tray
    seat_z: float = 22.7  # where the top's outer wall meets the tray rim; the
    # spigot below it is deep so the top cannot be tipped off the tray
    seat_gap: float = 0.3  # vertical gap in the 45 degree seat
    spigot_clr: float = 0.3  # top spigot to tray wall
    tray_rim_drop: float = 0.7  # tray rim below seat_z, leaves a shadow line
    pad_z: float = 14.9  # underside of a cup top, and top of the soap tray's pads
    pad_r: float = 3.0
    pad_inset: float = 9.0
    vent_w: float = 3.0  # a row of small openings just above the tray
    vent_z: float = 25.2
    vent_h: float = 3.0

    # Module heights (z of the rim; subtract plate_h for height above the plate)
    brush_z: float = 107.0
    electric_z: float = 107.0

    # Wide-mouth mason jars (pint or half-pint; sizes to be confirmed). The
    # pockets are pushed as far apart as the plate allows, which limits how
    # wide the lids can be before they touch: see jar_spacing(). A jar_step
    # raises the +x pocket so a wider lid band can sit above the other one.
    jar_d: float = 83.0
    jar_clr: float = 0.75  # radial
    jar_wall: float = 1.2  # thinnest wall, where a pocket nears the end
    jar_step: float = 0.0
    jar_depth: float = 30.0  # depth of the shallower pocket

    # Electric cup: chargers stand loose on the tray floor, their cords leave
    # through one slot in the back wall
    cord_w: float = 14.0  # room for two or three cords side by side
    cord_z: float = 31.0  # top of the cord slot in the cup

    # Bar soap grate
    grate_clr: float = 0.3
    grate_proud: float = 1.2  # grate above the tray rim, so a long bar can overhang
    slat: float = 3.0
    slat_gap: float = 4.0
    grate_frame: float = 2.0
    grate_notch_r: float = 7.0


P = Params()

# (name, ix, iy, nx, ny, turn): cell of the module's low corner, the cells it
# covers, and the rotation it is placed at. The back of the counter is +y,
# where the charger cords leave over the edge. The two cups stand in one
# row. The mason jar holder (make_jar_holder, 7 x 4) and the bar soap dish
# (make_soap_dish, 4 x 3) are left out of this version.
LAYOUT = (
    ("electric", 0, 0, 4, 3, 0),
    ("brush", 4, 0, 3, 3, 0),
)


# --- Solid-building helpers -------------------------------------------------


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl(r, z0, z1, x=0.0, y=0.0):
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(r).extrude(z1 - z0)


def rprism(w, d, r, z0, z1):
    """Rounded-rectangle prism centred on the z axis."""
    s = cq.Workplane("XY").workplane(offset=z0).rect(w, d).extrude(z1 - z0)
    return s.edges("|Z").fillet(r) if r > 0 else s


def _rrect(w, d, r):
    s = cq.Sketch().rect(w, d)
    return s.vertices().fillet(r) if r > 0 else s


def flare(w, d, r, z0, h, grow):
    """Rounded rectangle (w, d, r) at z0, offset outward by `grow` at z0 + h.

    grow == h gives 45 degree walls; a negative grow tapers inward. With r == 0
    the corners stay sharp all the way.
    """
    a = _rrect(w, d, r).moved(cq.Location(cq.Vector(0, 0, z0)))
    b = _rrect(w + 2 * grow, d + 2 * grow, r + grow if r > 0 else 0).moved(cq.Location(cq.Vector(0, 0, z0 + h)))
    return cq.Workplane("XY").placeSketch(a, b).loft(ruled=True)


def gable(w, z0, z1, y0, y1, x=0.0):
    """Slot cutter across y: `w` wide, square from z0 to z1, then a 45 degree
    peak so its roof prints without support."""
    h = w / 2
    pts = [(-h, z0), (h, z0), (h, z1), (0, z1 + h), (-h, z1)]
    s = cq.Workplane("XZ").polyline(pts).close().extrude((y1 - y0) / 2, both=True)
    return s.translate((x, (y0 + y1) / 2, 0))


def hold_rise(p=P):
    """Height of a latch's holding face per mm of ridge height."""
    return 1 / math.tan(math.radians(p.latch_hold))


def groove(a, z, depth, half_w, p=P):
    """Cutter for the groove a latch ridge clicks into, in a wall face at
    x = a facing -x: a 45 degree lower side, a short flat and a holding face
    at latch_hold. The holding face is a short overhang, `depth` deep."""
    k = hold_rise(p)
    pts = [(a - 0.05, z - depth - 0.15), (a, z - depth - 0.1), (a + depth, z - 0.1), (a + depth, z + 0.1)]
    pts += [(a, z + depth * k + 0.1), (a - 0.05, z + depth * k + 0.15)]
    return cq.Workplane("XZ").polyline(pts).close().extrude(half_w, both=True)


def combo(*parts):
    return cq.Workplane(obj=cq.Compound.makeCompound([s for p in parts for s in p.solids().vals()]))


def cut_all(part, cutters):
    """Cut many solids in one boolean. They must not overlap one another."""
    return part.cut(combo(*cutters)) if cutters else part


def round_rim(part, z, r, w, d):
    """Round the edges of the opening at height z, which fits inside w x d.
    The outside of the rim is already rolled over."""
    sel = cq.selectors.BoxSelector((-w / 2 - 0.3, -d / 2 - 0.3, z - 0.01), (w / 2 + 0.3, d / 2 + 0.3, z + 0.01))
    return part.edges(sel).fillet(r)


# --- Grid ---------------------------------------------------------------------


def footprint(nx, ny, p=P):
    """Outer size of a module, measured over the rib crests."""
    return nx * p.pitch - p.gap, ny * p.pitch - p.gap


def valley(nx, ny, p=P):
    """Size of a module's wall between the ribs."""
    w, d = footprint(nx, ny, p)
    return w - 2 * p.rib_d, d - 2 * p.rib_d


def cell_centres(nx, ny, p=P):
    return [
        ((i - (nx - 1) / 2) * p.pitch, (j - (ny - 1) / 2) * p.pitch)
        for i in range(nx)
        for j in range(ny)
    ]


def module_origin(ix, iy, nx, ny, p=P):
    """Centre of an (nx, ny) module whose low corner is cell (ix, iy)."""
    return ((ix + nx / 2 - p.nx / 2) * p.pitch, (iy + ny / 2 - p.ny / 2) * p.pitch)


def foot_z(p=P):
    """Height of the socket ledge, where the feet rest."""
    return p.plate_h - p.socket_d


def solid_z(p=P):
    """Height at which the flared tops of neighbouring feet merge."""
    return p.plate_h + (p.bar + 2 * p.foot_clr) / 2 + 0.1


def make_baseplate(nx=None, ny=None, p=P, margin=0.0):
    """`margin` widens the plate all round. The fit-test plates use it to give
    their outer walls the full bar width that walls inside the real plate have."""
    nx, ny = nx or p.nx, ny or p.ny
    plate = rprism(nx * p.pitch + 2 * margin, ny * p.pitch + 2 * margin, p.plate_r, 0, p.plate_h)
    side = p.pitch - p.bar
    z = foot_z(p)
    eps = 0.05
    socket = box(-side / 2, side / 2, -side / 2, side / 2, z, p.plate_h + eps)
    socket = socket.union(flare(side, side, 0, p.plate_h - p.lead_in, p.lead_in + eps, p.lead_in + eps))
    socket = socket.union(rprism(p.drain, p.drain, 2.0, -1, z + eps))
    # Latch groove right round the socket, so a module clicks in at any
    # rotation. Its top is the holding face, a short overhang.
    g, zg = p.foot_latch_proud, p.foot_latch_z
    socket = socket.union(flare(side, side, 0, zg - g - 0.1, g, g))
    socket = socket.union(box(-side / 2 - g, side / 2 + g, -side / 2 - g, side / 2 + g, zg - 0.1, zg + 0.1))
    socket = socket.union(flare(side + 2 * g, side + 2 * g, 0, zg + 0.1, g * hold_rise(p), -g))
    return cut_all(plate, [socket.translate((x, y, 0)) for x, y in cell_centres(nx, ny, p)])


def feet(nx, ny, p=P):
    """One straight-sided foot per cell. Above the plate each flares at 45
    degrees until it merges with its neighbours."""
    z = foot_z(p)
    side = p.pitch - p.bar - 2 * p.foot_clr
    c = p.foot_chamfer
    h = solid_z(p) - p.plate_h
    foot = flare(side - 2 * c, side - 2 * c, 0, z, c, c)
    foot = foot.union(box(-side / 2, side / 2, -side / 2, side / 2, z + c, p.plate_h))
    foot = foot.union(flare(side, side, 0, p.plate_h, h, h))
    out = None
    for x, y in cell_centres(nx, ny, p):
        f = foot.translate((x, y, 0))
        out = f if out is None else out.union(f)
    return out


# --- Reeded shell ----------------------------------------------------------------


def corner(nx, ny, p=P):
    """Corner radius of a module's wall, measured at the bottom of the grooves."""
    w, d = valley(nx, ny, p)
    return min(p.corner_r, min(w, d) / 2 - 0.5)


def outline_point(w, d, r, s):
    """Point and outward normal at distance `s` round a rounded rectangle,
    going clockwise (seen from above) from the middle of the +y side."""
    fx, fy = w / 2 - r, d / 2 - r
    q = math.pi * r / 2
    flats = [
        ((0, d / 2), (1, 0), fx),
        ((w / 2, fy), (0, -1), 2 * fy),
        ((fx, -d / 2), (-1, 0), 2 * fx),
        ((-w / 2, -fy), (0, 1), 2 * fy),
        ((-fx, d / 2), (1, 0), fx),
    ]
    arcs = [((fx, fy), 90), ((fx, -fy), 0), ((-fx, -fy), -90), ((-fx, fy), 180)]
    for i, ((x, y), (dx, dy), length) in enumerate(flats):
        if s <= length or i == 4:
            return (x + dx * s, y + dy * s), (-dy, dx)
        s -= length
        (cx, cy), a0 = arcs[i]
        if s <= q:
            a = math.radians(a0) - s / r
            n = (math.cos(a), math.sin(a))
            return (cx + r * n[0], cy + r * n[1]), n
        s -= q


def rib_step(nx, ny, p=P):
    """(number of ribs, exact pitch). A multiple of four ribs, so a groove
    falls on the middle of every side and the pattern is symmetric."""
    w, d = valley(nx, ny, p)
    r = corner(nx, ny, p)
    perim = 2 * (w + d) - 8 * r + 2 * math.pi * r
    n = 4 * round(perim / (4 * p.rib_pitch))
    return n, perim / n


def reeded(nx, ny, z0, z1, p=P):
    """Prism whose outline is a ring of touching round ribs."""
    w, d = valley(nx, ny, p)
    r = corner(nx, ny, p)
    n, step = rib_step(nx, ny, p)
    grooves = [cq.Vector(*outline_point(w, d, r, k * step)[0]) for k in range(n)]
    edges = []
    for k in range(n):
        (x, y), (ax, ay) = outline_point(w, d, r, (k + 0.5) * step)
        crest = cq.Vector(x + ax * p.rib_d, y + ay * p.rib_d)
        edges.append(cq.Edge.makeThreePointArc(grooves[k], crest, grooves[(k + 1) % n]))
    face = cq.Face.makeFromWires(cq.Wire.assembleEdges(edges))
    solid = cq.Solid.extrudeLinear(face, cq.Vector(0, 0, z1 - z0))
    return cq.Workplane(obj=solid).translate((0, 0, z0))


def crest_prism(nx, ny, z0, z1, p=P):
    """Smooth prism at rib-crest level."""
    w, d = valley(nx, ny, p)
    return rprism(w + 2 * p.rib_d, d + 2 * p.rib_d, corner(nx, ny, p) + p.rib_d, z0, z1)


def rolled(nx, ny, z0, z1, roll=None, p=P):
    """Smooth prism at rib-crest level whose top curves inward by `roll` over
    the last roll_h, on a quarter ellipse: upright at the bottom, level at the
    top. Cut against it, the ribs taper and fade into the rim."""
    a = roll or p.roll_r
    w, d = valley(nx, ny, p)
    w, d, r = w + 2 * p.rib_d, d + 2 * p.rib_d, corner(nx, ny, p) + p.rib_d
    h = min(p.roll_h, z1 - z0)
    zs = z1 - h
    # In 16 straight steps: a smooth loft cut against the ribs gives an
    # invalid solid on some module sizes, and the steps are finer than a layer
    sections = []
    for i in range(17):
        t = math.radians(90 * i / 16)
        inset = a * (1 - math.cos(t))
        sections.append(_rrect(w - 2 * inset, d - 2 * inset, r - inset).moved(cq.Location(cq.Vector(0, 0, zs + h * math.sin(t)))))
    roll_part = cq.Workplane("XY").placeSketch(*sections).loft(ruled=True)
    return rprism(w, d, r, z0, zs + 0.01).union(roll_part)


def ribbed(nx, ny, z0, z1, base_z=None, roll=None, p=P):
    """Solid outer form: fluted sides that run up to a rounded rim, where the
    ribs fade into the roll. With `base_z`, the form is smooth below that
    height, like the trays of the two-part modules."""
    start = z0 if base_z is None else base_z
    body = reeded(nx, ny, start, z1, p)
    if base_z is not None:
        body = body.union(crest_prism(nx, ny, z0, base_z + 0.01, p))
    return body.intersect(rolled(nx, ny, z0 - 1, z1, roll, p))


def vent_positions(nx, ny, side, p=P):
    """Every other groove on a flat side (0: +y, 1: -x, 2: -y, 3: +x)."""
    w, d = valley(nx, ny, p)
    flat = (w if side % 2 == 0 else d) - 2 * corner(nx, ny, p)
    _, step = rib_step(nx, ny, p)
    k = int((flat / 2 - p.vent_w) // (2 * step))
    return [2 * i * step for i in range(-k, k + 1)]


def base_line(p=P):
    """Height of the tray rim, repeated on one-piece modules as the top of
    their smooth base."""
    return p.seat_z - p.tray_rim_drop


def foot_latch_cells(nx, ny):
    """(i, j, side): each corner foot carries one latch, on the x face that
    looks inward at the bar it shares with the next foot. Those bars are full
    width, unlike the half bar round the plate's edge. A module one cell wide
    has no such bar, so it gets a latch on both faces."""
    if nx == 1:
        return [(0, j, side) for j in sorted({0, ny - 1}) for side in (-1, 1)]
    return [(i, j, 1 if i == 0 else -1) for i in (0, nx - 1) for j in sorted({0, ny - 1})]


def foot_latch(a, p=P):
    """Snap leaf in the side of a foot whose face is the plane x = a. Returns
    (solid to add, cutters to apply in order).

    The leaf is free at the bed and joins the body foot_latch_len above its
    ridge. The cutters free it: a slot behind it, a gap between it and the
    body above the plate, and a slit at each end. All are closed pockets with
    peaked roofs, so the module's floor stays watertight.
    """
    t, hw, s = p.foot_latch_t, p.foot_latch_w / 2, p.latch_slit
    gap, back, proud = p.latch_gap, p.foot_latch_back, p.foot_latch_proud
    z0, zc = foot_z(p), p.foot_latch_z
    zr = zc + p.foot_latch_len
    # The leaf keeps its full thickness down to the bed instead of the foot
    # chamfer, and carries the ridge
    top = zc + proud * hold_rise(p)
    pts = [(a - t, z0), (a, z0), (a, zc - proud), (a + proud, zc), (a, top), (a - t, top)]
    add = cq.Workplane("XZ").polyline(pts).close().extrude(hw, both=True)
    behind = gable(back, z0 - 1, zr, -hw - s, hw + s, a - t - back / 2)
    between = gable(gap, p.plate_h - 0.2, zr, -hw - s, hw + s, a + gap / 2)
    ends = [
        gable(s, z0 - 1, zr, -(a + gap), -(a - t - back), sy * (hw + s / 2)).rotate((0, 0, 0), (0, 0, 1), 90)
        for sy in (-1, 1)
    ]
    return add, [behind, between] + ends


def on_feet(outer, nx, ny, p=P):
    """Trim the bottom of a form down to its feet and add the snap latches
    that hold it in the plate."""
    keep = feet(nx, ny, p).union(box(-500, 500, -500, 500, solid_z(p), 500))
    part = outer.intersect(keep)
    add, cuts = foot_latch((p.pitch - p.bar) / 2 - p.foot_clr, p)
    for i, j, side in foot_latch_cells(nx, ny):
        x, y = (i - (nx - 1) / 2) * p.pitch, (j - (ny - 1) / 2) * p.pitch
        turn = 0 if side > 0 else 180
        part = part.union(add.rotate((0, 0, 0), (0, 0, 1), turn).translate((x, y, 0)))
        for c in cuts:
            part = part.cut(c.rotate((0, 0, 0), (0, 0, 1), turn).translate((x, y, 0)))
    return part


# --- One-piece modules ------------------------------------------------------------


def make_open_tray(nx, ny, z1, base=True, p=P):
    """Plain one-piece tray: reeded, or smooth if it is no taller than the
    smooth base the other modules share."""
    w, d = valley(nx, ny, p)
    if base and z1 <= base_line(p) + p.min_ribs:
        outer = rolled(nx, ny, foot_z(p), z1, p=p)
    else:
        outer = ribbed(nx, ny, foot_z(p), z1, base_line(p) if base else None, p=p)
    iw, idp = w - 2 * p.wall, d - 2 * p.wall
    cavity = rprism(iw, idp, corner(nx, ny, p) - p.wall, p.floor_z, z1 + 1)
    return round_rim(on_feet(outer, nx, ny, p).cut(cavity), z1, p.rim_r, iw, idp)


def jar_pockets(p=P):
    """(x of the pocket centres, pocket radius) for the 7 x 4 jar holder."""
    w, _ = valley(7, 4, p)
    r = p.jar_d / 2 + p.jar_clr
    return w / 2 - p.jar_wall - r, r


def jar_spacing(p=P):
    """Distance between the jar centres: the widest lid that fits at equal
    pocket depths."""
    return 2 * jar_pockets(p)[0]


def make_jar_holder(p=P):
    """One solid, watertight block with two jar pockets pushed as far apart as
    the plate allows."""
    nx, ny = 7, 4
    z1 = p.floor_z + p.jar_step + p.jar_depth
    # A small roll: the wall beside each pocket is thin at the top
    outer = on_feet(ribbed(nx, ny, foot_z(p), z1, base_line(p), roll=1.0, p=p), nx, ny, p)
    x, r = jar_pockets(p)
    holder = outer.cut(cyl(r, p.floor_z, z1 + 1, -x)).cut(cyl(r, p.floor_z + p.jar_step, z1 + 1, x))
    return round_rim(holder, z1, 0.8, 2 * (x + r), 2 * r)


def jar_blocks(band_d, p=P, height=110.0, band_h=18.0):
    """Stand-ins for the two jars: glass body with a lid band on top."""
    x, _ = jar_pockets(p)
    out = []
    for cx, z in ((-x, p.floor_z), (x, p.floor_z + p.jar_step)):
        jar = cyl(p.jar_d / 2, z, z + height - band_h, cx)
        out.append(jar.union(cyl(band_d / 2, z + height - band_h, z + height, cx)))
    return out


# --- Two-part modules -----------------------------------------------------------------


def spigot_off(p=P):
    """Inset of the top's spigot from the outer wall face."""
    return p.wall + p.spigot_clr


def seat_cone(nx, ny, zc, height, p=P):
    """Everything above a 45 degree surface that meets the valley outline at zc
    and runs inward and down to the spigot."""
    w, d = valley(nx, ny, p)
    so = spigot_off(p)
    return flare(w - 2 * so, d - 2 * so, corner(nx, ny, p) - so, zc - so, height, height)


def pad_centres(nx, ny, p=P):
    w, d = valley(nx, ny, p)
    x, y = w / 2 - p.pad_inset, d / 2 - p.pad_inset
    return [(x, y), (-x, y), (-x, -y), (x, -y)]


def make_tray(nx, ny, pads=True, p=P):
    """Drip tray: smooth, carries the feet. With `pads`, the top's floor rests
    on pads above the water; without, an open sleeve rests on the 45 degree
    seat."""
    w, d = valley(nx, ny, p)
    rim = base_line(p)
    outer = on_feet(crest_prism(nx, ny, foot_z(p), rim, p), nx, ny, p)
    cavity = rprism(w - 2 * p.wall, d - 2 * p.wall, corner(nx, ny, p) - p.wall, p.floor_z, rim + 1)
    tray = outer.cut(cavity).cut(seat_cone(nx, ny, p.seat_z - (p.seat_gap if pads else 0), 8, p))
    if pads:
        for x, y in pad_centres(nx, ny, p):
            tray = tray.union(cyl(p.pad_r, p.floor_z - 0.2, p.pad_z, x, y))
    g = groove(w / 2 - p.wall, p.top_latch_z, p.top_latch_proud, p.top_latch_w / 2 + 1.5, p)
    return tray.cut(g).cut(g.rotate((0, 0, 0), (0, 0, 1), 180))


def top_inner(nx, ny, p=P):
    """Inside size of the top at floor level."""
    w, d = valley(nx, ny, p)
    si = spigot_off(p) + p.wall
    return w - 2 * si, d - 2 * si


def top_latch(a, p=P):
    """Snap leaf that holds a cup top in its tray, on the side whose spigot
    face is the plane x = a. Returns (solid to add, cutters to apply in order).

    The leaf is free at the bottom of the spigot and joins the cup wall
    top_latch_len higher up, inside the cup. Its ridge clicks into a groove
    in the tray wall. The cutters free it: a slot behind it, a gap between it
    and the wall, and a slit at each end.
    """
    t, hw, s = p.top_latch_t, p.top_latch_w / 2, p.latch_slit
    gap, back, proud = p.latch_gap, p.top_latch_back, p.top_latch_proud
    z0, zr, zc = p.pad_z, p.pad_z + p.top_latch_len, p.top_latch_z
    # Leaf, ridge and the sloped block that ties the leaf into the wall
    pts = [(a - t, z0), (a, z0), (a, zc - proud), (a + proud, zc), (a, zc + proud * hold_rise(p)), (a, zr)]
    pts += [(a + gap, zr), (a + gap, zr + 3 + t + gap), (a - t, zr + 3)]
    add = cq.Workplane("XZ").polyline(pts).close().extrude(hw, both=True)

    za = p.seat_z - spigot_off(p) - p.wall + p.wall * math.sqrt(2)
    behind = box(a - t - back, a - t, -hw - s, hw + s, z0 - 1, za + 1.2)
    between = gable(gap, p.seat_z - spigot_off(p) - 0.3, zr, -hw - s, hw + s, a + gap / 2)
    ends = [
        gable(s, z0 - 1, zr, -(a + gap), -(a - t - back), sy * (hw + s / 2)).rotate((0, 0, 0), (0, 0, 1), 90)
        for sy in (-1, 1)
    ]
    return add, [behind, between] + ends


def make_top(nx, ny, z1, vents=True, skip_vent=lambda u: False, divider=None, p=P):
    """Open fluted sleeve whose lower edge is a 45 degree seat, which it rests
    on, ending in a spigot that drops inside the tray. Whatever it holds
    stands on the tray floor. A snap leaf on each x side clicks into the tray
    so the top cannot be knocked off it. Vents run along the back (+y) wall
    only. With `divider`, a wall across the inside at that x splits it in two."""
    w, d = valley(nx, ny, p)
    so = spigot_off(p)
    tall = z1 - p.seat_z + so + 5
    shape = seat_cone(nx, ny, p.seat_z, tall, p)
    r = corner(nx, ny, p)
    shape = shape.union(rprism(w - 2 * so, d - 2 * so, r - so, p.pad_z, p.seat_z - so + 0.05))
    outer = ribbed(nx, ny, p.pad_z, z1, p=p).intersect(shape)

    iw, idp = top_inner(nx, ny, p)
    ir = r - so - p.wall
    zf = p.pad_z - 1
    za = p.seat_z - so - p.wall + p.wall * math.sqrt(2)  # keeps the sloped wall full thickness
    inner = rprism(iw, idp, ir, zf, za + 0.05).union(flare(iw, idp, ir, za, tall, tall))
    cavity = rprism(w - 2 * p.wall, d - 2 * p.wall, r - p.wall, zf, z1 + 1).intersect(inner)
    if divider is not None:
        cavity = cavity.cut(box(divider - p.wall / 2, divider + p.wall / 2, -500, 500, -500, 500))
    top = round_rim(outer.cut(cavity), z1, p.rim_r, w - 2 * p.wall, d - 2 * p.wall)

    for turn in (0, 180):
        add, cuts = top_latch(w / 2 - so, p)
        top = top.union(add.rotate((0, 0, 0), (0, 0, 1), turn))
        for c in cuts:
            top = top.cut(c.rotate((0, 0, 0), (0, 0, 1), turn))

    cutters = []
    if vents:
        dist = d / 2
        for u in vent_positions(nx, ny, 0, p):
            if not skip_vent(u):
                cutters.append(gable(p.vent_w, p.vent_z, p.vent_z + p.vent_h, dist - p.wall - 1, dist + p.rib_d + 1, u))
    return cut_all(top, cutters)


def divider_x(nx, ny, p=P):
    """x of the divider that splits a cup 2:1 at the rim, toothbrushes on
    the -x side and toothpaste on the +x side."""
    inner = valley(nx, ny, p)[0] - 2 * p.wall
    return inner / 2 - (inner - p.wall) / 3 - p.wall / 2


def make_brush_cup(p=P):
    """3 x 3 cup split 2:1 by a divider: toothbrushes and toothpaste."""
    top = make_top(3, 3, p.brush_z, divider=divider_x(3, 3, p), p=p)
    return top, make_tray(3, 3, pads=False, p=p)


# --- Electric toothbrush cup ---------------------------------------------------------


def make_electric(p=P):
    """Open cup, 4 x 3, for electric toothbrushes standing on their chargers,
    which sit loose on the tray floor. The cords leave through one slot in
    the back (+y) wall: open at the top of the tray wall, so they drop in
    from above, and open at the bottom of the sleeve, so it lowers over them.
    The tray drains through the slot too."""
    nx, ny = 4, 3
    _, d = valley(nx, ny, p)
    y_out = d / 2 + p.rib_d + 1

    def near_cord(u):
        return abs(u) < p.cord_w / 2 + p.vent_w

    top = make_top(nx, ny, p.electric_z, skip_vent=near_cord, p=p)
    tray = make_tray(nx, ny, pads=False, p=p)
    top_slot = gable(p.cord_w, p.pad_z - 1, p.cord_z, d / 2 - spigot_off(p) - p.wall - 1, y_out)
    tray_slot = box(-p.cord_w / 2, p.cord_w / 2, d / 2 - p.wall - 1, y_out, p.floor_z, p.seat_z + 1)
    return top.cut(top_slot), tray.cut(tray_slot)


# --- Bar soap dish ------------------------------------------------------------------------


def make_soap_dish(p=P):
    """Slatted grate resting on the pads of a tray, standing just proud of the
    rim so a long bar can overhang it. Built 3 x 4 and turned to cover 4 x 3,
    so the slats run across the short way."""
    nx, ny = 3, 4
    grate_z = base_line(p) + p.grate_proud
    w, d = valley(nx, ny, p)
    gw = w - 2 * p.wall - 2 * p.grate_clr
    gd = d - 2 * p.wall - 2 * p.grate_clr
    gr = corner(nx, ny, p) - p.wall - p.grate_clr
    grate = rprism(gw, gd, gr, p.pad_z, grate_z)
    grate = grate.faces(">Z").edges().chamfer(0.5)
    step = p.slat + p.slat_gap
    n = int((gd - 2 * p.grate_frame - p.slat_gap) // step) + 1

    def half(y):
        """Half-length of the slot at `y`, kept a frame's width inside the
        rounded ends."""
        over = max(abs(y) + p.slat_gap / 2 + 0.5 - (gd / 2 - gr), 0)
        return gw / 2 - gr + math.sqrt(gr**2 - over**2) - p.grate_frame

    # Slot profile in (y, z), widened at the top to take the edge off each slat
    g, zt = p.slat_gap / 2, grate_z
    pts = [(-g, p.pad_z - 1), (g, p.pad_z - 1), (g, zt - 0.5), (g + 0.5, zt), (g + 0.5, zt + 1)]
    pts += [(-y, z) for y, z in reversed(pts[2:])]
    ys = [(k - (n - 1) / 2) * step for k in range(n)]
    slots = [cq.Workplane("YZ").polyline(pts).close().extrude(half(y), both=True).translate((0, y, 0)) for y in ys]
    grate = cut_all(grate, slots)
    # Finger notches at both ends for lifting the grate out
    grate = cut_all(grate, [cyl(p.grate_notch_r, p.pad_z - 1, grate_z + 1, 0, sy * gd / 2) for sy in (-1, 1)])
    return tuple(part.rotate((0, 0, 0), (0, 0, 1), 90) for part in (grate, make_tray(nx, ny, p=p)))


# --- Layout, checks and export ----------------------------------------------------------------


def make_modules(p=P):
    """Module name -> list of (part name, solid) in assembled position."""
    brush_top, brush_tray = make_brush_cup(p)
    electric_top, electric_tray = make_electric(p)
    return {
        "electric": [("electric_cup_top", electric_top), ("electric_cup_tray", electric_tray)],
        "brush": [("brush_cup_top", brush_top), ("brush_cup_tray", brush_tray)],
    }


def placed(modules, p=P):
    """(module name, part name, solid moved to its place on the plate)."""
    out = []
    for name, ix, iy, nx, ny, turn in LAYOUT:
        x, y = module_origin(ix, iy, nx, ny, p)
        out += [
            (name, part_name, part.rotate((0, 0, 0), (0, 0, 1), turn).translate((x, y, 0)))
            for part_name, part in modules[name]
        ]
    return out


def latch_overhangs(p=P):
    """(z0, z1) bands, in assembled heights, of the holding faces of the latch
    grooves: short overhangs steeper than 45 degrees, allowed on purpose."""
    k = hold_rise(p)
    zg, zt = p.foot_latch_z, p.top_latch_z
    return [(zg + 0.1, zg + 0.15 + p.foot_latch_proud * k), (zt + 0.1, zt + 0.15 + p.top_latch_proud * k)]


def overhang_area(part, max_deg=48.0, allow=()):
    """Area (mm^2) of downward faces flatter than `max_deg` from vertical,
    ignoring the face on the bed and any in the `allow` bands of height. The
    margin over 45 degrees absorbs meshing error where the reeding meets the
    45 degree seat on a corner."""
    verts, tris = part.val().tessellate(0.02, 0.1)
    zmin = min(v.z for v in verts)
    limit = -math.sin(math.radians(max_deg))
    total = 0.0
    for i, j, k in tris:
        a, b, c = verts[i], verts[j], verts[k]
        n = (b - a).cross(c - a)
        if n.Length < 1e-12:
            continue
        z = (a.z + b.z + c.z) / 3
        if n.z / n.Length < limit and z > zmin + 0.05 and not any(lo <= z <= hi for lo, hi in allow):
            total += n.Length / 2
    return total


def fit_test_parts(p=P):
    """Small prints that check the fits before committing to the full parts."""
    return {
        # The smallest test of the click into the baseplate: one socket with
        # full-width walls and a stub module with a latch on two sides
        "test_plate_1x1": make_baseplate(1, 1, p, margin=p.bar / 2),
        "test_module_1x1": make_open_tray(1, 1, p.floor_z + 2.5, base=False, p=p),
        "test_plate_2x2": make_baseplate(2, 2, p, margin=p.bar / 2),
        # A short 2 x 2 open cup: four feet and four foot latches on the test
        # plate, and the latches between a cup top and its tray
        "test_cup_tray_2x2": make_tray(2, 2, pads=False, p=p),
        "test_cup_top_2x2": make_top(2, 2, p.seat_z + 16, p=p),
    }


def on_bed(part):
    return part.translate((0, 0, -part.val().BoundingBox().zmin))


def assembled_parts(plate, modules, p=P):
    """Name -> solid for every part where it sits when assembled."""
    return {"baseplate": plate, **{name: part for _, name, part in placed(modules, p)}}


def main(out=Path(__file__).parent / "out"):
    out.mkdir(exist_ok=True)
    plate = make_baseplate()
    modules = make_modules()

    asm = cq.Assembly()
    for name, part in assembled_parts(plate, modules).items():
        asm.add(part, name=name, color=cq.Color("gray60"))
    asm.export(str(out / "assembly.step"))
    # Everything in place as one mesh, for previewing in the slicer (not for printing)
    whole = combo(plate, *[part for _, _, part in placed(modules)])
    cq.exporters.export(whole, str(out / "preview_assembled.stl"), tolerance=0.02, angularTolerance=0.2)
    # And as separate parts in place, so the project can show the assembly
    for name, part in assembled_parts(plate, modules).items():
        cq.exporters.export(part, str(out / f"assembled.{name}.stl"), tolerance=0.02, angularTolerance=0.2)

    parts = {"baseplate": plate}
    for items in modules.values():
        parts.update(items)
    parts.update(fit_test_parts())
    for name, part in parts.items():
        part = on_bed(part)
        bb = part.val().BoundingBox()  # measured before meshing, which loosens it
        cq.exporters.export(part, str(out / f"{name}.step"))
        cq.exporters.export(part, str(out / f"{name}.stl"), tolerance=0.01, angularTolerance=0.1)
        print(f"{name:20s} {bb.xlen:6.1f} x {bb.ylen:6.1f} x {bb.zlen:5.1f} mm")


if __name__ == "__main__":
    main()
