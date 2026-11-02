# Learnings

What earlier projects taught about designing, testing and simulating parts
in this repo. They apply to any project here. Each item names the project
that taught it.

## Print orientation comes first

- Pick each part's print orientation before modelling its details. Model
  parts where they sit in use, and give each part a function that turns it
  onto the bed. Every print check runs on the turned part.
- A bridge is fine. A feature that starts in mid-air is not. Bambu Studio
  calls the second a "floating cantilever".
  - A bridge is a flat underside held at both ends.
  - Mid-air features include a boss hanging off a wall that prints sideways,
    a flat underside held at only one end, and a flexure's free edge.
  - Fixes: a thin web down to the bed, a teardrop point, or a 45° face.
  - Example: craft drawers, the screw bosses and fork arms in a frame that
    prints on its back.
- `overhang_area()` with planned `allow` zones catches most problems. To
  catch the rest, slice each part through the Bambu Studio command line and
  read `warning_message` in `result.json`.
  - The command line crashes slicing a project with several filaments
    (`group_nozzle_info` errors). Slice single-filament copies of each part
    instead.
- Holes and round bosses that print sideways should be teardrops. Round
  shafts that print lying down need a flat, with a 45° keel up to it. The
  keel must clear every bearing at every angle the shaft turns through.

## Printed plastic is weak across its layers

- PLA holds about 40 MPa along its printed lines and about 20 MPa across
  its layers, sometimes less. Check which way the layers run in the print
  orientation, and keep tension and bending stress in the layers' plane.
  - A leaf that bends at a layer line, such as an upright tab rooted on the
    floor of a part printed upright, is the weak case.
  - A springy strip in a part's floor, printed flat, is the strong case.
- Load springy parts along their length (tension), not by twisting or
  bending them about a corner.
  - Example: craft drawers. The side-wall stop leaf broke at about 17 N
    because its bump sat off the leaf's plane and twisted it. A floor latch
    pulled lengthwise held about 100 N.
- Sharp ends on slits crack. Give them round reliefs.

## Small interference disappears in the print

- A detent pressing 0.7 mm turned almost freely on the first print:
  tolerances on the bore, the head and the leaf ate the overlap.
  - Use about 1 mm of press, a spring stiff enough to feel, and a notch
    with 45° sides.
  - Put hard stops at both ends of the travel, so each position is
    positive whatever the detent does.
  - Example: craft drawers, the key's click.
- Print a fit test before the big part. For a mechanism, build a mini
  version from the same code with a `Params` override.
  - Position everything relative to the mechanism, such as the rod's axis
    or fractions of the outside size, never as absolute numbers. Then the
    mini comes out of the same functions.
  - Add a test that the mini's moving parts are the full-size ones.

## Mechanisms: follow the load

- A rotating cam or latch that a pull pushes off-centre will turn,
  whatever the shape of its tip. A round tip only makes it easier.
  - Decide which way a pull turns it. Make unlocking turn the other way,
    and stop the rotation with a hard stop right next to the load.
  - Never stop it through a long shaft and a small tooth at the far end.
    Example: craft drawers, where the lug and tooth at the top of the rod
    failed at a 2 to 16 N pull.
- Walk every load path: where the force goes in, what resists it there, and
  how that reaches the frame. Small parts far from the load, and thin plates
  carrying a load sideways, are where things break.
- Also ask what else can push the mechanism, such as a drawer pushed back in
  while locked.

## Tests

- Overlap tests at fixed positions prove the kinematics: things fit, clear
  and catch. They don't prove strength, feel, or behaviour under a push.
  Add tests that act a scenario out:
  - pull a locked drawer at every angle the rod can reach before its stop
  - try to turn the key with a drawer ajar by 1, 2 and 5 mm
  - drop the rod in at the wrong angle
- Make sure each scenario test can fail. For example, a tip-over test should
  have a load that does tip it.
- A part that falls apart into slivers often still passes overlap tests.
  Assert one solid per part.

## CadQuery gotchas

- `cut_all()` cuts a compound of cutters in one boolean. If the cutters
  overlap, it silently does the wrong thing: a bore not cut, counterbores
  missing, slivers left behind. Cut overlapping cutters one at a time.
- `Workplane("XZ")` direction conventions are easy to get wrong. The
  `xz_prism()` and `yz_prism()` helpers (craft drawers) build from an
  outline in a known plane and rotate it into place.

## Finite element checks (craft-drawers/fea.py)

- The setup: Gmsh meshes a part cropped out of the CadQuery model, and
  scikit-fem solves linear elasticity with quadratic tetrahedra. Lengths are
  in mm and forces in N, so stresses come out in MPa. Use it to rank parts
  and find the weak spots, not to predict exact breaking loads.
- Validate the solver before trusting it, on cases with a textbook answer:
  - a short, wide cantilever
  - a long, slender strip (this is the case that catches iterative-solver
    problems)
- Algebraic multigrid (pyamg) without the six rigid-body modes doesn't
  converge on slender parts. It returned an answer ten times too stiff,
  with no error.
  - Pass the rigid-body modes as `B`.
  - Check the residual, and fall back to a direct solve if it hasn't
    converged.
- Crop boxes: clamp only the faces where the crop cuts through material
  that continues. A crop face that lands on a part's free edge clamps it.
  - Example: a leaf whose top edge was the crop's top looked three times
    stronger and a thousand times stiffer than it was.
- Leave out stresses within about 1.5 mm of where a load is applied
  (Saint-Venant). A force pressed on a small patch makes a peak there that a
  real contact doesn't have.
  - If a result barely changes when you leave those out, the weak spot is
    real.
- Before redesigning a part, find where its peak stress is. Fixes aimed at
  the wrong place cost several rounds.
- A linear model is enough for these checks:
  - Strength: the stress for a 1 N load scales to a breaking load.
  - Stiffness: displacement per newton gives the force for a required
    deflection, such as a detent's press or a latch's lift.
  - Feel: a detent's torque is about its force times its radius, on a 45°
    notch.
- Memory: quadratic elements on large crops use a lot of it, and a full
  report can be stopped for lack of it. Crop tight round the part, and run
  checks one at a time: `uv run fea.py latch`.

## Working in this repo

- Each project's spec carries dated revision notes. Record every call made
  for the user there, with what it costs if wrong.
- Other work may be uncommitted in the tree. Stage only your own files. To
  commit only your part of a file someone else has also edited, stage a
  blob built from `HEAD` plus your change:
  `git hash-object -w` then `git update-index --cacheinfo`.
