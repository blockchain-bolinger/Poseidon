from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from core.plugin_base import PluginBase
from utils.ui_helpers import print_header, menu_prompt, wait_for_enter, confirm
from utils.cli_safety import sanitize_device_input
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


def _code(command: str) -> Panel:
    syntax = Syntax(command, "bash", theme="monokai", line_numbers=False)
    return Panel(syntax, title="Payload", border_style="yellow")
BASE_DIR = Path(__file__).resolve().parents[1]


@dataclass
class PayloadTemplate:
    key: str
    title: str
    description: str
    language: str = "shell"
    command: Optional[str] = None
    confirm: bool = True
    destructive: bool = False
    execute: bool = False

    def render(self) -> Panel:
        return _code(self.preview())

    def preview(self) -> str:
        if self.language == "shell" and self.command:
            return self.command
        return self.description


@dataclass
class AuditContext:
    serial: str
    device_info: Dict[str, str] = field(default_factory=dict)
    sdk: str = ""
    debug_flags: Dict[str, str] = field(default_factory=dict)
    tcp_adb_enabled: bool = False
    export_count: int = 0
    interesting_packages: List[str] = field(default_factory=list)


class AuditContextBuilder:
    @staticmethod
    def build(adb: Any, serial: str) -> AuditContext:
        props = {
            "ro.build.version.sdk": "sdk",
            "ro.debuggable": "ro.debuggable",
            "ro.secure": "ro.secure",
            "persist.sys.debuggable": "persist.sys.debuggable",
            "service.adb.tcp.port": "adb_tcp_port",
            "ro.product.model": "model",
            "ro.product.brand": "brand",
            "ro.build.version.release": "android",
        }
        device_info: Dict[str, str] = {}
        debug_flags: Dict[str, str] = {}
        for prop, _ in props.items():
            try:
                device_info[prop] = adb.get_device_property(prop, serial=serial) or ""
            except Exception:
                device_info[prop] = ""
        debug_flags = {k: device_info.get(k, "") for k in ["ro.debuggable", "ro.secure", "persist.sys.debuggable"]}
        tcp_adb_enabled = (device_info.get("service.adb.tcp.port") or "").strip() not in {"", "0"}
        export_count = int(device_info.get("exported_components_count") or "0")
        return AuditContext(
            serial=serial,
            device_info=device_info,
            sdk=device_info.get("ro.build.version.sdk", ""),
            debug_flags=debug_flags,
            tcp_adb_enabled=tcp_adb_enabled,
            export_count=export_count,
            interesting_packages=device_info.get("interesting_packages", "").splitlines() if isinstance(device_info.get("interesting_packages"), str) else [],
        )
