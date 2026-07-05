from __future__ import annotations

from typing import Any, Optional

from plugins.phonesploit_pro import PhoneSploitProPlugin


class StubADB:
    def __init__(self) -> None:
        self.shell_calls = []

    def run_shell(self, command: str, serial: Optional[str] = None) -> tuple[str, str, int]:
        self.shell_calls.append((serial, command))
        if "pm list packages -3" in command:
            return "package:com.example.one\npackage:com.example.two\n", "", 0
        return "shell snapshot", "", 0


def test_phonesploit_export_recon_writes_markdown(tmp_path, monkeypatch):
    import plugins.phonesploit_pro as phonesploit_module

    monkeypatch.setattr(phonesploit_module, "BASE_DIR", tmp_path)

    plugin = PhoneSploitProPlugin()
    adb = StubADB()

    plugin._export_recon(adb, "SERIAL123")
    report_md = tmp_path / "logs" / "phonesploit_report_SERIAL123.md"
    report_json = tmp_path / "logs" / "phonesploit_report_SERIAL123.json"
    assert report_md.exists()
    assert report_json.exists()
    text = report_md.read_text(encoding="utf-8")
    assert "# PhoneSploit Pro Recon Report" in text
    assert "| com.example.one |" in text
