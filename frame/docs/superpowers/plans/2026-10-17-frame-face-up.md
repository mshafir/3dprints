# Picture frame, printed face up — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the two-half frame over so it prints front up with a flat top-surface face, drop the lattice for solid sides hollowed by the slicer, reshape the back features to print upside down, add a peel-off support wall under the lip, and make the button click firmer.

**Architecture:** `frame/frame.py` keeps modelling in frame coordinates (z = 0 the front, z grows to the back); a new `face_up()` turns finished parts over for export and for the print checks. The lip support is a separate solid, `lip_support()`, unioned in only when sections are made for printing (`make_sections(..., support=True)`), so the fit checks on contents and buttons see the bare frame. Planned bridges are listed by `bridge_zones()` and excused by `overhang_area(..., allow=...)`.

**Tech Stack:** Python 3.12 via uv, CadQuery 2.8, pytest, Bambu Studio 2.8 CLI.

**Spec:** `frame/docs/superpowers/specs/2026-10-17-frame-face-up-design.md` (on top of `2026-10-15-frame-design.md`)

## Global Constraints

- PLA, 0.4 mm nozzle, 0.2 mm layers, P1S; no slicer supports: no downward face flatter than 45 degrees except planned bridges.
- Every part fits the bed (`P.bed` = 250 mm) and the frame depth (13.5 mm).
- Outside 312.4 x 248.9 x 13.5 mm, border 21 mm, lip 4.5 mm, skin 2 mm: unchanged.
- No glue or hardware.
- Run everything from `frame/` with `uv run ...`; ad-hoc scripts with `PYTHONPATH=. uv run python ...`.
- Do not commit unless the user asks; never stage the sink-organizer files.

## Files

- Modify `frame/frame.py`: params, sizes, locks, keyhole, peg, pockets, button, lip support, print orientation, overhang check, export.
- Modify `frame/tests/test_frame.py`: drop lattice tests, add print-orientation, support, peg, detent tests.
- Modify `frame/make_3mf.py`: slicer settings, slicing and per-plate weights.
- Modify `README.md` (frame row only) and the 2026-10-15 spec (pointer to the new one).

---

### Task 1: Solid sides, no lattice

**Files:** Modify `frame/frame.py`, `frame/tests/test_frame.py`

**Interfaces:**
- Produces: `sides(p) -> [(name, deg, yr)]` (three-tuples now); `locks(p) -> [(deg, yr, c)]`, long-side keyholes at `lock_spots(p)`, short sides at 0; `lock_span(p) -> (start, end)` of a lock's features from its keyhole.
- Removes: `Params.face`, `Params.cell`, `Params.bar`, `lattice_cells`, `runs`, `lattice_cutters`, `pads`.

- [ ] **Step 1: Change the tests**

In `tests/test_frame.py` delete `test_lattice_is_open_at_the_back` and `test_every_lattice_run_holds_whole_cells`, and add:

```python
def test_sides_are_solid(body):
    """No lattice: just in front of the back, the border is solid but for the
    button pockets and keyholes."""
    w, h = fr.outer()
    rw, rh = fr.rabbet()
    border = (w * h - (4 - math.pi) * P.corner_r**2 - rw * rh) * 0.4
    got = overlap(body, fr.box(-w, w, -h, h, P.depth - 0.5, P.depth - 0.1))
    assert 0.85 * border < got < border
```

Rewrite the loop head of `test_nail_head_hangs_in_every_keyhole`:

```python
def test_nail_head_hangs_in_every_keyhole(body):
    zl = P.depth - P.key_lip
    for deg, yr, c in fr.locks():
        y0 = fr.key_entry(yr)
        ...  # body unchanged, with `side` in the messages replaced by (deg, c)
```

- [ ] **Step 2: Run, expect failure**

Run: `uv run pytest -q tests/test_frame.py::test_sides_are_solid`
Expected: FAIL (the lattice leaves well under 85% of the border).

- [ ] **Step 3: Implement**

In `Params` remove `face`, `cell`, `bar`; change the lattice comment block to:

```python
    pad: float = 20.0  # length of the seam fit-test pieces
```

Replace `lock_span`:

```python
def lock_span(p=P):
    """A lock's keyhole, pocket and notches along the side, from its keyhole:
    (start, end)."""
    return -(p.key_head / 2 + p.key_web), btn_x(p) + notch_c(p) + p.notch_r + p.key_web
```

`sides()` returns `(name, deg, yr)`:

```python
# Features are built on the top side (+y) and turned onto the others. Each side
# is (name, turn in degrees, distance of the rabbet wall from the centre).
def sides(p=P):
    rw, rh = rabbet(p)
    return [("top", 0, rh / 2), ("bottom", 180, rh / 2), ("right", -90, rw / 2), ("left", 90, rw / 2)]
```

Replace `pads` and `locks`:

```python
def locks(p=P):
    """(turn, yr, position) of every lock: a keyhole at the position and its
    button to the right of it. One in the middle of each section on the long
    sides, one in the middle of each short side."""
    return [(deg, yr, c) for side, deg, yr in sides(p) for c in (lock_spots(p) if side in ("top", "bottom") else [0.0])]
```

Delete the `# --- Lattice` section (`lattice_cells`, `runs`, `lattice_cutters`). In `make_body` replace `cut_all(body, lattice_cutters(p) + cutters)` with `cut_all(body, cutters)`. In `fit_test_parts` set `k = p.pad / 2`. Update the module docstring's first line to "Picture frame with plain solid sides, for a sheet of glass, ...".

- [ ] **Step 4: Run all tests**

Run: `uv run pytest -q`
Expected: all pass. If `test_parts_are_single_valid_solids` or the button tests fail because a lock moved, check `locks()` positions (`PYTHONPATH=. uv run python -c "import frame; print(frame.locks())"`): long sides at x = ±78.1, short sides at 0.

---

### Task 2: Back features that print upside down, and face-up export

**Files:** Modify `frame/frame.py`, `frame/tests/test_frame.py`

**Interfaces:**
- Consumes: `locks`, `btn_x`, `pocket_r` (Task 1).
- Produces: `Params.pocket_drop`; `pocket_floor(p) -> float`; `face_up(part, p) -> Workplane`; `bridge_zones(p) -> list[Workplane]` (frame coordinates); `overhang_area(part, max_deg=48.0, allow=())`.
- Removes: `Params.peg_cap` (the head now runs to the back).

- [ ] **Step 1: Write the tests**

Replace the `parts` fixture and `test_no_unsupported_overhangs`, replace `test_front_is_flat_on_the_bed`, and add two tests:

```python
@pytest.fixture(scope="module")
def parts(halves):
    """Every printed part, turned as it prints."""
    out = {n: fr.face_up(h) for n, h in zip(fr.section_names(), halves)}
    out.update({n: fr.face_up(t) for n, t in fr.fit_test_parts(parts=halves).items()})
    out["button"] = fr.button_print()
    return out


def test_no_unsupported_overhangs(parts):
    allow = [fr.face_up(z) for z in fr.bridge_zones()]
    for name, part in parts.items():
        assert fr.overhang_area(part, allow=allow) < 0.5, name


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


def test_bridges_are_short():
    assert fr.pocket_r() - P.peg_r <= 8.5  # pocket floor, peg to wall
```

- [ ] **Step 2: Run, expect failure**

Run: `uv run pytest -q tests/test_frame.py -k "overhang or face_up or bed or bridges"`
Expected: FAIL with `AttributeError: module 'frame' has no attribute 'face_up'`.

- [ ] **Step 3: Implement**

In `Params`, under the button params, remove `peg_cap` and add:

```python
    pocket_drop: float = 0.4  # pocket floor ahead of the stack's back: it prints as a bridge, which may sag
```

After `stack_back`:

```python
def pocket_floor(p=P):
    return stack_back(p) - p.pocket_drop
```

Replace `peg`:

```python
def peg(x, y, p=P):
    """The pivot for a button: a neck and a head whose top is flush with the
    back, so face up it prints from the bed, head first. The head's underside
    is 50 degrees."""
    zn = stack_back(p) + p.btn_t + 0.2  # 0.2 under the head
    rh, rise = p.peg_r + p.peg_head, p.peg_head * math.tan(math.radians(50))
    neck = cyl(p.peg_r, pocket_floor(p) - 0.01, zn + 0.01, x, y)
    # One loft for the underside and the top, so there is no seam between them
    rings = [cq.Sketch().circle(r).moved(cq.Location(cq.Vector(x, y, z))) for r, z in ((p.peg_r, zn), (rh, zn + rise), (rh, p.depth))]
    return neck.union(cq.Workplane("XY").placeSketch(*rings).loft(ruled=True))
```

In `lock_features` change both `stack_back(p)` to `pocket_floor(p)` (the pocket and the notches).

In `keyhole_cutter`, before the `return`, add a roof over the room and return it too:

```python
    # Face up the floor of the room is a ceiling: a 45 degree gabled roof
    roof = _stadium(c, y0, th, hd, zf + 0.01).workplane(offset=-(hd / 2 - 0.1)).slot2D(th + 0.2, 0.2, 90).loft(ruled=True)
    return entry.union(neck).union(room).union(roof)
```

After `turn()` in the helpers:

```python
def face_up(part, p=P):
    """A part turned over to print front up: z = 0 is then the back."""
    return part.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, p.depth))
```

In the checks section, before `overhang_area`:

```python
def bridge_zones(p=P):
    """Where a part printed face up may have flat undersides, in frame
    coordinates: the lip, which bridges to its support wall, and the pocket
    floors."""
    rw, rh = rabbet(p)
    sw, sh = sight(p)
    lip = box(-rw / 2, rw / 2, -rh / 2, rh / 2, p.skin - 0.1, p.skin + 0.1).cut(box(-sw / 2, sw / 2, -sh / 2, sh / 2, 0, p.depth))
    zf = pocket_floor(p)
    floors = [turn(cyl(pocket_r(p) + 2 * p.notch_r, zf - 0.1, zf + 0.1, c + btn_x(p), yr + p.btn_pivot), deg) for deg, yr, c in locks(p)]
    return [lip] + floors
```

Give `overhang_area` the allowance:

```python
def overhang_area(part, max_deg=48.0, allow=()):
    """Area (mm^2) of downward faces flatter than `max_deg` from vertical,
    ignoring the face on the bed and any inside the `allow` solids, which are
    planned bridges. The margin over 45 degrees absorbs meshing error on the
    45 degree faces."""
    verts, tris = part.val().tessellate(0.02, 0.1)
    zmin = min(v.z for v in verts)
    limit = -math.sin(math.radians(max_deg))
    total = 0.0
    for i, j, k in tris:
        a, b, c = verts[i], verts[j], verts[k]
        n = (b - a).cross(c - a)
        if n.Length < 1e-12:
            continue
        if n.z / n.Length < limit and (a.z + b.z + c.z) / 3 > zmin + 0.05:
            m = (a + b + c) * (1 / 3)
            if any(s.val().isInside(m, 0.01) for s in allow):
                continue
            total += n.Length / 2
    return total
```

In `main`, export the sections and fit tests face up (the assembly STEP stays in frame coordinates):

```python
    parts = {n: face_up(s, p) for n, s in parts.items()} | {n: face_up(t, p) for n, t in fit_test_parts(p, list(parts.values())).items()}
```

replacing the `parts.update(fit_test_parts(...))` line, and keep `parts["button"] = button_print(p)`.

- [ ] **Step 4: Run all tests**

Run: `uv run pytest -q`
Expected: all pass. If `test_no_unsupported_overhangs` fails, find the faces with:

```python
# scratchpad/overhangs.py
import math, frame as fr
part = fr.face_up(fr.make_sections()[1])
allow = [fr.face_up(z) for z in fr.bridge_zones()]
verts, tris = part.val().tessellate(0.02, 0.1)
for i, j, k in tris:
    a, b, c = verts[i], verts[j], verts[k]
    n = (b - a).cross(c - a)
    if n.Length > 1e-12 and n.z / n.Length < -math.sin(math.radians(48)):
        m = (a + b + c) * (1 / 3)
        if m.z > 0.05 and not any(s.val().isInside(m, 0.01) for s in allow):
            print(round(m.x, 1), round(m.y, 1), round(m.z, 2), round(n.Length / 2, 2))
```

run with `PYTHONPATH=. uv run python <scratchpad>/overhangs.py`; expected culprits are the dovetail socket (should be 45 degrees) and the keyhole room's ends.

---

### Task 3: Support wall under the lip

**Files:** Modify `frame/frame.py`, `frame/tests/test_frame.py`

**Interfaces:**
- Consumes: `sides`, `locks`, `seams`, `btn_x`, `pocket_r`, `face_up` (Tasks 1-2).
- Produces: `Params.sup_in, sup_w, sup_gap, tab_w, tab_h, tab_every`; `lip_support(p) -> Workplane` (frame coordinates); `make_sections(p=P, body=None, support=False)`.

- [ ] **Step 1: Write the tests**

Add a fixture and change `parts` to use it:

```python
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
```

Add:

```python
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
```

Update the seam test pieces' expectation: they now start at the rabbet face and carry no lip, so nothing else changes in `test_seam_test_pieces_join`.

- [ ] **Step 2: Run, expect failure**

Run: `uv run pytest -q tests/test_frame.py -k "lip"`
Expected: FAIL with `AttributeError: ... 'lip_support'`.

- [ ] **Step 3: Implement**

In `Params`, after the lattice/pad block:

```python
    # Support for the lip while printing face up: a wall one line thick under
    # it, round the opening, peeled off before use, held by tabs at its foot
    sup_in: float = 0.8  # from the opening's edge, so its scar is hidden
    sup_w: float = 0.5
    sup_gap: float = 0.2  # under the lip, like a slicer support's top gap
    tab_w: float = 2.0
    tab_h: float = 0.4  # two layers
    tab_every: float = 50.0
```

New function after `lock_features`:

```python
def lip_support(p=P):
    """The support wall under the lip, in frame coordinates, with tabs at its
    foot joining it to the rabbet wall. The tabs keep clear of the seams and of
    the button pockets, which cut the rabbet wall away."""
    sw, sh = sight(p)
    a, b = p.sup_in, p.sup_in + p.sup_w
    z0 = p.skin + p.sup_gap
    wall = box(-sw / 2 - b, sw / 2 + b, -sh / 2 - b, sh / 2 + b, z0, p.depth)
    wall = wall.cut(box(-sw / 2 - a, sw / 2 + a, -sh / 2 - a, sh / 2 + a, z0 - 1, p.depth + 1))
    tabs = []
    for side, deg, yr in sides(p):
        along = sw / 2 if side in ("top", "bottom") else sh / 2
        pockets = [(c + btn_x(p) - pocket_r(p), c + btn_x(p) + pocket_r(p)) for d, _, c in locks(p) if d == deg]
        n = int((along - 5) // p.tab_every)
        for k in range(-n, n + 1):
            u = k * p.tab_every
            if side in ("top", "bottom") and any(abs(u - s) < 5 for s in seams(p)):
                continue
            if any(lo - p.tab_w < u < hi + p.tab_w for lo, hi in pockets):
                continue
            y0 = yr - p.clr - p.lip + b - 0.01  # the wall's outer face
            tabs.append(turn(box(u - p.tab_w / 2, u + p.tab_w / 2, y0, yr + 0.01, p.depth - p.tab_h, p.depth), deg))
    return wall.union(combo(*tabs))
```

Change `make_sections`:

```python
def make_sections(p=P, body=None, support=False):
    """The frame cut into sections at the seams, left to right; with support,
    as printed, with the lip's support wall."""
    body = body if body is not None else make_body(p)
    if support:
        body = body.union(lip_support(p))
    ...  # rest unchanged
```

In `fit_test_parts`, start the seam pieces at the rabbet face so they carry no lip:

```python
        rh = rabbet(p)[1]
        crop = box(xs - k, xs + k, rh / 2, h / 2 + 1, -1, p.depth + 1)
```

In `main`, build the printed sections with `make_sections(p, body, support=True)` (the assembly STEP keeps the bare body: build both).

- [ ] **Step 4: Run all tests**

Run: `uv run pytest -q`
Expected: all pass. `test_parts_are_single_valid_solids` proves every wall segment is held by a tab, including the piece in `test_lock`.

---

### Task 4: Firmer click; buttons print on their underside

**Files:** Modify `frame/frame.py`, `frame/tests/test_frame.py`

**Interfaces:**
- Produces: `Params.det_h` (4.0), `Params.btn_lead` (0.3); `button_print(p)` returns the button as fitted, underside on the bed.

- [ ] **Step 1: Write the test**

```python
def test_detent_finger_is_taller_than_the_bar():
    """Force goes with the finger's height, strain does not: 4 mm against the
    3 mm bar is a third firmer. It stays clear of the back."""
    assert P.det_h >= P.btn_t * 4 / 3 - 1e-9
    assert fr.stack_back() + P.det_h <= P.depth - 0.5
    assert size(fr.button_print())[2] == pytest.approx(P.det_h)
```


- [ ] **Step 2: Run, expect failure**

Run: `uv run pytest -q tests/test_frame.py::test_detent_finger_is_taller_than_the_bar`
Expected: FAIL with `AttributeError: 'Params' object has no attribute 'det_h'`.

- [ ] **Step 3: Implement**

In `Params`:

```python
    btn_chamfer: float = 0.5  # tall, under the edges, to ride onto a thick backing
    btn_lead: float = 0.3  # its inset: steeper than 48 degrees, so it prints on the bed
    ...
    det_h: float = 4.0  # finger and nub, above the 3 mm bar: stiffer at the same strain
```

In `_bar` use the lead for the inset:

```python
    ch, ld, length, yc = p.btn_chamfer, p.btn_lead, y1 - y0, (y0 + y1) / 2
    lead = cq.Workplane("XY").center(0, yc).slot2D(length - 2 * ld, 2 * (hw - ld), 90)
```

In `button`, build the finger and nub to `p.det_h`:

```python
        ring = cyl(ro, 0, p.det_h).cut(cyl(ro - p.det_w, -1, p.det_h + 1))
        ring = ring.intersect(box(0, ro + 1, 0, ro + 1, -1, p.det_h + 1))
        nub = cyl(p.nub_r, 0, p.det_h, pocket_r(p) + p.det_press - p.nub_r)
```

Replace `button_print`:

```python
def button_print(p=P):
    """The button as fitted prints on its underside, the finger standing up."""
    return button(p)
```

- [ ] **Step 4: Run all tests**

Run: `uv run pytest -q`
Expected: all pass, including `test_buttons_click_into_closed_and_open` (the notches run the full pocket depth) and `test_no_unsupported_overhangs` for the button.

---

### Task 5: Slicer settings, weights, docs

**Files:** Modify `frame/make_3mf.py`, `README.md`, `frame/docs/superpowers/specs/2026-10-15-frame-design.md`

- [ ] **Step 1: Settings**

Replace `OVERRIDES` and its comment:

```python
# Changes from the standard process. The sides are solid in the model; two
# walls and a light gyroid make them hollow. Five top layers and ironing give
# the front, printed face up, a flat finish. Arachne prints the lip's 0.5 mm
# support wall as one line.
OVERRIDES = {
    "wall_loops": "2",
    "sparse_infill_density": "10%",
    "sparse_infill_pattern": "gyroid",
    "top_shell_layers": "5",
    "top_shell_thickness": "1",
    "bottom_shell_layers": "3",
    "ironing_type": "topmost",
    "wall_generator": "arachne",
    "enable_support": "0",
    # A brim would also run round the inside of the opening
    "brim_type": "no_brim",
    "enable_prime_tower": "0",
}
```

- [ ] **Step 2: Slice and report weights**

Add `cmd += ["--slice", "0"]` before the export arguments, and after `check(target)` in `main` call `report(target)`:

```python
def report(target):
    """Filament per plate, from the slice Studio stored in the project."""
    z = zipfile.ZipFile(target)
    if "Metadata/slice_info.config" not in z.namelist():
        print("not sliced: no weights")
        return
    info = z.read("Metadata/slice_info.config").decode()
    for plate, block in zip(PLATES, re.findall(r"<plate>(.*?)</plate>", info, re.S)):
        weight = re.search(r'key="weight" value="([\d.]+)"', block)
        print(f"{plate}: {weight.group(1) if weight else '?'} g")
```

Run: `uv run frame.py && uv run make_3mf.py`
Expected: three plates and a weight for each. If the weights print `?`, open `Metadata/slice_info.config` from `out/frame.3mf` (`unzip -p out/frame.3mf Metadata/slice_info.config | head -40`) and match the key it uses. Also check `ironing_type` was accepted (`check()` exits listing it otherwise; the valid values are in Studio's process settings).

- [ ] **Step 3: Docs**

- `README.md` frame row: "a plain boxy frame printed face up for a flat front, in two halves joined by sliding dovetails, with turn buttons that hold the backing and keyholes for hanging".
- At the top of `2026-10-15-frame-design.md`, under the date: "Print orientation, lattice and slicer settings superseded by `2026-10-17-frame-face-up-design.md`."
- Update `make_3mf.py`'s module docstring if it mentions the lattice.

- [ ] **Step 4: Full check**

Run: `uv run pytest -q`
Expected: all pass. Report the part sizes from `frame.py` and the plate weights from `make_3mf.py`.

---

### Task 6: Print and tune (with the user)

- [ ] Print the "Fit tests" plate. Check: the lip on `test_lock` is flat, its support wall peels off in one piece and leaves no visible scar; the front finish; the pocket floor did not sag onto the button; the button clicks firmly closed and open and presses on the backing; the seam pieces slide together and hold.
- [ ] Adjust: `sup_gap` (wall fused: 0.25; lip sagged: 0.15), `pocket_drop`, `det_h` or `det_press` (click), `slack` (press on the backing), `joint_clr`.
- [ ] Print the halves.
