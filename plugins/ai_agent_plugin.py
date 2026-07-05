from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from core.plugin_base import PluginBase
from plugins.artifact_library import combined_payloads, discover_apks
from utils.ui_helpers import print_header, wait_for_enter

BASE_DIR = Path(__file__).resolve().parents[1]


@dataclass
class AgentPayload:
    key: str
    title: str
    description: str
    intent_keywords: Sequence[str]
    requires_confirmation: bool = True
    destructive: bool = False
    runner: Optional[str] = None

    def score(self, text: str) -> int:
        q = text.lower().strip()
        score = 0
        for keyword in self.intent_keywords:
            kw = keyword.lower().strip()
            if not kw:
                continue
            if kw == q:
                score += 8
            if kw in q:
                score += 3 if len(kw) > 10 else 1
        return score

    def matches(self, text: str) -> bool:
        return self.score(text) > 0


@dataclass
class AgentTurn:
    user_text: str
    payload: Optional[AgentPayload]
    args: List[str] = field(default_factory=list)


class PoseidonAgent:
    def __init__(self) -> None:
        self.payloads = self._default_payloads()
        self.history: List[AgentTurn] = []

    def _default_payloads(self) -> List[AgentPayload]:
        return [
            AgentPayload("device_info", "📱 Geräteinformationen", "Modell, Android-Version, Akku", ["geräten", "device info", "modell", "android version", "battery", "akku", "info", "laufzeit", "akku laufzeit"]),
            AgentPayload("installed_apps", "👦 Installierte Apps auflisten", "User-Apps auflisten", ["installierte apps", "apps", "installiert", "packages", "pm list", "application"]),
            AgentPayload("running_processes", "⚙️ Laufende Prozesse/Top-Apps", "Top-Consumers Speicher und CPU", ["laufende prozesse", "prozess", "prozesse", "top", "running", "leistung"]),
            AgentPayload("logcat_recent", "📋 Letzte Logcat-Zeilen", "Fehler/Warnungen der letzten Minuten", ["logcat", "logs", "log", "fehler", "warnung", "protokoll"]),
            AgentPayload("perf_snapshot", "📊 Performance-Snapshot", "CPU, Speicher, Uptime", ["performance snapshot", "cpu", "speicher", "ram", "uptime", "auslastung"]),
            AgentPayload("security_summary", "🔒 Security-Properties", "ro.secure, ro.debuggable, ADB, AVB", ["security properties", "secure", "debuggable", "adb", "avb", "verified boot", "rootproperties", "tiereigenschaften"]),
            AgentPayload("system_property", "🔧 System-Eigenschaft lesen", "getprop für eine Property", ["system property", "property", "prop", "getprop", "systemeigenschaft", "einstellung"]),
            AgentPayload("cve_scan", "🛡️ CVE/Device-Audit starten", "Scannt generische Sicherheitsmerkmale", ["cve scan", "security audit", "audit", "sicherheit", "check", "prüfen"], runner="plugins.cve_scanner:CveScannerPlugin"),
            AgentPayload("intent_map", "📐 IntentMapper starten", "Exportierte Komponenten auflisten", ["exportierte intents", "intentmapper", "intent", "exported", "mapper", "komponenten", "activity", "receiver", "service", "provider"], runner="plugins.intentmapper:IntentMapperPlugin"),
            AgentPayload("debloat_scan", "🚫 Bloatware-Scan", "Scan nach bekannten Trackern/Ads/System-Helpern", ["bloatware scan", "bloatware", "debloat", "tracker", "werbung", "ads", "vorinstalliert"], runner="plugins.app_debloater:AppDebloaterPlugin"),
            AgentPayload("phonesploit_pro", "📡 PhoneSploit Pro", "ADB/Termux-Chains: TCP/IP, Reboot, Termux, Paket-/Intent-Audit", ["phonesploit", "termux", "adb tcp", "remote shell", "package audit", "apk installieren", "lokale apk"], runner="plugins.phonesploit_pro:PhoneSploitProPlugin"),
            AgentPayload("androidhack_backdoor", "🔐 AndroidHack BackDoor", "Audit-/Steuer-Konsole: APK-Info, exportierte Komponenten, Berechtigungen", ["androidhack", "backdoor", "audit konsole", "exportierte komponenten", "berechtigungen", "apk info", "apk-installation"], runner="plugins.androidhack_backdoor:AndroidHackBackdoorPlugin"),
            AgentPayload("androrat", "🕵️ AndroRAT", "Remote-Admin-Audit: Device-Info, Standort/Telefonie, Sensoren, Report", ["androrat", "report export", "sensoren", "standort", "telefonie", "apk report"], runner="plugins.androrat:AndroRATPlugin"),
            AgentPayload("payloads", "🧪 Safe Payload Templates", "Zeigt lokale Payload-Vorlagen und Demo-Templates", ["payload", "payloads", "exploit", "exploit erstellen", "generate payload", "create payload", "apk payload"]),
            AgentPayload("apk_inventory", "📦 Lokale APK-Inventur", "Zeigt lokale APKs aus data/ und assets/", ["apk", "apk liste", "apks", "apk inventory", "lokale apk", "install apk"]),
        ]

    def classify(self, text: str) -> AgentPayload:
        matches = [(p.score(text), idx, p) for idx, p in enumerate(self.payloads) if p.matches(text)]
        if matches:
            matches.sort(key=lambda item: (-item[0], item[1]))
            return matches[0][2]
        return self._fallback_payload()

    def _fallback_payload(self) -> AgentPayload:
        return AgentPayload("custom_shell", "💬 Benutzerdefinierte Shell", "Führt einen einzelnen Befehl aus", [], destructive=True)


class AIAgentPlugin(PluginBase):
    def __init__(self) -> None:
        self._agent = PoseidonAgent()

    @property
    def name(self) -> str:
        return "🤖 AI Agent"

    @property
    def description(self) -> str:
        return "Eingabe in natürlicher Sprache -> generische ADB-Payloads, APKs und lokale Audit-Flows."

    @property
    def version(self) -> str:
        return "2.0"

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

        print_header("AI Agent", "Natürliche Sprache in generische Payloads")
        print("Beispiele:")
        print("- 'Infos zum Gerät'")
        print("- 'Welche Apps sind installiert?'")
        print("- 'Zeige Fehler aus logcat'")
        print("- 'Security Audit starten'")
        print("- 'Payload Templates anzeigen'")
        print("- 'Lokale APKs anzeigen'")
        print("")

        text = input("Anfrage: ").strip()
        if not text:
            return

        payload = self._agent.classify(text)
        self._agent.history.append(AgentTurn(user_text=text, payload=payload))

        if payload.requires_confirmation and payload.destructive:
            if not input(f"{payload.title} - Aktion fortsetzen? (j/N): ").strip().lower() in {"j", "ja", "y", "yes"}:
                print("Abbruch.")
                wait_for_enter()
                return

        runner = self._resolve_runner(payload.runner)
        if runner:
            runner.run(device_manager, adb, config)
        else:
            self._execute(adb, serial, text, payload)
        wait_for_enter()

    def _resolve_runner(self, dotted: Optional[str]):
        if not dotted:
            return None
        module_path, _, cls_name = dotted.partition(":")
        try:
            module = import_module(module_path)
            cls = getattr(module, cls_name)
            return cls()
        except Exception as exc:
            print(f"Runner '{dotted}' konnte nicht geladen werden: {exc}")
            return None

    def _execute(self, adb: Any, serial: str, user_text: str, payload: AgentPayload) -> None:
        key = payload.key
        if key == "device_info":
            self._exec_device_info(adb, serial)
        elif key == "installed_apps":
            self._exec_installed_apps(adb, serial)
        elif key == "running_processes":
            self._exec_running_processes(adb, serial)
        elif key == "logcat_recent":
            self._exec_logcat_recent(adb, serial)
        elif key == "system_property":
            self._exec_system_property(adb, serial)
        elif key == "perf_snapshot":
            self._exec_perf_snapshot(adb, serial)
        elif key == "security_summary":
            self._exec_security_summary(adb, serial)
        elif key == "payloads":
            self._show_payloads()
        elif key == "apk_inventory":
            self._show_apks()
        else:
            self._exec_custom_shell(adb, serial, user_text)

    def _exec_device_info(self, adb: Any, serial: str) -> None:
        model = adb.get_device_property("ro.product.model", serial=serial)
        brand = adb.get_device_property("ro.product.brand", serial=serial)
        android = adb.get_device_property("ro.build.version.release", serial=serial)
        sdk = adb.get_device_property("ro.build.version.sdk", serial=serial)
        battery = adb.run_shell("dumpsys battery", serial=serial)[0]
        print(f"Modell: {model}")
        print(f"Brand: {brand}")
        print(f"Android: {android} (SDK {sdk})")
        print("Akku:")
        print(battery)

    def _exec_installed_apps(self, adb: Any, serial: str) -> None:
        out, _, _ = adb.run_shell("pm list packages -3", serial=serial)
        for line in out.splitlines()[:120]:
            print(line)
        if len(out.splitlines()) > 120:
            print("...")

    def _exec_running_processes(self, adb: Any, serial: str) -> None:
        out, _, rc = adb.run_shell("ps -A", serial=serial)
        if rc == 0 and out:
            print(out[:4000])
            return
        out, _, _ = adb.run_shell("top -n 1 -b | head -n 40", serial=serial)
        print(out)

    def _exec_logcat_recent(self, adb: Any, serial: str) -> None:
        out, _, _ = adb.run_shell("logcat -d -t 100", serial=serial)
        for line in out.splitlines():
            if any(token in line for token in ["E/", "W/", "F/"]):
                print(line)

    def _exec_system_property(self, adb: Any, serial: str) -> None:
        prop = input("Property-Name (z.B. ro.product.model): ").strip()
        if not prop:
            return
        out, _, _ = adb.run_shell_args("getprop", prop, serial=serial)
        print(out)

    def _exec_perf_snapshot(self, adb: Any, serial: str) -> None:
        load = adb.run_shell("cat /proc/loadavg", serial=serial)[0]
        mem = adb.run_shell("cat /proc/meminfo | head -n 10", serial=serial)[0]
        uptime = adb.run_shell("uptime", serial=serial)[0]
        print("Load:")
        print(load)
        print("Memory:")
        print(mem)
        print("Uptime:")
        print(uptime)

    def _exec_security_summary(self, adb: Any, serial: str) -> None:
        keys = ["ro.secure", "ro.debuggable", "ro.build.version.security_patch", "ro.boot.vbmeta.avb_version", "service.adb.tcp.port", "persist.sys.debuggable", "ro.build.tags"]
        for key in keys:
            value = adb.get_device_property(key, serial=serial)
            print(f"{key}: {value}")

    def _exec_custom_shell(self, adb: Any, serial: str, user_text: str) -> None:
        cmd = input(f"Shell auf {serial}: ").strip()
        if not cmd:
            return
        out, err, rc = adb.run(cmd, serial=serial)
        print(out)
        if err:
            print(err)

    def _show_payloads(self) -> None:
        payloads = combined_payloads()
        print("\nVerfügbare Payload-Vorlagen:")
        for idx, payload in enumerate(payloads, 1):
            print(f"{idx:>2}. [{payload.category}] {payload.title} - {payload.description}")
        print("\nHinweis: Es werden nur lokale, sichere Templates und Demo-Commands angezeigt.")

    def _show_apks(self) -> None:
        apks = discover_apks()
        if not apks:
            print("Keine APKs in data/apks oder assets/apks gefunden.")
            return
        print("\nLokale APKs:")
        for idx, apk in enumerate(apks, 1):
            print(f"{idx:>2}. {apk}")
