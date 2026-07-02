from __future__ import annotations

from plugins.mobile_toolbox import (
    FRIDA_PROCESS_PRESETS,
    OBJECTION_PRESETS,
    command_display,
    mobsf_multipart_body,
    normalize_command,
    run_command,
)


def test_normalize_command_splits_strings():
    assert normalize_command('apktool d -f "My App.apk" -o out') == ["apktool", "d", "-f", "My App.apk", "-o", "out"]


def test_command_display_joins_parts():
    assert command_display(["jadx-gui", "sample.apk"]) == "jadx-gui sample.apk"


def test_run_command_executes_python():
    result = run_command(["python3", "-c", "print('ok')"], timeout=30)
    assert result.returncode == 0
    assert result.stdout.strip() == "ok"


def test_mobsf_multipart_body_contains_filename_and_boundary():
    body, boundary = mobsf_multipart_body("file", "demo.apk", b"APKDATA", boundary="BOUNDARY123")
    assert boundary == "BOUNDARY123"
    assert b'demo.apk' in body
    assert b"APKDATA" in body
    assert b"--BOUNDARY123" in body


def test_presets_exist_for_runtime_workflows():
    assert any(name == "Discovery" for name, _, _ in FRIDA_PROCESS_PRESETS)
    assert any(name == "Explore" for name, _, _ in OBJECTION_PRESETS)
