from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parents[1]
SEARCH_DIRS = [
    BASE_DIR / "data" / "apks",
    BASE_DIR / "assets" / "apks",
    BASE_DIR / "data" / "payloads",
    BASE_DIR / "assets" / "payloads",
]


@dataclass
class PayloadTemplate:
    key: str
    title: str
    description: str
    command: str
    destructive: bool = False
    requires_confirmation: bool = True
    category: str = "general"


DEFAULT_PAYLOADS: List[PayloadTemplate] = [
    PayloadTemplate(
        key="adb_tcpip",
        title="ADB TCP/IP aktivieren",
        description="Aktiviert ADB over TCP/IP auf Port 5555.",
        command="setprop service.adb.tcp.port 5555 && stop adbd && start adbd",
        destructive=True,
        category="adb",
    ),
    PayloadTemplate(
        key="reboot_normal",
        title="Normaler Reboot",
        description="Startet das Gerät neu.",
        command="reboot",
        destructive=True,
        category="reboot",
    ),
    PayloadTemplate(
        key="reboot_bootloader",
        title="Bootloader-Reboot",
        description="Startet in den Bootloader/Download-Modus.",
        command="reboot bootloader",
        destructive=True,
        category="reboot",
    ),
    PayloadTemplate(
        key="reboot_recovery",
        title="Recovery-Reboot",
        description="Startet in das Recovery-Menü.",
        command="reboot recovery",
        destructive=True,
        category="reboot",
    ),
    PayloadTemplate(
        key="package_audit",
        title="Paket-/Intent-Audit",
        description="Listet installierte Pakete und exportierte Komponenten.",
        command="pm list packages -3 && dumpsys package com.android.shell | head -n 40",
        category="audit",
    ),
    PayloadTemplate(
        key="apk_install_local",
        title="Lokale APK installieren",
        description="Installiert eine lokal vorhandene Test-/Demo-APK.",
        command="adb install -r ./data/apks/<file.apk>",
        destructive=True,
        category="apk",
    ),
]


def discover_local_files(*extensions: str) -> List[Path]:
    results: List[Path] = []
    for directory in SEARCH_DIRS:
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            if path.is_file() and (not extensions or path.suffix.lower().lstrip(".") in extensions):
                results.append(path)
    return results


def discover_apks() -> List[Path]:
    return discover_local_files("apk")


def discover_payload_manifests() -> List[Dict[str, Any]]:
    manifests: List[Dict[str, Any]] = []
    for directory in SEARCH_DIRS:
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        item = dict(item)
                        item.setdefault("source", str(path))
                        manifests.append(item)
            elif isinstance(data, dict):
                payloads = data.get("payloads")
                if isinstance(payloads, list):
                    for item in payloads:
                        if isinstance(item, dict):
                            item = dict(item)
                            item.setdefault("source", str(path))
                            manifests.append(item)
                else:
                    data = dict(data)
                    data.setdefault("source", str(path))
                    manifests.append(data)
    return manifests


def combined_payloads() -> List[PayloadTemplate]:
    payloads = list(DEFAULT_PAYLOADS)
    seen = {p.key for p in payloads}
    for item in discover_payload_manifests():
        try:
            template = PayloadTemplate(
                key=str(item.get("key") or item.get("title") or "custom"),
                title=str(item.get("title") or item.get("key") or "Custom Payload"),
                description=str(item.get("description") or "Benutzerdefinierter Payload"),
                command=str(item.get("command") or ""),
                destructive=bool(item.get("destructive", False)),
                requires_confirmation=bool(item.get("requires_confirmation", True)),
                category=str(item.get("category") or "custom"),
            )
        except Exception:
            continue
        if template.key in seen:
            continue
        seen.add(template.key)
        payloads.append(template)
    return payloads
