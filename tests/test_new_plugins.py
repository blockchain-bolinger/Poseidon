from __future__ import annotations

from typing import Any, Dict, Optional
from unittest.mock import MagicMock

import pytest

from plugins.phonesploit_pro import PhoneSploitProPlugin
from plugins.androidhack_backdoor import AndroidHackBackdoorPlugin
from plugins.androrat import AndroRATPlugin


class StubADB:
    def __init__(self, props: Optional[Dict[str, str]] = None) -> None:
        self.props = props or {}
        self.shell_calls = []

    def get_device_property(self, name: str, serial: Optional[str] = None) -> str:
        return self.props.get(name, "")

    def run_shell(self, command: str, serial: Optional[str] = None) -> tuple:
        self.shell_calls.append((serial, command))
        return "stub-shell-output", "", 0

    def run_shell_args(self, *args: Any, **kwargs: Any) -> tuple:
        command = " ".join(args)
        return self.run_shell(command, kwargs.get("serial"))


class StubDeviceManager:
    def __init__(self, current: str = "SERIAL") -> None:
        self._current = current

    def get_current_device(self) -> str:
        return self._current


def test_phonesploit_pro_menu_exits(monkeypatch: pytest.MonkeyPatch):
    plugin = PhoneSploitProPlugin()
    adb = StubADB()
    dm = StubDeviceManager()

    monkeypatch.setattr("plugins.phonesploit_pro.wait_for_enter", lambda: None)
    monkeypatch.setattr("plugins.phonesploit_pro.print_header", lambda *_: None)
    monkeypatch.setattr("plugins.phonesploit_pro.confirm", lambda *_: True)
    monkeypatch.setattr("plugins.phonesploit_pro.menu_prompt", lambda *_, **__: 0)

    plugin.run(dm, adb, {})
    assert adb.shell_calls == []


def test_androidhack_backdoor_permission_audit(monkeypatch: pytest.MonkeyPatch):
    plugin = AndroidHackBackdoorPlugin()
    adb = StubADB(
        props={
            "service.adb.tcp.port": "",
            "persist.sys.debuggable": "",
            "ro.secure": "1",
            "ro.debuggable": "0",
        }
    )
    dm = StubDeviceManager()

    monkeypatch.setattr("plugins.androidhack_backdoor.wait_for_enter", lambda: None)
    monkeypatch.setattr("plugins.androidhack_backdoor.print_header", lambda *_: None)
    monkeypatch.setattr("plugins.androidhack_backdoor.menu_prompt", lambda *_, **__: 0)
    monkeypatch.setattr("plugins.androidhack_backdoor.confirm", lambda *_: True)
    monkeypatch.setattr("plugins.androidhack_backdoor.console.input", lambda *_: "com.example")

    plugin.run(dm, adb, {})


def test_androrat_skips_when_no_device(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture):
    plugin = AndroRATPlugin()
    dm = StubDeviceManager(current="")

    monkeypatch.setattr("plugins.androrat.wait_for_enter", lambda: None)
    monkeypatch.setattr("plugins.androrat.print_header", lambda *_: None)
    monkeypatch.setattr("plugins.androrat.menu_prompt", lambda *_, **__: 0)

    plugin.run(dm, MagicMock(), {})
    captured = capsys.readouterr()
    assert "Kein Gerät verbunden." in captured.out


def test_androrat_export_report_writes_file(tmp_path, monkeypatch: pytest.MonkeyPatch):
    import plugins.androrat as androrat_module
    monkeypatch.setattr(androrat_module, "BASE_DIR", tmp_path)

    plugin = AndroRATPlugin()
    adb = StubADB(
        props={
            "ro.product.model": "TestModel",
            "ro.product.brand": "TestBrand",
            "ro.build.version.release": "13",
            "ro.build.version.sdk": "33",
        }
    )
    dm = StubDeviceManager()

    plugin._export_report(adb, dm.get_current_device())
    report_md = tmp_path / "logs" / f"androrat_report_{dm.get_current_device()}.md"
    report_json = tmp_path / "logs" / f"androrat_report_{dm.get_current_device()}.json"
    assert report_md.exists()
    assert report_json.exists()
    text = report_md.read_text(encoding="utf-8")
    assert "# AndroRAT Device Report" in text
    assert "| Modell | TestModel |" in text
