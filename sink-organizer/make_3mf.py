"""Bundle the exported STLs into one Bambu Studio project (.3mf) with the print
settings and colours already chosen.

Run `../.venv/bin/python make_3mf.py` from this folder after
`sink_organizer.py` has written out/. It drives the Bambu Studio flatpak from
the command line, so the project is written by Studio itself, as
out/sink_organizer.3mf: one plate per group of parts, in two filaments.
"""

import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

APP = "com.bambulab.BambuStudio"
PRESETS = Path.home() / ".var/app" / APP / "config/BambuStudio/system/BBL"

MACHINE = "Bambu Lab P1S 0.4 nozzle"
FILAMENT = "Bambu PLA Basic @BBL P1S 0.4 nozzle"
PROCESS = "0.20mm Standard @BBL X1C"  # the P1S uses the X1C process presets

# Changes from the standard process. The walls are 2.0 to 2.8 mm thick, so
# three loops make them solid; the extra top layers close the floors that
# hold water.
OVERRIDES = {
    "wall_loops": "3",
    "sparse_infill_density": "15%",
    "sparse_infill_pattern": "gyroid",
    "top_shell_layers": "5",
    "bottom_shell_layers": "4",
    "enable_support": "0",
    # Each colour change is a single swap at a layer boundary, so a full-height
    # prime tower is not worth its filament
    "enable_prime_tower": "0",
}

# Filament slots: grey for the baseplate, the trays and the lips, white for
# the ribbed sections. Load whatever you like in the AMS and map the slots
# when you send the print.
GREY, WHITE = 1, 2
COLOURS = {GREY: "#8E9089", WHITE: "#FFFFFF"}


def top(name):
    """A cup top: white ribs under a grey lip, as two parts of one object."""
    return [(f"{name}.band0", WHITE), (f"{name}.band1", GREY)]


# Plate name -> objects; an object is a list of (STL name, filament) parts
# that are already in position relative to one another.
PLATES = {
    # The cheapest check of the click into the baseplate; print this first
    "Latch test 1x1": [[(n, GREY)] for n in ("test_plate_1x1", "test_module_1x1")],
    "Fit tests": [[(n, GREY)] for n in ("test_plate_2x2", "test_cup_tray_2x2", "test_cup_top_2x2", "test_charger_ring")],
    "Baseplate": [[("baseplate", GREY)]],
    "Trays and grate": [[(n, GREY)] for n in ("brush_cup_tray", "paste_cup_tray", "electric_tray", "soap_tray", "soap_grate")],
    # One top per plate: their lips are at different heights, so sharing a
    # plate would swap filament twice a layer while one lip prints.
    "Brush cup top": [top("brush_cup_top")],
    "Toothpaste cup top": [top("paste_cup_top")],
    "Electric collar": [top("electric_collar")],
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
    process.update({"inherits": PROCESS, "name": "0.20mm Sink Organizer", "from": "User"})
    paths = {"machine": folder / "machine.json", "process": folder / "process.json", "filaments": []}
    paths["machine"].write_text(json.dumps(preset("machine", MACHINE), indent=1))
    paths["process"].write_text(json.dumps(process, indent=1))
    for slot, colour in COLOURS.items():
        cfg = preset("filament", FILAMENT)
        cfg["default_filament_colour"] = [colour]
        path = folder / f"filament_{slot}.json"
        path.write_text(json.dumps(cfg, indent=1))
        paths["filaments"].append(path)
    return paths


def assemble_list(out):
    """Tell Studio which parts go on which plate, in which filament. Parts
    sharing an assemble_index are merged into one object."""
    plates = []
    index = 0
    for name, objects in PLATES.items():
        entries = []
        for parts in objects:
            index += 1
            for stl, filament in parts:
                entry = {"path": str(out / f"{stl}.stl"), "count": 1, "filaments": [filament]}
                if len(parts) > 1:
                    entry["assemble_index"] = [index]
                entries.append(entry)
        plates.append({"plate_name": name, "need_arrange": True, "objects": entries})
    return {"plates": plates}


def main(out=Path(__file__).parent / "out"):
    target = out / "sink_organizer.3mf"
    with tempfile.TemporaryDirectory(dir=out) as tmp:
        tmp = Path(tmp)
        presets = write_presets(tmp)
        (tmp / "assemble.json").write_text(json.dumps(assemble_list(out), indent=1))
        cmd = ["flatpak", "run", f"--filesystem={out}", "--command=bambu-studio", APP]
        cmd += ["--load-settings", f"{presets['machine']};{presets['process']}"]
        cmd += ["--load-filaments", ";".join(str(f) for f in presets["filaments"])]
        cmd += ["--load-assemble-list", str(tmp / "assemble.json")]
        cmd += ["--orient", "0", "--export-3mf", str(target)]
        run = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True)
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
            n = len(COLOURS)
            settings["filament_colour"] = [COLOURS[k] for k in sorted(COLOURS)]
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
    print(f"{target.name}: {len(plates)} plates {plates}")
    print("filament colours:", settings.get("filament_colour"))


if __name__ == "__main__":
    main()
