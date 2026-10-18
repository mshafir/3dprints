# Lattice picture frame — design

Date: 2026-10-15

Print orientation, lattice and slicer settings superseded by
`2026-10-17-frame-face-up-design.md`.

## Goal

A frame for an 11 x 8.5 in (279.4 x 215.9 mm) sheet of glass, a picture and a
cardboard backing that has its own easel. From the front the border is a
plain solid moulding; behind, a lattice saves plastic. It prints without
supports on the P1S and locks the contents in so they cannot fall out of the
back. Other picture sizes are a change of
parameters.

## Constraints

- Bambu Lab P1S, 256 x 256 mm bed (parts kept to 250 mm), 0.4 mm nozzle, PLA,
  0.2 mm layers, no supports: no downward face flatter than 45 degrees.
- One filament.
- The stack (glass + picture + backing) is 6.5 mm thick at its edge, where
  the buttons bear, measured with calipers. The folded easel makes the middle
  about 8 mm, which only the open back has to clear.
- Displayed landscape, on a wall or standing on the backing's easel. The lock
  must leave the middle of the backing clear for the easel.

## Why it is not one piece

The picture alone is 279.4 mm long, wider than the bed. A frame around it does
not fit diagonally either (a rectangle a x b fits a square bed s only if
roughly a + b < 1.41 s). The fewest pieces is two: the frame is cut down the
middle into two halves, each about 163 x 249 mm.

## Look

Seen from the front, the border is 21 mm wide:

| From the opening outwards | Width | |
|---|---|---|
| Front lip | 4.5 + 0.4 | solid, 2 mm thick, holds the glass by 4.5 mm |
| Rabbet wall | 1.8 | solid, full depth |
| Lattice band | 12.7 | open at the back, solid for its front 1.2 mm |
| Outer rim | 1.6 | solid, full depth |

The lattice is only seen from behind; from the front the border is solid.
The band is a trellis: a row of diamonds along its middle with triangles
between them at its edges, separated by 1.6 mm bars (four nozzle widths). The
pitch is about 15 mm, stretched on each run so every run holds a whole number
of cells. Each corner has a round opening (a rondel). Solid pads interrupt the band:
20 mm long at the joints, about 36 mm where a keyhole and a button are. On the long sides each
lock pad is centred in its half; on the short sides its keyhole is centred.

The frame is 13.5 mm deep and prints face down, so the front takes the finish
of the build plate. The outer and inner front edges have a 0.6 mm 45 degree
chamfer, which also hides elephant's foot.

Size: opening 270.4 x 206.9 mm, outside 312.4 x 248.9 mm. About 197 g of
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
- The tongue's sides taper 1 degree, narrower towards the front, so it has
  room going in (about 0.05 mm a side 3 mm before it seats) and no clearance
  when seated: the last few millimetres are a light press fit, to be tuned
  with `joint_clr` on the fit test. No glue is needed: in the plane the
  dovetail locks the halves, and once the contents are in, the glass and
  backing span both halves and stop them sliding apart front to back.
- Printed, the dovetail holds the halves on its own. A seam button across
  each dovetail was tried and taken out again as not needed.

## Lock

Six turn buttons: one in each long side's lock pad (two per long side) and one
in the middle of each short side. Snap tabs were tried first, but a ridge
1 mm proud grips an off-centre backing by as little as 0.2 mm.

- Each lock pad has a round pocket in its back, 9.5 mm in radius, whose floor
  is level with the back of the stack, and a peg in it: a 3 mm neck with a
  4.6 mm head, 1.6 mm tall, whose underside is 50 degrees, so it prints without support.
- The button is a flat bar 3 mm thick and 7.2 mm wide, printed on its top,
  with 1.2 mm round the hole for the peg's head (first 2 mm and 1 mm). It
  pivots on the peg's neck, and closed it reaches 5 mm over the backing (4.2 mm
  if the backing has slid away by the full clearance). Its lower edges are
  chamfered 0.5 mm so it rides onto a backing that is a little thick. Turned a
  quarter turn it lies along the side, clear of the opening.
- A detent holds it where it is turned: the first print turned too freely. A
  finger 1.1 mm wide runs a quarter turn round inside the pocket wall from the
  button's tail, bending in the plane of the button (the strong way for a part
  printed flat). The tail is narrower than the arm (2.8 mm either side of the
  peg) so the finger is longer, 11 mm. Its nub, 1 mm in radius, reaches 0.7 mm
  past the wall and clicks into notches in the wall at closed and open; in
  between it presses on the wall with about 1.8 N. The second print, with
  0.4 mm, did not click: that much was lost in the print's tolerances. Strain
  is about 0.95% turning and 1.9% once, when the button is taken off; PLA
  yields at about 2.5%. The pivot clearance is 0.1 mm.
- It goes on over the head by a hole in its arm and slides towards its tip so
  the neck sits at the end of a slot. Coming off means sliding 3.5 mm the
  other way, and from closed to open the pocket wall stops it after 0.1 mm.
  Turned with its arm pointing out from the opening, its tail is over the
  opening and it slides off. Lifting is stopped by the head.
- The neck is in tension across layers when the backing pushes back: about
  7 mm^2, good for roughly 140 N per button, against about 4 N of glass and
  backing.
- The pocket floor is level with the back of a 6.5 mm stack (plus `slack`,
  0). The first print, set for 8.0 mm, did not touch the backing: the stack
  is thinner at its edges than over the easel.

## Hanging

A keyhole in the back of every lock pad, next to its button: two in each long side, one in each
short side, so the frame hangs landscape from either long side, or portrait
from one nail. Entry 6 mm for the head, 3 mm slot, 5 mm throw towards the
outside edge. The slot's lips are 1.5 mm thick with 45 degree undersides, so
they print without support and give 3.5 mm of room for the head.

## Fit tests

- `test_seam_left` and `test_seam_right`: the pad either side of one seam, to
  check the dovetail slides in and holds.
- `test_lock` and one `button`: the short-side lock pad with its keyhole,
  pocket and peg and a length of lip, to check the button goes on, clicks
  closed and open and holds the real backing, and a nail in the keyhole.

## Files

- `frame/frame.py`: parameters, builders, sections, fit tests, export.
- `frame/tests/test_frame.py`: geometry checks.
- `frame/make_3mf.py`: Bambu Studio project, one plate for the fit tests and
  one per section, the six buttons with the last.

## Assumed, not measured

- Glass and backing are cut to 279.4 x 215.9 mm, no more than 0.4 mm over.
- The stack is 6.5 mm all round its edge, within 5 mm of it.
- A picture nail or screw head is at most 6 mm across with a shank under 3 mm.
- The 3 mm peg neck prints round and strong enough; checked on the fit test.
