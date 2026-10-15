"""Bundle the exported STLs into one Bambu Studio project (.3mf) with the print
settings already chosen.

Run `uv run make_3mf.py` from this folder after `frame.py` has written out/.
It drives Bambu Studio (the flatpak on Linux, the app on macOS) from the
command line, so the project is written by Studio itself, as out/frame.3mf:
the fit tests on the first plate, then one plate per section, in one
filament.
"""

import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import frame

APP = "com.bambulab.BambuStudio"
MAC_APP = Path("/Applications/BambuStudio.app/Contents/MacOS/BambuStudio")
if sys.platform == "darwin":
    PRESETS = Path.home() / "Library/Application Support/BambuStudio/system/BBL"
else:
    PRESETS = Path.home() / ".var/app" / APP / "config/BambuStudio/system/BBL"

MACHINE = "Bambu Lab P1S 0.4 nozzle"
FILAMENT = "Bambu PLA Basic @BBL P1S 0.4 nozzle"
COLOUR = "#2E2E2E"
PROCESS = "0.20mm Standard @BBL X1C"  # the P1S uses the X1C process presets

# Changes from the standard process. Two loops either side fill the 1.6 mm
# lattice bars solid; three make the rabbet wall, rim and tab leaves solid
# perimeter.
OVERRIDES = {
    "wall_loops": "3",
    "sparse_infill_density": "15%",
    "sparse_infill_pattern": "gyroid",
    "enable_support": "0",
    # A brim would also run round the inside of the opening and the lattice
    "brim_type": "no_brim",
    "enable_prime_tower": "0",
}

TITLES = {"frame": "Frame", "frame_left": "Left half", "frame_right": "Right half"}

# Plate name -> STL names. The fit tests come first: the seam pair checks the
# dovetail, the tab piece checks the click on the backing and a nail in the
# keyhole.
PLATES = {"Fit tests": [n for n in ("test_seam_left", "test_seam_right", "test_tab") if frame.sections() > 1 or n == "test_tab"]}
PLATES.update({TITLES.get(n, n.replace("_", " ").capitalize()): [n] for n in frame.section_names()})

NOT_SETTINGS = ("name", "type", "instantiation", "inherits", "include")


def preset(kind, name):
    """A system preset with its parents and includes merged in. The command
    line wants complete presets, not ones that inherit."""
    cfg = json.loads((PRESETS / kind / f"{name}.json").read_text())
    merged = preset(kind, cfg["inherits"]) if cfg.get("inherits") else {}
    for inc in cfg.get("include", []):
        merged.update({k: v for k, v in preset(kind, inc).items() if k not in NOT_SETTINGS})
    merged.update(cfg)
    merged.pop("include", None)
    return merged


def write_presets(folder):
    process = preset("process", PROCESS)
    process.update(OVERRIDES)
    process.update({"inherits": PROCESS, "name": "0.20mm Frame", "from": "User"})
    paths = {"machine": folder / "machine.json", "process": folder / "process.json", "filament": folder / "filament.json"}
    paths["machine"].write_text(json.dumps(preset("machine", MACHINE), indent=1))
    paths["process"].write_text(json.dumps(process, indent=1))
    cfg = preset("filament", FILAMENT)
    cfg["default_filament_colour"] = [COLOUR]
    paths["filament"].write_text(json.dumps(cfg, indent=1))
    return paths


def assemble_list(out):
    """Tell Studio which parts go on which plate."""
    plates = []
    for name, stls in PLATES.items():
        objects = [{"path": str(out / f"{stl}.stl"), "count": 1, "filaments": [1]} for stl in stls]
        plates.append({"plate_name": name, "need_arrange": True, "objects": objects})
    return {"plates": plates}


def main(out=Path(__file__).parent / "out"):
    target = out / "frame.3mf"
    with tempfile.TemporaryDirectory(dir=out) as tmp:
        tmp = Path(tmp)
        presets = write_presets(tmp)
        (tmp / "assemble.json").write_text(json.dumps(assemble_list(out), indent=1))
        if sys.platform == "darwin":
            cmd = [str(MAC_APP)]
        else:
            cmd = ["flatpak", "run", f"--filesystem={out}", "--command=bambu-studio", APP]
        cmd += ["--load-settings", f"{presets['machine']};{presets['process']}"]
        cmd += ["--load-filaments", str(presets["filament"])]
        cmd += ["--load-assemble-list", str(tmp / "assemble.json")]
        cmd += ["--orient", "0"]
        if sys.platform == "darwin":
            # The Mac build does not write result.json to the working folder
            # unless told to, and then exports relative to that folder
            cmd += ["--outputdir", str(tmp), "--export-3mf", target.name]
        else:
            cmd += ["--export-3mf", str(target)]
        run = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True)
        if (tmp / target.name).exists():
            (tmp / target.name).replace(target)
        result = json.loads((tmp / "result.json").read_text()) if (tmp / "result.json").exists() else {"return_code": -1, "error_string": "no result"}
        if result["return_code"] != 0:
            sys.exit(f"{result['error_string']}\n{(run.stdout + run.stderr)[-3000:]}")
    set_colour(target)
    check(target)


def set_colour(target):
    """The command line leaves the display colour at the preset default."""
    with zipfile.ZipFile(target) as z:
        files = {i: z.read(i.filename) for i in z.infolist()}
    for info, data in files.items():
        if info.filename == "Metadata/project_settings.config":
            settings = json.loads(data)
            settings["filament_colour"] = [COLOUR]
            files[info] = json.dumps(settings, indent=4).encode()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for info, data in files.items():
            z.writestr(info.filename, data)


def check(target):
    z = zipfile.ZipFile(target)
    settings = json.loads(z.read("Metadata/project_settings.config"))
    wrong = {k: settings.get(k) for k, v in OVERRIDES.items() if settings.get(k) != v}
    if wrong:
        sys.exit(f"settings not applied: {wrong}")
    model = z.read("Metadata/model_settings.config").decode()
    plates = re.findall(r'<metadata key="plater_name" value="([^"]*)"', model)
    if plates != list(PLATES):
        sys.exit(f"plates are {plates}, not {list(PLATES)}")
    print(f"{target.name}: {len(plates)} plates {plates}")
    print("filament:", settings.get("filament_settings_id"), settings.get("filament_colour"))


if __name__ == "__main__":
    main()
