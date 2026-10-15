"""Bundle the exported STLs into one Bambu Studio project (.3mf) with the print
settings and colours already chosen.

Run `uv run make_3mf.py` from this folder after `pill_case.py` has written
out/. It drives Bambu Studio (the flatpak on Linux, the app on macOS) from the
command line, so the project is written by Studio itself, as
out/pill_case.3mf: one plate per group of parts, in three filaments.
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

# Changes from the standard process. Three loops make the 1.6 mm wall and the
# flex arms (1.0 to 2.0 mm) solid perimeter with no infill in them.
OVERRIDES = {
    "wall_loops": "3",
    "sparse_infill_density": "25%",
    "sparse_infill_pattern": "gyroid",
    "bottom_shell_layers": "4",
    "enable_support": "0",
    # A brim would bridge the 0.3 mm gap round the printed-in-place door
    "brim_type": "no_brim",
    # The only colour change is a single swap at a layer boundary, so a
    # full-height prime tower is not worth its filament
    "enable_prime_tower": "0",
}

# Filament slots: dark for the base and dial, translucent for the lid and its
# door, white for the dial's raised letters. Load whatever you like in the AMS
# and map the slots when you send the print.
DARK, CLEAR, WHITE = 1, 2, 3
FILAMENTS = {
    DARK: ("Bambu PLA Basic @BBL P1S 0.4 nozzle", "#545454"),
    CLEAR: ("Bambu PLA Translucent @BBL X1C", "#B9D9EB"),  # lists the P1S as compatible
    WHITE: ("Bambu PLA Basic @BBL P1S 0.4 nozzle", "#FFFFFF"),
}

# Plate name -> objects; an object is a list of (STL name, filament) parts
# that are already in position relative to one another.
PLATES = {
    # Each fit test is in the filament its real part uses, since the fits are
    # what is being tested. Print "Fit tests, lid" first: it has the door.
    "Fit tests, lid": [[(n, CLEAR)] for n in ("test_door", "test_hub_lid")],
    "Fit tests, base and dial": [[(n, DARK)] for n in ("test_hub_base", "test_hub_dial")],
    "Base": [[("base", DARK)]],
    "Lid with door": [[("lid_with_door", CLEAR)]],
    # On its own plate so the swap to white happens once, above everything else
    "Dial": [[("dial.band0", DARK), ("dial.band1", WHITE)]],
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
    process.update({"inherits": PROCESS, "name": "0.20mm Pill Case", "from": "User"})
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
    target = out / "pill_case.3mf"
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
    print(f"{target.name}: {len(plates)} plates {plates}")
    print("filaments:", list(zip(settings.get("filament_settings_id"), settings.get("filament_colour"))))


if __name__ == "__main__":
    main()
