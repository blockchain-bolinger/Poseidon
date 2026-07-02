from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.plugin_base import PluginBase
from utils.ui_helpers import print_header, menu_prompt, wait_for_enter, confirm
from utils.cli_safety import sanitize_device_input
from rich.console import Console
from rich.table import Table

console = Console()
BASE_DIR = Path(__file__).resolve().parents[1]


class PhoneSploitProPlugin(PluginBase):
    @property
    def name(self) -> str:
        return "📡 PhoneSploit Pro"

    @property
    def description(self) -> str:
        return "ADB/Termux/HID-Automation: Debugging-Chains, Remote-Shell, App-Audit."

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def author(self) -> str:
        return "Poseidon Core"

    @property
    def destructive(self) -> bool:
        return False

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
            print("4. Termux-Remote-Shell starten")
            print("5. Paketliste abrufen (+ exportierte Intents)")
            print("0. Zurück")
            choice = menu_prompt("Option", range(0, 6))

            if choice == 0:
                break
            elif choice == 1:
                self._enable_tcpip(device_manager, adb, serial)
            elif choice == 2:
                self._reboot_device(adb, serial)
            elif choice == 3:
                self._install_termux(adb, serial)
            elif choice == 4:
                self._termux_remote_shell(adb, serial)
            elif choice == 5:
                self._package_audit(adb, serial)
            wait_for_enter()

    def _enable_tcpip(self, device_manager, adb, serial):
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

    def _reboot_device(self, adb, serial):
        mode = console.input("[yellow]Reboot-Modus (bootloader/recovery/正常) [正常]: [/]").strip().lower()
        mode = sanitize_device_input("reboot_mode", mode) or "正常"
        cmd = f"reboot {mode}" if mode != "正常" else "reboot"
        adb.run_shell(cmd, serial=serial)
        console.print("[green]Reboot ausgelöst.[/]")

    def _install_termux(self, adb, serial):
        console.print("[yellow]Prüfe Termux-Installation...[/]")
        out, _, rc = adb.run_shell("pm list packages | grep -i termux || true", serial=serial)
        if "com.termux" in out:
            console.print("[green]Termux ist installiert.[/]")
            return
        console.print("[red]Termux nicht gefunden. Bitte aus F-Droid/GPlay installieren.[/]")

    def _termux_remote_shell(self, adb, serial):
        out, _, rc = adb.run_shell("which termux-shell || which termux-open || true", serial=serial)
        if rc == 0 and out.strip():
            console.print(f"[green]Termux gefunden:[/] {out}")
        else:
            console.print("[yellow]Kein Termux-Shell-Binary erkannt. Paketstatus prüfen...[/]")
            out, _, _ = adb.run_shell("pm list packages | grep -i termux || true", serial=serial)
            console.print(out or "[red]Termux nicht installiert.[/]")

    def _package_audit(self, adb, serial):
        out, _, _ = adb.run_shell("pm list packages -3", serial=serial)
        packages = [l.split(":", 1)[-1].strip() for l in out.splitlines() if l.startswith("package:")]
        table = Table(title="User Packages")
        table.add_column("Paket", style="cyan")
        for pkg in packages[:120]:
            table.add_row(pkg)
        console.print(table)
        if len(packages) > 120:
            console.print(f"... {len(packages) - 120} weitere")
