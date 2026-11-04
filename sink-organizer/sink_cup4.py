"""The single wide cup (sink_cup.py) for four electric toothbrushes.

Run `uv run sink_cup4.py` from this folder to write STEP and STL files to
out/, prefixed `cup4_`.

The same 6 x 3 fluted sleeve and drip tray, with places for three
separators instead of five, dividing the inside into four even sections,
one per toothbrush on its charger. Each section has its own opening in the
back wall for the charger's cord, in sleeve and tray alike.
"""

from dataclasses import replace

import sink_cup as sc

C4 = replace(sc.C, name="cup4", stops=tuple(k / 4 for k in range(1, 4)), cords=(0, 1, 2, 3))


def make_parts(c=C4):
    return sc.make_parts(c)


if __name__ == "__main__":
    sc.main(c=C4)
