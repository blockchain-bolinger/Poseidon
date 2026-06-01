# Contributing to Poseidon

Thank you for contributing to **Poseidon**.

This repository is currently evolving from a legacy menu-driven ADB toolkit into a more modular platform with:
- interactive terminal workflows
- headless CLI automation
- monitoring and export services
- OCR / UI vision features
- safer staged upgrades

The goal is to keep changes **practical, testable, and production-oriented**.

---

## Contribution principles

Please prefer:
- small, focused changes
- explicit error handling
- stable CLI behavior
- backwards-aware upgrades
- readable documentation
- Linux / Debian / Raspberry Pi compatibility where possible

Avoid:
- large unrelated refactors in one change
- hidden breaking changes
- silent failure paths
- undocumented dependencies

---

## Recommended workflow

1. Review the current recommended path:
   - `main_v5.py`
   - `cli_v4.py`
   - `core/adb_handler_v2.py`
   - `services/monitoring_service_v2.py`
   - `services/vision_service_v2.py`

2. Make one logically scoped change.

3. Validate using:
   - `TESTING.md`
   - `scripts/smoke_test_v4.sh`

4. Update documentation if behavior changed.

---

## Coding guidelines

### Python
- prefer clear function boundaries
- keep side effects explicit
- do not swallow exceptions without logging
- prefer structured return data over ad-hoc tuples for new code
- keep terminal output readable and operator-focused

### CLI
- stable exit codes matter
- JSON output should remain machine-readable
- destructive actions should support dry-run or confirmation where possible

### ADB workflows
- assume devices may disconnect unexpectedly
- handle missing devices gracefully
- keep timeouts explicit for long-running commands

---

## Documentation expectations

Update the relevant docs when you change:
- commands
- dependencies
- startup flow
- exported files
- required environment setup

Primary documentation files:
- `README_v4.md`
- `TESTING.md`

---

## Pull request expectations

A good PR should include:
- what changed
- why it changed
- whether behavior is backward compatible
- how it was tested
- any new dependencies
- any operator-visible impact

---

## Scope preference

Strong contribution areas:
- ADB runtime hardening
- monitoring metrics and export quality
- OCR / vision robustness
- Raspberry Pi friendliness
- CLI polish
- testability
- documentation quality

---

## Security note

Poseidon must only be used on:
- devices you own
- lab devices
- devices you are explicitly authorized to assess

Do not contribute functionality that assumes unauthorized use.
