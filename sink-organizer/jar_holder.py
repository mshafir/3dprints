"""Holder for two wide-mouth pint mason jars, beside the single cup.

Run `uv run jar_holder.py` from this folder to write STEP and STL files to
out/, prefixed `jar_`.

A low block with the single cup's flutes and rounded top (sink_cup.py,
whose builders this reuses). It is flat on top, with two round pockets the
jars drop into about an inch. The pockets have closed floors that catch
drips, a 45 degree lead-in at the opening, and a rounded corner at the floor
so they wipe out. The outline is a stadium round the two pockets. A short
plain test ring checks the jar's size first.

Parts are modelled z up, centred on the origin in x and y; z = 0 is the
counter. The jars stand side by side along x.
"""

import math
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq

import sink_cup as sc
import sink_organizer as so


@dataclass(frozen=True)
class JarParams:
    # Ball wide-mouth pint. No caps go on in the holder, so the widest part
    # is the glass rim with its threads: 87 mm, measured. The body was
    # taken as 83 mm at first; the first test ring (85 mm pocket) had room
    # to spare, so the pocket is now 82.2 mm. The whole holder must fit
    # 7 in (177.8 mm) of counter, which sets the slim rim below.
    jar_d: float = 80.2
    lid_d: float = 87.0  # the rim, threads included
    jar_clr: float = 1.0  # radial, so a jar drops in and lifts out easily
    lid_gap: float = 1.0  # between the two rims, so one lifts out clear
    depth: float = 25.0  # how far a jar sits in
    floor_t: float = 2.4
    floor_r: float = 2.0  # rounds the pocket's floor into its wall
    lead: float = 1.0  # 45 degree chamfer round each opening
    land: float = 0.5  # flat top between the chamfer and the curve
    # Top: the cup's curve scaled down; roll_curve() reads these two
    roll_in: float = 1.0
    roll_steps: int = 8
    rib_d: float = 1.3  # shallower than the single cup's 1.8 flutes
    rib_pitch: float = 4.0
    test_depth: float = 8.0  # the test ring's height
    test_wall: float = 2.0  # the test ring's wall beyond its lead-in


J = JarParams()


def pocket_r(j=J):
    return j.jar_d / 2 + j.jar_clr


def spacing(j=J):
    """Distance between the jar centres: the lid bands keep lid_gap apart."""
    return j.lid_d + j.lid_gap


def outline_r(j=J):
    """Radius of the stadium's ends at the bottom of the flutes: the pocket,
    then the chamfer, a flat and the curve's inset."""
    return pocket_r(j) + j.lead + j.land + j.roll_in


def top_z(j=J):
    return j.floor_t + j.depth


def flute_count(w, d, r, j=J):
    """A multiple of four flutes at about rib_pitch, as on the cup."""
    perim = 2 * (w + d) - 8 * r + 2 * math.pi * r
    return 4 * round(perim / (4 * j.rib_pitch))


def body(centres, z1, j=J):
    """Fluted outer form from the counter to z1: a stadium round the pocket
    centres (a circle for one), straight flutes, then the curve at the top
    with the flutes carried round it."""
    r = outline_r(j)
    w, d = 2 * r + (max(centres) - min(centres)), 2 * r
    n = flute_count(w, d, r, j)
    h, curve = sc.roll_curve(j)
    zs = z1 - h
    base = sc.reeded_wire(w, d, r, n, j.rib_d, 0)
    straight = cq.Solid.extrudeLinear(cq.Face.makeFromWires(base), cq.Vector(0, 0, zs))
    wires = [sc.reeded_wire(w - 2 * i, d - 2 * i, r - i, n, j.rib_d, zs + dz) for dz, i in curve]
    top = cq.Solid.makeLoft(wires, True)
    return cq.Workplane(obj=straight).union(cq.Workplane(obj=top))


def pocket(x, z1, j=J, floor=True):
    """Cutter for one pocket at (x, 0) with its top at z1: a round-cornered
    floor, an upright wall and a 45 degree lead-in at the opening. Without
    a floor it is a plain hole through."""
    r = pocket_r(j)
    if floor:
        bore = so.cyl(r, j.floor_t, z1 + 1, x).faces("<Z").edges().fillet(j.floor_r)
    else:
        bore = so.cyl(r, -1, z1 + 1, x)
    cone = cq.Solid.makeCone(r, r + j.lead + 1, j.lead + 1, cq.Vector(x, 0, z1 - j.lead))
    return bore.union(cq.Workplane(obj=cone))


def holder(centres, z1, j=J, floor=True):
    part = body(centres, z1, j)
    for x in centres:
        part = part.cut(pocket(x, z1, j, floor))
    return part


def jar_xs(j=J):
    s = spacing(j) / 2
    return (-s, s)


def make_holder(j=J):
    return holder(jar_xs(j), top_z(j), j=j)


def make_test_ring(j=J):
    """A plain open ring test_depth tall with the holder's pocket and
    lead-in, to check the jar's size before printing the holder. It stands
    on the counter and the jar's base drops into it. No flutes and no floor:
    only the pocket's diameter is being checked."""
    outer = so.cyl(pocket_r(j) + j.lead + j.test_wall, 0, j.test_depth)
    return outer.cut(pocket(0.0, j.test_depth, j, floor=False))


def jar_stand_in(x, j=J, height=120.0, band_h=15.0, heel_r=3.0):
    """A jar standing in a pocket: glass body with the lid band on top. Glass
    jars have a rounded heel, which clears the round at the pocket's floor."""
    body_ = so.cyl(j.jar_d / 2, j.floor_t, j.floor_t + height - band_h, x).faces("<Z").edges().fillet(heel_r)
    return body_.union(so.cyl(j.lid_d / 2, j.floor_t + height - band_h, j.floor_t + height, x))


def make_parts(j=J):
    return {"jar_test_ring": make_test_ring(j), "jar_holder": make_holder(j)}


def main(out=Path(__file__).parent / "out"):
    out.mkdir(exist_ok=True)
    parts = make_parts()
    holder_ = parts["jar_holder"]
    jars = [jar_stand_in(x) for x in jar_xs()]
    for name, part in [("jar_holder", holder_), ("jar_1", jars[0]), ("jar_2", jars[1])]:
        cq.exporters.export(part, str(out / f"assembled.{name}.stl"), tolerance=0.02, angularTolerance=0.2)
    for name, part in parts.items():
        part = so.on_bed(part)
        bb = part.val().BoundingBox()
        cq.exporters.export(part, str(out / f"{name}.step"))
        cq.exporters.export(part, str(out / f"{name}.stl"), tolerance=0.01, angularTolerance=0.1)
        print(f"{name:20s} {bb.xlen:6.1f} x {bb.ylen:6.1f} x {bb.zlen:5.1f} mm, {part.val().Volume() / 1000:5.1f} cm^3")


if __name__ == "__main__":
    main()
