#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

from core.app import AppContext
from core.updater import check_for_updates, show_update_menu
from core.batch_processor import show_batch_menu

from utils.ansi_colors import fg, style, set_theme
from utils.ui_helpers import clear_screen, print_header, menu_prompt, confirm, wait_for_enter
from core.logger import logger
from utils.i18n import get_text, set_language, get_available_languages
from core.device_manager import DeviceManager
from core.adb_handler import ADBHandler
from core.plugin_manager import PluginManager

from modules import (
    info,
    apps,
    media,
    control,
    network,
    system,
    logcat,
    backup,
    developer,
    security,
    macro,
    dumpsys_gui,
    whatsapp_backup,
    dashboard,
    files,
    analyzer,
    monitoring,
    ui_vision,
)

from plugins.phonesploit_pro import PhoneSploitProPlugin
from plugins.androidhack_backdoor import AndroidHackBackdoorPlugin
from plugins.androrat import AndroRATPlugin

BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "assets" / "logo.txt"
CONTEXT = AppContext()


def save_config(config: Dict[str, Any]) -> None:
    path = CONTEXT.config_path
    with path.open("w", encoding="utf-8") as f:
        import json
        json.dump(config, f, indent=4, ensure_ascii=False)


def run_dependency_checks() -> None:
    CONTEXT.check_dependencies()


def show_logo() -> None:
    if LOGO_PATH.exists():
        try:
            with open(LOGO_PATH, "r", encoding="utf-8") as f:
                print(fg.CYAN + f.read() + style.RESET)
                return
        except Exception:
            pass
    print_header("POSEIDON", "v5.0-dev - ADB Power Tool")


def auto_check_updates(config: Dict[str, Any]) -> None:
    if not config.get("auto_update_check", True):
        return
    try:
        has_update, latest = check_for_updates(config.get("version", "5.0-dev"))
        if has_update:
            print(f"{fg.YELLOW}{get_text('update_available').format(version=latest)}{style.RESET}")
    except Exception as e:
        logger.error(f"Fehler beim Update-Check: {e}")


def build_context():
    config = CONTEXT.init_runtime()
    set_language(config.get("language", "de"))
    set_theme(config.get("theme", "light"))
    return config, CONTEXT.device_manager, CONTEXT.adb, CONTEXT.plugin_manager


def settings_menu(config: Dict[str, Any], device_manager: DeviceManager) -> None:
    while True:
        clear_screen()
        print_header(get_text("settings_title"), get_text("settings_subtitle"))
        print(f"1. {get_text('setting_backup_path')}: {config['global']['backup_path']}")
        print(f"2. {get_text('setting_screenshot_path')}: {config['global']['screenshot_path']}")
        print(f"3. {get_text('setting_record_duration')}: {config['global']['record_duration']} s")
        print(f"4. {get_text('setting_scrcpy_path')}: {config['global']['scrcpy_path']}")
        print(f"5. {get_text('setting_theme')}: {config.get('theme', 'light')}")
        print(f"6. {get_text('setting_language')}: {config.get('language', 'de')}")
        print(f"7. {get_text('setting_auto_update')}: {'an' if config.get('auto_update_check', True) else 'aus'}")
        print(f"8. Log-Pfad: {config['global'].get('log_path', './logs')}")
        print(f"9. MobSF-URL: {config['global'].get('mobsf_url', 'http://127.0.0.1:8000')}")
        print("10. MobSF API-Key: " + ("gesetzt" if config["global"].get("mobsf_api_key") else "leer"))
        print(f"11. JADX GUI Command: {config['global'].get('jadx_gui_cmd', 'jadx-gui')}")
        print(f"12. apktool Command: {config['global'].get('apktool_cmd', 'apktool')}")
        print(f"13. Frida PS Command: {config['global'].get('frida_cmd', 'frida-ps')}")
        print(f"14. Frida Trace Command: {config['global'].get('frida_trace_cmd', 'frida-trace')}")
        print(f"15. Objection Command: {config['global'].get('objection_cmd', 'objection')}")
        print(f"16. mitmproxy Command: {config['global'].get('mitmproxy_cmd', 'mitmproxy')}")
        print(f"17. Burp Command: {config['global'].get('burp_cmd', 'burp')}")
        print(f"18. Ghidra Command: {config['global'].get('ghidra_cmd', 'ghidraRun')}")
        print("0. " + get_text("back"))
        choice = menu_prompt(get_text("choose_option"), range(0, 19))
        if choice == 0:
            break
        elif choice == 1:
            new_path = input(get_text("new_backup_path") + ": ").strip()
            if new_path:
                config["global"]["backup_path"] = new_path
        elif choice == 2:
            new_path = input(get_text("new_screenshot_path") + ": ").strip()
            if new_path:
                config["global"]["screenshot_path"] = new_path
        elif choice == 3:
            try:
                config["global"]["record_duration"] = int(input(get_text("new_record_duration") + ": ").strip())
            except ValueError:
                print(get_text("invalid_input"))
        elif choice == 4:
            new_scrcpy = input(get_text("new_scrcpy_path") + ": ").strip()
            if new_scrcpy:
                config["global"]["scrcpy_path"] = new_scrcpy
        elif choice == 5:
            new_theme = input(get_text("theme_prompt") + " (light/dark): ").strip().lower()
            if new_theme in ("light", "dark"):
                config["theme"] = new_theme
                set_theme(new_theme)
        elif choice == 6:
            langs = get_available_languages()
            if langs:
                print(get_text("available_languages") + ": " + ", ".join(langs))
                new_lang = input(get_text("language_prompt") + ": ").strip()
                if new_lang in langs:
                    config["language"] = new_lang
                    set_language(new_lang)
        elif choice == 7:
            config["auto_update_check"] = not config.get("auto_update_check", True)
        elif choice == 8:
            new_log_path = input("Neuer Log-Pfad: ").strip()
            if new_log_path:
                config["global"]["log_path"] = new_log_path
        elif choice == 9:
            new_url = input("Neue MobSF-URL: ").strip()
            if new_url:
                config["global"]["mobsf_url"] = new_url
        elif choice == 10:
            new_key = input("Neuer MobSF API-Key (leer zum Entfernen): ").strip()
            config["global"]["mobsf_api_key"] = new_key
        elif choice == 11:
            new_cmd = input("Neuer JADX GUI-Command: ").strip()
            if new_cmd:
                config["global"]["jadx_gui_cmd"] = new_cmd
        elif choice == 12:
            new_cmd = input("Neuer apktool-Command: ").strip()
            if new_cmd:
                config["global"]["apktool_cmd"] = new_cmd
        elif choice == 13:
            new_cmd = input("Neuer Frida PS-Command: ").strip()
            if new_cmd:
                config["global"]["frida_cmd"] = new_cmd
        elif choice == 14:
            new_cmd = input("Neuer Frida Trace-Command: ").strip()
            if new_cmd:
                config["global"]["frida_trace_cmd"] = new_cmd
        elif choice == 15:
            new_cmd = input("Neuer Objection-Command: ").strip()
            if new_cmd:
                config["global"]["objection_cmd"] = new_cmd
        elif choice == 16:
            new_cmd = input("Neuer mitmproxy-Command: ").strip()
            if new_cmd:
                config["global"]["mitmproxy_cmd"] = new_cmd
        elif choice == 17:
            new_cmd = input("Neuer Burp-Command: ").strip()
            if new_cmd:
                config["global"]["burp_cmd"] = new_cmd
        elif choice == 18:
            new_cmd = input("Neuer Ghidra-Command: ").strip()
            if new_cmd:
                config["global"]["ghidra_cmd"] = new_cmd
        save_config(config)
        wait_for_enter()


def render_main_menu(device_manager: DeviceManager) -> None:
    print()
    print(f"{fg.YELLOW}{get_text('main_menu')}{style.RESET}")
    print("=" * 50)
    device = device_manager.get_current_device()
    if device:
        print(f"{fg.GREEN}{get_text('device_connected').format(serial=device)}{style.RESET}")
    else:
        print(f"{fg.RED}{get_text('no_device')}{style.RESET}")
    print("\n" + get_text("categories"))
    print(" 1. 📱 " + get_text("menu_device_info"))
    print(" 2. 📦 " + get_text("menu_app_management"))
    print(" 3. 🎥 " + get_text("menu_media"))
    print(" 4. 🎮 " + get_text("menu_control"))
    print(" 5. 🌐 " + get_text("menu_network"))
    print(" 6. ⚙️ " + get_text("menu_system"))
    print(" 7. 🛠️ " + get_text("menu_developer"))
    print(" 8. 🔒 " + get_text("menu_security"))
    print(" 9. 📋 " + get_text("menu_logcat"))
    print("10. 💾 " + get_text("menu_backup"))
    print("11. ⚙️ " + get_text("menu_settings"))
    print("12. 🎬 " + get_text("menu_macro"))
    print("13. 🧩 " + get_text("menu_plugins"))
    print("14. 📦 " + get_text("menu_batch"))
    print("15. 🖥️ " + get_text("menu_dumpsys"))
    print("16. 💬 WhatsApp Backup")
    print("17. 🔄 Update")
    print("18. 📊 " + get_text("menu_dashboard"))
    print("19. 📁 " + get_text("menu_files"))
    print("20. 🕵️ " + get_text("menu_analyzer"))
    print("21. 📈 Monitoring v2")
    print("22. 👁️ Vision / OCR v2")
    print("23. 📡 PhoneSploit Pro")
    print("24. 🔐 AndroidHack BackDoor")
    print("25. 🕵️ AndroRAT")
    print(" 0. ❌ " + get_text("exit"))


def handle_menu_choice(choice: int, config: Dict[str, Any], device_manager: DeviceManager, adb: ADBHandler, plugin_manager: PluginManager) -> bool:
    if choice == 0:
        if confirm(get_text("confirm_exit")):
            print(f"{fg.GREEN}{get_text('goodbye')}{style.RESET}")
            return False
    elif choice == 1:
        info.show_menu(device_manager, adb)
    elif choice == 2:
        apps.show_menu(device_manager, adb)
    elif choice == 3:
        media.show_menu(device_manager, adb, config["global"])
    elif choice == 4:
        control.show_menu(device_manager, adb)
    elif choice == 5:
        network.show_menu(device_manager, adb, config)
    elif choice == 6:
        system.show_menu(device_manager, adb)
    elif choice == 7:
        developer.show_menu(device_manager, adb)
    elif choice == 8:
        security.show_menu(device_manager, adb)
    elif choice == 9:
        logcat.show_menu(device_manager, adb)
    elif choice == 10:
        backup.show_menu(device_manager, adb, config["global"])
    elif choice == 11:
        settings_menu(config, device_manager)
    elif choice == 12:
        macro.show_menu(device_manager, adb)
    elif choice == 13:
        plugin_manager.show_plugin_menu(device_manager, adb, config)
    elif choice == 14:
        show_batch_menu(device_manager, adb, config)
    elif choice == 15:
        dumpsys_gui.show_menu(device_manager, adb)
    elif choice == 16:
        whatsapp_backup.show_menu(device_manager, adb)
    elif choice == 17:
        show_update_menu(device_manager, adb, config)
    elif choice == 18:
        dashboard.show_dashboard(device_manager, adb)
    elif choice == 19:
        files.show_manager(device_manager, adb, config["global"])
    elif choice == 20:
        analyzer.show_menu(device_manager, adb)
    elif choice == 21:
        monitoring.show_menu(device_manager, adb, config)
    elif choice == 22:
        ui_vision.show_menu(device_manager, adb, config)
    elif choice == 23:
        plugin_manager.run_plugin_by_class(PhoneSploitProPlugin, device_manager, adb, config)
    elif choice == 24:
        plugin_manager.run_plugin_by_class(AndroidHackBackdoorPlugin, device_manager, adb, config)
    elif choice == 25:
        plugin_manager.run_plugin_by_class(AndroRATPlugin, device_manager, adb, config)
    return True


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    set_theme(CONTEXT.config.get("theme", "light") if hasattr(CONTEXT, "config") and CONTEXT.config else "light")
    logger.info("Poseidon v5.0-dev wird gestartet...")
    run_dependency_checks()
    config, device_manager, adb, plugin_manager = build_context()
    auto_check_updates(config)
    show_logo()
    running = True
    while running:
        render_main_menu(device_manager)
        choice = menu_prompt(get_text("choose_category"), range(0, 26))
        running = handle_menu_choice(choice, config, device_manager, adb, plugin_manager)


if __name__ == "__main__":
    try:
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
        main()
    except KeyboardInterrupt:
        print(f"\n{fg.YELLOW}{get_text('aborted')}{style.RESET}")
        sys.exit(0)
    except Exception as e:
        logger.exception("Kritischer Fehler im Hauptprogramm")
        print(f"\n{fg.RED}Ein unerwarteter Fehler ist aufgetreten: {e}{style.RESET}")
        sys.exit(1)
