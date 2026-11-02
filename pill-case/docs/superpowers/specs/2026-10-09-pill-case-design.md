# Four-week click-dial pill case — design

Date: 2026-10-09 (revision 4: flex-arm door latch and dial lock after first print)

## Revision 13 (2026-10-20) — supersedes everything below where it differs

- The pocket test print showed 3.7 mm fits best, so the pockets are now
  3.7 mm wide (was 4.0).
- Ribs round the base, to tell it apart from a smooth case by feel in the
  dark: 40 vertical triangular ribs, 0.7 mm proud and 1.8 mm wide at the
  foot, running the full height of the base. Their feet are cut back to
  follow the bottom chamfer, so they need no support. The lid rim still
  sticks out past them, and the base is 83.0 mm across.

## Revision 12 (2026-10-20)

After printing revision 11: the pocket depth was fine, but tablets turned
sideways in the pockets and some wedged there.

- Each pocket is now a straight slot 4.0 mm wide (tablet 3.0 mm thick) and
  8.2 mm long radially (tablet 7.5 mm across). A tablet can only stand on
  its edge with its faces to the sides, pointing at the centre. It cannot
  turn face-out or lie flat. The walls between slots are 3.0 mm at the
  inside and 4.8 mm at the outside, where they were 1.0 mm before.
- Pockets are 1 mm deeper (8.7 mm). The floor fillet is 0.5 mm (was 1.0) so
  that it clears the tablet's edge in the narrower slot. The base is 17.7 mm
  tall and the case is 18.3 mm overall.
- New check: a tablet turned face-out or lying flat collides with the slot.
- Fit test `test_pocket` (its own plate in the 3mf): a 16 x 22 x 9.9 mm
  block with three full-depth pockets 3.7, 4.0 and 4.3 mm wide, each width
  engraved beside it. The 4.0 mm pocket is the real one.

## Revision 11 (2026-10-19)

After printing revision 10: the day click is right and stays as is. The
printed-in release buttons broke off at once. With them gone, the latch arms
are easy to push aside with a finger to open the dial, and the latch holds
better than before but could take more hook.

- Buttons removed, along with the grooves in the base for them. Each opening
  they left is now a plain finger pocket, 3.5 mm wide, inside its latch arm
  (r = 10.3 to 13.8 mm, from 12 degrees clockwise to 16 degrees
  anticlockwise of the lug). To open, push both arms outward into their back
  slots and twist anticlockwise. A push of about 0.8 mm at the pocket frees
  the hook, because the arm swings out further toward its end.
- Hooks overlap the lugs by 1.8 mm (was 1.4). Their tips are 0.45 mm clear
  of the post. The slot behind each arm is 2.4 mm (was 1.9), so the hook can
  swing clear going on and coming off.
- The dial is 4.2 mm thick again with nothing above it but the letters.
  Overall height is 17.3 mm.
- Checks for the buttons replaced by: the finger push needed is well inside
  the pocket width; the back slot has room; the hook tips clear the post.

## Revision 10 (2026-10-19)

After printing revision 9: the dial still came off too easily, and the day
click was still a little too firm.

- Release buttons. Each latch arm now has a button beside it: a plunger
  printed in place in the dial, 2.7 x 6 mm across, standing 1.2 mm proud of
  the dial top. Its outer face is a 45 degree cam against a matching face on
  the arm. Pressing it 1.42 mm pushes the arm out 1.0 mm partway along. The
  arm swings out further toward its end, so the hook moves an estimated
  2.5 mm, well past the 1.7 mm it needs to clear the lug. To open, press both
  buttons and twist the dial anticlockwise; the press and the twist can be
  done with one hand. Without the buttons pressed, twisting only pulls the
  hooks in tighter.
- A step at the foot of each plunger sits under a ledge on the dial wall, so
  the button cannot be pulled out. The arm's spring pushes it back up through
  the cam. The print gap is 0.3 mm normal to every face.
- The pressed plungers drop into two curved grooves, 1.8 mm deep, cut into the
  top of the base's sprocket. The grooves run the length of the twist, so the
  buttons can stay pressed throughout.
- Latch arm moved out to r = 13.8 to 15.1 mm, 1.3 mm thick (was 1.5), rooted
  45 degrees from the lug (was 30). The hook has a blunt 5 degree nose instead
  of a sharp tip. Estimated button force is about 8 N each.
- Week numbers are 5 mm, at r = 20.5 mm, clear of the latch slots.
- The dial is exported with its buttons in place. The button tops print in
  the white band with the letters. Overall height is 17.9 mm.
- Day click about 20 % lighter than revision 9 (about 1.3 times revision 7):
  notch sides at 41 degrees (was 38), arms 2.9 mm (was 3.0).
- Added checks: the buttons are two free solids at least 0.25 mm from the
  dial; they cannot lift out; pressed, they clear the base all through the
  twist and cam the arms; the estimated hook travel clears the lugs; the
  labels stay off the latch.
- Not verifiable in software: whether the plungers free cleanly after
  printing and how hard they are to press. Print `test_hub_dial` (now 39 mm
  across, with its buttons) and `test_hub_base` first. If the hooks do not
  clear the lugs, raise `cam_w` (1.0 to 1.2 mm) or `btn_proud`. If the
  buttons are too stiff, lower `latch_t` (1.3 to 1.1 mm).

## Revision 9 (2026-10-19)

After printing revision 8: the dial latch is good and stays as is, but the day
click was too firm to turn. Revision 7 was too easy to move by accident, so
this aims between the two.

- Notch sides are 38 degrees from the radius (was 30; revision 7 was 45). At
  30 degrees, friction between PLA parts nearly locks the nub in the notch,
  which is why it would not turn.
- Notches 1.5 mm deep (was 1.7), nubs 1.3 mm (was 1.5), flex arms 3.0 mm
  thick (was 3.2), still sweeping 80 degrees.
- Estimated turning force: about 1.7 times revision 7 and about 40 % of
  revision 8. Arm strain about 1.0 %.
- Tuning: `detent_angle` changes the feel most (lower is firmer; keep it
  above about 32). `arm_t` changes it in smaller steps (0.2 mm is roughly
  20 %).

## Revision 8 (2026-10-18)

Requested after printing the revision 7 hub test pieces: the day click still
turned too easily, and the dial could still be twisted back and lifted off.

- Dial latch rebuilt. The latch arms used to be rooted clockwise of the hook,
  so untwisting pushed each arm end-on; it bowed outward and the hook slid off
  the lug. Each arm now sits outside a 1.6 mm wall around the lug seat. It is
  rooted 30 degrees anticlockwise of the locked lug and runs clockwise over
  it to a hook behind the lug. Untwisting now pulls the arm, so it cannot bow
  out of the way, and the leaning hook face draws the hook in tighter. The
  hook overlaps the lug by 1.4 mm (was 1.1 mm). The arm is 1.5 mm thick and
  about 15 mm long, with a 1.9 mm slot behind it to flex over the lug going
  on; peak strain is about 1.4 %. To remove the dial, push both hooks outward
  with a small screwdriver through the openings beside the post.
- Week numbers moved out to r = 18 mm to clear the latch slots.
- Day click much firmer. The sprocket notches are V-shaped with sides 30
  degrees from the radius (was 45) and 1.7 mm deep (was 1.2 mm); the nubs are
  1.5 mm and match the notch shape with 0.15 mm clearance. The steeper sides
  alone take roughly twice the turning force to push the nub out. The lid's
  flex arms are 3.2 mm thick (was 2.3 mm) and sweep 80 degrees (was 62). They
  are now mirror images that both run away from the door, so they can be this
  long. The lid's hub zone grew to r = 20.5 mm to make room. In all, about
  3.5 to 4 times the turning force of revision 7, with lower arm strain
  (about 1.3 %).
- `test_hub_dial` is now 33 mm across, so it includes the latch arms and the
  dial around them, and it has no raised text.
- Added checks: the latch arm is rooted anticlockwise of the lug and has room
  to flex; the day notches are at least 1.5 mm deep with sides no flatter
  than 30 degrees.
- If the click is now too hard to turn, ease `arm_t` first (3.2 to 2.8 mm).
  If the dial will not twist on, ease `latch_nub` (1.4 to 1.2 mm).

## Revision 7 (2026-10-18)

Requested after the fourth print:

- Dial much harder to remove. The bayonet lugs stand out 2.5 mm from the post
  instead of 1.5 mm and are 6.4 mm wide instead of 5 mm. They now overlap the
  dial by 2.25 mm instead of 1.25 mm, which is about twice the plastic that has
  to give way before the dial pulls off. The latch hooks overlap the lugs by
  1.1 mm instead of 0.8 mm. The dial is 4.2 mm thick instead of 3.8 mm so
  there is still material under the deeper seat. Overall height is now 17.3 mm.
- Firmer day click. The sprocket notches are 1.2 mm deep instead of 1.0 mm,
  the lid's nubs are 1.15 mm instead of 0.95 mm, and the lid's flex arms are
  2.3 mm thick instead of 2.0 mm. This makes the arms roughly 1.9 times
  stiffer, with peak bending strain of about 1.5 % (it was about 1.1 %).
- Added check: the lugs overlap the dial by at least 2 mm and resist a pull.
- Reprint `test_hub_base`, `test_hub_lid` and `test_hub_dial` first. If the
  click is too stiff or the dial will not twist on, go back towards the
  revision 6 values: `arm_t`, `nub` and `notch` for the click, `latch_nub` for
  the dial.

## Revision 6 (2026-10-11)

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
