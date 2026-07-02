from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from core.plugin_base import PluginBase
from utils.ui_helpers import print_header, menu_prompt, wait_for_enter


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

    def matches(self, text: str) -> bool:
        q = text.lower()
        return any(keyword in q for keyword in self.intent_keywords)


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
            AgentPayload(
                key="device_info",
                title="\ud83d\udcf1 Ger\u00e4teinformationen",
                description="Modell, Android-Version, Akku",
                intent_keywords=["ger\u00e4teinformationen", "device info", "device", "modell", "android version", "battery", "akku", "info"],
                destructive=False,
            ),
            AgentPayload(
                key="installed_apps",
                title="\ud83d\udc66 Installierte Apps auflisten",
                description="User-Apps auflisten",
                intent_keywords=["installierte apps", "apps", "installiert", "packages", "pm list", "application"],
                destructive=False,
            ),
            AgentPayload(
                key="running_processes",
                title="\u2699\ufe0f Laufende Prozesse/Top-Apps",
                description="Top-Consumers speicher und cpu",
                intent_keywords=["laufende prozesse", "prozess", "prozesse", "top", "running", "leistung"],
                destructive=False,
            ),
            AgentPayload(
                key="logcat_recent",
                title="\ud83d\udccb Letzte Logcat-Zeilen",
                description="Fehler/Warnungen der letzten Minuten",
                intent_keywords=["logcat", "logs", "log", "fehler", "warnung", "protokoll"],
                destructive=False,
            ),
            AgentPayload(
                key="perf_snapshot",
                title="\ud83d\udcca Performance-Snapshot",
                description="CPU, Speicher, Uptime",
                intent_keywords=["performance snapshot", "cpu", "speicher", "ram", "uptime", "auslastung"],
                destructive=False,
            ),
            AgentPayload(
                key="security_summary",
                title="\ud83d\udd12 Security-Properties",
                description="ro.secure, ro.debuggable, ADB, AVB",
                intent_keywords=["security properties", "secure", "debuggable", "adb", "avb", "verified boot", "rootproperties", "tiereigenschaften"],
                destructive=False,
            ),
            AgentPayload(
                key="system_property",
                title="\ud83d\udd27 System-Eigenschaft lesen",
                description="getprop f\u00fcr eine Property",
                intent_keywords=["system property", "property", "prop", "getprop", "systemeigenschaft", "einstellung"],
                destructive=False,
            ),
            AgentPayload(
                key="cve_scan",
                title="\ud83d\udee1\ufe0f CVE/Device-Audit starten",
                description="Scannt generische Sicherheitsmerkmale",
                intent_keywords=["cve scan", "security audit", "audit", "sicherheit", "check", "pr\u00fcfen"],
                destructive=False,
                runner="plugins.cve_scanner:CveScannerPlugin",
            ),
            AgentPayload(
                key="intent_map",
                title="\ud83d\udcd0 IntentMapper starten",
                description="Exportierte Komponenten auflisten",
                intent_keywords=["exportierte intents", "intentmapper", "intent", "exported", "mapper", "komponenten", "activity", "receiver", "service", "provider"],
                destructive=False,
                runner="plugins.intentmapper:IntentMapperPlugin",
            ),
            AgentPayload(
                key="debloat_scan",
                title="🚫 Bloatware-Scan",
                description="Scan nach bekannten Trackern/Ads/System-Helpern universell",
                intent_keywords=["bloatware scan", "bloatware", "debloat", "tracker", "werbung", "ads", "vorinstalliert"],
                destructive=False,
                runner="plugins.app_debloater:AppDebloaterPlugin",
            ),
            AgentPayload(
                key="phonesploit_pro",
                title="📡 PhoneSploit Pro",
                description="ADB/Termux-Chains: TCP/IP, Reboot, Termux, Paket-/Intent-Audit",
                intent_keywords=["phonesploit", "termux", "adb tcp", "remote shell", "package audit"],
                destructive=False,
                runner="plugins.phonesploit_pro:PhoneSploitProPlugin",
            ),
            AgentPayload(
                key="androidhack_backdoor",
                title="🔐 AndroidHack BackDoor",
                description="Audit-/Steuer-Konsole: APK-Info, exportierte Komponenten, Berechtigungen",
                intent_keywords=["androidhack backdoor", "audit konsole", "exportierte komponenten", "berechtigungen"],
                destructive=False,
                runner="plugins.androidhack_backdoor:AndroidHackBackdoorPlugin",
            ),
            AgentPayload(
                key="androrat",
                title="🕵️ AndroRAT",
                description="Remote-Admin-Audit: Device-Info, Standort/Telefonie, Sensoren, Report",
                intent_keywords=["androrat", "report export", "sensoren", "standort", "telefonie"],
                destructive=False,
                runner="plugins.androrat:AndroRATPlugin",
            ),
            AgentPayload(
                key="clear_cache",
                title="🗑️ Cache leeren (all)",
                description="Cache-Partition leeren",
                intent_keywords=["cache", "leeren", "clear"],
                destructive=True,
                requires_confirmation=True,
            ),
        ]

    def classify(self, text: str) -> AgentPayload:
        matches = [p for p in self.payloads if p.matches(text)]
        if matches:
            return matches[0]
        return self._fallback_payload()

    def _fallback_payload(self) -> AgentPayload:
        return AgentPayload(
            key="custom_shell",
            title="\ud83d\udcac Benutzerdefinierte Shell",
            description="F\u00fchrt einen einzelnen Befehl aus",
            intent_keywords=[],
            destructive=True,
            requires_confirmation=True,
        )


class AIAgentPlugin(PluginBase):
    def __init__(self) -> None:
        self._agent = PoseidonAgent()

    @property
    def name(self) -> str:
        return "\ud83e\udd16 AI Agent"

    @property
    def description(self) -> str:
        return "Eingabe in nat\u00fcrlicher Sprache -> generische ADB-Payloads."

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
            print("Kein Ger\u00e4t verbunden.")
            wait_for_enter()
            return

        print_header("AI Agent", "Nat\u00fcrliche Sprache in generische Payloads")
        print("Beispiele:")
        print("- 'Infos zum Ger\u00e4t'")
        print("- 'Welche Apps sind installiert?'")
        print("- 'Zeige Fehler aus logcat'")
        print("- 'Wie ist die Akkulaufzeit / Battery?'")
        print("- 'Security Audit starten'")
        print("- 'Exportierte Intents auflisten'")
        print("- 'Performance Snapshot'")
        print("- 'Security Properties anzeigen'")
        print("- 'Bloatware Scan'")
        print("")

        text = input("Anfrage: ").strip()
        if not text:
            return

        payload = self._agent.classify(text)
        self._agent.history.append(AgentTurn(user_text=text, payload=payload))

        if payload.destructive and payload.requires_confirmation:
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
        elif key == "clear_cache":
            self._exec_clear_cache(adb, serial)
        elif key == "perf_snapshot":
            self._exec_perf_snapshot(adb, serial)
        elif key == "security_summary":
            self._exec_security_summary(adb, serial)
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

    def _exec_clear_cache(self, adb: Any, serial: str) -> None:
        adb.run_shell_args("rm", "-rf", "/data/local/tmp/*", serial=serial)
        adb.run_shell_args("rm", "-rf", "/sdcard/.Trashes", serial=serial)
        print("Cache-Bereinigung simulativ ausgef\u00fchrt.")

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
        keys = [
            "ro.secure",
            "ro.debuggable",
            "ro.build.version.security_patch",
            "ro.boot.vbmeta.avb_version",
            "service.adb.tcp.port",
            "persist.sys.debuggable",
            "ro.build.tags",
        ]
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
