from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence

from core.plugin_base import PluginBase
from utils.ui_helpers import print_header, menu_prompt, wait_for_enter
from utils.cli_safety import sanitize_device_input
from rich.console import Console
from rich.table import Table

console = Console()
_KEYWORDS_RE = re.compile(r"^(Activity|Service|Receiver|Provider)[^:]*:")
_ATTRIBUTE_RE = re.compile(r'^ *(?:android:exported="true"|IntentFilter|android:targetPackage=|android:name=)')


def print_payload(title: str, payload: Dict[str, Any]) -> None:
    console.print(f"\n[bold]{title}[/]")
    for key, value in payload.items():
        if value is None:
            continue
        console.print(f"[cyan]{key}[/]: {value}")


class IntentMapperPlugin(PluginBase):
    @property
    def name(self) -> str:
        return "📐 IntentMapper"

    @property
    def description(self) -> str:
        return "Listet exportierte Activities/Receivers/Services/Provider auf."

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

        print_header("IntentMapper", "Exportierte Komponenten")
        print("1. Alle exportierten Intents auflisten")
        print("2. Gefiltert nach Package/Keyword")
        print("0. Zurück")

        choice = menu_prompt("Option", range(0, 3))
        if choice == 0:
            return

        keyword = ""
        if choice == 2:
            keyword = input("Filter-Keyword ohne Leerzeichen: ").strip()
            keyword = sanitize_device_input("package", keyword)
            if not keyword:
                print("Ungültiger Filter.")
                wait_for_enter()
                return

        result = self.scan(device_manager, adb, keyword=keyword or None)
        print_payload("IntentMapper", result)
        wait_for_enter()

    def _list_packages(self, adb: Any, serial: str) -> List[str]:
        out, _, _ = adb.run_shell("pm list packages", serial=serial)
        packages: List[str] = []
        for line in out.splitlines():
            if line.startswith("package:"):
                pkg = line.split(":", 1)[-1].strip()
                if pkg:
                    packages.append(pkg)
        return packages

    def _dump_package_components(self, adb: Any, serial: str, package: str) -> List[tuple]:
        safe_package = sanitize_device_input("package", package)
        if not safe_package:
            return []

        out, _, _ = adb.run_shell(f"dumpsys package {safe_package}", serial=serial)
        return self._parse_dumpsys_package(out, safe_package)

    def _parse_dumpsys_package(self, payload: str, package: str) -> List[tuple]:
        results: List[tuple] = []
        current_kind = ""
        current: List[str] = []
        in_block = False
        for line in payload.splitlines():
            if f"Package [{package}]" in line:
                in_block = True

            if not in_block:
                continue

            if line.startswith("Package [") and f"Package [{package}]" not in line:
                break

            kind_match = _KEYWORDS_RE.match(line)
            if kind_match:
                if current and current_kind:
                    results.append((current_kind, current))
                current_kind = kind_match.group(1)
                current = [line.strip()]
                if _ATTRIBUTE_RE.search(line):
                    current.append(line.strip())
                continue

            if current_kind and _ATTRIBUTE_RE.search(line):
                current.append(line.strip())

        if current and current_kind:
            results.append((current_kind, current))
        return results

    def scan(self, device_manager: Any, adb: Any, keyword: Optional[str] = None) -> Dict[str, Any]:
        serial = device_manager.get_current_device()
        if not serial:
            return {"error": "no_device"}

        packages = self._list_packages(adb, serial)
        results: List[Dict[str, Any]] = []

        for package in packages[:60]:
            entries = self._dump_package_components(adb, serial, package)
            for kind, lines in entries:
                for line in lines:
                    if keyword and keyword.lower() not in line.lower() and keyword.lower() not in package.lower():
                        continue
                    results.append(
                        {
                            "package": package,
                            "kind": kind,
                            "entry": line,
                        }
                    )

        return {
            "matches": results[:400],
            "truncated": len(results) > 400,
            "package_count": len(packages),
            "keyword": keyword,
        }
