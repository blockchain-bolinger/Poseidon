from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from core.plugin_base import PluginBase
from plugins.artifact_library import combined_payloads, discover_apks
from utils.ui_helpers import print_header, menu_prompt, wait_for_enter, confirm
from utils.cli_safety import sanitize_device_input
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()
BASE_DIR = Path(__file__).resolve().parents[1]


class AndroRATPlugin(PluginBase):
    @property
    def name(self) -> str:
        return "🕵️ AndroRAT"

    @property
    def description(self) -> str:
        return "Remote-Admin-Audit: Device-Info, Sensor/Location-Abfrage, Reporting, APKs & Payloads."

    @property
    def version(self) -> str:
        return "2.0"

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
            print_header("AndroRAT", "Device Audit Frame")
            print("1. Device-Info exportieren")
            print("2. Standort/Telefonie-Status prüfen")
            print("3. Sensorliste ausgeben")
            print("4. Report nach Datei exportieren")
            print("5. Lokale APKs installieren")
            print("6. Payload-Templates anzeigen")
            print("0. Zurück")
            choice = menu_prompt("Option", range(0, 7))

            if choice == 0:
                break
            if choice == 1:
                self._device_info_export(adb, serial)
            elif choice == 2:
                self._location_telephony(adb, serial)
            elif choice == 3:
                self._sensor_list(adb, serial)
            elif choice == 4:
                self._export_report(adb, serial)
            elif choice == 5:
                self._install_local_apk(adb, serial)
            elif choice == 6:
                self._show_payloads()
            wait_for_enter()

    def _device_info_export(self, adb: Any, serial: str) -> None:
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

    def _location_telephony(self, adb: Any, serial: str) -> None:
        out, _, _ = adb.run_shell("dumpsys location", serial=serial)
        console.print(out[:5000])

    def _sensor_list(self, adb: Any, serial: str) -> None:
        out, _, _ = adb.run_shell("dumpsys sensorservice", serial=serial)
        console.print(out[:5000])

    def _export_report(self, adb: Any, serial: str) -> None:
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

    def _install_local_apk(self, adb: Any, serial: str) -> None:
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

    def _show_payloads(self) -> None:
        payloads = combined_payloads()
        table = Table(title="Payload-Templates")
        table.add_column("Nr", justify="right", style="cyan")
        table.add_column("Titel", style="green")
        table.add_column("Kategorie", style="yellow")
        for idx, payload in enumerate(payloads, 1):
            table.add_row(str(idx), payload.title, payload.category)
        console.print(table)
        console.print(Panel("Lokale APKs und Payload-Templates werden nur aus data/ oder assets/ geladen.", title="Hinweis", border_style="blue"))
