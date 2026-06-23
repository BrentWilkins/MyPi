#!/usr/bin/env python3
# games-curate.py — reduce the ROM sets to the curated keep-lists.
#
# Moves every ROM NOT on the keep-list into ~/ROMs/_archive/<system>/ so the
# kiosk only shows a manageable set. Fully reversible: nothing is deleted, and a
# timestamped inventory of everything present is written first. Run AFTER ROMs
# have been restored to ~/ROMs (deployed + invoked by playbooks/games.yml).
#
# Keep-lists live next to this script:
#   games-nes-keep.txt     full No-Intro filenames (with .zip)
#   games-arcade-keep.txt  MAME short names (one per line, no extension)
import os, shutil, datetime, sys

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser("~")
ROMS = os.path.join(HOME, "ROMs")

def load(name):
    p = os.path.join(HERE, name)
    return {l.strip() for l in open(p) if l.strip()}

def snapshot():
    stamp = datetime.date.today().strftime("%Y%m%d")
    out = os.path.join(ROMS, f"_inventory_{stamp}.txt")
    with open(out, "w") as f:
        for d in ("arcade", "nes", "snes", "gba", "n64"):
            sd = os.path.join(ROMS, d)
            if os.path.isdir(sd):
                for n in sorted(os.listdir(sd)):
                    if os.path.isfile(os.path.join(sd, n)):
                        f.write(f"{sd}/{n}\n")
    print(f"inventory snapshot -> {out}")

def curate(system, keep):
    src = os.path.join(ROMS, system)
    if not os.path.isdir(src):
        print(f"[{system}] no ROM dir, skipping")
        return
    arch = os.path.join(ROMS, "_archive", system)
    os.makedirs(arch, exist_ok=True)
    files = [n for n in os.listdir(src) if os.path.isfile(os.path.join(src, n))]
    missing = keep - set(files)
    if missing:
        print(f"[{system}] WARNING keep entries not present: {sorted(missing)}")
    moved = 0
    for n in files:
        if n not in keep:
            shutil.move(os.path.join(src, n), os.path.join(arch, n))
            moved += 1
    print(f"[{system}] kept={len(files) - moved} archived={moved}")

snapshot()
curate("nes", load("games-nes-keep.txt"))
curate("snes", load("games-snes-keep.txt"))
curate("arcade", {s + ".zip" for s in load("games-arcade-keep.txt")})
