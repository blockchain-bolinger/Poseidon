# Poseidon Testing Guide

This file documents the recommended smoke-test and validation workflow for the current Poseidon parallel upgrade path.

## Recommended targets

Interactive target:
- `main_v5.py`

Headless target:
- `cli_v4.py`

Core upgrade candidates:
- `core/adb_handler_v2.py`
- `services/monitoring_service_v2.py`
- `services/vision_service_v2.py`

---

## 1. Prepare environment

### Linux / Debian / Ubuntu / Raspberry Pi

```bash
sudo apt update
sudo apt install -y python3 python3-venv adb scrcpy ffmpeg tesseract-ocr
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements_v4.txt
```

---

## 2. Verify ADB availability

```bash
adb version
adb devices
```

Expected:
- `adb version` returns a valid ADB version string
- `adb devices` lists at least one Android device in `device` state

---

## 3. Headless smoke tests

### Device listing

```bash
python cli_v4.py devices list
python cli_v4.py devices list --json
```

Expected:
- command exits successfully
- connected devices are shown

### Health check

```bash
python cli_v4.py health check
python cli_v4.py health check --json
```

Expected:
- return code `0` if ADB is functioning
- JSON output is valid when `--json` is used

### Monitoring snapshot

```bash
python cli_v4.py monitor once --json
python cli_v4.py monitor once --export both --json
```

Expected:
- metrics include timestamp, serial, battery, memory and optional CPU load
- export files appear under `./logs`

### Monitoring stream

```bash
python cli_v4.py monitor stream --interval 2 --count 3
python cli_v4.py monitor stream --interval 2 --count 3 --export jsonl
```

Expected:
- multiple snapshots printed
- optional JSONL export appended correctly

### OCR / Vision search

```bash
python cli_v4.py vision find-text "WLAN" --annotate --json
python cli_v4.py vision find-text "Einstellungen" --min-confidence 20 --json
```

Expected:
- screenshot is created
- OCR matches are returned when visible on the display
- annotated image is written if `--annotate` is used

### OCR / Vision tap dry-run

```bash
python cli_v4.py vision tap-text "WLAN" --json
```

Expected:
- no actual tap is sent
- dry-run payload contains `tap.x`, `tap.y`, and the best OCR match

### OCR / Vision tap force

```bash
python cli_v4.py vision tap-text "WLAN" --force --json
```

Expected:
- an actual `input tap` command is sent
- use only on a safe / owned test device

---

## 4. Interactive smoke tests

Launch:

```bash
python main_v5.py
```

Check the following manually:
- application starts without traceback
- menus render correctly
- device status is shown
- menu item `21. Monitoring v2` opens
- menu item `22. Vision / OCR v2` opens
- monitoring snapshot prints values
- OCR search can capture and analyze a screenshot

---

## 5. File output checks

Verify runtime directories:

```bash
ls -la logs
ls -la screenshots
ls -la backups
```

Expected:
- `logs/` contains exported monitoring files if export was used
- `screenshots/` contains OCR capture / annotation images

---

## 6. Failure checks

### No ADB installed
Expected:
- startup exits early with a clear error

### No device connected
Expected:
- device list is empty or selection fails gracefully
- CLI should not crash with an unhandled exception

### OCR dependencies missing
Expected:
- vision commands fail with a clear dependency message
- no silent success

---

## 7. Recommended release gate

Before promoting the new path to the canonical files (`main.py`, `cli.py`, `README.md`), verify:
- all smoke tests above pass
- OCR works on at least one real test screen
- monitoring export produces valid CSV and JSONL
- `main_v5.py` launches without regressions
- `cli_v4.py` returns stable exit codes

---

## 8. Promotion step after successful validation

Local consolidation example:

```bash
cp main_v5.py main.py
cp cli_v4.py cli.py
cp README_v4.md README.md
cp core/adb_handler_v2.py core/adb_handler.py
```

Re-run smoke tests after promotion.
