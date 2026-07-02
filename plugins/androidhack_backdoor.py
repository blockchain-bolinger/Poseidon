from __future__ import annotations

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


class AndroidHackBackdoorPlugin(PluginBase):
    @property
    def name(self) -> str:
        return "🔐 AndroidHack BackDoor"

    @property
    def description(self) -> str:
        return "Audit-/Steuer-Konsole: ADB/Intents/Debloat-Checklisten."

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
            print_header("AndroidHack BackDoor", "Audit-/Steuer-Konsole")
            print("1. ADB-Aktivierung prüfen/erkennen")
            print("2. APK-Info einer installierten App anzeigen")
            print("3. Exportierte Komponenten auflisten")
            print("4. Berechtigungsaudit")
            print("5. Diagnose-Code starten *#*#4636#*#*")
            print("0. Zurück")
            choice = menu_prompt("Option", range(0, 6))

            if choice == 0:
                break
            elif choice == 1:
                self._adb_activation_check(adb, serial)
            elif choice == 2:
                self._apk_info(adb, serial)
            elif choice == 3:
                self._exported_components(adb, serial)
            elif choice == 4:
                self._permission_audit(adb, serial)
            elif choice == 5:
                self._diag_code(adb, serial)
            wait_for_enter()

    def _adb_activation_check(self, adb, serial):
        props = ["service.adb.tcp.port", "persist.sys.debuggable", "ro.secure", "ro.debuggable"]
        for prop in props:
            value = adb.get_device_property(prop, serial=serial)
            console.print(f"{prop}: [cyan]{value}[/]")

    def _apk_info(self, adb, serial):
        pkg = console.input("[yellow]Paketname: [/]").strip()
        pkg = sanitize_device_input("package", pkg)
        if not pkg:
            return
        info, _, rc = adb.run_shell(f"dumpsys package {pkg}", serial=serial)
        print(info[:8000])

    def _exported_components(self, adb, serial):
        out, _, _ = adb.run_shell("pm list packages", serial=serial)
        packages = [l.split(":", 1)[-1].strip() for l in out.splitlines() if l.startswith("package:")]
        matches = []
        for pkg in packages[:60]:
            dump, _, _ = adb.run_shell(f"dumpsys package {sanitize_device_input('package', pkg) or pkg}", serial=serial)
            if "android:exported=\"true\"" in dump:
                matches.append(pkg)
        table = Table(title="Pakete mit exportierten Komponenten")
        table.add_column("Paket", style="red")
        for pkg in matches[:120]:
            table.add_row(pkg)
        console.print(table)

    def _permission_audit(self, adb, serial):
        out, _, _ = adb.run_shell("pm list packages -3", serial=serial)
        packages = [l.split(":", 1)[-1].strip() for l in out.splitlines() if l.startswith("package:")]
        interesting = []
        for pkg in packages[:60]:
            pkg = sanitize_device_input("package", pkg) or pkg
            dump, _, _ = adb.run_shell(f"dumpsys package {pkg}", serial=serial)
            interesting_perms = [
                line.strip()
                for line in dump.splitlines()
                if "android.permission." in line and any(t in line.lower() for t in ["sms", "call", "camera", "mic", "location", "contacts"])
            ]
            if interesting_perms:
                interesting.append((pkg, interesting_perms))
        for pkg, perms in interesting[:80]:
            console.print(f"[bold]{pkg}[/]")
            for perm in perms[:20]:
                console.print(f"  - {perm}")

    def _diag_code(self, adb, serial):
        out, _, _ = adb.run_shell("am start -a android.intent.action.DIAL -d tel:4636", serial=serial)
        console.print("[yellow]Diagnose-Code per ACTION_DIAL vorbereitet.[/]")
