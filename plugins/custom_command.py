"""
Plugin: Benutzerdefinierten ADB-Befehl ausführen
"""
from utils.ui_helpers import wait_for_enter
from utils.cli_safety import sanitize_device_input

def setup():
    return ("⚙️ Benutzerdefinierten ADB-Befehl ausführen", run)

def run(device_manager, adb, config):
    serial = device_manager.get_current_device()
    if not serial:
        print("Kein Gerät verbunden.")
        wait_for_enter()
        return

    cmd = input("ADB-Befehl (ohne 'adb -s <serial>'): ")
    if not cmd:
        return
    safe_cmd = sanitize_device_input("custom_command", cmd)
    if not safe_cmd:
        print("Ungültiger Befehl.")
        wait_for_enter()
        return
    stdout, stderr, rc = adb.run(safe_cmd, serial)
    print("--- Ausgabe ---")
    print(stdout)
    if stderr:
        print("--- Fehler ---")
        print(stderr)
    wait_for_enter()
