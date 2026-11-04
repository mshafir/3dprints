"""Bundle the exported STLs into one Bambu Studio project (.3mf) with the print
settings and colours already chosen.

Run `uv run make_3mf.py` from this folder after `sink_organizer.py`,
`sink_cup.py`, `sink_cup4.py` and `jar_holder.py` have written out/. It drives Bambu Studio from the command line,
so the projects are written by Studio itself: out/sink_organizer.3mf for the
grid organizer, out/sink_cup.3mf for the single wide cup,
out/sink_cup4.3mf for its four-toothbrush version and
out/jar_holder.3mf for the mason jar holder. Each has one
plate per group of parts, all in one filament, and a last plate that shows
them all assembled.
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
FILAMENT = "Bambu PLA Basic @BBL P1S 0.4 nozzle"
PROCESS = "0.20mm Standard @BBL X1C"  # the P1S uses the X1C process presets

# Changes from the standard process. The walls are 2.0 to 3.5 mm thick, so
# three loops make them nearly solid; the extra top layers close the floors that
# hold water.
OVERRIDES = {
    "wall_loops": "3",
    "sparse_infill_density": "15%",
    "sparse_infill_pattern": "gyroid",
    "top_shell_layers": "5",
    "bottom_shell_layers": "4",
    "enable_support": "0",
    "enable_prime_tower": "0",
}

# One filament for everything; the colour is only what Studio shows. Load
# whatever you like and map the slot when you send the print.
GREY = 1
COLOURS = {GREY: "#8E9089"}


# Plate name -> objects; an object is a list of (STL name, filament) parts
# that are already in position relative to one another.
PLATES = {
    # The cheapest check of the click into the baseplate; print this first
    "Latch test 1x1": [[(n, GREY)] for n in ("test_plate_1x1", "test_module_1x1")],
    "Fit tests": [[(n, GREY)] for n in ("test_plate_2x2", "test_cup_tray_2x2", "test_cup_top_2x2")],
    "Baseplate": [[("baseplate", GREY)]],
    "Trays": [[(n, GREY)] for n in ("electric_cup_tray", "brush_cup_tray")],
    "Cup tops": [[(n, GREY)] for n in ("electric_cup_top", "brush_cup_top")],
}

# The single wide cup (sink_cup.py): it has places for five separators; four
# are printed, on a plate of their own
CUP_PLATES = {
    "Tray": [[("cup_tray", GREY)]],
    "Sleeve": [[("cup_sleeve", GREY)]],
    "Separators": [[("cup_separator", GREY)]] * 4,
}

# Last, the whole thing put together, to look at. It is one
# object made of every real part in its assembled position. It stays printable,
# because Studio draws objects that are not as colourless ghosts, so skip this
# plate when slicing.
ASSEMBLED = "Assembled (not for printing)"
PLATES[ASSEMBLED] = [
    [
        (f"assembled.{stl}", filament)
        for objects in list(PLATES.values())
        for parts in objects
        for stl, filament in parts
        if not stl.startswith("test_")
    ]
]
CUP_PLATES[ASSEMBLED] = [
    [(f"assembled.{stl}", GREY) for stl in ("cup_tray", "cup_sleeve")]
    + [(f"assembled.cup_separator_{i}", GREY) for i in range(1, 6)]
]

# The single cup for four electric toothbrushes (sink_cup4.py): three
# separators, all printed
CUP4_PLATES = {
    "Tray": [[("cup4_tray", GREY)]],
    "Sleeve": [[("cup4_sleeve", GREY)]],
    "Separators": [[("cup4_separator", GREY)]] * 3,
    ASSEMBLED: [
        [(f"assembled.{stl}", GREY) for stl in ("cup4_tray", "cup4_sleeve")]
        + [(f"assembled.cup4_separator_{i}", GREY) for i in range(1, 4)]
    ],
}

# The mason jar holder (jar_holder.py): the test ring first, to check the
# jar's size before the holder
JAR_PLATES = {
    "Test ring": [[("jar_test_ring", GREY)]],
    "Holder": [[("jar_holder", GREY)]],
    ASSEMBLED: [[(f"assembled.{stl}", GREY) for stl in ("jar_holder", "jar_1", "jar_2")]],
}

PROJECTS = {"sink_organizer.3mf": PLATES, "sink_cup.3mf": CUP_PLATES, "sink_cup4.3mf": CUP4_PLATES, "jar_holder.3mf": JAR_PLATES}

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


def assemble_list(out, plates_by_name):
    """Tell Studio which parts go on which plate, in which filament. Parts
    sharing an assemble_index are merged into one object."""
    plates = []
    index = 0
    for name, objects in plates_by_name.items():
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
    for name, plates in PROJECTS.items():
        build(out / name, plates)


def build(target, plates):
    out = target.parent
    with tempfile.TemporaryDirectory(dir=out) as tmp:
        tmp = Path(tmp)
        presets = write_presets(tmp)
        (tmp / "assemble.json").write_text(json.dumps(assemble_list(out, plates), indent=1))
        if sys.platform == "darwin":
            cmd = [str(MAC_APP)]
        else:
            cmd = ["flatpak", "run", f"--filesystem={out}", "--command=bambu-studio", APP]
        cmd += ["--load-settings", f"{presets['machine']};{presets['process']}"]
        cmd += ["--load-filaments", ";".join(str(f) for f in presets["filaments"])]
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
    set_colours(target)
    check(target, plates)


def set_colours(target):
    """Set the display colour, which the command line leaves at the preset's."""
    with zipfile.ZipFile(target) as z:
        files = {i: z.read(i.filename) for i in z.infolist()}
    for info, data in files.items():
        if info.filename == "Metadata/project_settings.config":
            settings = json.loads(data)
            settings["filament_colour"] = [COLOURS[k] for k in sorted(COLOURS)]
            files[info] = json.dumps(settings, indent=4).encode()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for info, data in files.items():
            z.writestr(info.filename, data)


def check(target, plates_by_name):
    z = zipfile.ZipFile(target)
    settings = json.loads(z.read("Metadata/project_settings.config"))
    wrong = {k: settings.get(k) for k, v in OVERRIDES.items() if settings.get(k) != v}
    if wrong:
        sys.exit(f"settings not applied: {wrong}")
    model = z.read("Metadata/model_settings.config").decode()
    plates = re.findall(r'<metadata key="plater_name" value="([^"]*)"', model)
    if plates != list(plates_by_name):
        sys.exit(f"plates are {plates}, not {list(plates_by_name)}")
    print(f"{target.name}: {len(plates)} plates {plates}")
    print("filament colours:", settings.get("filament_colour"))


if __name__ == "__main__":
    main()
