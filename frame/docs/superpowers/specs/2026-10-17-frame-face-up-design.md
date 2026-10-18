# Picture frame, printed face up — design

Date: 2026-10-17

Supersedes the print orientation, lattice and slicer settings of
`2026-10-15-frame-design.md`. Everything not mentioned here (sizes, contents,
dovetails, the turn buttons and their detent, keyholes, fit-test approach)
carries over from it.

## Goal

A plain, boxy frame whose front, seen from the front, is one flat surface
with the smooth finish of a top surface, not the texture of the build plate.
No corner pieces, no lip seam: the only lines are the two hairline seams in
the middle of the top and bottom sides. It uses as little plastic as gives a
stiff frame.

## Why face up

The front came off the textured build plate. Printed face up the front is
the last layers, a flat top surface (ironed). A face plate laid over the
sides was considered and dropped: both it and the sides would print with
their joining faces on the bed, so neither could carry a tongue or peg to
hold the other, and it would need glue or loose keys. Separate lip strips and
corner squares were dropped for the seams they add.

## Layout

The same two halves, joined by the same sliding dovetails, the same outside
(312.4 x 248.9 x 13.5 mm), border (21 mm), lip (4.5 mm over the contents, 2 mm
thick) and rabbet, printed with the front up. Each half still fits the bed.

| From the opening outwards | Width | |
|---|---|---|
| Front lip | 4.5 + 0.4 | 2 mm thick, holds the glass |
| Side | 16.1 | solid in the model, hollowed by the slicer's infill |

The lattice goes: printed face up, every opening would need a 45 degree roof
under the front, which uses most of what the openings save, and from the
back the frame is not seen. The lock pads go with it; the keyholes and
buttons keep their positions, the long-side keyholes back in the middle of
each half.

## Interior and plastic

The model of a side is solid; the slicer makes it hollow:

- 2 walls (0.84 mm), enough round a 21 x 13.5 mm section.
- 10% gyroid infill: even strength every way, and it carries the top layers
  evenly so the front does not show the infill through.
- 5 top layers (1 mm) at the front for a flat face; 3 bottom layers at the
  back.
- Ironing on the topmost surface only, the front.

By estimate a side is about half its solid weight. A hollow modelled inside
the sides was considered: it needs a 45 degree roof so the front does not sag
over it, and its walls weigh about what the infill does, so it is not worth
the complication. The weights are taken from the slicer, not estimated, once
built.

## Printing features upside down

Face up, everything at the back is at the bed and every ceiling is the
underside of something:

- **Lip.** It overhangs the rabbet by 4.9 mm. A support wall, one line
  (0.5 mm) thick, stands under the lip all the way round, 0.8 mm in from the
  opening's edge so its scar is hidden, stopping 0.2 mm short of the lip's
  underside like a slicer support. The lip prints as a short bridge between
  the side and the wall. It is held to the half by small tabs at its foot and
  peels off before the contents go in. About 6 g in all; the slicer's own
  supports under the lip would be 8 to 12 g and less predictable.
- **Button pockets.** The peg's top is flush with the back, so it grows from
  the bed head first; its head's 50 degree underside now faces up. The pocket
  floor is a bridge, at most 8 mm from the peg to the wall; it is set 0.4 mm
  further forward than the back of the stack so a little sag does not touch
  the button.
- **Keyholes.** The lips are at the bed; the room for the nail head behind
  them gets a 45 degree gabled roof instead of a flat ceiling.
- **Dovetails.** The socket's front is already a 45 degree ramp, which is
  now its ceiling; the tongue grows from the bed. No change.
- The front's 0.6 mm chamfers are now at the top. The back edge, at the bed,
  relies on the slicer's elephant's foot compensation.

## Buttons

As before, with a firmer click: the detent finger rises to 4 mm, above the
3 mm bar, which makes it a third stiffer at the same strain (force goes with
its height; strain only with its width and how far it bends). The pocket
leaves room for it, still below the back. The buttons print on their
underside so the finger stands up; the lead chamfer under their edges is
made steeper than 48 degrees so it prints on the bed.

Printing the buttons in place on the frame was considered: the button would
have to start on the bed, so be 5 mm thick and carry the pin, whose head
would sit in a closed, roofed chamber in the pad; print-in-place needs about
0.3 mm of clearance, which makes the pivot loose; and a broken button would
mean reprinting a half. They stay separate and replaceable.

## Fit tests

- `test_seam_left` and `test_seam_right`, printed face up.
- `test_lock` and one button, now with a length of lip and its support wall,
  to check the lip prints, the wall peels off cleanly, the front finish, the
  pocket bridge, the click and the hold on the backing.

## Checks

- Parts are exported in print orientation; the overhang check allows
  horizontal undersides only where they are planned bridges (the lip over its
  wall, the pocket floors) and checks the bridges' spans.
- The front is flat and on top; the back is on the bed.
- Contents fit and are held, buttons turn clear, stay on, click, and come
  off as before; the finger strain stays under the existing limits.
- `make_3mf.py` slices the plates and reports the filament weight.

## Assumed, not measured

- A 5 mm bridge from the side to the support wall prints flat enough at the
  lip; checked on the fit test.
- A 19 mm round pocket floor bridged round its peg prints without sagging
  more than 0.4 mm.
- Ironing gives the look wanted; it can be turned off in `make_3mf.py`.
