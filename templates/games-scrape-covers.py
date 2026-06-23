#!/usr/bin/env python3
# games-scrape-covers.py — fetch box-art covers for the curated games.
#
# Source: libretro-thumbnails (public HTTP, no credentials). Covers are saved
# into ES-DE's media tree so the kiosk shows box art:
#   ~/ES-DE/downloaded_media/<system>/covers/<rombasename>.png
#
#  - NES:    libretro filename == No-Intro ROM name.
#  - Arcade: libretro filename == MAME full description (from `mame -listfull`).
# Tries fallback variants (libretro char-munge + trimming trailing "(...)").
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

# NES — match by ROM filename
nes = keep("games-nes-keep.txt")
hit = sum(fetch("Nintendo - Nintendo Entertainment System",
                os.path.splitext(fn)[0],
                f"{MEDIA}/nes/covers/{os.path.splitext(fn)[0]}.png") for fn in nes)
print(f"NES covers: {hit}/{len(nes)}")

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
