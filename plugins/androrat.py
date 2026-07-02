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


class AndroRATPlugin(PluginBase):
    @property
    def name(self) -> str:
        return "🕵️ AndroRAT"

    @property
    def description(self) -> str:
        return "Remote-Admin-Audit: Device-Info, Sensor/Location-Abfrage, Reporting."

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
            print_header("AndroRAT", "Device Audit Frame")
            print("1. Device-Info exportieren")
            print("2. Standort/Telefonie-Status prüfen")
            print("3. Sensorliste ausgeben")
            print("4. Report nach Datei exportieren")
            print("0. Zurück")
            choice = menu_prompt("Option", range(0, 5))

            if choice == 0:
                break
            elif choice == 1:
                self._device_info_export(adb, serial)
            elif choice == 2:
                self._location_telephony(adb, serial)
            elif choice == 3:
                self._sensor_list(adb, serial)
            elif choice == 4:
                self._export_report(adb, serial)
            wait_for_enter()

    def _device_info_export(self, adb, serial):
        props = {
            "Modell": "ro.product.model",
            "Brand": "ro.product.brand",
            "Android": "ro.build.version.release",
            "SDK": "ro.build.version.sdk",
            "Hardware": "ro.hardware",
            "Board": "ro.board",
        }
        table = Table(title="Device Info")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")
        for key, prop in props.items():
            value = adb.get_device_property(prop, serial=serial)
            table.add_row(key, value or "-")
        console.print(table)

    def _location_telephony(self, adb, serial):
        out, _, _ = adb.run_shell("dumpsys location", serial=serial)
        print(out[:5000])

    def _sensor_list(self, adb, serial):
        out, _, _ = adb.run_shell("dumpsys sensorservice", serial=serial)
        print(out[:5000])

    def _export_report(self, adb, serial):
        path = BASE_DIR / "logs" / f"androrat_report_{serial}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        info_props = ["ro.product.model", "ro.product.brand", "ro.build.version.release", "ro.build.version.sdk"]
        lines = []
        for prop in info_props:
            value = adb.get_device_property(prop, serial=serial)
            lines.append(f"{prop}={value}")
        out, _, _ = adb.run_shell("dumpsys location", serial=serial)
        lines.append("--- location ---")
        lines.append(out[:4000])
        path.write_text("\n".join(lines), encoding="utf-8")
        console.print(f"[green]Report gespeichert:[/] {path}")
