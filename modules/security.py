import time
import shlex
import subprocess
import re
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from utils.ui_helpers import print_header, menu_prompt, wait_for_enter, confirm
from utils.decorators import require_device
from utils.file_utils import get_timestamp
from modules.advanced_ops import AdvancedOps

console = Console()

@require_device
def show_menu(device_manager, adb):
    serial = device_manager.get_current_device()
    ops = AdvancedOps(adb, serial)
    
    while True:
        print_header("ADVANCED SECURITY & OPS", "Underground Mode")
        table = Table(title="Select Option")
        table.add_column("ID", style="cyan")
        table.add_column("Action", style="magenta")
        
        menu_items = [
            ("1", "👻 Ghost Mode (Cleanup)"),
            ("2", "🔍 UI Tree Dump"),
            ("3", "🕵️ Hidden Intents Scan"),
            ("4", "🛡️ Security Audit"),
            ("5", "📜 Kernel Sniffer (dmesg)"),
            ("6", "🆔 Set Identity (Root)"),
            ("7", "📹 Auto Trigger Recorder"),
            ("0", "Exit")
        ]
        
        for id, name in menu_items:
            table.add_row(id, name)
        console.print(table)

        choice = menu_prompt("Option", range(0, 8))
        if choice == 0: break
        elif choice == 1: ops.ghost_clean(); wait_for_enter()
        elif choice == 2: ops.dump_ui_tree(); wait_for_enter()
        elif choice == 3:
            pkg = console.input("[yellow]Package: [/]")
            if pkg: ops.list_hidden_intents(pkg); wait_for_enter()
        elif choice == 4:
            run_security_audit(adb, serial)
        elif choice == 5:
            console.print("[cyan]Sniffing Kernel Events... (Ctrl+C to stop)[/]")
            try:
                for line in adb.run_shell_stream("dmesg -w", serial, max_duration_s=120, max_lines=2000, heartbeat="dmesg_sniffer"):
                    console.print(line.strip())
            except KeyboardInterrupt:
                console.print("\n[yellow]Sniffer gestoppt.[/]")
        elif choice == 6:
            model = console.input("[yellow]New Model: [/]")
            brand = console.input("[yellow]New Brand: [/]")
            ops.set_device_identity(model, brand); wait_for_enter()
        elif choice == 7:
            run_auto_recorder(adb, serial)
            wait_for_enter()

def run_security_audit(adb, serial):
    console.print("[bold yellow]Running Security Audit...[/]")
    out, _, _ = adb.run_shell("pm list permissions -d -g", serial)
    
    table = Table(title="Dangerous Permissions Found")
    table.add_column("Permission")
    for line in out.splitlines()[:15]:
        table.add_row(line)
    console.print(table)
    
    with open("logs/audit.log", "a") as f:
        f.write("[SECURITY_AUDIT] Scan run\n")
    wait_for_enter()

def run_auto_recorder(adb, serial):
    console.print("\n[bold yellow]=== Auto Trigger-Recorder ===[/]")
    pkg = console.input("[yellow]Welches App-Paket soll überwacht werden? (z.B. com.android.settings): [/]").strip()
    if not pkg:
        return
        
    duration = 15
    try:
        duration_input = console.input("[yellow]Aufnahmedauer in Sekunden [Standard: 15s]: [/]").strip()
        if duration_input:
            duration = int(duration_input)
    except ValueError:
        console.print("[red]Ungültige Eingabe, benutze 15s.[/]")
        
    console.print(f"[cyan]Warte darauf, dass {pkg} geöffnet wird... (Strg+C zum Abbrechen)[/]")
    
    try:
        while True:
            # Aktuellen Fokus auf dem Gerät prüfen
            out, _, _ = adb.run_shell("dumpsys window windows | grep -E 'mCurrentFocus'", serial)
            if pkg in out:
                console.print(f"\n[bold green][+] {pkg} im Vordergrund erkannt! Starte screenrecord...[/]")
                
                device_file = "/sdcard/poseidon_trigger_record.mp4"
                
                # Befehl für adb shell aufbauen
                full_cmd = adb._build_cmd(f"shell screenrecord --time-limit {duration} {device_file}", serial)
                cmd_list = shlex.split(full_cmd)
                
                process = subprocess.Popen(
                    cmd_list,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                console.print(f"[cyan]Aufnahme läuft für max. {duration}s. Bitte am Gerät interagieren...[/]")
                
                started = time.time()
                try:
                    while time.time() - started < duration:
                        if process.poll() is not None:
                            break
                        time.sleep(0.5)
                except KeyboardInterrupt:
                    console.print("\n[yellow][!] Aufnahme vorzeitig gestoppt.[/]")
                    process.terminate()
                    process.wait()
                    adb.run_shell("pkill -INT screenrecord", serial)
                    time.sleep(1)
                
                process.wait()
                
                local_filename = f"trigger_record_{pkg}_{get_timestamp()}.mp4"
                local_path = f"./backups/{local_filename}"
                console.print("[cyan]Übertrage Videodatei zum PC...[/]")
                
                pull_out, pull_err, pull_rc = adb.run(f"pull {device_file} {local_path}", serial)
                if pull_rc == 0:
                    console.print(f"[bold green][+] Video erfolgreich gespeichert unter: {local_path}[/]")
                    adb.run_shell(f"rm {device_file}", serial)
                else:
                    console.print(f"[bold red][-] Pull-Fehler: {pull_err}[/]")
                break
                
            time.sleep(1.0)
    except KeyboardInterrupt:
        console.print("\n[yellow]Überwachung abgebrochen.[/]")
