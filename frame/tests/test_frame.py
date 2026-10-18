import math
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
def btn():
    """Without its detent finger, whose nub presses on the pocket wall by
    design; the detent has its own tests."""
    return fr.button(finger=False)


@pytest.fixture(scope="module")
def btn_det():
    return fr.button()


@pytest.fixture(scope="module")
def supported(body):
    return fr.make_sections(body=body, support=True)


@pytest.fixture(scope="module")
def parts(supported):
    """Every printed part, turned as it prints, the halves with their lip support."""
    out = {n: fr.face_up(h) for n, h in zip(fr.section_names(), supported)}
    out.update({n: fr.face_up(t) for n, t in fr.fit_test_parts(parts=supported).items()})
    out["button"] = fr.button_print()
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
    allow = [fr.face_up(z) for z in fr.bridge_zones()]
    for name, part in parts.items():
        assert fr.overhang_area(part, allow=allow) < 0.5, name


def test_parts_fit_the_bed(parts):
    for name, part in parts.items():
        x, y, z = size(part)
        assert max(x, y) <= P.bed and z <= P.depth + 0.01, name


def zmin(part):
    return min(v.Z for v in part.vertices().vals())


def test_halves_print_face_up(parts):
    """Turned to print, the back is on the bed and the solid front is the top."""
    w, h = fr.outer()
    sw, sh = fr.sight()
    ring = (w * h - (4 - math.pi) * P.corner_r**2 - sw * sh) * 0.4
    for name in fr.section_names():
        part = parts[name]
        assert zmin(part) == pytest.approx(0, abs=1e-6), name
        top = fr.box(-w, w, -h, h, P.depth - P.chamfer - 0.5, P.depth - P.chamfer - 0.1)
        assert overlap(part, top) == pytest.approx(ring / 2, rel=0.02), name


def test_pegs_start_on_the_bed(body):
    """Each peg's head is flush with the back, so face up it prints from the bed."""
    for deg, yr, c in fr.locks():
        dot = fr.turn(fr.cyl(0.5, P.depth - 0.1, P.depth, c + fr.btn_x(), yr + P.btn_pivot), deg)
        assert overlap(body, dot) == pytest.approx(math.pi * 0.25 * 0.1, rel=0.02), (deg, c)


def test_lip_is_supported_while_printing(body):
    """A wall one line thick under the lip stops just short of it, inside the
    opening's edge, and touches the frame only by the tabs at its foot."""
    wall = fr.lip_support()
    tabs = wall.intersect(fr.box(-500, 500, -500, 500, P.depth - P.tab_h, P.depth))
    assert overlap(wall, body) < tabs.val().Volume() * 0.05  # the tabs' 0.01 mm into the rabbet wall
    assert overlap(moved(wall, z=-(P.sup_gap + 0.05)), body) > EPS  # raised by the gap, it meets the lip
    assert overlap(wall, contents()) > EPS  # it stands where the contents go: peeled off first


def test_lip_bridge_is_short():
    assert P.lip + P.clr - P.sup_in - P.sup_w <= 4.5


def test_bridges_are_short():
    assert fr.pocket_r() - P.peg_r <= 8.5  # pocket floor, peg to wall


# --- Size and contents --------------------------------------------------------


def test_frame_is_cut_in_two(halves):
    assert fr.sections() == 2 and len(halves) == 2


def test_opening_and_outside(body):
    assert fr.sight() == pytest.approx((270.4, 206.9))
    x, y, z = size(body)
    assert (x, y, z) == pytest.approx((312.4, 248.9, P.depth), abs=0.01)


def test_contents_fit_with_clearance(body):
    assert overlap(body, contents()) < EPS
    for dx, dy in ((P.clr - 0.05, 0), (0, P.clr - 0.05)):
        assert overlap(body, moved(contents(), dx, dy)) < EPS
    for dx, dy in ((P.clr + 0.1, 0), (0, P.clr + 0.1)):
        assert overlap(body, moved(contents(), dx, dy)) > EPS


def test_lip_stops_the_contents_at_the_front(body):
    assert overlap(body, moved(contents(), z=-0.1)) > EPS


def test_front_is_solid(body):
    """From the front the border is solid all the way round."""
    w, h = fr.outer()
    sw, sh = fr.sight()
    ring = (w * h - (4 - math.pi) * P.corner_r**2 - sw * sh) * 0.4
    slab = fr.box(-w, w, -h, h, P.chamfer + 0.1, P.chamfer + 0.5)
    assert overlap(body, slab) == pytest.approx(ring, rel=1e-3)


def test_sides_are_solid(body):
    """No lattice: just in front of the back, the border is solid but for the
    button pockets and keyholes."""
    w, h = fr.outer()
    rw, rh = fr.rabbet()
    border = (w * h - (4 - math.pi) * P.corner_r**2 - rw * rh) * 0.4
    got = overlap(body, fr.box(-w, w, -h, h, P.depth - 0.5, P.depth - 0.1))
    assert 0.85 * border < got < border


def test_six_buttons_hold_the_contents_in(body, btn):
    """Every closed button sits clear of the frame and the contents, and stops
    the backing moving back, even when it has slid away by the full clearance."""
    assert len(fr.locks()) == 6
    for deg, yr, c in fr.locks():
        b = fr.button_at(deg, yr, c, part=btn)
        assert overlap(body, b) < EPS and overlap(contents(), b) < EPS
        for dx, dy in ((0, 0), (P.clr, 0), (-P.clr, 0), (0, P.clr), (0, -P.clr)):
            assert overlap(b, moved(contents(), dx, dy, 0.1)) > EPS, (deg, c, dx, dy)


def test_buttons_turn_clear_of_the_frame(body, btn):
    for deg, yr, c in fr.locks():
        for theta in (30, 60, 90, 120, 150, 180):
            assert overlap(body, fr.button_at(deg, yr, c, theta, part=btn)) < EPS, (deg, c, theta)
        open_ = fr.button_at(deg, yr, c, 90, part=btn)
        assert overlap(open_, moved(contents(), z=1)) < EPS  # open, the contents lift out


def test_buttons_stay_on_while_in_use(body, btn):
    """From closed to open the peg's head stops a button lifting off, and the
    pocket wall stops it sliding back far enough for its hole to pass over
    the head."""
    assert fr.pocket_r() - fr.btn_tail() < P.btn_off - 0.5
    for deg, yr, c in fr.locks():
        for theta in (0, 45, 90):
            b = fr.button_at(deg, yr, c, theta, part=btn)
            assert overlap(body, moved(b, z=0.5)) > EPS, (deg, c, theta)
            a = math.radians(theta + deg)
            back = (-math.sin(a) * P.btn_off, math.cos(a) * P.btn_off)
            assert overlap(body, moved(b, *back)) > EPS, (deg, c, theta)


def test_buttons_come_off_turned_outwards(body, btn):
    for deg, yr, c in fr.locks():
        a = math.radians(deg)
        for s in (1.0, 2.0, 3.0, P.btn_off):
            b = moved(fr.button_at(deg, yr, c, 180, part=btn), math.sin(a) * s, -math.cos(a) * s)
            assert overlap(body, b) < EPS, (deg, c, s)
        assert overlap(body, moved(b, z=P.depth)) < EPS


def test_buttons_click_into_closed_and_open(body, btn_det):
    """The nub sits in a notch at closed and open, and presses on the pocket
    wall in between, so the button stays where it is turned."""
    for deg, yr, c in fr.locks():
        for theta in (0, 90):
            assert overlap(body, fr.button_at(deg, yr, c, theta, part=btn_det)) < EPS, (deg, c, theta)
        for theta in (20, 45, 70):
            assert overlap(body, fr.button_at(deg, yr, c, theta, part=btn_det)) > EPS, (deg, c, theta)


def test_detent_finger_strain_is_low():
    """Cantilever strain 3 t d / (2 L^2): turning, the nub is pushed in by
    det_press; taking the button off pushes it in further where the pocket
    wall meets the rabbet. PLA yields at about 2.5%."""
    L = fr.det_len()
    assert 3 * P.det_w * P.det_press / (2 * L**2) < 0.01
    off = fr.pocket_r() + P.det_press - math.sqrt(fr.pocket_r() ** 2 - P.btn_pivot**2)
    assert 3 * P.det_w * off / (2 * L**2) < 0.02


def test_detent_finger_is_taller_than_the_bar():
    """Force goes with the finger's height, strain does not: 4 mm against the
    3 mm bar is a third firmer. It stays clear of the back."""
    assert P.det_h >= P.btn_t * 4 / 3 - 1e-9
    assert fr.stack_back() + P.det_h <= P.depth - 0.5
    assert size(fr.button_print())[2] == pytest.approx(P.det_h)


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
    for z in (0.5, 2, 4, 6, 8, 10, 12, P.depth + 1):  # clear of the seam button pegs all the way
        assert overlap(moved(left, z=z), right) < EPS, z
    assert overlap(moved(left, z=-0.1), right) > EPS  # the ramp stops it seated


def test_seam_is_flush_at_the_front(halves):
    """Both halves reach the front right up to the seam, so only a hairline shows."""
    _, h = fr.outer()
    for half, x0, x1 in ((halves[0], -0.5, -0.1), (halves[1], 0.1, 0.5)):
        assert overlap(half, fr.box(x0, x1, -h, h, 0, 0.05)) > EPS


def test_dovetail_is_snug_when_seated_with_room_going_in(halves):
    """No clearance when seated; the taper gives room until the last few mm."""
    left, right = halves
    room = math.tan(math.radians(P.joint_taper)) * 3
    for dy in (0.05, -0.05):
        assert overlap(left, moved(right, y=dy)) > EPS
    for dy in (room - 0.02, -(room - 0.02)):
        assert overlap(moved(left, z=3), moved(right, y=dy)) < EPS


# --- Hanging -------------------------------------------------------------------


def test_nail_head_hangs_in_every_keyhole(body):
    zl = P.depth - P.key_lip
    for deg, yr, c in fr.locks():
        y0 = fr.key_entry(yr)
        zs = zl - (P.key_head - P.key_neck) / 2  # top of the straight-sided room
        head = fr.cyl(P.key_head / 2 - 0.2, zs - 1.4, zs - 0.1, c, y0 + P.key_throw)
        shank = fr.cyl(P.key_neck / 2 - 0.2, zs - 0.1, P.depth + 2, c, y0 + P.key_throw)
        nail = fr.turn(head.union(shank), deg)
        assert overlap(body, nail) < EPS, (deg, c)
        assert overlap(body, moved(nail, z=0.5)) > EPS, (deg, c)  # cannot pull out
        entry = fr.turn(fr.cyl(P.key_head / 2 - 0.1, zs - 1.4, P.depth + 2, c, y0), deg)
        assert overlap(body, entry) < EPS, (deg, c)


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


# --- Fit tests -----------------------------------------------------------------


def test_fit_tests_use_little_plastic(parts):
    for name in ("test_seam_left", "test_seam_right", "test_lock"):
        assert fr.grams(parts[name]) < 12, name


def test_frame_takes_six_buttons():
    assert fr.buttons() == 6


def test_seam_test_pieces_join(parts):
    a, b = parts["test_seam_left"], parts["test_seam_right"]
    assert overlap(a, b) < EPS
    assert overlap(a, moved(b, 0.6)) > EPS
