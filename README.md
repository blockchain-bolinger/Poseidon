# 🌊 Poseidon

**Poseidon** is a professional ADB-based Android toolkit for diagnostics, automation, monitoring, and OCR-driven UI workflows.

It combines:
- interactive terminal workflows
- headless CLI automation
- device monitoring with CSV / JSONL export
- OCR-assisted UI text detection
- structured operator-focused workflows
- Raspberry Pi / Linux friendly deployment

> ⚠️ Use Poseidon only on devices you own or are explicitly authorized to assess.

---

# Highlights

## Core capabilities
- Android device operations via **ADB**
- interactive terminal menus
- headless CLI automation
- monitoring snapshots and streaming workflows
- CSV / JSONL metric export
- OCR-assisted UI target detection
- best-match text selection for UI interaction
- plugin support
- terminal-first operator workflow

## Canonical runtime
This repository is now centered around the canonical runtime path:

- `main.py`
- `cli.py`
- `README.md`
- `core/adb_handler.py`

These files represent the current primary user-facing path.

---

# Repository structure

```text
Poseidon/
├─ main.py
├─ cli.py
├─ config.json
├─ requirements.txt
├─ README.md
├─ LICENSE
├─ core/
│  ├─ adb_handler.py
│  ├─ device_manager.py
│  ├─ exceptions.py
│  ├─ logger.py
│  ├─ plugin_manager.py
│  └─ result.py
├─ services/
│  ├─ monitoring_service.py
│  ├─ monitoring_service_v2.py
│  ├─ vision_service.py
│  └─ vision_service_v2.py
├─ modules/
│  ├─ monitoring.py
│  ├─ monitoring_v2.py
│  ├─ ui_vision.py
│  ├─ ui_vision_v2.py
│  └─ additional feature modules
├─ scripts/
│  └─ smoke_test_v4.sh
├─ docs/
│  └─ ROADMAP.md
├─ plugins/
├─ logs/
├─ screenshots/
└─ backups/


---

Requirements

System packages

Recommended on Debian, Ubuntu, Kali, or Raspberry Pi OS:

sudo apt update
sudo apt install -y python3 python3-venv adb scrcpy ffmpeg tesseract-ocr

Python environment

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements_v4.txt

> Pillow and pytesseract are required for OCR / vision workflows.




---

Quick start

Interactive mode

Start Poseidon with the interactive terminal UI:

python main.py

Headless CLI

Use the CLI for automation and scripting:

python cli.py


---

CLI usage

Device commands

python cli.py devices list
python cli.py devices list --json

Health check

python cli.py health check
python cli.py health check --json

Monitoring snapshot

python cli.py monitor once --json
python cli.py monitor once --export csv --json
python cli.py monitor once --export jsonl --json
python cli.py monitor once --export both --json

Monitoring stream

python cli.py monitor stream --interval 2 --count 5
python cli.py monitor stream --interval 2 --count 5 --export jsonl
python cli.py monitor stream --interval 2 --count 5 --export both --json

OCR / Vision search

python cli.py vision find-text "WLAN" --annotate --json
python cli.py vision find-text "Einstellungen" --min-confidence 20 --json
python cli.py vision find-text "WLAN Einstellungen" --annotate --json

OCR / Vision tap

Dry-run preview:

python cli.py vision tap-text "WLAN" --json

Real tap:

python cli.py vision tap-text "WLAN" --force --json

> Without --force, Poseidon performs a dry run and shows the selected tap position without executing it.




---

Interactive menus

Monitoring

The interactive monitoring menu provides:

battery level

battery temperature

memory usage

memory availability

optional CSV / JSONL export


Vision / OCR

The interactive OCR menu provides:

screenshot capture

OCR text matching

annotation of OCR matches

best-match selection

optional tap on the best detected target



---

Monitoring

Poseidon supports monitoring through the service layer.

Current metrics include:

timestamp

active serial

battery level

battery temperature

memory used

memory free

basic CPU load support in the v2 path


Export support

Monitoring data can be exported as:

CSV

JSONL


Default export location:

./logs



---

OCR / Vision

Poseidon supports OCR-based UI workflows through screenshot analysis.

Current OCR features include:

screenshot capture

normalized OCR matching

multi-word OCR search

confidence filtering

best-match selection

screenshot annotation


Default screenshot location:

./screenshots



---

Testing

Basic validation:

python -m py_compile main.py
python -m py_compile cli.py
python cli.py devices list
python cli.py health check --json
python cli.py monitor once --json

Full smoke test:

chmod +x scripts/smoke_test_v4.sh
./scripts/smoke_test_v4.sh

For the full testing workflow, see:

TESTING.md



---

Configuration

Poseidon uses config.json for runtime settings such as:

backup path

screenshot path

log path

theme

language

scrcpy path

update behavior


Runtime directories commonly used:

./logs

./screenshots

./backups



---

Recommended workflow

Interactive operator workflow

python main.py

Automation / scripting workflow

python cli.py

Validation workflow

Use:

TESTING.md

scripts/smoke_test_v4.sh


PR template


These files define the supported workflow, security posture, contribution style, and release direction.


---

Safety

Poseidon is intended for:

personal devices

lab devices

explicitly authorized environments


Do not use it against third-party devices or systems without authorization.


---

Roadmap

The long-term direction for Poseidon is:

stable canonical runtime

hardened ADB execution

stronger monitoring fidelity

more robust OCR / vision

clearer CLI behavior

reliable Raspberry Pi deployment

cleaner public release surface


See:

docs/ROADMAP.md



---

License

MIT License. See:

LICENSE