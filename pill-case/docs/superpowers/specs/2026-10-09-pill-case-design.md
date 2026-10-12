# Four-week click-dial pill case — design

Date: 2026-10-09 (revision 4: flex-arm door latch and dial lock after first print)

## Revision 6 (2026-10-11) — supersedes everything below where it differs

Requested after the third print:

- Dial lock firmer. The post lugs' sides now lean in toward the post by
  10 degrees and the dial hooks match, so trying to untwist pulls the hooks in
  tighter instead of camming them outward (the cause of the dial still coming
  off). The dial only comes off by prying both arms back.
- Door cannot drop out. The slot now has a 0.9 mm ledge at the bottom as well
  as the 0.9 mm lip at the top, and the door's edges are wider in the middle
  than at top or bottom, so it is captive in both directions without relying
  on the base underneath. Print gap is 0.3 mm on the vertical faces and 0.4 mm
  horizontally on the sloped faces (0.28 mm at the tightest point). The window
  opening is 5.6 mm wide.
- Softer edges. The lid rim has a 0.7 mm rounded top and a 0.4 mm chamfered
  bottom edge; grip scallops are wider and shallower; rail tops are chamfered;
  the door's thumb ridge is rounded on all exposed edges; the dial's lower
  edge is chamfered.
- Added checks: the door cannot drop out, open or closed; the lug side leans
  the right way for the hooks to self-lock.

## Revision 5 (2026-10-11)

Requested after the second print:

- Tablets stand on edge. Pockets are 8.2 mm long (r = 31.0 to 39.2 mm) and
  7.7 mm deep, sized for tablets up to 7.5 mm across (my assumption; the exact
  size was not given). Wall top is at z = 8.9 mm.
- Overall size is 83.2 mm diameter x 16.9 mm tall (16.3 mm without the raised
  letters).
- The dial no longer comes off. Its two latch hooks have a face square to the
  post lugs and overlap them by 0.8 mm, so it does not untwist; removing it
  means prying both arms back with a tool. Pockets are filled through the door.
- The door is printed in place as one piece with the lid. It sits in a slot
  7.4 mm wide that goes through the lid from the hub zone to the rim; the part
  the door uncovers is the window. The slot's closed ends are the open and
  closed stops (9 mm travel), rail lips 0.7 mm over the door edges stop it
  lifting out, and the rim is now continuous. The slot is narrower than one
  pocket plus its dividers, so it never opens a neighbouring pocket.
- Door is 6.8 mm wide x 11.2 mm long x 3 mm thick. Print gap to the lid is
  0.3 mm (0.28 mm at the tightest point).
- Door latch: the flex arms moved from the door to the rails, inboard of the
  pockets (1.0 mm thick, 9.7 mm long, 0.5 mm nub). Closed, the nubs sit behind
  the door's ramped inner corners; open, they sit in notches in its edges.
- Dial radius is 29 mm so the door's thumb ridge clears it when open.
- Deliverables are now `base`, `lid_with_door` and `dial`, with fit-test
  pieces `test_hub_base`, `test_hub_lid`, `test_hub_dial` and `test_door`.
- Added checks: a tablet on edge fits under the lid and door; the slot does not
  open neighbouring pockets; the door cannot lift out; the door is at least
  0.25 mm from the lid as printed.
- Not verifiable in software: whether the print-in-place door frees cleanly.
  Print `test_door` first.

## Goal

A round pill case for a Bambu P1S that holds four weeks of one small tablet per
day, labelled by weekday (Sunday start). A translucent lid shows which pockets
still hold a tablet. The lid clicks into each day, and a small sliding door over
the current pocket opens to take the tablet out.

## Requirements (from the user)

- Tablets up to about 6 mm diameter x 3 mm thick, one per pocket. Tablets are
  pastel coloured.
- 28 pockets: 4 weeks x 7 days, Sunday first. No blank or closed positions.
- Lid printed in a separate translucent PLA so tablets are visible through it.
- Lid clicks into each day position.
- A small door gives access to one pocket.
- Smaller than the 107 mm of revision 1.
- PLA throughout.
- P1S, 0.4 mm nozzle, 0.2 mm layers, no supports.

## Decisions (mine)

- No springs or other hardware. A 10 mm spring does not fit upright in a 5.2 mm
  base, so the day detent is two printed flex arms. They rest unloaded in the
  notches, so PLA creep does not slacken them.
- Base and dial in a dark opaque PLA so pastel tablets contrast through the lid.
- Not a child-resistant closure.

## Layout

- 28 pockets in a single ring, 12.857 degrees apart, S M T W T F S four times,
  clockwise seen from above.
- Overall size 83.2 mm diameter x 13.3 mm tall.

## Parts

Four printed parts, all printed in the orientation they sit in when assembled.

### Base (opaque)

- Floor 1.2 mm; pockets 4 mm deep; divider and wall top at z = 5.2 mm.
- Pocket ring r = 32.2 to 39.2 mm, 1.0 mm dividers, 1.0 mm floor fillets.
- Outer wall 1.6 mm thick, r = 40.8 mm.
- Hub sprocket, r = 14 mm, with 28 V-notches 1.0 mm deep, rising 3.7 mm above
  the wall top. The lid turns on it and the dial rests on it.
- Centre post, 12 mm diameter, with two bayonet lugs (45 degree chamfered
  undersides).

### Lid (translucent)

- Disc r = 41.6 mm, 1.2 mm thick over the pockets, resting on the wall and
  dividers.
- Hub zone (r < 19.5 mm) and outer rim 3.4 mm thick. The rim overhangs the base
  by 0.8 mm and has 56 grip scallops.
- Two flex arms cut into the hub zone, 2.0 mm thick and about 19 mm long, each
  with a nub that drops into a sprocket notch.
- One pocket-shaped window, flanked by two dovetail rails that guide the door.
  The rim is open between the rails so the door can be slid in.
- Each rail has two notches for the door latch: one at closed, square on its
  outer side so the door cannot slide out, and one at open, ramped so the door
  can be pushed shut again.

### Door (opaque, accent colour)

- Slider 13.2 mm wide x 12 mm long x 2 mm thick with a 2 mm thumb ridge, held
  down by a 0.7 mm lip on each rail.
- Slides 8 mm toward the centre to uncover the window, passing under the dial.
  The lid's hub zone is the open stop.
- A flex arm 1.2 mm wide and 9.5 mm long runs along each edge, outside the
  footprint of the window. Each carries a 0.5 mm nub that clicks into the rail
  notches at closed and at open. The arms are relaxed in both positions.

### Dial cap (opaque)

- Fixed disc, r = 30 mm, 3.8 mm thick, flat underside. Retains the lid.
- Locks to the post with a 60 degree bayonet twist against a hard stop. Two
  flex arms beside the keyways each carry a hooked nub that drops in behind a
  lug, overlapping it by 0.5 mm, so the dial has to be deliberately twisted to
  release. Axial play is 0.2 mm at the lid plus 0.15 mm at the bayonet seat.
- Weekday letters raised 0.6 mm at the rim, each in line with its pocket; week
  numbers 1 to 4; a groove between weeks. Raised labels allow a second colour.

## Use

- Turn the lid by its rim; it clicks from day to day in either direction.
- Slide the door inward, tip the tablet out, slide it shut until it snaps.
- Refill: twist the dial 60 degrees anticlockwise, lift off dial and lid.

## Tooling and deliverables

- `pill_case.py`: parametric CadQuery script, run from the local `.venv`. All
  dimensions are fields of `Params`.
- `out/`: STEP and STL per part in print orientation, plus `assembly.step`.
- Fit-test pieces: `test_hub_base`, `test_hub_lid`, `test_hub_dial` (day click
  and bayonet) and `test_door_lid` with `door` (door slide and latch).

## Verification

- `tests/test_pill_case.py` checks by boolean intersection: each part is one
  valid solid; a tablet fits a pocket; the lid clears the base on each day and
  the detent engages between days; the window lines up with a pocket; the door
  clears everything open and closed, covers the window only when closed, and is
  held by its latch nubs and both end stops; the dial is retained when locked,
  is blocked by its latch hooks when untwisted, releases after the full twist
  and has a hard stop; raised text adds volume;
  no unsupported overhang beyond 45 degrees; overall size.
- Not verifiable in software: click feel, latch stiffness and real clearances.
  Print the fit-test pieces first and adjust `Params`.

## Out of scope

- Child resistance, water-tightness, multiple pills per day.
