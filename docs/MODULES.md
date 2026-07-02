# Poseidon Module

Module und Plugins erweitern die Kernfunktionen um spezialisierte Audit-, Steuer- und Automatisierungs-Workflows.
Alle Module respektieren den Legal-Frame: ausschließlich eigene/autorisiierte Geräte. Destruktive Aktionen sind jeweils explizit gekennzeichnet und bestätigungspflichtig.

## Übersicht

| Module | Plugin | Modus |
|---|---|---|
| `modules/info.py` | — | Geräteinformationen, PROP-Mapping |
| `modules/apps.py` | — | Paketlisten, Permission-Audit |
| `modules/media.py` | — | Screenshots, Aufnahmen, Dateimanager |
| `modules/control.py` | — | Remote-Input, Navigation |
| `modules/network.py` | — | WLAN/ADB/Daten Netzwerkinfo |
| `modules/system.py` | — | Dumpsys, Speicher, Storage |
| `modules/backup.py` | — | Backup-Workflows |
| `modules/developer.py` | — | Developer-/USB-Debugging-Status |
| `modules/security.py` | — | Secure/Verify Boot, Signaturprüfung |
| `modules/logcat.py` | — | Logcat-Stream und Filter |
| `modules/macro.py` | — | Makrorekorder/-wiedergabe |
| `modules/dumpsys_gui.py` | — | Dumpsys-GUI |
| `modules/dashboard.py` | — | Dashboard-Ansicht |
| `modules/files.py` | — | Dateimanager |
| `modules/analyzer.py` | — | Intent-/Komponentenanalyse |
| `modules/monitoring.py`, `services/monitoring_service.py` | — | Metrik-Polling, CSV/JSONL |
| `modules/ui_vision.py`, `services/vision_service.py` | — | OCR/Vision, Tap-on-Text |

## Plugins

### PhoneSploit Pro
Plugin: `plugins/phonesploit_pro.py`
- ADB TCP/IP-Aktivierung, Remote-Shell-Vorbereitung
- Reboot-Modi: normal, bootloader, recovery, sideload
- Termux-Prüfung/-Remote-Shell
- Paket-/Intent-Audit
- Lokale APK-Installationen aus `data/apks` oder `assets/apks`
- Payload-Templates und Recon-Report-Export
- Führt keine persistente Installation ohne Nutzerbestätigung aus; Ziel ist Awareness und Demonstrationskontrolle

### AndroidHack BackDoor
Plugin: `plugins/androidhack_backdoor.py`
- ADB-Status, debuggable-Bits, Security-Patch-Sichtprüfung
- APK-Info via `dumpsys package`
- Exportierte Components: Activities, Services, Receivers, Providers
- Permission-Audit für gefährliche Gruppen: SMS, Call, Camera, Mic, Location, Contacts
- Proof-of-Concept-Payloads: Intent-Sonden, Activity-Launch-Skizzen
- Backdoor-Begrenzung: keine Persistenz-APK ohne ausdrückliche Bestätigung; keine Datenexfiltration

### AndroRAT
Plugin: `plugins/androrat.py`
- Device-Info-Export
- Standort/Telefonie-Status
- Sensorliste
- Report-Export nach `logs/`
- Begrenzung: keine dauerhafte Verbindung, keine persistente Komponente

### AI Agent
Plugin: `plugins/ai_agent_plugin.py`
- NL-Classification auf Payloads
- Dispatch auf feste Runner: CVE Scanner, IntentMapper, Debloater, PhoneSploit Pro, AndroidHack BackDoor, AndroRAT
- Generiert passende Payload-Vorschläge für Web-UI/TUI und fragt aktive Bestätigungen ab
- Fallback: benutzerdefinierte Shell-Aktion mit Destruktiv-Check

### CVE Scanner
Plugin: `plugins/cve_scanner.py`
- Generische Prüfregeln über Device-Properties und SDK
- Beispielregeln: CVE-2024-0044, CVE-2023-28432, debuggable-Flags, ADB-over-TCP-Hinweise
- Liefert findings plus konkrete Hinweise, keine Exploit-Ausführung

### IntentMapper
Plugin: `plugins/intentmapper.py`
- Exportierte Activities/Receivers/Services/Providers auflisten
- Keyword-Filter pro Package
- Begrenzung: nur Erkennung/Darstellung, keine unbefugte Nutzung fremder Komponenten

### App Debloater
Plugin: `plugins/app_debloater.py`
- Scan über `data/bloatware.json`
- Hersteller- und Modell-Präfix-Filter
- Deinstallations- und Restore-Aktionen für aktiven User
- Destruktive Aktion mit Bestätigung

## Begrenzungen

Module und Plugins führen keine Persistenz-, Exfiltrations- oder Stealth-Aktionen aus, sofern nicht explizit als Demonstration mit Bestätigung markiert.
Ziel ist Awareness, Audit und autorisierte pentest-relevante Kontrolle eigener Geräte. Exploits und Payloads dienen ausschließlich der Darstellung von Angriffsfäche.

## Erweiterung

- Neue Plugins über `core.plugin_base.PluginBase`
- Registry/Auto-Discovery über `core.plugin_manager.PluginManager`
- Destruktive Aktionen mit `destructive = True` und Bestätigungsprompt
