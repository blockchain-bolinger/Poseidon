from __future__ import annotations

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

from core.logger import logger
from core.plugin_base import PluginBase
from plugins.artifact_library import combined_payloads, discover_apks
from plugins.mobile_toolbox import (
    OBJECTION_PRESETS,
    FRIDA_PROCESS_PRESETS,
    command_available,
    command_display,
    mobsf_upload_and_scan,
    normalize_command,
    open_url,
    run_command,
    spawn_command,
)
from utils.ui_helpers import confirm, menu_prompt, print_header, wait_for_enter


class PluginManager:
    """Verwaltet alle Plugins und deren Menüpunkte."""

    def __init__(self, plugin_dir: str = "plugins") -> None:
        self.plugin_dir = Path(__file__).parent.parent / plugin_dir
        self.plugins: List[Any] = []
        self.menu_entries: List[Tuple[str, Any, str]] = []

    def discover_plugins(self) -> None:
        """Durchsucht den Plugin-Ordner nach gültigen Plugins."""
        if not self.plugin_dir.exists():
            self.plugin_dir.mkdir(exist_ok=True)
            init_file = self.plugin_dir / "__init__.py"
            if not init_file.exists():
                init_file.touch()
            return

        logger.info(f"Suche nach Plugins in {self.plugin_dir}...")
        for _, name, _ in pkgutil.iter_modules([str(self.plugin_dir)]):
            try:
                module = importlib.import_module(f"plugins.{name}")

                plugin_classes = [
                    cls
                    for _, cls in inspect.getmembers(module, inspect.isclass)
                    if issubclass(cls, PluginBase) and cls is not PluginBase
                ]

                if plugin_classes:
                    for cls in plugin_classes:
                        instance = cls()
                        self.plugins.append(instance)
                        self.menu_entries.append((instance.name, instance.run, instance.description))
                        logger.info(f"[Plugin] Geladen (Klasse): {instance.name} v{instance.version}")
                elif hasattr(module, "setup"):
                    plugin_info = module.setup()
                    if isinstance(plugin_info, tuple) and len(plugin_info) >= 2:
                        titel, callback = plugin_info[0], plugin_info[1]
                        desc = plugin_info[2] if len(plugin_info) > 2 else ""
                        self.plugins.append(module)
                        self.menu_entries.append((titel, callback, desc))
                        logger.info(f"[Plugin] Geladen (Legacy): {titel}")
            except Exception as e:
                logger.error(f"[Plugin] Fehler beim Laden von {name}: {e}")

    def show_plugin_menu(self, device_manager, adb, config) -> None:
        """Zeigt den Analyse-Hub an."""
        while True:
            print_header("Analyse-Hub", "Alt + Neu zusammengeführt")
            print("═" * 60)
            print("1. Legacy / Device Actions")
            print("2. Mobile Analysis – Android")
            print("3. Mobile Analysis – iOS")
            print("4. Reports & Export")
            print("0. Zurück")

            choice = menu_prompt("Bereich wählen", range(0, 5))
            if choice == 0:
                return
            if choice == 1:
                self._show_legacy_menu(device_manager, adb, config)
            elif choice == 2:
                self._show_android_menu(device_manager, adb, config)
            elif choice == 3:
                self._show_ios_menu(device_manager, adb, config)
            elif choice == 4:
                self._show_reports_menu()

    def _show_legacy_menu(self, device_manager, adb, config) -> None:
        if not self.menu_entries:
            print("Keine Plugins installiert.")
            wait_for_enter()
            return

        while True:
            print_header("Legacy / Device Actions", "Bestehende Plugins und direkte Shortcuts")
            for i, (titel, _, desc) in enumerate(self.menu_entries, 1):
                entry = f"{i}. {titel}"
                if desc:
                    entry += f" - {desc}"
                print(entry)
            print("0. Zurück")

            choice = menu_prompt("Plugin wählen", range(0, len(self.menu_entries) + 1))
            if choice == 0:
                return

            callback = self.menu_entries[choice - 1][1]
            titel = self.menu_entries[choice - 1][0]
            plugin = self.plugins[choice - 1]

            if self._is_destructive(plugin) and not confirm(
                f"Dieses Plugin kann destruktive Aktionen ausführen: '{titel}'. Trotzdem fortsetzen?"
            ):
                continue

            logger.info(f"Plugin wird ausgeführt: {titel}")
            try:
                callback(device_manager, adb, config)
            except Exception as e:
                logger.error(f"Kritischer Fehler im Plugin {titel}: {e}")
                print(f"Fehler im Plugin: {e}")
                wait_for_enter()

    def _show_android_menu(self, device_manager, adb, config) -> None:
        while True:
            print_header("Mobile Analysis – Android", "Workflow statt Tool-Liste")
            print("1. Static Analysis")
            print("2. Runtime Analysis")
            print("3. Network Analysis")
            print("4. Native / Binary Analysis")
            print("5. APK Inventory & Payload Templates")
            print("0. Zurück")

            choice = menu_prompt("Android-Bereich wählen", range(0, 6))
            if choice == 0:
                return
            if choice == 1:
                self._android_static_menu(config)
            elif choice == 2:
                self._android_runtime_menu(device_manager, adb, config)
            elif choice == 3:
                self._android_network_menu(device_manager, adb, config)
            elif choice == 4:
                self._android_native_menu(config)
            elif choice == 5:
                self._show_android_assets()

    def _show_ios_menu(self, device_manager, adb, config) -> None:
        while True:
            print_header("IOS · MOBILE ANALYSIS", "Workflow statt Tool-Liste")
            print("═" * 60)
            print("1. Static Analysis")
            print("2. Runtime Analysis")
            print("3. Network Analysis")
            print("4. Native / Binary Analysis")
            print("0. Zurück")

            choice = menu_prompt("iOS-Bereich wählen", range(0, 5))
            if choice == 0:
                return
            if choice == 1:
                self._show_reference_panel(
                    "iOS Static Analysis",
                    ["MobSF", "Binary-Inspektion", "Strings", "Info.plist", "Entitlements"],
                )
            elif choice == 2:
                self._ios_runtime_menu(config)
            elif choice == 3:
                self._ios_network_menu(config)
            elif choice == 4:
                self._show_reference_panel(
                    "iOS Native / Binary Analysis",
                    ["Ghidra", "Binary-Analyse", "Frameworks / Libraries", "Symbols / Strings / Mach-O"],
                )

    def _show_reports_menu(self) -> None:
        while True:
            print_header("Reports & Export", "Zusammenführung der Analyseergebnisse")
            print("1. Quick Report")
            print("2. Full Report")
            print("3. JSON / Markdown Export")
            print("4. Findings Bundle")
            print("0. Zurück")

            choice = menu_prompt("Report-Option wählen", range(0, 5))
            if choice == 0:
                return
            if choice == 1:
                self._show_reference_panel("Quick Report", ["Kurzstatus", "Top Findings", "Risiko", "Empfohlene nächste Schritte"])
            elif choice == 2:
                self._show_reference_panel("Full Report", ["Kontext", "Artefakte", "Analyse", "Bewertung", "Empfehlungen"])
            elif choice == 3:
                self._show_reference_panel("Export", ["JSON", "Markdown", "Screenshots", "Logs", "Anhänge"])
            elif choice == 4:
                self._show_reference_panel("Findings Bundle", ["Befunde bündeln", "Artefakte zusammenführen", "Team-Weitergabe vorbereiten"])

    def _android_static_menu(self, config) -> None:
        while True:
            print_header("ANDROID · STATIC", "MobSF • JADX • apktool")
            print("1. MobSF APK Upload & Scan")
            print("2. MobSF Dashboard öffnen")
            print("3. JADX GUI auf lokale APK starten")
            print("4. APK mit apktool dekodieren")
            print("5. APK- & Payload-Inventur anzeigen")
            print("0. Zurück")
            choice = menu_prompt("Static-Option", range(0, 6))
            if choice == 0:
                return
            if choice == 1:
                apk = self._choose_local_apk()
                if not apk:
                    continue
                api_key = str(config["global"].get("mobsf_api_key", "")).strip()
                if not api_key:
                    print("MobSF API-Key fehlt. Bitte in den Einstellungen setzen.")
                    wait_for_enter()
                    continue
                url = str(config["global"].get("mobsf_url", "http://127.0.0.1:8000")).strip()
                timeout = int(config["global"].get("mobsf_timeout", 120))
                try:
                    result = mobsf_upload_and_scan(apk, url, api_key, timeout=timeout)
                except Exception as exc:
                    print(f"MobSF-Fehler: {exc}")
                    wait_for_enter()
                    continue
                upload = result.get("upload", {})
                scan = result.get("scan", {})
                print(f"MobSF Upload OK: {upload.get('file_name') or upload.get('filename') or apk}")
                print(f"Hash: {result.get('hash')}")
                if isinstance(scan, dict):
                    for key in ("scan_type", "app_name", "version", "status", "scan", "url"):
                        if key in scan and scan[key]:
                            print(f"{key}: {scan[key]}")
                print(f"Upload-Endpoint: {result.get('upload_url')}")
                print(f"Scan-Endpoint: {result.get('scan_url')}")
                wait_for_enter()
            elif choice == 2:
                url = str(config["global"].get("mobsf_url", "http://127.0.0.1:8000")).strip()
                if not open_url(url):
                    print(f"MobSF-URL konnte nicht geöffnet werden: {url}")
                else:
                    print(f"MobSF geöffnet: {url}")
                wait_for_enter()
            elif choice == 3:
                apk = self._choose_local_apk()
                if not apk:
                    continue
                self._spawn_named_tool(config["global"].get("jadx_gui_cmd", "jadx-gui"), [apk])
            elif choice == 4:
                apk = self._choose_local_apk()
                if not apk:
                    continue
                out_dir = input("Output-Verzeichnis [default: ./backups/apktool_out]: ").strip() or "./backups/apktool_out"
                self._run_named_tool(
                    config["global"].get("apktool_cmd", "apktool"),
                    ["d", "-f", apk, "-o", out_dir],
                )
            elif choice == 5:
                self._show_android_assets()

    def _android_runtime_menu(self, device_manager, adb, config) -> None:
        while True:
            print_header("ANDROID · RUNTIME", "Frida • Objection • Live Checks")
            print("1. Frida Discovery (frida-ps)")
            print("2. Frida Presets")
            print("3. Objection Presets")
            print("4. frida-server Status prüfen")
            print("0. Zurück")
            choice = menu_prompt("Runtime-Option", range(0, 5))
            if choice == 0:
                return
            if choice == 1:
                self._run_named_tool(config["global"].get("frida_cmd", "frida-ps"), ["-U"])
            elif choice == 2:
                self._frida_presets_menu(config)
            elif choice == 3:
                self._objection_presets_menu(config)
            elif choice == 4:
                self._check_frida_server(device_manager, adb)

    def _frida_presets_menu(self, config) -> None:
        while True:
            print_header("Frida Presets", "Schnelle Startpunkte für Runtime-Analyse")
            for idx, (name, _, description) in enumerate(FRIDA_PROCESS_PRESETS, 1):
                print(f"{idx}. {name} - {description}")
            print("0. Zurück")
            choice = menu_prompt("Preset wählen", range(0, len(FRIDA_PROCESS_PRESETS) + 1))
            if choice == 0:
                return
            preset_name, preset_args, _ = FRIDA_PROCESS_PRESETS[choice - 1]
            if preset_name == "Discovery":
                self._run_named_tool(config["global"].get("frida_cmd", "frida-ps"), preset_args)
            elif preset_name == "Spawn attach":
                target = input("Package/Binary für frida-trace: ").strip()
                if target:
                    trace_cmd = config["global"].get("frida_trace_cmd", "frida-trace")
                    self._run_named_tool(trace_cmd, ["-U", "-f", target, "--no-pause"])
            elif preset_name == "Attach target":
                target = input("Process-Name für frida-trace: ").strip()
                if target:
                    trace_cmd = config["global"].get("frida_trace_cmd", "frida-trace")
                    self._run_named_tool(trace_cmd, ["-U", "-n", target])

    def _objection_presets_menu(self, config) -> None:
        while True:
            print_header("Objection Presets", "Schnelle Explore-/Inspect-Workflows")
            for idx, (name, _, description) in enumerate(OBJECTION_PRESETS, 1):
                print(f"{idx}. {name} - {description}")
            print("0. Zurück")
            choice = menu_prompt("Preset wählen", range(0, len(OBJECTION_PRESETS) + 1))
            if choice == 0:
                return
            preset_name, _, _ = OBJECTION_PRESETS[choice - 1]
            objection_cmd = config["global"].get("objection_cmd", "objection")
            if preset_name == "Explore":
                target = input("Package-Name: ").strip()
                if target:
                    self._run_named_tool(objection_cmd, ["-g", target, "explore"])
            elif preset_name == "Run command":
                target = input("Package-Name: ").strip()
                if not target:
                    continue
                objection_action = input("Objection-Command (z.B. android hooking list activities): ").strip()
                if objection_action:
                    self._run_named_tool(objection_cmd, ["-g", target, "run", objection_action])
            elif preset_name == "Device info":
                target = input("Package-Name: ").strip()
                if target:
                    self._run_named_tool(objection_cmd, ["-g", target, "device", "info"])

    def _android_network_menu(self, device_manager, adb, config) -> None:
        while True:
            print_header("Android Network Analysis", "Proxy, Capture, Replay")
            print("1. mitmproxy starten")
            print("2. Burp starten")
            print("3. ADB Proxy setzen")
            print("4. ADB Proxy deaktivieren")
            print("0. Zurück")
            choice = menu_prompt("Network-Option", range(0, 5))
            if choice == 0:
                return
            if choice == 1:
                self._spawn_named_tool(config["global"].get("mitmproxy_cmd", "mitmproxy"), [])
            elif choice == 2:
                self._spawn_named_tool(config["global"].get("burp_cmd", "burp"), [])
            elif choice == 3:
                self._set_adb_proxy(device_manager, adb)
            elif choice == 4:
                self._disable_adb_proxy(device_manager, adb)

    def _android_native_menu(self, config) -> None:
        while True:
            print_header("Android Native / Binary Analysis", "Ghidra & String/Library Checks")
            print("1. Ghidra starten")
            print("2. strings auf lokaler Datei ausführen")
            print("3. file auf lokaler Datei ausführen")
            print("0. Zurück")
            choice = menu_prompt("Native-Option", range(0, 4))
            if choice == 0:
                return
            if choice == 1:
                self._spawn_named_tool(config["global"].get("ghidra_cmd", "ghidraRun"), [])
            elif choice == 2:
                self._strings_or_file("strings")
            elif choice == 3:
                self._strings_or_file("file")

    def _ios_runtime_menu(self, config) -> None:
        while True:
            print_header("IOS · RUNTIME", "Frida • Objection")
            print("1. Frida Discovery (frida-ps)")
            print("2. Frida Presets")
            print("3. Objection Presets")
            print("0. Zurück")
            choice = menu_prompt("Runtime-Option", range(0, 4))
            if choice == 0:
                return
            if choice == 1:
                self._run_named_tool(config["global"].get("frida_cmd", "frida-ps"), ["-U"])
            elif choice == 2:
                self._frida_presets_menu(config)
            elif choice == 3:
                self._objection_presets_menu(config)

    def _ios_network_menu(self, config) -> None:
        while True:
            print_header("iOS Network Analysis", "Proxy & Capture")
            print("1. mitmproxy starten")
            print("2. Burp starten")
            print("0. Zurück")
            choice = menu_prompt("Network-Option", range(0, 3))
            if choice == 0:
                return
            if choice == 1:
                self._spawn_named_tool(config["global"].get("mitmproxy_cmd", "mitmproxy"), [])
            elif choice == 2:
                self._spawn_named_tool(config["global"].get("burp_cmd", "burp"), [])

    def _show_android_assets(self) -> None:
        apks = discover_apks()
        payloads = combined_payloads()
        print_header("APK Inventory & Payload Templates", "Lokale Assets aus data/ und assets/")
        if apks:
            print("Lokale APKs:")
            for idx, apk in enumerate(apks, 1):
                print(f"  {idx}. {apk}")
        else:
            print("Lokale APKs: keine gefunden.")

        print("")
        print("Payload-Templates:")
        for idx, payload in enumerate(payloads, 1):
            print(f"  {idx}. [{payload.category}] {payload.title} - {payload.description}")
        print("")
        print("Hinweis: Editierbare Assets liegen in data/apks/ und data/payloads/.")
        wait_for_enter()

    def _choose_local_apk(self) -> str | None:
        apks = discover_apks()
        if apks:
            print("Verfügbare lokale APKs:")
            for idx, apk in enumerate(apks, 1):
                print(f"  {idx}. {apk}")
            print("  0. Eigenen Pfad eingeben")
            choice = input("APK wählen: ").strip()
            if choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(apks):
                    return str(apks[idx - 1])
            path = input("APK-Pfad: ").strip()
            return path or None
        path = input("APK-Pfad: ").strip()
        return path or None

    def _run_named_tool(self, tool: str, args: Sequence[str]) -> None:
        if not command_available(tool):
            print(f"Tool nicht gefunden: {tool}")
            wait_for_enter()
            return
        command = normalize_command(tool) + [str(arg) for arg in args]
        try:
            result = run_command(command, timeout=900)
        except Exception as exc:
            print(f"Fehler beim Ausführen von {command_display(command)}: {exc}")
            wait_for_enter()
            return

        print(f"\n== {command_display(command)} ==")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print(f"Returncode: {result.returncode}")
        wait_for_enter()

    def _spawn_named_tool(self, tool: str, args: Sequence[str]) -> None:
        if not command_available(tool):
            print(f"Tool nicht gefunden: {tool}")
            wait_for_enter()
            return
        command = normalize_command(tool) + [str(arg) for arg in args]
        try:
            spawn_command(command)
            print(f"Gestartet: {command_display(command)}")
        except Exception as exc:
            print(f"Fehler beim Starten von {command_display(command)}: {exc}")
        wait_for_enter()

    def _strings_or_file(self, tool: str) -> None:
        path = input("Dateipfad: ").strip()
        if not path:
            return
        if not Path(path).exists():
            print(f"Datei nicht gefunden: {path}")
            wait_for_enter()
            return
        self._run_named_tool(tool, [path])

    def _check_frida_server(self, device_manager, adb) -> None:
        serial = device_manager.get_current_device()
        if not serial:
            print("Kein Gerät verbunden.")
            wait_for_enter()
            return
        out, err, rc = adb.run_shell("ps -A | grep frida", serial)
        print("frida-server Check:")
        print(out or "kein Treffer")
        if err:
            print(err)
        print(f"Returncode: {rc}")
        wait_for_enter()

    def _set_adb_proxy(self, device_manager, adb) -> None:
        serial = device_manager.get_current_device()
        if not serial:
            print("Kein Gerät verbunden.")
            wait_for_enter()
            return
        host = input("Proxy-Host (z.B. 127.0.0.1): ").strip() or "127.0.0.1"
        port = input("Proxy-Port (z.B. 8080): ").strip() or "8080"
        adb.run_shell(f"settings put global http_proxy {host}:{port}", serial)
        print(f"Proxy gesetzt auf {host}:{port}")
        wait_for_enter()

    def _disable_adb_proxy(self, device_manager, adb) -> None:
        serial = device_manager.get_current_device()
        if not serial:
            print("Kein Gerät verbunden.")
            wait_for_enter()
            return
        adb.run_shell("settings put global http_proxy :0", serial)
        print("Proxy deaktiviert.")
        wait_for_enter()

    def _show_reference_panel(self, title: str, items: List[str]) -> None:
        print_header(title, "Nur die gewünschte Analysephase")
        for item in items:
            print(f"- {item}")
        wait_for_enter()

    def _is_destructive(self, plugin) -> bool:
        try:
            if hasattr(plugin, "destructive"):
                return bool(plugin.destructive)
        except Exception:
            pass
        return False

    def _resolve_instance(self, plugin_class):
        if isinstance(plugin_class, type):
            return plugin_class()
        return plugin_class

    def run_plugin_by_class(self, plugin_class, device_manager, adb, config) -> None:
        try:
            plugin = self._resolve_instance(plugin_class)
        except Exception as exc:
            print(f"Plugin konnte nicht geladen werden: {exc}")
            wait_for_enter()
            return

        name = getattr(plugin, "name", str(plugin))

        if getattr(plugin, "destructive", False) and not confirm(
            f"Dieses Plugin kann destruktive Aktionen ausführen: '{name}'. Trotzdem fortsetzen?"
        ):
            return

        logger.info(f"Plugin wird ausgeführt: {name}")
        try:
            plugin.run(device_manager, adb, config)
        except Exception as exc:
            logger.error(f"Kritischer Fehler im Plugin {name}: {exc}")
            print(f"Fehler im Plugin: {exc}")
            wait_for_enter()
