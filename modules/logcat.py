import re
import time
from rich.console import Console
from rich.text import Text
from utils.ui_helpers import clear_screen, print_header, menu_prompt, wait_for_enter, confirm
from utils.file_utils import get_timestamp, save_file

console = Console()

def show_menu(device_manager, adb):
    while True:
        clear_screen()
        print_header("Logcat Viewer", "System-Logs anzeigen")
        print("1. 📋 Logcat live anzeigen (Farbcodiert)")
        print("2. 💾 Logcat in Datei speichern")
        print("3. 🔍 Nach Schlagwort filtern")
        print("4. 📊 Logcat nach Priorität filtern")
        print("5. 🧹 Logcat löschen")
        print("0. Zurück")

        choice = menu_prompt("Option", range(0, 6))

        if choice == 0:
            break
        elif choice == 1:
            logcat_live(device_manager, adb)
        elif choice == 2:
            logcat_save(device_manager, adb)
        elif choice == 3:
            logcat_filter(device_manager, adb)
        elif choice == 4:
            logcat_priority(device_manager, adb)
        elif choice == 5:
            logcat_clear(device_manager, adb)

def logcat_live(device_manager, adb):
    serial = device_manager.get_current_device()
    if not serial:
        return
    
    console.print("[bold yellow]Starte farbcodiertes Logcat live Streaming... (Strg+C zum Beenden)[/]")
    time.sleep(1.0) # Kurze Pause, damit Hinweistext lesbar ist
    
    try:
        # Verwende threadtime für strukturiertere Timestamps und PIDs
        for line in adb.run_shell_stream("logcat -v threadtime", serial, max_duration_s=300, max_lines=5000, heartbeat="logcat_live"):
            line = line.strip()
            if not line:
                continue
                
            # Pattern 1: threadtime (z. B. "06-01 14:54:40.123  1234  5678 I ActivityManager: Displayed ...")
            threadtime_match = re.match(r"^(\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d{3})\s+(\d+)\s+(\d+)\s([VDIWEF])\s+(.*?):\s(.*)$", line)
            if threadtime_match:
                time_str, pid, tid, level, tag, msg = threadtime_match.groups()
                level_styles = {
                    'V': ('cyan', 'VERBOSE'),
                    'D': ('blue', 'DEBUG'),
                    'I': ('green', 'INFO'),
                    'W': ('yellow', 'WARN'),
                    'E': ('red', 'ERROR'),
                    'F': ('bold red reverse', 'FATAL'),
                }
                style_color, level_name = level_styles.get(level, ('white', 'UNKNOWN'))
                
                text = Text()
                text.append(f"{time_str} ", style="dim")
                text.append(f"{level_name:<7} ", style=style_color)
                text.append(f"[{tag.strip()}] ", style="magenta")
                text.append(msg)
                console.print(text)
                continue

            # Pattern 2: brief (z. B. "I/ActivityManager( 1234): Displayed ...")
            brief_match = re.match(r"^([VDIWEF])\/(.*?)\(\s*(\d+)\):\s(.*)$", line)
            if brief_match:
                level, tag, pid, msg = brief_match.groups()
                level_styles = {
                    'V': ('cyan', 'VERBOSE'),
                    'D': ('blue', 'DEBUG'),
                    'I': ('green', 'INFO'),
                    'W': ('yellow', 'WARN'),
                    'E': ('red', 'ERROR'),
                    'F': ('bold red reverse', 'FATAL'),
                }
                style_color, level_name = level_styles.get(level, ('white', 'UNKNOWN'))
                
                text = Text()
                text.append(f"{level_name:<7} ", style=style_color)
                text.append(f"[{tag.strip()}] ", style="magenta")
                text.append(msg)
                console.print(text)
                continue
                
            # Fallback: Einfaches Highlighten per Substring
            fallback_color = "white"
            if " E/" in line or line.startswith("E/"):
                fallback_color = "red"
            elif " W/" in line or line.startswith("W/"):
                fallback_color = "yellow"
            elif " I/" in line or line.startswith("I/"):
                fallback_color = "green"
            elif " D/" in line or line.startswith("D/"):
                fallback_color = "blue"
            elif " V/" in line or line.startswith("V/"):
                fallback_color = "cyan"
            elif " F/" in line or line.startswith("F/"):
                fallback_color = "bold red"
                
            console.print(line, style=fallback_color)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Live-Logcat gestoppt.[/]")
    wait_for_enter()

def logcat_save(device_manager, adb):
    serial = device_manager.get_current_device()
    if not serial:
        return
    filename = f"logcat_{get_timestamp()}.txt"
    out, _, _ = adb.run("logcat -d", serial)
    save_file(out, filename, "logs")
    print(f"Logcat gespeichert unter: logs/{filename}")
    wait_for_enter()

def logcat_filter(device_manager, adb):
    serial = device_manager.get_current_device()
    if not serial:
        return
    tag = input("Nach welchem Schlagwort filtern? ")
    if not tag:
        return
    out, _, _ = adb.run(f"logcat -d | grep -i {tag}", serial)
    print(out)
    wait_for_enter()

def logcat_priority(device_manager, adb):
    serial = device_manager.get_current_device()
    if not serial:
        return
    print("Priorität: V(erbose), D(ebug), I(nfo), W(arn), E(rror), F(atal)")
    prio = input("Buchstabe: ").upper()
    if prio not in "VDIWEF":
        print("Ungültig.")
        return
    out, _, _ = adb.run(f"logcat -d *:{prio}", serial)
    print(out)
    wait_for_enter()

def logcat_clear(device_manager, adb):
    serial = device_manager.get_current_device()
    if not serial:
        return
    adb.run("logcat -c", serial)
    print("Logcat gelöscht.")
    wait_for_enter()