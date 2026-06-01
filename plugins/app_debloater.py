import os
import time
from typing import Dict, Any, List, Set
from core.plugin_base import PluginBase
from utils.ui_helpers import print_header, menu_prompt, wait_for_enter, confirm
from rich.console import Console
from rich.table import Table

console = Console()

BLOATWARE_LIST = {
    "Facebook / Meta": [
        "com.facebook.katana",
        "com.facebook.system",
        "com.facebook.appmanager",
        "com.facebook.services",
        "com.facebook.orca" # Messenger
    ],
    "Google (Optionale Apps)": [
        "com.google.android.apps.youtube.music",
        "com.google.android.videos", # Google TV
        "com.google.android.music",
        "com.google.android.apps.docs", # Google Drive
        "com.google.android.apps.photos",
        "com.google.android.apps.tachyon", # Google Duo / Meet
        "com.google.android.feedback",
        "com.google.android.youtube"
    ],
    "Samsung Bloatware": [
        "com.samsung.android.bixby.agent",
        "com.samsung.android.bixby.wakeup",
        "com.samsung.android.app.spage", # Bixby Home
        "com.samsung.android.singlesake.service",
        "com.sec.android.app.sbrowser", # Samsung Browser
        "com.samsung.android.email.provider",
        "com.samsung.android.kidshome"
    ],
    "Xiaomi (MIUI Bloat/Ads)": [
        "com.miui.analytics",
        "com.miui.daemon",
        "com.miui.msa.global", # MIUI System Ads
        "com.mi.android.globalminusscreen", # App Vault
        "com.xiaomi.mipicks", # Mi GetApps
        "com.xiaomi.glgm", # Xiaomi Games
        "com.xiaomi.payment"
    ],
    "Microsoft Integration": [
        "com.microsoft.skydrive", # OneDrive
        "com.microsoft.office.officehubrow", # Office Hub
        "com.microsoft.office.outlook",
        "com.microsoft.todos"
    ]
}

class AppDebloaterPlugin(PluginBase):
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

    def run(self, device_manager: Any, adb: Any, config: Dict[str, Any]) -> None:
        serial = device_manager.get_current_device()
        if not serial:
            console.print("[red]Fehler: Kein Gerät verbunden.[/]")
            wait_for_enter()
            return

        while True:
            print_header("App-Debloater", "Unerwünschte Apps deinstallieren")
            
            console.print("[yellow]Scanne Gerät nach bekannten Bloatware-Paketen...[/]")
            installed = self.get_installed_packages(adb, serial)
            
            # Bloatware filtern, die tatsächlich auf dem Gerät existiert
            detected_bloat: Dict[str, List[str]] = {}
            flat_detected_list: List[tuple] = [] # List of (category, package)
            
            for category, packages in BLOATWARE_LIST.items():
                category_matches = [pkg for pkg in packages if pkg in installed]
                if category_matches:
                    detected_bloat[category] = category_matches
                    for pkg in category_matches:
                        flat_detected_list.append((category, pkg))
            
            if not flat_detected_list:
                console.print("\n[bold green][+] Keine bekannte Bloatware auf diesem Gerät gefunden![/]")
                console.print("1. Custom App deinstallieren")
                console.print("0. Zurück")
                choice = menu_prompt("Auswahl", range(0, 2))
                if choice == 0:
                    break
                elif choice == 1:
                    self.uninstall_custom(adb, serial)
                continue

            # Gefundene Bloatware als Tabelle anzeigen
            table = Table(title="Gefundene Bloatware-Pakete")
            table.add_column("Nr.", style="cyan", justify="right")
            table.add_column("Kategorie", style="magenta")
            table.add_column("Paketname", style="green")
            
            for idx, (cat, pkg) in enumerate(flat_detected_list, 1):
                table.add_row(str(idx), cat, pkg)
            
            console.print(table)
            
            console.print("\nOptionen:")
            console.print(f"1 bis {len(flat_detected_list)}: Einzelne App deinstallieren")
            console.print("A. Alle gefundenen Bloatware-Apps deinstallieren")
            console.print("R. Eine deinstallierte App wiederherstellen (Restore)")
            console.print("C. Custom App deinstallieren (Paketname eingeben)")
            console.print("0. Zurück")
            
            choice_str = console.input("[bold yellow]Auswahl[/]: ").strip()
            
            if choice_str == "0" or not choice_str:
                break
            elif choice_str.upper() == "A":
                if confirm("Möchtest du wirklich ALLE aufgelisteten Bloatware-Pakete deinstallieren?"):
                    for cat, pkg in flat_detected_list:
                        self.uninstall_package(adb, serial, pkg)
                    wait_for_enter()
            elif choice_str.upper() == "R":
                self.restore_package(adb, serial)
            elif choice_str.upper() == "C":
                self.uninstall_custom(adb, serial)
            else:
                try:
                    num = int(choice_str)
                    if 1 <= num <= len(flat_detected_list):
                        cat, pkg = flat_detected_list[num - 1]
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
        console.print(f"[cyan]Deinstalliere {pkg}...[/]")
        stdout, stderr, rc = adb.run_shell(f"pm uninstall -k --user 0 {pkg}", serial=serial)
        if rc == 0 and "Success" in stdout:
            console.print(f"[bold green][+] {pkg} erfolgreich entfernt![/]")
        else:
            console.print(f"[bold red][-] Fehler bei {pkg}: {stdout} {stderr}[/]")

    def uninstall_custom(self, adb: Any, serial: str) -> None:
        pkg = console.input("[yellow]Paketname der zu deinstallierenden App: [/]").strip()
        if pkg:
            self.uninstall_package(adb, serial, pkg)
            wait_for_enter()

    def restore_package(self, adb: Any, serial: str) -> None:
        """Stellt eine zuvor deinstallierte System-App wieder her."""
        pkg = console.input("[yellow]Paketname der wiederherzustellenden App: [/]").strip()
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
