#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from core.device_manager import DeviceManager
from core.adb_handler import ADBHandler
from core.plugin_manager import PluginManager
from core.logger import logger

from utils.ansi_colors import set_theme
from utils.ui_helpers import print_header
from utils.dependency_checker import check_all_dependencies


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = BASE_DIR / "config.json"


class AppContext:
    def __init__(self, config_path: Path = DEFAULT_CONFIG_PATH) -> None:
        self.config_path = config_path
        self.raw_config: Dict[str, Any] = {}
        self.config: Dict[str, Any] = {}
        self.device_manager: Optional[DeviceManager] = None
        self.adb: Optional[ADBHandler] = None
        self.plugin_manager: Optional[PluginManager] = None

    def _defaults(self) -> Dict[str, Any]:
        return {
            "version": "5.0-dev",
            "language": "de",
            "theme": "light",
            "auto_update_check": True,
            "license_check_enabled": False,
            "global": {
                "backup_path": "./backups",
                "screenshot_path": "./screenshots",
                "record_duration": 30,
                "scrcpy_path": "scrcpy",
                "log_path": "./logs",
                "monitor_stream_max_duration_s": 300,
                "monitor_stream_max_lines": 5000,
                "monitor_stream_heartbeat_interval_lines": 50,
                "dmesg_stream_max_duration_s": 120,
                "dmesg_stream_max_lines": 2000,
            },
            "devices": {},
        }

    def load_config(self) -> Dict[str, Any]:
        defaults = self._defaults()
        if not self.config_path.exists():
            self.raw_config = defaults
            self.config = defaults
            return self.config

        try:
            raw = json.loads(self.config_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.error("Konfiguration konnte nicht geladen werden: %s", exc)
            self.raw_config = defaults
            self.config = defaults
            return self.config

        self.raw_config = raw
        self.config = json.loads(json.dumps(defaults))
        self.config.update({k: v for k, v in raw.items() if k != "global"})
        self.config["global"].update(raw.get("global", {}))
        self.config["devices"] = raw.get("devices", {})
        return self.config

    def ensure_runtime_dirs(self) -> None:
        base = self.config_path.parent
        for relative in [
            self.config["global"].get("backup_path", "./backups"),
            self.config["global"].get("screenshot_path", "./screenshots"),
            self.config["global"].get("log_path", "./logs"),
        ]:
            (base / relative).mkdir(parents=True, exist_ok=True)
        (base / "plugins").mkdir(parents=True, exist_ok=True)

    def check_dependencies(self) -> None:
        results, warnings = check_all_dependencies()
        if not bool(results.get("adb")):
            logger.critical("'adb' wurde nicht im Systempfad gefunden. Abbruch.")
            print_header("POSEIDON", "v5.0-dev - ADB Power Tool")
            print("\033[31mKRITISCHER FEHLER: 'adb' wurde nicht gefunden!\033[0m")
            sys.exit(1)

        if warnings:
            for warning in warnings:
                logger.warning(warning)

    def init_runtime(self) -> Dict[str, Any]:
        if not self.config:
            self.load_config()
        self.ensure_runtime_dirs()
        self.check_dependencies()
        self.device_manager = DeviceManager(self.config)
        self.adb = ADBHandler(self.device_manager)
        self.plugin_manager = PluginManager()
        self.plugin_manager.discover_plugins()
        return self.config

    def current_device(self) -> Optional[str]:
        if not self.device_manager:
            self.init_runtime()
        return self.device_manager.get_current_device()
