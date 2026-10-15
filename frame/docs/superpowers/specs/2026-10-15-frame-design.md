# Lattice picture frame — design

Date: 2026-10-15

## Goal

A frame for an 11 x 8.5 in (279.4 x 215.9 mm) sheet of glass, a picture and a
cardboard backing that has its own easel. The frame should look decorative,
use little plastic, print without supports on the P1S, and lock the contents
in so they cannot fall out of the back. Other picture sizes are a change of
parameters.

## Constraints

- Bambu Lab P1S, 256 x 256 mm bed (parts kept to 250 mm), 0.4 mm nozzle, PLA,
  0.2 mm layers, no supports: no downward face flatter than 45 degrees.
- One filament.
- The stack (glass + picture + backing, easel folded) is 8.0 mm thick,
  measured by the user.
- Displayed landscape, on a wall or standing on the backing's easel. The lock
  must leave the middle of the backing clear for the easel.

## Why it is not one piece

The picture alone is 279.4 mm long, wider than the bed. A frame around it does
not fit diagonally either (a rectangle a x b fits a square bed s only if
roughly a + b < 1.41 s). The fewest pieces is two: the frame is cut down the
middle into two halves, each about 163 x 249 mm.

## Look

Seen from the front, the border is 20 mm wide:

| From the opening outwards | Width | |
|---|---|---|
| Front lip | 3.5 + 0.4 | solid, 2 mm thick, holds the glass |
| Rabbet wall | 1.8 | solid, full depth |
| Lattice band | 12.7 | cut right through the full depth |
| Outer rim | 1.6 | solid, full depth |

The band is a trellis: a row of diamonds along its middle with triangles
between them at its edges, separated by 1.6 mm bars (four nozzle widths). The
pitch is about 15 mm, stretched on each run so every run holds a whole number
of cells. Each corner has a round opening (a rondel). Solid pads 20 mm long
interrupt the band where the joints, tabs and keyholes are, at regular
spacing, so they read as part of the pattern.

The frame is 13.5 mm deep and prints face down, so the front takes the finish
of the build plate. The outer and inner front edges have a 0.6 mm 45 degree
chamfer, which also hides elephant's foot.

Size: opening 272.4 x 208.9 mm, outside 312.4 x 248.9 mm. About 180 g of
PLA if printed solid; less with infill in the pads and rim.

## Sections and joints

- The frame is cut into as few equal sections along its length as fit the bed:
  one for 5 x 7 in, two for 11 x 8.5 in, three for something like 20 x 8 in.
  If the short side does not fit the bed the script stops with an error
  rather than also splitting the other way.
- At each seam a sliding dovetail joins the top side and another the bottom
  side. Both tongues (6 mm at the neck, 10 mm at the tip, 7 mm long) belong to
  the section on the left, because all the joints at a seam have to slide
  apart in the same direction: with one tongue on each half, the halves could
  not be put together. So the two halves are different parts.
- The tongue goes in from the back. Its front face is a 45 degree ramp that
  rests on a matching ramp in the socket, so it stops at the right depth, the
  front of the frame is flush and only a straight hairline shows at the seam,
  and the ramp prints without support.
- The tongue's sides taper 1 degree, narrower towards the front, with 0.1 mm
  clearance when seated, so it wedges tight as it bottoms out. No glue is
  needed: in the plane the dovetail locks the halves, and once the contents
  are in, the glass and backing span both halves and stop them sliding apart
  front to back.

## Lock

Six snap tabs in the rabbet wall: one in each long side pad (two per long
side) and one in the middle of each short side. Each is a leaf 0.8 mm thick
and 10 mm wide, cut free of the wall by two slits and a 1.2 mm gap behind it,
joined to the front lip. A ridge 1.0 mm proud with 45 degree faces stands
behind the stack: its lower slope reaches the edge of a centred backing 0.2 mm
behind the back of the stack, so the stack can only shift back 0.2 mm, and an
off-centre backing is pushed back to the middle as it goes in. The backing
pushes the ridges aside going in and is held by them; pulling it out firmly by
the easel cams them aside again. With 0.4 mm side clearance the grip is
0.6 mm per side. Bending strain at full deflection is about 1.6%, an estimate
to check with the test piece.

## Hanging

A keyhole in the back of every tab pad: two in each long side, one in each
short side, so the frame hangs landscape from either long side, or portrait
from one nail. Entry 6 mm for the head, 3 mm slot, 5 mm throw towards the
outside edge. The slot's lips are 1.5 mm thick with 45 degree undersides, so
they print without support and give 3.5 mm of room for the head.

## Fit tests

- `test_seam_left` and `test_seam_right`: the pad either side of one seam, to
  check the dovetail slides in and holds.
- `test_tab`: one short-side pad with its tab and keyhole and a length of lip,
  to check the click against the real backing and a nail in the keyhole.

## Files

- `frame/frame.py`: parameters, builders, sections, fit tests, export.
- `frame/tests/test_frame.py`: geometry checks.
- `frame/make_3mf.py`: Bambu Studio project, one plate for the fit tests and
  one per section.

## Assumed, not measured

- Glass and backing are cut to 279.4 x 215.9 mm, no more than 0.4 mm over.
- The stack is 8.0 mm everywhere, including over the folded easel.
- A picture nail or screw head is at most 6 mm across with a shank under 3 mm.
