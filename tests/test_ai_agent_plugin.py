from __future__ import annotations

from importlib import import_module

import pytest

from plugins.ai_agent_plugin import AgentPayload, AIAgentPlugin, PoseidonAgent
from plugins.artifact_library import combined_payloads, discover_apks


def test_fallback_when_no_keyword_hits():
    agent = PoseidonAgent()
    payload = agent.classify("irgendwas unbekanntes")
    assert isinstance(payload, AgentPayload)
    assert payload.key == "custom_shell"
    assert payload.destructive is True
    assert payload.requires_confirmation is True


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Welche Apps sind installiert?", "installed_apps"),
        ("Zeige mir die Akkulaufzeit", "device_info"),
        ("Security Audit starten", "cve_scan"),
        ("exportierte Intents anzeigen", "intent_map"),
        ("Performance Snapshot", "perf_snapshot"),
        ("Security Properties anzeigen", "security_summary"),
        ("Bloatware Scan starten", "debloat_scan"),
    ],
)
def test_classify_matches_intents(text, expected):
    agent = PoseidonAgent()
    assert agent.classify(text).key == expected


def test_classify_prefers_earliest_matching_payload():
    agent = PoseidonAgent()
    assert agent.classify("Scan security audit jetzt").key == "cve_scan"
    assert agent.classify("Zeige properties").key == "system_property"


def test_manifest_payloads_are_loaded():
    payloads = combined_payloads()
    keys = {payload.key for payload in payloads}
    assert "battery_snapshot" in keys
    assert "installed_packages" in keys
    assert "logcat_snapshot" in keys


def test_ai_classify_prefers_local_inventory_and_templates():
    agent = PoseidonAgent()
    assert agent.classify("zeige lokale apks").key == "apk_inventory"
    assert agent.classify("zeige payload templates").key == "payloads"


def test_resolve_runner_loads_plugin_class_by_dotted_path():
    plugin = AIAgentPlugin()._resolve_runner("plugins.cve_scanner:CveScannerPlugin")
    assert plugin is not None
    module = import_module("plugins.cve_scanner")
    assert isinstance(plugin, module.CveScannerPlugin)


def test_discover_apks_returns_list():
    assert isinstance(discover_apks(), list)
