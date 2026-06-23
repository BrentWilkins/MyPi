#!/usr/bin/env python3
# games-scrape-covers.py — fetch box-art covers for the curated games.
#
# Source: libretro-thumbnails (public HTTP, no credentials). Covers are saved
# into ES-DE's media tree so the kiosk shows box art:
#   ~/ES-DE/downloaded_media/<system>/covers/<rombasename>.png
#
#  - NES/SNES: libretro filename == No-Intro ROM name.
#  - Arcade:   libretro filename == MAME full description (from `mame -listfull`).
# Tries fallback variants (libretro char-munge + trimming trailing "(...)").
# A few covers libretro simply doesn't carry are fetched from a direct URL
# override instead (see *_OVERRIDE maps below).
# Deployed + invoked by playbooks/games.yml. Re-runnable (idempotent overwrite).
import os, re, subprocess, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser("~")
MEDIA = os.path.join(HOME, "ES-DE", "downloaded_media")
B = "https://thumbnails.libretro.com"
UA = {"User-Agent": "Mozilla/5.0 cover-scraper"}

# A few arcade games have their libretro box art filed under a parent-set name
# that doesn't match MAME's exact description, so the auto-fallback can't reach
# it. Map MAME short name -> libretro title for those.
ARCADE_OVERRIDE = {
    "ddragon": "Double Dragon (World)",
    "tmnt": "Teenage Mutant Ninja Turtles (World 4 Players)",
}

# Covers libretro-thumbnails doesn't carry under any name variant. Keyed by ROM
# basename (no extension) -> direct image URL. Saved with the URL's extension.
NES_OVERRIDE = {
    "Ice Climber (USA, Europe, Asia) (En)":
        "https://upload.wikimedia.org/wikipedia/en/d/df/IceClimberboxartnes.jpg",
}

def keep(name):
    return [l.strip() for l in open(os.path.join(HERE, name)) if l.strip()]

def munge(t):
    return re.sub(r'[&*/:`<>?\\|]', '_', t)

def candidates(title):
    seen, out, base = set(), [], title
    while True:
        for v in (munge(base), base):
            if v not in seen:
                seen.add(v); out.append(v)
        m = re.match(r'^(.*) \([^()]*\)\s*$', base)
        if not m:
            return out
        base = m.group(1)

def fetch(sysname, title, dest):
    for cand in candidates(title):
        url = f"{B}/{urllib.parse.quote(sysname)}/Named_Boxarts/{urllib.parse.quote(cand)}.png"
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read()
            if len(data) < 100:
                continue
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            open(dest, "wb").write(data)
            return True
        except Exception:
            continue
    return False

def fetch_url(url, dest):
    try:
        data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read()
        if len(data) < 100:
            return False
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "wb").write(data)
        return True
    except Exception:
        return False

# Console systems whose libretro filename == the (No-Intro) ROM filename.
def scrape_by_filename(sysname, system, keeplist, override=None):
    names, override, hit = keep(keeplist), override or {}, 0
    for fn in names:
        base = os.path.splitext(fn)[0]
        if base in override:
            url = override[base]
            ext = os.path.splitext(url)[1] or ".png"
            ok = fetch_url(url, f"{MEDIA}/{system}/covers/{base}{ext}")
        else:
            ok = fetch(sysname, base, f"{MEDIA}/{system}/covers/{base}.png")
        hit += ok
        if not ok:
            print(f"  miss: {base}")
    print(f"{system.upper()} covers: {hit}/{len(names)}")

def mame_desc(short):
    try:
        out = subprocess.run(["/usr/games/mame", "-listfull", short],
                             capture_output=True, text=True, timeout=30).stdout
        for line in out.splitlines():
            m = re.match(r'^\s*' + re.escape(short) + r'\s+"(.+)"\s*$', line)
            if m:
                return m.group(1)
    except Exception:
        pass
    return None

# NES / SNES — match by ROM filename
scrape_by_filename("Nintendo - Nintendo Entertainment System",
                   "nes", "games-nes-keep.txt", NES_OVERRIDE)
scrape_by_filename("Nintendo - Super Nintendo Entertainment System",
                   "snes", "games-snes-keep.txt")

# Arcade — match by MAME description
arc = keep("games-arcade-keep.txt")
hit = 0
for short in arc:
    title = ARCADE_OVERRIDE.get(short) or mame_desc(short)
    if title and fetch("MAME", title, f"{MEDIA}/arcade/covers/{short}.png"):
        hit += 1
    else:
        print(f"  miss: {short} ({title})")
print(f"Arcade covers: {hit}/{len(arc)}")
