# Security Policy

## Supported path

The current recommended path for active validation is:
- `main_v5.py`
- `cli_v4.py`
- `core/adb_handler_v2.py`
- `services/monitoring_service_v2.py`
- `services/vision_service_v2.py`

Legacy files may still exist during the transition period and should be treated as migration candidates unless explicitly promoted.

---

## Responsible use

Poseidon is intended for:
- personal devices
- lab devices
- explicitly authorized environments

It must not be used against third-party devices or systems without authorization.

---

## Reporting a security issue

When reporting a security issue, include:
- affected file or module
- exact command or workflow
- device / OS context
- reproduction steps
- observed behavior
- expected behavior
- impact assessment

If the issue includes sensitive operational details, avoid posting them publicly in a normal issue.

---

## Examples of relevant security issues

Examples include:
- command injection risks
- unsafe shell argument handling
- destructive actions without confirmation safeguards
- unintended data export or disclosure
- path traversal in file or export handling
- unsafe defaults in remote or automation workflows
- privilege escalation or trust-boundary issues

---

## Hardening priorities

Primary security priorities for Poseidon are:
- explicit operator intent
- clear device targeting
- safe command execution
- understandable logs and error surfaces
- predictable CLI behavior
- minimizing destructive defaults

---

## Dependency hygiene

If a report is related to:
- `adb`
- `scrcpy`
- `ffmpeg`
- `tesseract`
- Python package dependencies

please specify the exact installed versions.
