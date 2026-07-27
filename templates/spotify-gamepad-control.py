#!/usr/bin/env python3
# Maps DragonRise stick buttons to Spotify (spotifyd/MPRIS) transport controls via
# playerctl, but only while ES-DE is the foreground app — never while RetroArch is
# running, so gameplay buttons are never hijacked.
#
# Hold Select (BTN_BASE3) + one of the top-row buttons:
#   Select + Y (BTN_TRIGGER) -> play/pause
#   Select + X (BTN_THUMB)   -> previous track
#   Select + L (BTN_THUMB2)  -> next track
#   Select + B (BTN_TOP)     -> volume down
#   Select + A (BTN_TOP2)    -> volume up

import selectors
import subprocess
import time

import evdev
from evdev import ecodes

VENDOR = 0x0079
PRODUCT = 0x0006

SELECT_CODE = ecodes.BTN_BASE3

ACTIONS = {
    ecodes.BTN_TRIGGER: ["playerctl", "play-pause"],
    ecodes.BTN_THUMB: ["playerctl", "previous"],
    ecodes.BTN_THUMB2: ["playerctl", "next"],
    ecodes.BTN_TOP: ["playerctl", "volume", "0.05-"],
    ecodes.BTN_TOP2: ["playerctl", "volume", "0.05+"],
}

DEBOUNCE_SECONDS = 0.25


def find_devices():
    devices = []
    for path in evdev.list_devices():
        dev = evdev.InputDevice(path)
        if dev.info.vendor == VENDOR and dev.info.product == PRODUCT:
            devices.append(dev)
    return devices


def retroarch_running():
    return subprocess.run(
        ["pgrep", "-x", "retroarch"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def main():
    sel = selectors.DefaultSelector()
    devices = {}

    def rescan():
        for dev in find_devices():
            if dev.path not in devices:
                devices[dev.path] = dev
                sel.register(dev, selectors.EVENT_READ)

    rescan()
    select_held = False
    last_fired = {}
    last_rescan = time.monotonic()

    while True:
        events = sel.select(timeout=2)
        now = time.monotonic()
        if now - last_rescan > 2:
            rescan()
            last_rescan = now

        for key, _ in events:
            dev = key.fileobj
            try:
                for event in dev.read():
                    if event.type != ecodes.EV_KEY:
                        continue
                    if event.code == SELECT_CODE:
                        select_held = event.value != 0
                        continue
                    if event.value != 1 or not select_held:
                        continue
                    action = ACTIONS.get(event.code)
                    if action is None or retroarch_running():
                        continue
                    if now - last_fired.get(event.code, 0) < DEBOUNCE_SECONDS:
                        continue
                    last_fired[event.code] = now
                    subprocess.run(action, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except OSError:
                sel.unregister(dev)
                del devices[dev.path]


if __name__ == "__main__":
    main()
