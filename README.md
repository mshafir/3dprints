# 3dprints

Parametric models for 3D printing, written as Python scripts with
[CadQuery](https://cadquery.readthedocs.io/). Each project is one script that
generates every part, a test file that checks the parts fit together, and a
second script that packs the parts into a ready-to-print Bambu Studio project.

Everything is designed for a Bambu Lab P1S with a 0.4 mm nozzle, PLA, 0.2 mm
layers and no supports.

## Projects

| Folder | What it is | Status |
|---|---|---|
| [`pill-case/`](pill-case/) | Round four-week pill case with a click dial and a sliding door | Printed and revised several times |
| [`sink-organizer/`](sink-organizer/) | Bathroom sink organizer: a 1 inch grid baseplate with snap-in modules for toothbrushes, toothpaste, an electric toothbrush charger and bar soap | Snap latches redesigned after the first test prints; the new latches are not yet printed |

## Layout

Every project folder has the same shape:

```
<project>/
  <project>.py        the model: a Params class, builders, one function per part, main() to export
  make_3mf.py         packs the exported STLs into one Bambu Studio project
  tests/              pytest geometry checks
  docs/superpowers/
    specs/            the design: goals, dimensions, and a dated revision note per change
    plans/            the implementation plan the first build followed
  out/                generated STEP, STL and 3MF files (not in git)
```

At the repo root, `pyproject.toml` pins CadQuery and pytest, `uv.lock` records
the exact versions of everything they pull in, and one `.venv` is shared by
all projects.

## Setup

Dependencies are managed with [uv](https://docs.astral.sh/uv/). Install it,
then from the repo root:

```
uv sync
```

This creates `.venv` with Python 3.12 (uv downloads it if needed) and installs
the locked dependencies. `uv run` also does this on first use, so the step is
optional.

`make_3mf.py` also needs Bambu Studio (written against 2.8.2): the flatpak
(`com.bambulab.BambuStudio`) on Linux, or the app in `/Applications` on macOS.
The models and tests do not need Studio.

## Building a project

Run these from inside the project folder, for example `sink-organizer/`:

```
uv run sink_organizer.py     # write STEP and STL files to out/
uv run pytest tests -q       # check the geometry
uv run make_3mf.py           # write out/sink_organizer.3mf
```

Open the `.3mf` in Bambu Studio to print. It has one plate per group of parts,
with the printer, filament, process settings and colours already set. The small
fit-test plates come first.

`out/` is not checked in, so a fresh clone has no print files until the
scripts are run.

## How a design gets made

1. **Spec.** Agree what the object has to do and write it down in
   `docs/superpowers/specs/`, with dimensions and a list of what is assumed
   but not measured.
2. **Plan.** Break the build into tasks in `docs/superpowers/plans/`.
3. **Model.** Write the CadQuery script. Every dimension and clearance is a
   named field on `Params`, so tuning a fit means changing one number. Parts
   are modelled in the position they are printed in.
4. **Check.** The tests build the parts and test them against one another:
   each part is a single valid solid, mating parts do not intersect, clearances
   are in range, nothing overhangs past 45 degrees, and everything fits the
   bed.
5. **Test print.** Each project exports small fit-test pieces (a single
   socket, a short section of a snap joint) that use a few grams of plastic.
   Print these before the full parts.
6. **Revise.** Change the parameters or the geometry based on how the print
   felt, add a dated revision note to the top of the spec, and go back to
   step 4.

The geometry checks catch parts that collide or cannot be printed. They do not
tell you how a snap feels in the hand; only the test print does. The spec
revision notes record what each print showed and what changed because of it.

The plans describe the first build only. Where a plan and a spec disagree, the
newest revision note in the spec is correct.

## Working with Claude Code

These models were designed and written in conversation with
[Claude Code](https://claude.com/claude-code), following the spec, plan and
build steps above. The `docs/superpowers/` folders are the written record of
that process.

## License

[MIT](LICENSE)
