import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from core.plugin_base import PluginBase
from utils.ui_helpers import print_header, menu_prompt, wait_for_enter, confirm
from utils.cli_safety import sanitize_device_input
from rich.console import Console
from rich.table import Table
import json

console = Console()

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_BLOATWARE_PATH = BASE_DIR / "data" / "bloatware.json"


class BloatwareIndex:
    def __init__(self, path: Path = DEFAULT_BLOATWARE_PATH) -> None:
        self.packages: Dict[str, Dict[str, Any]] = {}
        self.path = path
        self._load(path)

    def _load(self, path: Path) -> None:
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for item in data:
                pkg = item.get("package")
                if not pkg:
                    continue
                self.packages[pkg] = {
                    "category": item.get("category", "Unkategorisiert"),
                    "vendor": item.get("vendor"),
                    "model_prefix": item.get("model_prefix"),
                }
        except Exception as exc:
            console.print(f"[red]Bloatware-DB konnte nicht geladen werden: {exc}[/]")

    def detect(self, installed: Set[str], vendor: Optional[str] = None, model_prefix: Optional[str] = None) -> List[tuple]:
        matches = []
        for pkg, meta in self.packages.items():
            if pkg not in installed:
                continue
            if vendor and meta.get("vendor") and meta["vendor"] != vendor:
                continue
            if model_prefix and meta.get("model_prefix") and meta["model_prefix"] not in {"all", model_prefix}:
                continue
            matches.append((meta.get("category", "Unkategorisiert"), pkg))
        return matches


class AppDebloaterPlugin(PluginBase):
    def __init__(self) -> None:
        self._index = BloatwareIndex()

    @property
    def name(self) -> str:
        return "🚫 App-Debloater (Bloatware-Entferner)"

    @property
    def description(self) -> str:
        return "Scannt und entfernt ungenutzte System-Apps & Werbedienste."

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def author(self) -> str:
        return "Poseidon Core"

    def get_installed_packages(self, adb: Any, serial: str) -> Set[str]:
        """Ruft alle installierten Pakete auf dem Android-Gerät ab."""
        stdout, _, _ = adb.run_shell("pm list packages", serial=serial)
        packages = set()
        for line in stdout.splitlines():
            if line.startswith("package:"):
                packages.add(line.split(":")[-1].strip())
        return packages

    @property
    def destructive(self) -> bool:
        return True

    def run(self, device_manager: Any, adb: Any, config: Dict[str, Any]) -> None:
        serial = device_manager.get_current_device()
        if not serial:
            console.print("[red]Fehler: Kein Gerät verbunden.[/]")
            wait_for_enter()
            return

        while True:
            print_header("App-Debloater", "Unerwünschte Apps deinstallieren")

            model = (adb.get_device_property("ro.product.model", serial=serial) or "").lower()
            brand = (adb.get_device_property("ro.product.brand", serial=serial) or "").lower()
            vendor = brand.split(" ")[0] if brand else ""
            model_prefix = model.split(" ")[0] if model else ""

            console.print(f"[white]Gerät:[/] {vendor or '-'} / {model_prefix or '-'}")
            console.print("[yellow]Scanne Gerät nach bekannten Bloatware-Paketen...[/]")
            installed = self.get_installed_packages(adb, serial)

            detected = self._index.detect(installed, vendor=vendor or None, model_prefix=model_prefix or None)

            if not detected:
                console.print("\n[bold green][+] Keine bekannte Bloatware auf diesem Gerät gefunden![/]")
                console.print("1. Custom App deinstallieren")
                console.print("0. Zurück")
                choice = menu_prompt("Auswahl", range(0, 2))
                if choice == 0:
                    break
                elif choice == 1:
                    self.uninstall_custom(adb, serial)
                continue

            table = Table(title="Gefundene Bloatware-Pakete")
            table.add_column("Nr.", style="cyan", justify="right")
            table.add_column("Kategorie", style="magenta")
            table.add_column("Paketname", style="green")

            for idx, (category, pkg) in enumerate(detected, 1):
                table.add_row(str(idx), category, pkg)

            console.print(table)

            console.print("\nOptionen:")
            console.print(f"1 bis {len(detected)}: Einzelne App deinstallieren")
            console.print("A. Alle gefundenen Bloatware-Apps deinstallieren")
            console.print("R. Eine deinstallierte App wiederherstellen (Restore)")
            console.print("C. Custom App deinstallieren (Paketname eingeben)")
            console.print("0. Zurück")

            choice_str = console.input("[bold yellow]Auswahl[/]: ").strip()

            if choice_str == "0" or not choice_str:
                break
            elif choice_str.upper() == "A":
                if confirm("Möchtest du wirklich ALLE aufgelisteten Bloatware-Pakete deinstallieren?"):
                    for category, pkg in detected:
                        self.uninstall_package(adb, serial, pkg)
                    wait_for_enter()
            elif choice_str.upper() == "R":
                self.restore_package(adb, serial)
            elif choice_str.upper() == "C":
                self.uninstall_custom(adb, serial)
            else:
                try:
                    num = int(choice_str)
                    if 1 <= num <= len(detected):
                        category, pkg = detected[num - 1]
                        if confirm(f"Möchtest du {pkg} deinstallieren?"):
                            self.uninstall_package(adb, serial, pkg)
                            wait_for_enter()
                    else:
                        console.print("[red]Ungültige Nummer.[/]")
                        time.sleep(1)
                except ValueError:
                    console.print("[red]Ungültige Eingabe.[/]")
                    time.sleep(1)

    def uninstall_package(self, adb: Any, serial: str, pkg: str) -> None:
        """Deinstalliert das Paket für den aktuellen Benutzer (User 0)."""
        safe_pkg = sanitize_device_input("package", pkg)
        if not safe_pkg:
            console.print("[red]Ungültiger Paketname.[/]")
            wait_for_enter()
            return
        console.print(f"[cyan]Deinstalliere {safe_pkg}...[/]")
        stdout, stderr, rc = adb.run_shell(f"pm uninstall -k --user 0 {safe_pkg}", serial=serial)
        if rc == 0 and "Success" in stdout:
            console.print(f"[bold green][+] {safe_pkg} erfolgreich entfernt![/]")
        else:
            console.print(f"[bold red][-] Fehler bei {safe_pkg}: {stdout} {stderr}[/]")

    def uninstall_custom(self, adb: Any, serial: str) -> None:
        pkg = console.input("[yellow]Paketname der zu deinstallierenden App: [/]").strip()
        pkg = sanitize_device_input("package", pkg)
        if pkg:
            self.uninstall_package(adb, serial, pkg)
            wait_for_enter()

    def restore_package(self, adb: Any, serial: str) -> None:
        """Stellt eine zuvor deinstallierte System-App wieder her."""
        pkg = console.input("[yellow]Paketname der wiederherzustellenden App: [/]").strip()
        pkg = sanitize_device_input("package", pkg)
        if not pkg:
            return
        console.print(f"[cyan]Versuche {pkg} wiederherzustellen...[/]")
        stdout, stderr, rc = adb.run_shell(f"cmd package install-existing {pkg}", serial=serial)
        # Typischerweise gibt dies 'Package <name> installed for user: 0' zurück
        if rc == 0 and "installed" in stdout:
            console.print(f"[bold green][+] {pkg} erfolgreich wiederhergestellt![/]")
        else:
            console.print(f"[bold red][-] Wiederherstellung fehlgeschlagen: {stdout} {stderr}[/]")
        wait_for_enter()
