# micro-server

Ansible provisioning for a Raspberry Pi 5 running headless 64-bit Raspberry Pi OS Lite.

---

## Setup

```bash
uv run ansible uServer -m ping   # verify connectivity
```

---

## Playbooks

Run everything:
```bash
uv run ansible-playbook site.yml
```

Run a specific playbook by tag:
```bash
uv run ansible-playbook site.yml --tags <tag>
```

| Playbook | Tag | Description |
|---|---|---|
| `system-update.yml` | `system-update` | apt full-upgrade + EEPROM update + reboot |
| `network.yml` | `network` | Static WiFi IP via NetworkManager |
| `base-packages.yml` | `base` | vim, git, curl, htop, network tools |
| `display.yml` | `display` | X11 + Openbox (headless kiosk stack) |
| `mame.yml` | `mame` | MAME emulator |
| `retroarch.yml` | `retroarch` | RetroArch emulator |
| `kiosk.yml` | `kiosk` | ES-DE frontend, auto-login, ROM directories |
| `docker.yml` | `docker` | Docker CE + Compose plugin |
| `homeassistant.yml` | `homeassistant` | Home Assistant + Matter server in Docker |

---

## Backup & Restore

### Backup

Pulls HA config and Matter server data to `backups/YYYY-MM-DD/` on this machine:

```bash
uv run ansible-playbook playbooks/backup.yml
```

Two files are written locally:
- `backups/YYYY-MM-DD/ha-config.tar.gz` — full HA config directory
- `backups/YYYY-MM-DD/matter-server-data.tar.gz` — Matter fabric + node data

> HA's built-in backup also runs automatically inside the container and covers automations, scenes, and integrations. This playbook adds the Matter server volume which HA's backup system can't see.

### Restore

After provisioning a fresh Pi through `homeassistant.yml`, restore from a backup:

```bash
# Latest backup:
uv run ansible-playbook playbooks/restore.yml

# Specific date:
uv run ansible-playbook playbooks/restore.yml -e "backup_date=2026-03-07"
```

The restore playbook stops containers, restores both archives, and restarts everything.

---

## Loading ROMs

The kiosk playbook creates ROM directories under `~/ROMs/` on the Pi. Copy ROMs over with rsync:

```bash
rsync -av ~/path/to/roms/*.nes uServer:/home/brent/ROMs/nes/
rsync -av ~/path/to/roms/*.z64 uServer:/home/brent/ROMs/n64/
rsync -av ~/path/to/roms/*.sfc uServer:/home/brent/ROMs/snes/
```

Note: filenames with `!` in them (common in No-Intro sets) need single quotes in zsh:

```bash
rsync -av ~/path/to/roms/'Game Name [!].z64' uServer:/home/brent/ROMs/n64/
```

ES-DE supports zipped ROMs — no need to unzip first.

---

## ES-DE Build (ARM64)

No official ES-DE ARM64 binary exists. Build from source:

```bash
bash scripts/build-esde.sh
```

Produces `dist/es-de`. Publish to GitHub Releases, then `kiosk.yml` downloads it onto the Pi.

---

## Project Structure

```
micro-server/
├── ansible.cfg
├── site.yml
├── inventory/
│   ├── hosts.yml
│   └── host_vars/uServer.yml
├── playbooks/
│   ├── system-update.yml
│   ├── network.yml
│   ├── base-packages.yml
│   ├── display.yml
│   ├── mame.yml
│   ├── retroarch.yml
│   ├── kiosk.yml
│   ├── docker.yml
│   ├── homeassistant.yml
│   ├── backup.yml
│   └── restore.yml
├── docker/
│   └── Dockerfile.esde
├── scripts/
│   └── build-esde.sh
└── backups/           # local backups (gitignored)
```
