from __future__ import annotations

import json
import time
from typing import Any, Dict, List

from core.plugin_base import PluginBase
from core.result import CommandResult
from utils.ui_helpers import print_header, menu_prompt, wait_for_enter, confirm
from utils.cli_safety import sanitize_device_input
from rich.console import Console
from rich.table import Table

console = Console()

VULN_RULES: List[Dict[str, Any]] = [
    {
        "key": "cve_2024_0044",
        "title": "CVE-2024-0044: Android System UI dialog injection",
        "affected_sdk_max": 34,
        "checks": [
            {
                "getprop": "ro.build.version.sdk",
                "condition": lambda value: value.isdigit() and int(value) <= 34,
            }
        ],
        "hint": "Patch-Level prüfen; ggf. aktuelle Security Updates installieren.",
    },
    {
        "key": "cve_2023_28432",
        "title": "CVE-2023-28432: E/AVB verification bypass",
        "affected_sdk_max": 33,
        "checks": [
            {
                "getprop": "ro.boot.vbmeta.avb_version",
                "condition": lambda value: value in {"", "0"},
            },
            {
                "getprop": "ro.build.version.sdk",
                "condition": lambda value: value.isdigit() and int(value) <= 33,
            },
        ],
        "hint": "AVB-Status prüfen; Bootloader-Lock und Verified Boot aktivieren, falls möglich.",
    },
    {
        "key": "debuggable_device",
        "title": "ro.debuggable=1 / ro.secure=0",
        "checks": [
            {
                "getprop": "ro.debuggable",
                "condition": lambda value: value.lower() == "1",
            }
        ],
        "hint": "Global debuggbares Build; auf Produktivgeräten unüblich.",
    },
    {
        "key": "adb_enabled_property",
        "title": "ADB über TCP dauerhaft aktiviert",
        "checks": [
            {
                "getprop": "persist.sys.debuggable",
                "condition": lambda value: value.lower() in {"1", "true"},
            }
        ],
        "hint": "Prüfe, ob ADB over TCP autorisiert ausreichend geschützt ist.",
    },
    {
        "key": "known_exploit_surface",
        "title": "Allgemeine Angriffsfäche: exportierte Activities/Receivers/Services",
        "checks": [
            {
                "getprop": "ro.build.version.sdk",
                "condition": lambda value: value.isdigit() and int(value) >= 21,
            }
        ],
        "hint": "Je mehr exportierte Komponenten, desto mehr Angriffsfäche. Plugin 'IntentMapper' liefert Details.",
    },
]


class CveScannerPlugin(PluginBase):
    @property
    def name(self) -> str:
        return "🛡️ CVE/Device-Audit"

    @property
    def description(self) -> str:
        return "Prüft SDK, Debuggable-Bits und generische Angriffsfläche."

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def author(self) -> str:
        return "Poseidon Core"

    @property
    def destructive(self) -> bool:
        return False

    def run(self, device_manager: Any, adb: Any, config: Dict[str, Any]) -> None:
        serial = device_manager.get_current_device()
        if not serial:
            print("Kein Gerät verbunden.")
            wait_for_enter()
            return

        print_header("CVE/Device-Audit", "Generische Android-Prüfungen")
        if not confirm("Audit starten? Dies ist rein lesend."):
            return

        result = self.scan(device_manager, adb)
        print_payload("CVE/Device-Audit", result)
        wait_for_enter()

    def _collect_device_info(self, adb: Any, serial: str) -> Dict[str, str]:
        props = [
            "ro.product.model",
            "ro.product.brand",
            "ro.build.version.release",
            "ro.build.version.sdk",
            "ro.build.version.security_patch",
            "ro.debuggable",
            "ro.secure",
            "ro.boot.vbmeta.avb_version",
            "persist.sys.debuggable",
            "ro.product.cpu.abi",
            "ro.hardware",
            "ro.board",
            "ro.build.tags",
        ]
        info: Dict[str, str] = {}
        for prop in props:
            value = adb.get_device_property(prop, serial=serial)
            info[prop] = value
        return info

    def _collect_extra_props(self, adb: Any, serial: str) -> str:
        out, _, _ = adb.run_shell(r"getprop | grep -E 'ro\.|persist\.'", serial=serial)
        return out[:2000]

    def scan(self, device_manager: Any, adb: Any) -> Dict[str, Any]:
        serial = device_manager.get_current_device()
        if not serial:
            return {"error": "no_device"}

        device_info = self._collect_device_info(adb, serial)
        findings: List[Dict[str, Any]] = []

        for rule in VULN_RULES:
            matched = True
            missing = []
            for check in rule.get("checks", []):
                if "getprop" in check:
                    value = device_info.get(check["getprop"], "")
                    safe_value = sanitize_device_input("prop", value) or value
                    try:
                        if not check["condition"](safe_value):
                            matched = False
                            break
                    except Exception:
                        missing.append(check["getprop"])
                        matched = False
                        break
            if matched and not missing:
                findings.append(
                    {"key": rule["key"], "title": rule["title"], "hint": rule["hint"]}
                )

        return {
            "findings": findings or None,
            "device_info": device_info,
            "extra_props": self._collect_extra_props(adb, serial),
        }


def print_payload(title: str, payload: Dict[str, Any]) -> None:
    console.print(f"\n[bold]{title}[/]")
    for key, value in payload.items():
        if value is None:
            continue
        console.print(f"[cyan]{key}[/]: {value}")
