from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from core.plugin_base import PluginBase
from plugins.artifact_library import PayloadTemplate, combined_payloads, discover_apks
from plugins.report_builder import ReportBuilder
from utils.ui_helpers import print_header, menu_prompt, wait_for_enter, confirm
from utils.cli_safety import sanitize_device_input
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

console = Console()
BASE_DIR = Path(__file__).resolve().parents[1]


def _code(command: str) -> Panel:
    return Panel(Syntax(command, "bash", theme="monokai", line_numbers=False), title="Payload", border_style="yellow")


class PhoneSploitProPlugin(PluginBase):
    @property
    def name(self) -> str:
        return "📡 PhoneSploit Pro"

    @property
    def description(self) -> str:
        return "ADB/Termux/HID-Automation: Debugging-Chains, Remote-Shell, App-Audit, Payloads & APKs."

    @property
    def version(self) -> str:
        return "2.1"

    @property
    def author(self) -> str:
        return "Poseidon Core"

    @property
    def destructive(self) -> bool:
        return True

    def run(self, device_manager: Any, adb: Any, config: Dict[str, Any]) -> None:
        serial = device_manager.get_current_device()
        if not serial:
            console.print("[red]Kein Gerät verbunden.[/]")
            wait_for_enter()
            return

        while True:
            print_header("PhoneSploit Pro", "ADB/Termux Chains")
            print("1. ADB über TCP/IP aktivieren")
            print("2. ADB-Gerät neu starten")
            print("3. Termux installieren/aktualisieren")
            print("4. Paketliste abrufen (+ exportierte Intents)")
            print("5. Lokale APKs anzeigen/installieren")
            print("6. Payloads durchsuchen")
            print("7. Payload ausführen")
            print("8. Recon-Report exportieren")
            print("0. Zurück")
            choice = menu_prompt("Option", range(0, 9))

            if choice == 0:
                break
            if choice == 1:
                self._enable_tcpip(adb, serial)
            elif choice == 2:
                self._reboot_device(adb, serial)
            elif choice == 3:
                self._install_termux(adb, serial)
            elif choice == 4:
                self._package_audit(adb, serial)
            elif choice == 5:
                self._local_apk_menu(adb, serial)
            elif choice == 6:
                self._browse_payloads()
            elif choice == 7:
                self._run_payload(adb, serial)
            elif choice == 8:
                self._export_recon(adb, serial)
            wait_for_enter()

    def _enable_tcpip(self, adb: Any, serial: str) -> None:
        console.print("[yellow]Aktiviere ADB over TCP/IP auf Port 5555...[/]")
        adb.run_shell("setprop service.adb.tcp.port 5555", serial=serial)
        adb.run_shell("stop adbd; start adbd", serial=serial)
        ip, _, _ = adb.run_shell("ip route | awk '{print $9}' | head -n 1", serial=serial)
        ip = (ip or "").strip()
        if not ip:
            ip, _, _ = adb.run_shell("ifconfig wlan0 | awk '/inet /{print $2}'", serial=serial)
            ip = (ip or "").strip()
        console.print(f"[green]ADB TCP/IP sollte aktiv sein. IP: {ip or 'unbekannt'}[/]")
        console.print(f"adb connect {ip or '<IP>'}:5555")

    def _reboot_device(self, adb: Any, serial: str) -> None:
        mode = console.input("[yellow]Reboot-Modus (bootloader/recovery/sideload) [normal]: [/]").strip().lower()
        mode = sanitize_device_input("reboot_mode", mode) or ""
        cmd = f"reboot {mode}".strip()
        if not mode:
            cmd = "reboot"
        if confirm(f"Reboot ausführen: {cmd}"):
            adb.run_shell(cmd, serial=serial)
            console.print("[green]Reboot ausgelöst.[/]")

    def _install_termux(self, adb: Any, serial: str) -> None:
        console.print("[yellow]Prüfe Termux-Installation...[/]")
        out, _, _ = adb.run_shell("pm list packages | grep -i termux || true", serial=serial)
        if "com.termux" in out:
            console.print("[green]Termux ist installiert.[/]")
        else:
            console.print("[red]Termux nicht gefunden. Bitte aus F-Droid/GPlay installieren.[/]")

    def _package_audit(self, adb: Any, serial: str) -> None:
        out, _, _ = adb.run_shell("pm list packages -3", serial=serial)
        packages = [l.split(":", 1)[-1].strip() for l in out.splitlines() if l.startswith("package:")]
        table = Table(title="User Packages")
        table.add_column("Paket", style="cyan")
        for pkg in packages[:120]:
            table.add_row(pkg)
        console.print(table)
        if len(packages) > 120:
            console.print(f"... {len(packages) - 120} weitere")

    def _local_apk_menu(self, adb: Any, serial: str) -> None:
        apks = discover_apks()
        if not apks:
            console.print("[yellow]Keine APKs in data/apks oder assets/apks gefunden.[/]")
            return
        table = Table(title="Lokale APKs")
        table.add_column("Nr", justify="right", style="cyan")
        table.add_column("Datei", style="green")
        for idx, apk in enumerate(apks, 1):
            table.add_row(str(idx), str(apk.relative_to(BASE_DIR)))
        console.print(table)
        choice = menu_prompt("APK wählen", range(0, len(apks) + 1))
        if choice == 0:
            return
        apk = apks[choice - 1]
        if not confirm(f"APK installieren: {apk.name}?"):
            return
        out, err, rc = adb.run(f"install -r {apk}", serial=serial)
        console.print(f"rc={rc}")
        console.print((out or err or "").strip() or "(keine Ausgabe)")

    def _browse_payloads(self) -> None:
        payloads = combined_payloads()
        table = Table(title="Payload-Templates")
        table.add_column("Nr", justify="right", style="cyan")
        table.add_column("Titel", style="green")
        table.add_column("Kategorie", style="yellow")
        for idx, payload in enumerate(payloads, 1):
            table.add_row(str(idx), payload.title, payload.category)
        console.print(table)
        console.print(Panel("Diese Templates dienen als sichere, lokale Demo- und Audit-Vorlagen.\nAPK- und Payload-Dateien werden aus data/ oder assets/ geladen, falls vorhanden.", title="Hinweis", border_style="blue"))

    def _choose_payload(self) -> Optional[PayloadTemplate]:
        payloads = combined_payloads()
        if not payloads:
            console.print("[yellow]Keine Payload-Templates gefunden.[/]")
            return None
        table = Table(title="Payload-Auswahl")
        table.add_column("Nr", justify="right", style="cyan")
        table.add_column("Titel", style="green")
        table.add_column("Kategorie", style="yellow")
        for idx, payload in enumerate(payloads, 1):
            table.add_row(str(idx), payload.title, payload.category)
        console.print(table)
        choice = menu_prompt("Payload wählen", range(0, len(payloads) + 1))
        if choice == 0:
            return None
        return payloads[choice - 1]

    def _run_payload(self, adb: Any, serial: str) -> None:
        payload = self._choose_payload()
        if not payload:
            return
        if payload.requires_confirmation and not confirm(f"Payload '{payload.title}' ausführen?"):
            console.print("[yellow]Abbruch.[/]")
            return
        if not payload.command:
            console.print("[yellow]Kein Kommando definiert.[/]")
            return
        console.print(_code(payload.command))
        out_dry, _, _ = adb.run_shell(payload.command + " || true", serial=serial)
        console.print("[yellow]Dry Run:[/]")
        console.print(out_dry[:1000] or "(keine Ausgabe)")
        if not confirm("Jetzt echte Ausführung fortsetzen?"):
            return
        out, err, rc = adb.run_shell(payload.command, serial=serial)
        console.print(f"rc={rc}")
        console.print((out or err or "")[:4000])

    def _export_recon(self, adb: Any, serial: str) -> None:
        info, _, _ = adb.run_shell("dumpsys package com.android.shell | head -n 80", serial=serial)
        packages, _, _ = adb.run_shell("pm list packages -3", serial=serial)
        base_path = BASE_DIR / "logs" / f"phonesploit_report_{serial}"
        package_lines = [line.split(":", 1)[-1].strip() for line in (packages or "").splitlines() if line.startswith("package:")]
        builder = ReportBuilder("PhoneSploit Pro Recon Report")
        builder.add_metadata("Gerät", serial)
        builder.add_code("Shell Snapshot", (info or "").strip()[:5000] or "(keine Ausgabe)")
        builder.add_table(
            "User Packages",
            [(pkg,) for pkg in package_lines[:200]],
            headers=("Paket",),
        )
        if len(package_lines) > 200:
            builder.add_text("Hinweis", f"... {len(package_lines) - 200} weitere Pakete")
        md_path, json_path = builder.write_bundle(base_path)
        console.print(f"[green]Markdown-Recon-Report gespeichert:[/] {md_path}")
        console.print(f"[green]JSON-Recon-Report gespeichert:[/] {json_path}")
