import sys
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import frame as fr  # noqa: E402

P = fr.P
EPS = 0.01  # mm^3, boolean noise floor


def overlap(a, b):
    return a.intersect(b).val().Volume()


def moved(part, x=0.0, y=0.0, z=0.0):
    return part.translate((x, y, z))


def size(part):
    """Measured over the vertices: the bounding box is loose once the shape
    has been meshed by an earlier test."""
    pts = [v.toTuple() for v in part.vertices().vals()]
    return [max(c) - min(c) for c in zip(*pts)]


@pytest.fixture(scope="module")
def body():
    return fr.make_body()


@pytest.fixture(scope="module")
def halves(body):
    return fr.make_sections(body=body)


@pytest.fixture(scope="module")
def parts(halves):
    out = dict(zip(fr.section_names(), halves))
    out.update(fr.fit_test_parts(parts=halves))
    return out


def contents(p=P):
    """The glass, picture and backing as one block, centred in the rabbet."""
    return fr.box(-p.content_w / 2, p.content_w / 2, -p.content_h / 2, p.content_h / 2, p.skin, p.skin + p.stack)


# --- Every part -------------------------------------------------------------


def test_parts_are_single_valid_solids(parts):
    for name, part in parts.items():
        assert part.solids().size() == 1, name
        assert part.val().isValid(), name


def test_no_unsupported_overhangs(parts):
    for name, part in parts.items():
        assert fr.overhang_area(part) < 0.5, name


def test_parts_fit_the_bed(parts):
    for name, part in parts.items():
        x, y, z = size(part)
        assert max(x, y) <= P.bed and z <= P.depth + 0.01, name


def zmin(part):
    return min(v.Z for v in part.vertices().vals())


def test_front_is_flat_on_the_bed(halves):
    for half in halves:
        assert zmin(half) == pytest.approx(0, abs=1e-6)


# --- Size and contents --------------------------------------------------------


def test_frame_is_cut_in_two(halves):
    assert fr.sections() == 2 and len(halves) == 2


def test_opening_and_outside(body):
    assert fr.sight() == pytest.approx((272.4, 208.9))
    x, y, z = size(body)
    assert (x, y, z) == pytest.approx((312.4, 248.9, P.depth), abs=0.01)


def test_contents_fit_with_clearance(body):
    """The stack fits centred. Off-centre it fits as far back as the ridges,
    whose slopes then centre the backing."""
    assert overlap(body, contents()) < EPS
    front = fr.box(-P.content_w / 2, P.content_w / 2, -P.content_h / 2, P.content_h / 2, P.skin, fr.ridge_z())
    for dx, dy in ((P.clr - 0.05, 0), (0, P.clr - 0.05)):
        assert overlap(body, moved(front, dx, dy)) < EPS
    for dx, dy in ((P.clr + 0.1, 0), (0, P.clr + 0.1)):
        assert overlap(body, moved(front, dx, dy)) > EPS


def test_lip_stops_the_contents_at_the_front(body):
    assert overlap(body, moved(contents(), z=-0.1)) > EPS


def test_tabs_hold_the_contents_in(body):
    """Pushed back by more than the slack, the backing meets every ridge,
    even when it has slid to one side by the full clearance."""
    stack = contents()
    for dx, dy in ((0, 0), (P.clr, 0), (-P.clr, 0), (0, P.clr), (0, -P.clr)):
        assert overlap(body, moved(stack, dx, dy, P.slack + 0.1)) > EPS


def test_six_tabs_with_ridges_behind_the_stack(body):
    rw, rh = fr.rabbet()
    found = 0
    for side, deg, yr, _ in fr.sides():
        for c, has_tab in fr.pads(side):
            if not has_tab:
                continue
            found += 1
            z = fr.ridge_z() + P.tab_proud
            probe = fr.turn(fr.box(c - 1, c + 1, yr - P.tab_proud + 0.1, yr - 0.1, z, z + 0.2), deg)
            assert overlap(body, probe) == pytest.approx(probe.val().Volume(), rel=1e-3), side
            gap = fr.turn(fr.box(c - 1, c + 1, yr + P.tab_t + 0.1, yr + P.tab_t + fr.tab_back() - 0.1, P.skin + 0.1, P.depth - 0.1), deg)
            assert overlap(body, gap) < EPS, side  # room behind the leaf to bend
    assert found == 6


def test_leaf_bending_strain_is_moderate():
    """Cantilever strain at full deflection: 3 t d / (2 L^2)."""
    length = fr.ridge_z() + P.tab_proud - P.skin
    assert 3 * P.tab_t * P.tab_proud / (2 * length**2) < 0.017


# --- Joints -----------------------------------------------------------------


def test_halves_meet_without_colliding(halves):
    left, right = halves
    assert overlap(left, right) < EPS


def test_left_half_carries_both_tongues(halves):
    left, right = halves
    _, h = fr.outer()
    for y0, y1 in ((0, h), (-h, 0)):
        past_seam = fr.box(0.5, P.tongue_len - 0.5, y0, y1, P.depth - 1, P.depth)
        assert overlap(left, past_seam) > EPS
        assert overlap(right, fr.box(-P.tongue_len + 0.5, -0.5, y0, y1, 0, P.depth)) < EPS


def test_dovetails_lock_the_halves_sideways(halves):
    """The flare is shallow, so pulling apart takes up the clearance over
    about 0.4 mm before the dovetail bears."""
    left, right = halves
    for d in ((0.6, 0, 0), (0, 0.3, 0), (0, -0.3, 0)):
        assert overlap(left, moved(right, *d)) > EPS, d


def test_halves_slide_apart_only_out_of_the_back(halves):
    left, right = halves
    assert overlap(moved(left, z=P.depth + 1), right) < EPS
    assert overlap(moved(left, z=0.5), right) < EPS
    assert overlap(moved(left, z=-0.1), right) > EPS  # the ramp stops it seated


def test_seam_is_flush_at_the_front(halves):
    """Both halves reach the front right up to the seam, so only a hairline shows."""
    _, h = fr.outer()
    for half, x0, x1 in ((halves[0], -0.5, -0.1), (halves[1], 0.1, 0.5)):
        assert overlap(half, fr.box(x0, x1, -h, h, 0, 0.05)) > EPS


def test_joint_clearance_when_seated(halves):
    left, right = halves
    clr = P.joint_clr
    assert overlap(left, moved(right, y=clr - 0.03)) < EPS
    assert overlap(left, moved(right, y=-(clr - 0.03))) < EPS


# --- Hanging -------------------------------------------------------------------


def test_nail_head_hangs_in_every_keyhole(body):
    zl = P.depth - P.key_lip
    for side, deg, yr, _ in fr.sides():
        for c, has_tab in fr.pads(side):
            if not has_tab:
                continue
            y0 = yr + P.tab_t + fr.tab_back() + P.key_web + P.key_head / 2
            zs = zl - (P.key_head - P.key_neck) / 2  # top of the straight-sided room
            head = fr.cyl(P.key_head / 2 - 0.2, zs - 1.4, zs - 0.1, c, y0 + P.key_throw)
            shank = fr.cyl(P.key_neck / 2 - 0.2, zs - 0.1, P.depth + 2, c, y0 + P.key_throw)
            nail = fr.turn(head.union(shank), deg)
            assert overlap(body, nail) < EPS, side
            assert overlap(body, moved(nail, z=0.5)) > EPS, side  # cannot pull out
            entry = fr.turn(fr.cyl(P.key_head / 2 - 0.1, zs - 1.4, P.depth + 2, c, y0), deg)
            assert overlap(body, entry) < EPS, side


# --- Other sizes ----------------------------------------------------------------


def test_section_count_follows_the_size():
    assert fr.sections(replace(P, content_w=177.8, content_h=127.0)) == 1  # 7 x 5
    assert fr.sections(replace(P, content_w=508.0, content_h=203.2)) == 3  # 20 x 8
    with pytest.raises(ValueError):
        fr.sections(replace(P, content_w=355.6, content_h=279.4))  # 14 x 11
    with pytest.raises(ValueError):
        fr.sections(replace(P, content_w=215.9, content_h=279.4))  # long side not along x


def test_small_frame_prints_in_one_piece():
    p = replace(P, content_w=177.8, content_h=127.0)
    (part,) = fr.make_sections(p)
    assert part.solids().size() == 1 and part.val().isValid()
    assert overlap(part, contents(p)) < EPS


def test_every_lattice_run_holds_whole_cells():
    for side, _, _, half in fr.sides():
        for a, b in fr.runs(side, half):
            n = round((b - a) / P.cell)
            assert abs((b - a) / n - P.cell) < P.cell * 0.15, (side, a, b)


# --- Fit tests -----------------------------------------------------------------


def test_fit_tests_use_little_plastic(parts):
    for name in ("test_seam_left", "test_seam_right", "test_tab"):
        assert fr.grams(parts[name]) < 8, name


def test_seam_test_pieces_join(parts):
    a, b = parts["test_seam_left"], parts["test_seam_right"]
    assert overlap(a, b) < EPS
    assert overlap(a, moved(b, 0.6)) > EPS
