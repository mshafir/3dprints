# Snap fits, latches and detents

General knowledge for sizing anything that bends to catch: snap hooks,
latch leaves, detent arms. Most of it comes from *Snap-Fit Joints for
Plastics – A Design Guide* (Bayer MaterialScience, now Covestro; 26 pages;
copies at [SparkFun](https://cdn.sparkfun.com/assets/home_page_posts/1/4/1/0/Plastic_Snap_fit_design.pdf)
and [MIT](https://fab.cba.mit.edu/classes/S62.12/people/vernelle.noel/Plastic_Snap_fit_design.pdf)).
The guide is written for injection-moulded engineering plastics. Notes
marked *(ours)* are how it carries over to printed PLA. They are estimates
until a print confirms them.

## Size a snap by strain, not stress

- The arm bends by the undercut while it goes in. The undercut is the
  overlap the hook has to pass. Size the arm so the strain at its root stays
  under the material's limit at that deflection.
- Rectangular arm with the load at the tip. `l` is the length, `h` the
  thickness in the bending direction at the root, `b` the width, `ε` the
  strain at the root (0.01 = 1%):

  | Arm shape | Deflection it allows |
  |---|---|
  | Constant section | `y = 0.67 ε l² / h` |
  | Thickness tapers to h/2 at the tip | `y = 1.09 ε l² / h` |
  | Width tapers to b/4 at the tip | `y = 0.86 ε l² / h` |

  To check an existing arm, turn it round. For a constant section,
  `ε = y h / (0.67 l²)`.
- The force to bend it (all three shapes) is `P = b h² E ε / (6 l)`. For a
  constant section that is `P = b h³ E y / (4 l³)`. E is the secant modulus
  at that strain. For PLA use about 3 GPa *(ours)*, or take displacement
  per newton from `fea.py`.
- What this means in practice:
  - Strain grows with `y h / l²`. Length is the cheapest fix: twice the
    length allows four times the deflection. That is how the sink
    organizer's latches were fixed.
  - At a fixed deflection, force grows with `b h³ / l³`. To make a click
    stiffer without raising the strain, make the arm wider, not thicker.
  - Tapering the thickness to half at the tip allows over 60% more
    deflection at the same strain, and uses less material. *(ours)* Keep the
    tip at least two perimeters thick (about 0.8 mm with a 0.4 mm nozzle).
- The root takes the peak stress. Stress concentration falls steeply as the
  root radius grows to about 0.6 h, and barely changes beyond that. The
  guide stops short of 0.6 h only because thick sections spoil a moulding.
  A print doesn't have that problem, so use R ≈ 0.5 to 0.6 h. Never go
  under 0.4 mm.

## Strain limits

- What the guide says:
  - For one snap, a semi-crystalline plastic can go nearly to its yield
    strain. An amorphous one can go to about 70% of it.
  - Glass-filled plastics can go to about half their strain at break.
  - For parts taken apart and put back often, use about 60% of the
    one-snap value.
  - Its examples: PC 4%, PC/ABS 2.5%, PC with 20% glass 2%.
- *(ours)* PLA is amorphous and brittle, and printing weakens it across its
  layers (see LEARNINGS.md). Applying the guide's rules to its strength
  would give about 0.7% across the layers, but our prints have taken more:

  | Where the root's tension runs | What we have printed | Working budget for repeated use |
  |---|---|---|
  | Across the layers (an upright leaf rooted on a layer line) | 1.7% survived a few snaps in the foot-latch test. 1.45% on the wider cup-top leaf felt too stiff to trust. | about 1% |
  | Along the printed lines (an arm that prints flat and bends in the bed's plane) | About 2.7%: the pill case dial latch, printed and holding. It is opened rarely. | about 2% |

  These numbers come from a few snaps on a fit test. How many cycles a part
  survives is still unknown. A strain-ladder print with repeated snaps would
  settle it.
- Measure `l` from the root to where the ridge or nub presses, not the full
  leaf length. A ridge near the root strains the leaf much more than the
  same ridge at its tip.

- A snap should come back to zero stress once it is home. *(ours)* PLA
  creeps. An arm that stays pressed, such as a detent resting preloaded on a
  flat, slowly loses its force.

### Our parts against these limits

Constant-section estimate, `ε = y h / (0.67 l²)`. Here y is the insertion
deflection (how far the nub stands proud, less the clearance), and l runs
from the root to the ridge. Checked against main at 31a2b6a.

| Part | h (mm) | l (mm) | y (mm) | Root strain | Layers at root | Verdict |
|---|---|---|---|---|---|---|
| Sink organizer foot latch (grid) | 1.2 | 8 | 0.6 | 1.7% | across | Test-printed; the click felt right |
| Sink organizer cup-top leaf (grid cups and the single cup) | 1.2 | 14.1 | 1.0 | 0.9% | across | Lengthened in revision 7. At 11.1 mm (1.45%) the printed cup clicked in so hard it felt likely to crack. |
| Pill case dial latch (curved arm, rough) | 1.3 | ≈11.3 | 1.8 | ≈2.7% | along | The highest. Printed and holding; opened rarely. Next time, root the arm further back (a larger `latch_root`) to lower the strain. |
| Frame turn-button detent | 1.1 | 11.1 | 0.7 | 0.9% | along | Fine |
| Pill case door arms | 1.0 | 9.7 | 0.5 | 0.8% | along | Fine |
| Craft drawers key click arm | 2.2 | 40 | 1.0 | 0.2% | across | Low strain; the feel comes from its stiffness |

- *(ours)* "It clicks, but it takes enough force that I worry it will
  crack" means the strain is too high, even if nothing has broken yet. The
  sink organizer's cup-top leaf felt like that at 1.45%, across the layers.
  1.7% passed in a small foot-latch test, but that only means it survived a
  few snaps.
- To soften a latch without reprinting the part it clicks into, lengthen
  the leaf at its root end. The ridge and the groove stay where they are.
  Force falls with `l³`, so a small change goes a long way: 11 to 14 mm
  halves it.

## Insertion and pull-out force

- To push a hook in, you have to overcome the bending force P plus friction
  on the ramp. The mating force is `W = P (μ + tan α) / (1 − μ tan α)`,
  where α is the lead angle. The pull-out force is the same formula with
  the return angle α′.
- The friction coefficient μ for plastic on steel is about 0.4 to 0.6 for
  amorphous plastics. Between two parts of the same plastic, it is about 1.2
  times that. *(ours)* Take μ ≈ 0.5 for PLA on PLA, and higher on rough
  layer lines.
- How much the ramp multiplies the force, `(μ + tan α)/(1 − μ tan α)`:

  | μ | 30° | 45° | 60° | Locks at |
  |---|---|---|---|---|
  | 0.4 | 1.3 | 2.3 | 6.9 | 68° |
  | 0.5 | 1.5 | 3.0 | 17 | 63° |
  | 0.6 | 1.8 | 4.0 | locks | 59° |

  - When `tan α ≥ 1/μ` the face locks. No push along the axis frees it, and
    the arm has to be lifted out.
  - Close to that angle, the force depends sharply on friction, which a
    print can't control. Use 45° or less for a click that releases, and 75°
    to 90° for a hold that's meant to be permanent. Don't use anything in
    between.
- A rotary detent's torque is `W × r`, not `P × r`. On a 45° notch with
  μ ≈ 0.5, that is about 3 P r.
- A tilted entry assembles with much less force than a straight push,
  because only part of the bead deflects at once.

## Other joint types

- **Torsion snap**: a rocker on a round torsion bar. It allows a total twist
  of `φ = (180/π) γ l / r` degrees, where l is the bar length, r its radius,
  and `γ ≈ 1.35 ε`.
  - This is a bar designed to twist. A flat leaf twisted by an off-centre
    load is a different case, and that is how the craft drawers stop leaf
    broke.
- **Annular snap** (a ring bead on a shaft or cap): the undercut it allows
  is `y = ε d`.
  - A groove at least `1.8 √(d t)` from the tube's end takes about three
    times the force of one at the end.
  - If both parts flex equally, each takes half the undercut.
- **Both parts flexible**: the undercut is split between the two parts in
  proportion to how soft each one is. Find the split by plotting each part's
  force against its deflection and taking where the curves cross.
  *(ours)* Or let `fea.py` handle it by meshing the wall the hook catches on
  as well.

## What doesn't carry over from moulding

- Tolerances. A moulding holds its undercut. A print loses a few tenths of
  a millimetre of it (see LEARNINGS.md). Draw the nominal undercut as the
  one you need plus the expected loss, then check the strain at the nominal
  size, since some prints will come out that tight.
- The guide's secant modulus curves are for Bayer's plastics only.
- Draft, ejection, and the warning about thick sections at the root.
