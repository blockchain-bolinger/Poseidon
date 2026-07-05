import re
from typing import Dict, Any, Optional
from core.plugin_base import PluginBase
from utils.ui_helpers import print_header, wait_for_enter
from rich.console import Console

console = Console()

class WifiADBPlugin(PluginBase):
    @property
    def name(self) -> str:
        return "📶 Wi-Fi ADB Automator (mit QR-Code)"

    @property
    def description(self) -> str:
        return "Schaltet ADB auf Port 5555 um und generiert Verbindungs-QR-Codes im Terminal."

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def author(self) -> str:
        return "Poseidon Core"

    def get_device_ip(self, adb: Any, serial: str) -> Optional[str]:
        """Ermittelt die IP-Adresse des Gerätes im wlan0-Netzwerk."""
        # 1. Option: dhcp.wlan0.ipaddress Eigenschaft
        ip = adb.get_device_property("dhcp.wlan0.ipaddress", serial).strip()
        if ip and re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
            return ip
            
        # 2. Option: ip addr show wlan0 auslesen
        stdout, _, rc = adb.run_shell("ip addr show wlan0 2>/dev/null", serial=serial)
        if rc == 0:
            match = re.search(r"inet\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", stdout)
            if match:
                return match.group(1)

        # 3. Option: ifconfig wlan0 auslesen (ältere Android-Geräte)
        stdout, _, rc = adb.run_shell("ifconfig wlan0 2>/dev/null", serial=serial)
        if rc == 0:
            match = re.search(r"inet addr:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", stdout)
            if match:
                return match.group(1)
                
        # 4. Option: Globale ip route auslesen
        stdout, _, rc = adb.run_shell("ip route 2>/dev/null", serial=serial)
        if rc == 0:
            match = re.search(r"src\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", stdout)
            if match:
                return match.group(1)

        return None

    def run(self, device_manager: Any, adb: Any, config: Dict[str, Any]) -> None:
        serial = device_manager.get_current_device()
        if not serial:
            console.print("[red]Fehler: Kein Gerät verbunden.[/]")
            wait_for_enter()
            return

        print_header("Wi-Fi ADB Automator", "Kabellose Verbindung einrichten")
        
        console.print("[cyan]Ermittle Geräte-IP-Adresse...[/]")
        ip = self.get_device_ip(adb, serial)
        
        if not ip:
            console.print("[bold red][-] IP-Adresse des Geräts konnte nicht ermittelt werden.[/]")
            console.print("[yellow]Hinweis: Stellen Sie sicher, dass das Handy mit demselben WLAN wie Ihr PC verbunden ist.[/]")
            wait_for_enter()
            return

        console.print(f"[bold green][+] Gefundene IP-Adresse: {ip}[/]")
        console.print("[cyan]Schalte ADB-Daemon auf dem Gerät in den Netzwerkmodus (Port 5555)...[/]")
        
        # adb tcpip 5555 ausführen (muss per adb-Befehl und nicht shell aufgerufen werden)
        stdout, stderr, rc = adb.run("tcpip 5555", serial=serial)
        
        if rc == 0:
            console.print("[bold green][+] ADB-Daemon lauscht nun auf Port 5555![/]")
            console.print("\nDu kannst das USB-Kabel jetzt abziehen und dich wie folgt verbinden:")
            console.print(f"👉 [bold yellow]adb connect {ip}:5555[/]\n")
            
            # QR-Code generieren und im Terminal anzeigen
            try:
                import qrcode
                console.print("[cyan]Generiere QR-Code für einfache Freigabe / Scan:[/]")
                
                qr = qrcode.QRCode(version=1, box_size=1, border=2)
                qr.add_data(f"adb connect {ip}:5555")
                qr.make(fit=True)
                
                # ASCII/ANSI QR-Code im Terminal zeichnen
                qr.print_tty()
                
            except Exception as e:
                console.print(f"[dim](QR-Code konnte nicht gedruckt werden: {e})[/dim]")
                
        else:
            console.print(f"[bold red][-] Umschalten fehlgeschlagen: {stdout} {stderr}[/]")

        wait_for_enter()
