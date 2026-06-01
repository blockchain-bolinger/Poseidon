import os
import shlex
from typing import Dict, Any
from core.plugin_base import PluginBase
from utils.ui_helpers import print_header, menu_prompt, wait_for_enter, confirm
from rich.console import Console

console = Console()

class AppLauncherPlugin(PluginBase):
    @property
    def name(self) -> str:
        return "🚀 App Launcher & Intent Sender"

    @property
    def description(self) -> str:
        return "Startet Apps, versteckte Activities, Services und sendet benutzerdefinierte Intents."

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def author(self) -> str:
        return "Poseidon Core"

    def run(self, device_manager: Any, adb: Any, config: Dict[str, Any]) -> None:
        serial = device_manager.get_current_device()
        if not serial:
            console.print("[red]Fehler: Kein Gerät verbunden.[/]")
            wait_for_enter()
            return

        while True:
            print_header("App Launcher & Intent Sender", "Entwickler- & Security-Werkzeuge")
            console.print("1. 📱 App normal starten (per Paketname)")
            console.print("2. 🔍 Spezifische Activity starten (am start)")
            console.print("3. 📡 Broadcast-Intent senden (am broadcast)")
            console.print("4. ⚙️ Hintergrund-Service starten (am startservice)")
            console.print("0. Zurück")
            
            choice = menu_prompt("Auswahl", range(0, 5))
            if choice == 0:
                break
            elif choice == 1:
                self.launch_app_monkey(adb, serial)
            elif choice == 2:
                self.launch_activity(adb, serial)
            elif choice == 3:
                self.send_broadcast(adb, serial)
            elif choice == 4:
                self.start_service(adb, serial)

    def launch_app_monkey(self, adb: Any, serial: str) -> None:
        pkg = console.input("[yellow]Paketname der App (z.B. com.android.settings): [/]").strip()
        if not pkg:
            return
        
        console.print(f"[cyan]Starte {pkg} über Monkey-Launcher...[/]")
        # Nutzen von monkey, um die App ohne explizite Activity-Kenntnis zu starten
        stdout, stderr, rc = adb.run_shell(f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1", serial=serial)
        if rc == 0 and "events injected" in stdout.lower():
            console.print(f"[bold green][+] App {pkg} erfolgreich gestartet![/]")
        else:
            console.print(f"[bold red][-] Starten fehlgeschlagen. Ist die App installiert? {stdout} {stderr}[/]")
        wait_for_enter()

    def launch_activity(self, adb: Any, serial: str) -> None:
        console.print("\nFormat: [bold]com.example/.MyActivity[/] oder komplett [bold]com.example/com.example.MyActivity[/]")
        act = console.input("[yellow]Activity-Name: [/]").strip()
        if not act:
            return
            
        extras = self.prompt_for_extras()
        cmd = f"am start -n {act} {extras}"
        console.print(f"[cyan]Führe aus: {cmd}...[/]")
        stdout, stderr, rc = adb.run_shell(cmd, serial=serial)
        console.print(f"[bold white]Ausgabe:[/]\n{stdout}")
        if stderr:
            console.print(f"[bold red]Fehler:[/]\n{stderr}")
        wait_for_enter()

    def send_broadcast(self, adb: Any, serial: str) -> None:
        action = console.input("[yellow]Broadcast Action (z.B. android.intent.action.BOOT_COMPLETED): [/]").strip()
        if not action:
            return
            
        extras = self.prompt_for_extras()
        cmd = f"am broadcast -a {action} {extras}"
        console.print(f"[cyan]Führe aus: {cmd}...[/]")
        stdout, stderr, rc = adb.run_shell(cmd, serial=serial)
        console.print(f"[bold white]Ausgabe:[/]\n{stdout}")
        if stderr:
            console.print(f"[bold red]Fehler:[/]\n{stderr}")
        wait_for_enter()

    def start_service(self, adb: Any, serial: str) -> None:
        service = console.input("[yellow]Service-Name (z.B. com.example/.MyService): [/]").strip()
        if not service:
            return
            
        extras = self.prompt_for_extras()
        cmd = f"am startservice -n {service} {extras}"
        console.print(f"[cyan]Führe aus: {cmd}...[/]")
        stdout, stderr, rc = adb.run_shell(cmd, serial=serial)
        console.print(f"[bold white]Ausgabe:[/]\n{stdout}")
        if stderr:
            console.print(f"[bold red]Fehler:[/]\n{stderr}")
        wait_for_enter()

    def prompt_for_extras(self) -> str:
        """Fragt optional Intent-Extras ab."""
        if not confirm("Möchtest du Intent-Extras (Parameter) hinzufügen?"):
            return ""
            
        extras_list = []
        while True:
            console.print("\n[bold]Extra-Typen:[/] [cyan]S[/]tring, [cyan]I[/]nt, [cyan]B[/]oolean, [cyan]X[/] (Fertig)")
            type_choice = console.input("[yellow]Typ wählen: [/]").strip().upper()
            if type_choice == "X" or not type_choice:
                break
                
            key = console.input("[yellow]Key (Name): [/]").strip()
            if not key:
                continue
                
            val = console.input("[yellow]Wert: [/]").strip()
            
            if type_choice == "S":
                extras_list.append(f"--es {key} {shlex.quote(val)}")
            elif type_choice == "I":
                try:
                    int_val = int(val)
                    extras_list.append(f"--ei {key} {int_val}")
                except ValueError:
                    console.print("[red]Ungültiger Integer-Wert.[/]")
            elif type_choice == "B":
                bool_val = "true" if val.lower() in ("true", "t", "1", "y") else "false"
                extras_list.append(f"--ez {key} {bool_val}")
                
        return " ".join(extras_list)
