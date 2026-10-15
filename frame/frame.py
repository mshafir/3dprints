"""Picture frame with a cut-through lattice border, for a sheet of glass, a
picture and a backing board, in as few sections as fit the bed.

Run `uv run frame.py` from this folder to write STEP and STL files to out/.

The frame is modelled face down, which is also how it prints: z = 0 is the
front and z grows towards the back. It is centred on the origin with its long
side along x, and every section is modelled where it sits in the frame. The
contents go in from the back and are held by snap tabs in the rabbet wall.
"""

import math
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq


@dataclass(frozen=True)
class Params:
    # Contents: glass, picture and backing board, as one stack. content_w is
    # the long side.
    content_w: float = 279.4  # 11 in
    content_h: float = 215.9  # 8.5 in
    stack: float = 8.0  # with the backing's easel folded flat
    clr: float = 0.4  # per side, between the contents and the rabbet wall

    # Border, from the edge of the opening to the outside
    border: float = 20.0
    lip: float = 3.5  # how far the front lip overlaps the contents
    skin: float = 2.0  # thickness of the front lip
    wall: float = 1.8  # rabbet wall
    rim: float = 1.6  # outer rim
    depth: float = 13.5
    chamfer: float = 0.6  # 45 degrees, round the front edges inside and out
    corner_r: float = 1.0  # outside corners seen from the front

    # Lattice: diamonds along the middle of the band, triangles at its edges
    cell: float = 15.0  # target pitch; each run is stretched to a whole number
    bar: float = 1.6
    pad: float = 20.0  # solid pads for the joints, tabs and keyholes

    bed: float = 250.0  # largest part either way; the P1S bed is 256

    # Sliding dovetail at each seam, put in from the back. Its front is a 45
    # degree ramp that rests on a matching ramp in the socket.
    tongue_neck: float = 6.0
    tongue_tip: float = 10.0
    tongue_len: float = 7.0
    ramp_z: float = 1.0  # where the ramp meets the seam; the socket's thinnest front
    joint_clr: float = 0.1  # per side, when seated
    joint_taper: float = 1.0  # degrees, narrower towards the front

    # Snap tabs: a leaf in the rabbet wall with a 45 degree ridge that clicks
    # over the back of the backing board
    tab_t: float = 0.8
    tab_w: float = 10.0
    tab_slit: float = 0.6
    tab_proud: float = 1.0  # less clr is the grip
    tab_flat: float = 0.4
    slack: float = 0.2  # how far a centred stack can move back before the ridges stop it

    # Keyholes for a picture nail or a small screw
    key_head: float = 6.0
    key_neck: float = 3.0
    key_throw: float = 5.0  # entry centre to slot end, towards the outside edge
    key_lip: float = 1.5
    key_room: float = 3.5  # under the lips, including their 45 degree undersides
    key_web: float = 1.2  # between the tab's gap and the keyhole


P = Params()


# --- Sizes --------------------------------------------------------------------


def rabbet(p=P):
    return p.content_w + 2 * p.clr, p.content_h + 2 * p.clr


def sight(p=P):
    return p.content_w - 2 * p.lip, p.content_h - 2 * p.lip


def outer(p=P):
    w, h = sight(p)
    return w + 2 * p.border, h + 2 * p.border


def band(p=P):
    return p.border - p.lip - p.clr - p.wall - p.rim


def tab_back(p=P):
    """Gap behind a tab's leaf: room to bend clear of the backing."""
    return p.tab_proud + 0.2


def ridge_z(p=P):
    """Where a tab's ridge starts. Its 45 degree face reaches the edge of a
    centred backing `slack` behind the back of the stack, so it also pushes an
    off-centre backing back to the middle as it goes in."""
    return p.skin + p.stack + p.slack - p.clr


def sections(p=P):
    """How many sections along x the frame is cut into to fit the bed."""
    w, h = outer(p)
    if p.content_h > p.content_w:
        raise ValueError("content_w must be the long side")
    if h > p.bed:
        raise ValueError(f"frame is {h:.1f} mm on its short side, more than the {p.bed} mm bed")
    n = 1
    while w / n + (p.tongue_len if n > 1 else 0) > p.bed:
        n += 1
    return n


def seams(p=P):
    w, _ = outer(p)
    n = sections(p)
    return [-w / 2 + k * w / n for k in range(1, n)]


def tab_spots(p=P):
    """x of the tab pads on the long sides: the middle of each section."""
    w, _ = outer(p)
    n = sections(p)
    return [-w / 2 + (k + 0.5) * w / n for k in range(n)]


# --- Solid-building helpers ---------------------------------------------------


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
    """Rounded rectangle (w, d, r) at z0, offset outward by `grow` at z0 + h."""
    a = _rrect(w, d, r).moved(cq.Location(cq.Vector(0, 0, z0)))
    b = _rrect(w + 2 * grow, d + 2 * grow, r + grow if r > 0 else 0).moved(cq.Location(cq.Vector(0, 0, z0 + h)))
    return cq.Workplane("XY").placeSketch(a, b).loft(ruled=True)


def grow(pts, d):
    """A convex polygon with every edge moved outward by d (inward if d < 0)."""
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


# Features are built on the top side (+y) and turned onto the others. Each side
# is (name, turn in degrees, distance of the rabbet wall from the centre,
# half-length of the lattice run).
def sides(p=P):
    rw, rh = rabbet(p)
    return [
        ("top", 0, rh / 2, rw / 2 + p.wall),
        ("bottom", 180, rh / 2, rw / 2 + p.wall),
        ("right", -90, rw / 2, rh / 2 + p.wall),
        ("left", 90, rw / 2, rh / 2 + p.wall),
    ]


def pads(side, p=P):
    """Centres of the pads along a side, as (position, carries a tab)."""
    if side in ("top", "bottom"):
        return sorted([(x, True) for x in tab_spots(p)] + [(x, False) for x in seams(p)])
    return [(0.0, True)]


# --- Lattice ------------------------------------------------------------------


def lattice_cells(a, b, h, p=P):
    """Openings for a run of band from u = a to u = b, the band spanning
    v = -h/2 to h/2: diamonds touching the band edges and triangles between
    them, every edge set back half a bar."""
    n = max(1, round((b - a) / p.cell))
    s = (b - a) / n
    out = []
    for j in range(n):
        u = a + (j + 0.5) * s
        out.append([(u - s / 2, 0), (u, h / 2), (u + s / 2, 0), (u, -h / 2)])
    for j in range(n + 1):
        u = a + j * s
        for e in (1, -1):
            if j == 0:
                tri = [(a, 0), (a + s / 2, e * h / 2), (a, e * h / 2)]
            elif j == n:
                tri = [(b, 0), (b, e * h / 2), (b - s / 2, e * h / 2)]
            else:
                tri = [(u, 0), (u + s / 2, e * h / 2), (u - s / 2, e * h / 2)]
            out.append(tri)
    return [grow(c, -p.bar / 2) for c in out]


def runs(side, half, p=P):
    """The stretches of a side's band between the corners and the pads."""
    edges = [-half]
    for c, _ in pads(side, p):
        edges += [c - p.pad / 2, c + p.pad / 2]
    edges.append(half)
    return list(zip(edges[::2], edges[1::2]))


def lattice_cutters(p=P):
    h = band(p)
    out = []
    for side, deg, yr, half in sides(p):
        vc = yr + p.wall + h / 2
        for a, b in runs(side, half, p):
            for cell in lattice_cells(a, b, h, p):
                out.append(turn(prism([(u, vc + v) for u, v in cell], -1, p.depth + 1), deg))
    rw, rh = rabbet(p)
    cx, cy = rw / 2 + p.wall + h / 2, rh / 2 + p.wall + h / 2
    for sx in (1, -1):
        for sy in (1, -1):
            out.append(cyl((h - p.bar) / 2, -1, p.depth + 1, sx * cx, sy * cy))
    return out


# --- Tabs and keyholes ----------------------------------------------------------


def tab_cutter(c, yr, p=P):
    """Slits and gap that free a leaf in the rabbet wall at y = yr, x = c."""
    w, s, t = p.tab_w, p.tab_slit, p.tab_t
    gap = box(c - w / 2 - s, c + w / 2 + s, yr + t, yr + t + tab_back(p), p.skin, p.depth + 1)
    slits = [box(x0, x0 + s, yr - 0.1, yr + t + 0.01, p.skin, p.depth + 1) for x0 in (c - w / 2 - s, c + w / 2)]
    return gap.union(slits[0]).union(slits[1])


def tab_ridge(c, yr, p=P):
    z, g, f = ridge_z(p), p.tab_proud, p.tab_flat
    pts = [(yr + 0.05, z - 0.05), (yr - g, z + g), (yr - g, z + g + f), (yr + 0.05, z + 2 * g + f + 0.05)]
    return cq.Workplane("YZ").polyline(pts).close().extrude(p.tab_w / 2, both=True).translate((c, 0, 0))


def _stadium(c, y0, length, width, z):
    return cq.Workplane("XY").workplane(offset=z).center(c, y0 + length / 2).slot2D(length + width, width, 90)


def keyhole_cutter(c, yr, p=P):
    """Keyhole in the back of a pad, its slot running out towards the edge."""
    y0 = yr + p.tab_t + tab_back(p) + p.key_web + p.key_head / 2  # entry centre
    zl = p.depth - p.key_lip  # underside of the lips
    zs = zl - (p.key_head - p.key_neck) / 2  # where the 45 degree underside starts
    zf = zl - p.key_room  # floor
    th, hd, nk = p.key_throw, p.key_head, p.key_neck
    entry = cyl(hd / 2, zf, p.depth + 1, c, y0)
    neck = _stadium(c, y0, th, nk, zl - 0.01).extrude(p.depth + 1 - zl)
    # Room for the head under the lips, as one loft so there is no seam where
    # the straight sides meet the 45 degree undersides
    room = _stadium(c, y0, th, hd, zf).workplane(offset=zs - zf).slot2D(th + hd, hd, 90)
    room = room.workplane(offset=zl - zs).slot2D(th + nk, nk, 90).loft(ruled=True)
    return entry.union(neck).union(room)


def tab_features(p=P):
    """(cutters, ridges) for every tab pad."""
    cutters, ridges = [], []
    for side, deg, yr, _ in sides(p):
        for c, has_tab in pads(side, p):
            if has_tab:
                cutters.append(turn(tab_cutter(c, yr, p).union(keyhole_cutter(c, yr, p)), deg))
                ridges.append(turn(tab_ridge(c, yr, p), deg))
    return cutters, ridges


# --- Frame ----------------------------------------------------------------------


def make_body(p=P):
    """The whole frame as one piece, before it is cut into sections."""
    w, h = outer(p)
    sw, sh = sight(p)
    rw, rh = rabbet(p)
    c, r = p.chamfer, p.corner_r
    # One ruled loft for the chamfer and the sides, so there is no seam between them
    rings = [_rrect(w - 2 * c, h - 2 * c, r - c), _rrect(w, h, r), _rrect(w, h, r)]
    rings = [s.moved(cq.Location(cq.Vector(0, 0, z))) for s, z in zip(rings, (0, c, p.depth))]
    body = cq.Workplane("XY").placeSketch(*rings).loft(ruled=True)
    body = body.cut(box(-rw / 2, rw / 2, -rh / 2, rh / 2, p.skin, p.depth + 1))
    body = body.cut(box(-sw / 2, sw / 2, -sh / 2, sh / 2, -1, p.skin + 0.1))
    body = body.cut(flare(sw + 2 * c, sh + 2 * c, 0, -0.01, c + 0.01, -c - 0.01))
    cutters, ridges = tab_features(p)
    body = cut_all(body, lattice_cutters(p) + cutters)
    for ridge in ridges:
        body = body.union(ridge)
    return body


def tongue(xs, p=P, clr=0.0, extra=0.0):
    """The dovetail on the top side at the seam x = xs, pointing +x. With clr
    and extra it is the socket cutter: grown by clr and run out past the back."""
    _, rh = rabbet(p)
    yc = rh / 2 + (p.wall + band(p) + p.rim) / 2
    n, t = p.tongue_neck / 2, p.tongue_tip / 2
    pts = [(xs - 1, yc - n), (xs, yc - n), (xs + p.tongue_len, yc - t), (xs + p.tongue_len, yc + t), (xs, yc + n), (xs - 1, yc + n)]
    z0, z1 = p.ramp_z - 0.5, p.depth + extra
    taper = math.tan(math.radians(p.joint_taper))
    # The taper is measured from the seated front of the tongue
    flanks = loft(grow(pts, clr - taper * (p.ramp_z - z0)), z0, grow(pts, clr + taper * (z1 - p.ramp_z)), z1)
    ramp = [(xs - 2, p.ramp_z - 2), (xs + p.tongue_len + 2, p.ramp_z + p.tongue_len + 2), (xs + p.tongue_len + 2, z1 + 1), (xs - 2, z1 + 1)]
    ramp = cq.Workplane("XZ").polyline(ramp).close().extrude(20, both=True).translate((0, yc, 0))
    return flanks.intersect(ramp)


def tongues(xs, p=P, clr=0.0, extra=0.0):
    """Both dovetails at the seam x = xs, top and bottom side, pointing +x.
    They belong to the section on the left, so at every seam that section goes
    in from the back of the one on its right."""
    top = tongue(xs, p, clr, extra)
    return top.union(top.mirror("XZ"))


def make_sections(p=P, body=None):
    """The frame cut into sections at the seams, left to right."""
    body = body if body is not None else make_body(p)
    xs = seams(p)
    w, h = outer(p)
    lo, hi = -w, w
    out = []
    edges = [lo] + xs + [hi]
    for k, (x0, x1) in enumerate(zip(edges, edges[1:])):
        region = box(x0, x1, -h, h, -1, p.depth + 1)
        if k > 0:  # sockets for the left neighbour's tongues
            region = region.cut(tongues(x0, p, p.joint_clr, 1.0))
        if k < len(edges) - 2:
            region = region.union(tongues(x1, p))
        out.append(body.intersect(region))
    return out


def section_names(p=P):
    n = sections(p)
    if n == 1:
        return ["frame"]
    if n == 2:
        return ["frame_left", "frame_right"]
    return [f"frame_section_{k + 1}" for k in range(n)]


def fit_test_parts(p=P, parts=None):
    """Small pieces cut from the real sections: the pads either side of one
    seam, and one short-side pad with its tab and keyhole."""
    parts = parts if parts is not None else make_sections(p)
    w, h = outer(p)
    sw, sh = sight(p)
    k = p.pad / 2 + p.bar / 2 - 0.1  # just inside the solid pad
    out = {}
    if len(parts) > 1:
        xs = seams(p)[0]
        crop = box(xs - k, xs + k, sh / 2 - 1, h / 2 + 1, -1, p.depth + 1)
        out["test_seam_left"] = parts[0].intersect(crop)
        out["test_seam_right"] = parts[1].intersect(crop)
    out["test_tab"] = parts[-1].intersect(box(sw / 2 - 1, w / 2 + 1, -k, k, -1, p.depth + 1))
    return out


# --- Checks and export ------------------------------------------------------------


def overhang_area(part, max_deg=48.0):
    """Area (mm^2) of downward faces flatter than `max_deg` from vertical,
    ignoring the face on the bed. The margin over 45 degrees absorbs meshing
    error on the 45 degree faces."""
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


def grams(part):
    """Solid PLA weight; the print is lighter where infill replaces solid."""
    return part.val().Volume() / 1000 * 1.24


def main(out=Path(__file__).parent / "out", p=P):
    out.mkdir(exist_ok=True)
    body = make_body(p)
    parts = dict(zip(section_names(p), make_sections(p, body)))
    asm = cq.Assembly()
    for name, part in parts.items():
        asm.add(part, name=name, color=cq.Color("gray20"))
    asm.export(str(out / "assembly.step"))
    parts.update(fit_test_parts(p, list(parts.values())))
    for name, part in parts.items():
        bb = part.val().BoundingBox()
        cq.exporters.export(part, str(out / f"{name}.step"))
        cq.exporters.export(part, str(out / f"{name}.stl"), tolerance=0.01, angularTolerance=0.1)
        print(f"{name:16s} {bb.xlen:6.1f} x {bb.ylen:6.1f} x {bb.zlen:5.1f} mm  {grams(part):5.1f} g")
    w, h = outer(p)
    print(f"frame {w:.1f} x {h:.1f} mm, opening {sight(p)[0]:.1f} x {sight(p)[1]:.1f} mm, {grams(body):.0f} g")


if __name__ == "__main__":
    main()
