import time
from typing import Dict, Any, List
from core.plugin_base import PluginBase
from utils.ui_helpers import print_header, menu_prompt, wait_for_enter, confirm
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel

console = Console()

class HardwareMonitorPlugin(PluginBase):
    @property
    def name(self) -> str:
        return "🌡️ Hardware Monitor & Stress Tester"

    @property
    def description(self) -> str:
        return "Überwacht CPU-Taktung, RAM, Temperaturen und führt CPU-Stresstests durch."

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def author(self) -> str:
        return "Poseidon Core"

    def get_num_cores(self, adb: Any, serial: str) -> int:
        """Ermittelt die Anzahl der CPU-Kerne des Geräts."""
        stdout, _, rc = adb.run_shell("ls -d /sys/devices/system/cpu/cpu[0-9]* 2>/dev/null", serial=serial)
        if rc == 0:
            lines = [l for l in stdout.splitlines() if l.strip()]
            return len(lines)
        return 8 # Fallback

    def get_mem_info(self, adb: Any, serial: str) -> Dict[str, float]:
        """Liest RAM-Daten aus /proc/meminfo aus (in MB)."""
        stdout, _, rc = adb.run_shell("cat /proc/meminfo", serial=serial)
        total = 0.0
        available = 0.0
        if rc == 0:
            for line in stdout.splitlines():
                if "MemTotal:" in line:
                    total = float(line.split()[1]) / 1024.0
                elif "MemAvailable:" in line:
                    available = float(line.split()[1]) / 1024.0
        used = total - available
        used_pct = (used / total) * 100.0 if total > 0 else 0.0
        return {"total": total, "used": used, "used_pct": used_pct}

    def get_battery_info(self, adb: Any, serial: str) -> Dict[str, Any]:
        """Holt Akku-Ladezustand und Temperatur."""
        stdout, _, rc = adb.run_shell("dumpsys battery", serial=serial)
        level = 0
        temp = 0.0
        if rc == 0:
            for line in stdout.splitlines():
                if "level:" in line:
                    try:
                        level = int(line.split(":")[-1].strip())
                    except: pass
                elif "temperature:" in line:
                    try:
                        temp = float(line.split(":")[-1].strip()) / 10.0
                    except: pass
        return {"level": level, "temp": temp}

    def get_cpu_freqs(self, adb: Any, serial: str, num_cores: int) -> List[str]:
        """Liest die aktuellen Frequenzen der einzelnen CPU-Kerne aus (in MHz)."""
        # Batch query for efficiency
        cmd_parts = []
        for i in range(num_cores):
            cmd_parts.append(f"cat /sys/devices/system/cpu/cpu{i}/cpufreq/scaling_cur_freq 2>/dev/null || echo 0")
        
        stdout, _, rc = adb.run_shell(" && ".join(cmd_parts), serial=serial)
        freqs = []
        if rc == 0:
            for line in stdout.splitlines():
                line = line.strip()
                if line:
                    try:
                        khz = int(line)
                        freqs.append(f"{khz / 1000.0:.0f} MHz" if khz > 0 else "Offline / Standby")
                    except:
                        freqs.append("Offline")
        
        # Padding in case output length mismatches
        while len(freqs) < num_cores:
            freqs.append("Offline")
        return freqs

    def generate_monitor_table(self, adb: Any, serial: str, num_cores: int, stress_active: bool, threads: int) -> Table:
        # Graphen & Daten holen
        mem = self.get_mem_info(adb, serial)
        bat = self.get_battery_info(adb, serial)
        freqs = self.get_cpu_freqs(adb, serial, num_cores)

        table = Table(title=f"Hardware-Status für [bold cyan]{serial}[/]", show_lines=True)
        table.add_column("Kategorie", style="magenta")
        table.add_column("Metrik / Wert", style="green")

        # Battery Row
        table.add_row("Akku", f"Ladung: {bat['level']}% | Temp: {bat['temp']}°C")
        
        # RAM Row
        table.add_row("Arbeitsspeicher (RAM)", f"Genutzt: {mem['used']:.0f} MB / {mem['total']:.0f} MB ({mem['used_pct']:.1f}%)")

        # Stress Test Status
        stress_status = f"[bold red]AKTIV ({threads} Threads)[/]" if stress_active else "[bold green]Inaktiv[/]"
        table.add_row("CPU-Stresstest", stress_status)

        # CPU Cores
        for i in range(num_cores):
            table.add_row(f"CPU Kern {i}", freqs[i])

        return table

    def run(self, device_manager: Any, adb: Any, config: Dict[str, Any]) -> None:
        serial = device_manager.get_current_device()
        if not serial:
            console.print("[red]Fehler: Kein Gerät verbunden.[/]")
            wait_for_enter()
            return

        num_cores = self.get_num_cores(adb, serial)
        stress_active = False
        stress_threads = 0

        while True:
            print_header("Hardware Monitor & Stress Tester", f"Kerne erkannt: {num_cores}")
            console.print("1. 📈 Live-Überwachung starten")
            console.print("2. ⚡ CPU-Stresstest STARTEN")
            console.print("3. 🛑 CPU-Stresstest STOPPEN")
            console.print("0. Zurück")
            
            choice = menu_prompt("Auswahl", range(0, 4))
            if choice == 0:
                # Beende Stresstest beim Verlassen
                if stress_active:
                    self.stop_stress_test(adb, serial)
                break
            elif choice == 1:
                self.run_live_monitor(adb, serial, num_cores, stress_active, stress_threads)
            elif choice == 2:
                if stress_active:
                    console.print("[yellow]Stresstest läuft bereits.[/]")
                    wait_for_enter()
                    continue
                try:
                    threads_input = console.input(f"[yellow]Wie viele Threads belasten? (1-{num_cores}, Standard: {num_cores}): [/]").strip()
                    threads = int(threads_input) if threads_input else num_cores
                    if 1 <= threads <= num_cores * 2:
                        self.start_stress_test(adb, serial, threads)
                        stress_active = True
                        stress_threads = threads
                        console.print(f"[bold red][+] Stresstest mit {threads} Threads gestartet![/]")
                    else:
                        console.print("[red]Ungültige Thread-Anzahl.[/]")
                except ValueError:
                    console.print("[red]Ungültige Eingabe.[/]")
                wait_for_enter()
            elif choice == 3:
                if not stress_active:
                    console.print("[yellow]Kein Stresstest aktiv.[/]")
                else:
                    self.stop_stress_test(adb, serial)
                    stress_active = False
                    stress_threads = 0
                    console.print("[bold green][+] Stresstest erfolgreich gestoppt.[/]")
                wait_for_enter()

    def start_stress_test(self, adb: Any, serial: str, threads: int) -> None:
        """Startet CPU-belastende Prozesse im Hintergrund auf dem Android-Gerät."""
        # yes > /dev/null erzeugt 100% Last auf einem CPU-Kern
        for _ in range(threads):
            adb.run_shell("yes > /dev/null &", serial=serial)

    def stop_stress_test(self, adb: Any, serial: str) -> None:
        """Beendet alle stressauslösenden Prozesse auf dem Gerät."""
        adb.run_shell("pkill -9 yes", serial=serial)
        adb.run_shell("killall yes", serial=serial)

    def run_live_monitor(self, adb: Any, serial: str, num_cores: int, stress_active: bool, threads: int) -> None:
        console.print("[cyan]Starte Live-Hardwareüberwachung. Drücke Strg+C zum Beenden...[/]")
        time.sleep(1.0)
        
        try:
            with Live(self.generate_monitor_table(adb, serial, num_cores, stress_active, threads), refresh_per_second=1) as live:
                while True:
                    time.sleep(1.0)
                    live.update(self.generate_monitor_table(adb, serial, num_cores, stress_active, threads))
        except KeyboardInterrupt:
            console.print("\n[yellow]Überwachung gestoppt.[/]")
            wait_for_enter()
