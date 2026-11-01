"""Bundle the exported STLs into one Bambu Studio project (.3mf) with the print
settings and colours already chosen.

Run `uv run make_3mf.py` from this folder after `craft_drawers.py` has written
out/. It drives Bambu Studio (the flatpak on Linux, the app on macOS) from the
command line, so the project is written by Studio itself, as
out/craft_drawers.3mf: the fit test first, then the frame, one plate per
drawer in its own colour, the lock parts and the dividers. Slice each plate
in Studio before sending it.
"""

import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

APP = "com.bambulab.BambuStudio"
MAC_APP = Path("/Applications/BambuStudio.app/Contents/MacOS/BambuStudio")
if sys.platform == "darwin":
    PRESETS = Path.home() / "Library/Application Support/BambuStudio/system/BBL"
else:
    PRESETS = Path.home() / ".var/app" / APP / "config/BambuStudio/system/BBL"

MACHINE = "Bambu Lab P1S 0.4 nozzle"
PROCESS = "0.20mm Standard @BBL X1C"  # the P1S uses the X1C process presets

# Changes from the standard process. The walls are mostly 1.2 to 2 mm, so two
# loops make them solid; the light gyroid only fills the thicker spots.
# Arachne keeps the drawers' 1.2 mm walls and the springy leaves to whole
# lines.
OVERRIDES = {
    "wall_loops": "2",
    "sparse_infill_density": "10%",
    "sparse_infill_pattern": "gyroid",
    "wall_generator": "arachne",
    "enable_support": "0",
    "brim_type": "no_brim",
    "enable_prime_tower": "0",
}

# Filament slots: one colour per plate, so no colour changes within a print.
# Load whatever you like and map the slots when you send each plate.
PLA = "Bambu PLA Basic @BBL P1S 0.4 nozzle"
WHITE, RED, YELLOW, BLUE, GREEN = 1, 2, 3, 4, 5
FILAMENTS = {
    WHITE: (PLA, "#FFFFFF"),
    RED: (PLA, "#E53935"),
    YELLOW: (PLA, "#FDD835"),
    BLUE: (PLA, "#1E88E5"),
    GREEN: (PLA, "#43A047"),
}

# Plate name -> (STL name, filament, copies). Print the fit test first: it
# checks the keyhole, the key and the click before the 10 hour frame.
PLATES = {
    "Fit test": [("test_corner", WHITE, 1), ("test_rod", WHITE, 1), ("badge", WHITE, 1), ("key", WHITE, 1)],
    "Frame": [("frame", WHITE, 1)],
    "Drawer 1": [("drawer_0", RED, 1)],
    "Drawer 2": [("drawer_1", YELLOW, 1)],
    "Drawer 3": [("drawer_2", BLUE, 1)],
    "Drawer 4": [("drawer_3", GREEN, 1)],
    "Lock": [("rod", WHITE, 1), ("badge", WHITE, 1), ("key", WHITE, 2)],
    "Dividers": [("divider", WHITE, 4)],
}

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
    process.update({"inherits": PROCESS, "name": "0.20mm Craft Drawers", "from": "User"})
    paths = {"machine": folder / "machine.json", "process": folder / "process.json", "filaments": []}
    paths["machine"].write_text(json.dumps(preset("machine", MACHINE), indent=1))
    paths["process"].write_text(json.dumps(process, indent=1))
    for slot, (name, colour) in sorted(FILAMENTS.items()):
        cfg = preset("filament", name)
        cfg["default_filament_colour"] = [colour]
        path = folder / f"filament_{slot}.json"
        path.write_text(json.dumps(cfg, indent=1))
        paths["filaments"].append(path)
    return paths


def assemble_list(out):
    """Tell Studio which parts go on which plate, in which filament."""
    plates = []
    for name, parts in PLATES.items():
        objects = [{"path": str(out / f"{stl}.stl"), "count": n, "filaments": [f]} for stl, f, n in parts]
        plates.append({"plate_name": name, "need_arrange": True, "objects": objects})
    return {"plates": plates}


def main(out=Path(__file__).parent / "out"):
    target = out / "craft_drawers.3mf"
    with tempfile.TemporaryDirectory(dir=out) as tmp:
        tmp = Path(tmp)
        presets = write_presets(tmp)
        (tmp / "assemble.json").write_text(json.dumps(assemble_list(out), indent=1))
        if sys.platform == "darwin":
            cmd = [str(MAC_APP)]
        else:
            cmd = ["flatpak", "run", f"--filesystem={out}", "--command=bambu-studio", APP]
        cmd += ["--load-settings", f"{presets['machine']};{presets['process']}"]
        cmd += ["--load-filaments", ";".join(str(f) for f in presets["filaments"])]
        cmd += ["--load-assemble-list", str(tmp / "assemble.json")]
        # No --slice: with five filaments the command line crashes slicing
        # (group_nozzle_info errors). Studio slices each plate on opening.
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
    set_colours(target)
    check(target)


def set_colours(target):
    """Finish the multi-filament settings the command line leaves incomplete:
    the display colours and the tables that must have one entry per filament."""
    with zipfile.ZipFile(target) as z:
        files = {i: z.read(i.filename) for i in z.infolist()}
    name = "Metadata/project_settings.config"
    for info, data in files.items():
        if info.filename == name:
            settings = json.loads(data)
            n = len(FILAMENTS)
            settings["filament_colour"] = [FILAMENTS[k][1] for k in sorted(FILAMENTS)]
            # Per-filament tables the command line leaves sized for one filament
            for key in ("filament_map", "filament_map_2", "filament_nozzle_map", "filament_volume_map"):
                if key in settings:
                    settings[key] = settings[key][:1] * n
            purge = settings["flush_volumes_matrix"][1]
            settings["flush_volumes_matrix"] = ["0" if i == j else purge for i in range(n) for j in range(n)]
            settings["flush_volumes_vector"] = settings["flush_volumes_vector"][:1] * (2 * n)
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
    print("filaments:", list(zip(settings.get("filament_settings_id"), settings.get("filament_colour"))))


if __name__ == "__main__":
    main()
