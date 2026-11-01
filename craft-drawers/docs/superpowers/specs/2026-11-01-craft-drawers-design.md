# Craft drawers design

## Revision 3 (2026-11-01)

This note supersedes the earlier revisions and the body below where they
differ.

- **The user asked for handles that are easier to use, all the same, with no
  fun shapes.** Every drawer now has the same bar handle. It is 98 mm wide
  overall and stands 22 mm off the front. There is a 16 mm deep, 82 mm wide
  gap behind the bar, so a child's whole hand can wrap round it and pull.
  The posts and the bar's underside slope at 45 degrees, so it prints upright.
- **The chest is now 208.4 mm deep at the handles.** The handles stand about
  5 mm past the front of an 8 in shelf, which the user accepted. The frame
  and drawer fronts still fit within 8 in.
- **The drawer colours and the recessed shapes on the frame's sides stay.**

## Revision 2 (2026-11-01, after the final review)

This note supersedes Revision 1 and the body below where they differ. All of
these are my calls, fixing problems the review found.

- **The key unlocks by turning toward the back, not the front.** Locked,
  the cams point at the drawers. Unlocked, they point back. A pull on a
  locked drawer pushes the cam off-centre and twists the rod. That twist now
  runs away from unlocked and into a hard stop: a lug on the rod meets a
  tooth hanging from the badge's tube. Before this, a firm tug could swing
  the rod open.
- **A locked drawer opens about 4 mm before it is held.** The notch in the
  fin has to be that long for the cam to swing back past it.
- **The drawer stop is stronger.** The leaf is 20 mm wide and 26 mm long,
  springing from partway up the wall. The bump catches the rail by 1.1 mm. A
  low rib on each right ledge keeps the drawer from shifting more than
  0.5 mm sideways, so it can't dodge the rail.
- **Fit fixes:**
  - The detent leaf's slits now cut it free.
  - The rod has 0.35 mm clearance in its forks and floor socket.
  - The key has 0.25 mm clearance in the socket.
  - The socket's lobes are turned clear of the detent notches.
  - The floor socket is 6 mm deep, so the rod can't lift out.
  - The screws moved back, clear of the top drawer.

## Revision 1 (2026-11-01, while planning)

This note supersedes the body below where they differ. All four are my
calls, made when the geometry was worked out.

- **The rod is at the front right corner, not the back.** A tab on the
  drawer's side can only block the cam while the tab is still level with the
  rod. At the back, that is just the first 20 mm of travel. At the front, the
  tab is the whole length of the drawer's side behind the cam, so an open
  drawer blocks the key at every position out to the stop. The rod sits behind
  a front post of the frame, which takes the pull on a locked drawer and hides
  the rod.
- **The rod goes in from the top, not the back.** A slot in the top wall
  above the rod's corner is closed by a raised lock badge, about 25 x 34 mm and
  3 mm tall, held by the two M3 screws. The keyhole and the lock and unlock
  icons are on the badge. A tube under the badge leads the key down to the
  socket, and the rod's head closes the bottom of that tube, so nothing poked
  into the keyhole reaches the drawers. The back stays a plain closed wall.
  The total height is about 251 mm.
- **The drawer stop releases with a press, not a lift.** At the back of each
  drawer's left wall there is a springy strip with a small bump on it. At
  about two thirds of the way out, the bump catches the end of a short rail on
  the frame's inner wall. To take a drawer out, an adult reaches into the
  drawer, presses the strip in at the back left corner, and pulls. Pushing a
  drawer in needs no press: the bump ramps over the rail.
- **No finger grip recesses on the sides.** The left side has only 2 mm of
  room inside, so a recess would cut into the drawer's path. The unit is
  carried from underneath. The side decorations are shallow recessed shapes
  (circle, triangle, square, star), so the width stays 8 in.

## Intent

A small chest of four drawers for the family's craft supplies: markers,
crayons, colored pencils and brushes. It lives on a bookshelf next to the
craft area and gets carried to the craft table and back. The drawers lock
with a printed key, so the adults decide when the kids can get at the
supplies. It should look fun to the kids, stand steady, and not use more
plastic than it needs.

## Goals

- Fit a bookshelf that is 8 in (203 mm) deep, sliding in front first.
- Hold full-length colored pencils (about 7 in, 178 mm) lying flat, plus
  standard markers, crayons and ordinary paint brushes. The largest brushes
  do not have to fit.
- Four drawers in one frame that prints as a single piece on a Bambu P1S.
- One key locks and unlocks all four drawers at once.
- Light and compact enough to carry with two hands, and steady on a table or
  shelf when a drawer is pulled out.
- Fun for the kids: a different color and a simple pull shape on each drawer.

## Non-goals

- No labels or label holders. The family will label the drawers themselves,
  so drawer fronts stay plain apart from the pull.
- Hardware is limited to two M3 screws for the lock cover and optional
  stick-on bumpers. Everything else is printed.
- No real security. The lock should stop young kids. A determined
  7-year-old with a screwdriver may get past it, and that is acceptable.
- Not stackable or modular.

## Anti-goals

- No openings in the frame that a child could push a pencil, crayon or
  finger through to reach the lock or jam a drawer. The outside of the frame
  is closed on the top, bottom, sides and back.
- The lock must not be workable with a fingertip, a pencil, a coin or a
  common hex key.
- The parts must not be heavier than they need to be. Thick solid walls
  "just to be safe" go against what the user asked for.

## Constraints

- Bambu Lab P1S, 256 x 256 x 256 mm build volume, 0.4 mm nozzle, PLA,
  0.2 mm layers, no supports. These match the rest of the repo.
- Same project layout as the other projects in this repo: `craft_drawers.py`
  with a `Params` class and one function per part, `make_3mf.py`, pytest
  geometry checks in `tests/`, outputs in `out/`.
- The user does not have to own an AMS. Colors come from printing each part
  in its own filament, with no color changes within a part.

## Overall size (decided)

- Width 8 in (203.2 mm), as the user asked.
- Depth about 196 mm, a little under 8 in, so it slides fully onto the
  8 in shelf. The builder may adjust this by a few mm.
- Height about 248 mm, as tall as the P1S allows with some margin.
- Four drawers stacked vertically, each about 2.3 in (about 58 mm) tall on
  the outside. The user picked four shorter drawers in one frame over two
  stacked halves with 3 in drawers.

## Frame

- One printed piece: an open-fronted box with top, bottom, two sides and a
  closed back.
- *My call:* print the frame lying on its back, open front facing up. The
  frame is about 248 mm long on the bed, and every wall and runner is then a
  vertical wall with nothing to bridge.
- *My call:* no full shelves between drawers. Each drawer runs on a pair of
  ledges, one on each side wall. This saves a lot of plastic compared with
  three solid shelves. The drawer above covers the drawer below closely
  enough that overfilled contents rub rather than fall behind.
- *My call:* walls thin enough to save plastic but stiff enough to carry by
  the sides, about 1.8 mm for the sides and 2.0 mm for the top and bottom.
  The back can be thinner, about 1.2 mm, since the box shape stiffens it. The
  builder can stiffen with shallow outside ribs or raised shapes instead of
  thicker walls.
- *My call:* finger grip recesses near the bottom of each side, so it is
  easy to lift off the shelf and carry. These are recesses only. They do not
  go through the wall.
- *My call:* four shallow round recesses under the base for stick-on rubber
  bumpers, so it does not slide on the table. The bumpers are optional.

## Drawers

- Four identical drawers, each printed in its own color.
- Inside, each drawer must take a 180 mm pencil lying front to back, with a
  few mm to spare. It is about 180 mm wide and about 50 mm deep inside.
- *My call:* walls and floor about 1.2 mm, with a solid floor so crayon bits
  don't fall into the drawer below.
- The drawer front is a slightly oversized plate that covers the frame edges
  around the opening. It has rounded corners and is about 3 mm thick.
- Each front has a pull in a simple shape: circle, triangle, square and star,
  one per drawer. A child's fingers must be able to grip each pull and pull
  it toward them. Whether the pull is a raised knob or a recessed finger pocket
  in that shape is up to the builder. It must print without supports in the
  drawer's print orientation.
- *My call:* a drawer stop. A drawer pulls out about two thirds of the way and
  then stops, so a child cannot yank it out and spill it. An adult takes it
  out fully by lifting the front a little while pulling. The builder chooses
  the mechanism, for example a bump under the drawer that catches the front
  of its ledge.
- *My call:* optional dividers. Each drawer has a few pairs of shallow slots
  in its side walls so thin divider plates can be dropped in, separating
  pencils from crayons, for example. The dividers are separate parts printed
  in any color. A drawer works without them.

## Lock

- A single rod runs vertically inside the frame, in one back corner (the
  builder picks the left or right side). It turns about 90 degrees between
  locked and unlocked.
- The rod has one cam per drawer, printed as part of the rod. Each drawer has
  a tab on the matching back corner. Locked, every cam stands in front of its
  drawer's tab, so the closed drawer cannot be pulled out more than a mm or
  two. Unlocked, the cams swing clear into a recess beside the drawer, and
  the drawer slides freely.
- *My call:* the key only turns to locked when all four drawers are shut.
  Each drawer has a fin running along its side at cam height, all the way
  from the tab to the front, so an open drawer at any position blocks its cam.
  The rod then stops partway, and the missing detent click tells the user
  something is open. The cams are rigid. With a drawer removed entirely, the
  user unlocks before sliding it back in. No self-latching: one shared rod
  can't let a single drawer latch without unlocking the others.
- The rod is a separate part, printed lying flat (about 240 mm long). It goes
  in through a slot in the back of the frame, behind the rod's corner, sized
  to pass the cams. A printed cover plate closes the slot and is held by two
  M3 screws (the user has M3 screws). The builder chooses the screw length
  and whether they thread into the plastic directly or into printed bosses.
  Once assembled, the rod cannot be reached or removed from the front, and the
  cover comes off only with a screwdriver. The cover and its screws must not
  stop the unit sliding fully back on the shelf, so the screw heads are
  recessed.
- *My call:* a detent that clicks at the locked and unlocked positions, so the
  rod does not drift and the user can feel when it is locked.
- **Keyhole:** on top of the frame above the rod there is a round hole about
  12 to 15 mm across. Some distance down it (deep enough that a fingertip
  cannot reach, about 15 mm or more) the rod ends in a socket with an unusual
  shape. Not a hex, square or slot, so common tools and coins do not fit. A
  three-lobed or asymmetric shape is fine.
- **Key:** a short printed key, about 50 to 60 mm long, with a tip matching the
  socket, a wide grip with a hole for a keyring or string, and a fun shape on
  the grip. *My call:* print two keys, one as a spare.
- Small raised or recessed lock and unlock icons beside the keyhole show which
  way to turn.

## Colors and style

- Each drawer gets its own color. The frame is one color, ideally white or a
  neutral, so the drawers stand out. The builder sets up the Bambu Studio
  project so each part is a separate object the user can assign a filament to.
- The fun comes from the colored drawers, the pull shapes, and optionally
  raised or recessed simple shapes on the frame's sides. Nothing goes through
  the walls.
- Rounded outer edges everywhere a child might grab or bump into.

## Plastic budget

- *My call:* aim for about 1 kg of PLA for the frame and four drawers
  together, roughly half in the frame. Thin walls and runners instead of
  shelves are what keep it there. The builder should report the actual
  estimate from Bambu Studio.

## Stability

- With one drawer fully out at its stop and loaded with supplies, the unit
  must not tip forward. The stop at about two thirds of the drawer's travel
  is part of what keeps this true. The builder should check it with rough
  weights, for example a 300 g drawer load against the frame's own weight.

## Tests (geometry checks, following the repo pattern)

- Every part fits the P1S build volume in its print orientation.
- Each drawer's side fin blocks its cam at every open position, so the rod
  can only reach the locked position with all four drawers shut.
- The rod's cams pass through the back slot, and the cover plate closes it.
- The outside depth fits within 203 mm, and the outside height fits the bed.
- A 180 mm by 8 mm pencil fits inside a drawer lying front to back.
- Each drawer clears its opening and runs on its ledges with clearance.
- With the rod locked, each cam overlaps its drawer's tab when the drawer is
  closed. With the rod unlocked, each cam clears the drawer's travel
  completely.
- The key tip fits the socket, and a 6 mm hex key does not turn it.
- The pull shapes on the four drawers all differ.

## Left to the builder

- Exact clearances, ledge sizes, cam shape and rod diameter.
- How the rod is retained in the frame, and which back corner it sits in.
- The detent mechanism.
- The drawer stop mechanism.
- Key and socket shapes, within the rules above.
- Pull style (raised knob or recessed pocket) and decoration on the sides.
- Print orientation of the drawers, rod and key.
