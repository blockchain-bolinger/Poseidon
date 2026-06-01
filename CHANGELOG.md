# Changelog

All notable changes to **Poseidon** should be documented in this file.

The project is currently transitioning from a legacy ADB toolkit toward a more modular and testable runtime path.

---

## [Unreleased]

### Planned
- promotion of `main_v5.py` to `main.py`
- promotion of `cli_v4.py` to `cli.py`
- promotion of `README_v4.md` to `README.md`
- migration from `core/adb_handler.py` to `core/adb_handler_v2.py`
- stronger end-to-end smoke testing on real Android devices

---

## [5.0-dev] - 2026-04-15

### Added
- `main_v5.py` as a new interactive entrypoint wired to the v2 monitoring and vision modules
- `cli_v4.py` as a headless CLI wired to `MonitoringServiceV2` and `VisionServiceV2`
- `modules/monitoring_v2.py`
- `modules/ui_vision_v2.py`
- `services/monitoring_service_v2.py` with CSV and JSONL export support
- `services/vision_service_v2.py` with normalized OCR matching, multi-word search, and best-match selection
- `TESTING.md` with a structured validation and smoke-test guide
- `scripts/smoke_test_v4.sh` for Linux / Debian / Raspberry Pi smoke testing
- `requirements_v4.txt` for the current recommended runtime path
- governance and repo-professionalization files:
  - `CONTRIBUTING.md`
  - `SECURITY.md`
  - PR and issue templates
  - `REPO_BRANDING.md`

### Improved
- repository documentation and public-facing project positioning
- monitoring and OCR workflows for both interactive and headless operation
- operator safety through dry-run behavior for OCR-driven tap flows

### Notes
- this version is a **parallel upgrade path**, not yet a full in-place replacement of the legacy entrypoint files

---

## [4.0-dev] - 2026-04-15

### Added
- `main_v4.py` as a cleaned and extended main entrypoint
- `main_clean.py` as a drop-in cleaned replacement candidate for the original main flow
- `cli_v3.py` with monitoring stream and OCR tap-text support
- `core/adb_handler_v2.py` as a hardened ADB runtime candidate
- `modules/monitoring.py`
- `modules/ui_vision.py`
- `services/monitoring_service.py`
- `services/vision_service.py`
- `README_v4.md` as an optimized documentation path

### Improved
- repository layout for staged modernization
- first operator-facing monitoring and OCR menu integrations
- safer structure for future consolidation

---

## Legacy baseline

Legacy Poseidon already provided:
- ADB-driven device control
- app and media handling
- network and system tooling
- logcat and backup flows
- plugin loading
- menu-driven terminal interaction

This baseline remains important during migration, but the recommended future-facing path is now the v4/v5 architecture.
