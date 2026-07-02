# Poseidon 🌊

Herstellerunabhängiges Android-Audit- und Steuerungsframework auf Basis von ADB. Poseidon kombiniert interaktive Terminal-UI, Web-Remote-Dashboard, Headless-CLI, generische Recon- und Audit-Payloads sowie einen KI-Agenten für natürliche Sprache.

> **Hinweis:** Dieses Tool ist für **legitime Sicherheitstests an eigenen oder autorisierten Geräten** gedacht. Nutzung auf fremden Geräten ohne ausdrückliche Zustimmung ist rechtswidrig.

---

## Kernfähigkeiten

| Bereich | Highlights |
|---|---|
| **Interfaces** | TUI `main.py`, Web-UI `web_ui.py`, Headless-CLI `cli.py` |
| **Geräte-Stack** | Geräteerkennung, Eigenschaftsabfragen, ADB-Health-Checks, Themes |
| **Audit-Module** | CVE-Scanner, Recon für exported components, IntentMapper, Bloatware-Scan |
| **Medien & Steuerung** | Screenshots, Aufnahme, Dateimanager, Input/Tap, Remote-Keyboard |
| **System/Developer** | Paket-/App-Management, Konsolen, Backup, Developer-Optionen |
| **KI-Agent** | Natürliche Sprache → Plugin/Modul-Dispatch |
| **Pluginsystem** | Auto-Discovery, destruktive Kennzeichnung, Bestätigungsprompt |
| **OCR/Vision** | Tesseract + Pillow, Mehrwortsuche, Bounding-Box-Bewertung, Annotationen |
| **Monitoring** | Metrik-Polling, CSV/JSONL-Export, Streaming |
| **Internationalisierung** | Mehrsprachigkeit über `utils/i18n.py` |

---

## Voraussetzungen

| Komponente | Empfehlung |
|---|---|
| Python | ≥ 3.10 |
| Systemtool | `adb` auf `PATH` |
| Grafisches Backend optional | `scrcpy` |
| OCR optional | `tesseract`, deutsche Sprachpakete falls gewünscht |
| Paketmanager | `pip` oder `uv` |

---

## Installation

```bash
git clone https://github.com/USERNAME/Poseidon.git
cd Poseidon
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

Zusätzliche optionale Abhängigkeiten für OCR/Vision:

```bash
# Debian/Kali
sudo apt install tesseract-ocr tesseract-ocr-deu
```

---

## Schnellstart

### Konfiguration anpassen

```json
{
  "version": "5.0-dev",
  "language": "de",
  "theme": "light",
  "auto_update_check": true,
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
    "dmesg_stream_max_lines": 2000
  },
  "devices": {}
}
```

### TUI starten

```bash
python3 main.py
```

### Web-UI starten

```bash
python3 web_ui.py
```

Optionaler API-Token für die Web-API:

```bash
POSEIDON_API_TOKEN="geheim" python3 web_ui.py
```

### Headless-CLI

```bash
python3 cli.py devices list
python3 cli.py health check
python3 cli.py monitor once --export both --json
python3 cli.py vision find-text "Einstellungen"
python3 cli.py vision tap-text "OK" --force --json
```

---

## Projektstruktur

```
Poseidon
├── cli.py                      # Headless CLI
├── main.py                     # TUI Dashboard + Menü
├── web_ui.py                   # FastAPI Web Remote + API
├── config.json                 # Nutzerkonfiguration
├── requirements.txt
├── tests/
├── core/
│   ├── app.py                  # AppContext, Config-Loader, Runtime-Setup
│   ├── adb_handler.py          # ADB-Kapsel, Shell/Result-Handling
│   ├── device_manager.py       # Device-Erkennung, Auswahl, Metadata
│   ├── plugin_base.py          # Abstrakte Plugin-Basisklasse
│   ├── plugin_manager.py       # Plugin-Discovery + Menü-Dispatch
│   ├── updater.py              # Update-Check-Menü
│   ├── batch_processor.py      # Batch-Run-Logik
│   ├── logger.py
├── services/
│   ├── vision_service.py       # OCR/Vision-Pipeline
│   └── monitoring_service.py   # Device-Metriken + Export
├── modules/
│   ├── info.py
│   ├── apps.py
│   ├── media.py
│   ├── control.py
│   ├── network.py
│   ├── system.py
│   ├── logcat.py
│   ├── backup.py
│   ├── developer.py
│   ├── security.py
│   ├── macro.py
│   ├── dumpsys_gui.py
│   ├── whatsapp_backup.py
│   ├── dashboard.py
│   ├── files.py
│   ├── analyzer.py
│   ├── monitoring.py
│   ├── ui_vision.py
├── plugins/
│   ├── phonesploit_pro.py
│   ├── androidhack_backdoor.py
│   ├── androrat.py
│   ├── ai_agent_plugin.py
│   ├── cve_scanner.py
│   ├── intentmapper.py
│   ├── app_debloater.py
│   └── custom_command.py
├── utils/
│   ├── cli_safety.py           # Eingabesanitizer für CLI-Eingaben
│   ├── i18n.py                 # Übersetzungen/Locale
│   ├── ansi_colors.py          # Theme-Support
│   ├── ui_helpers.py
│   ├── qr_helper.py
│   ├── file_utils.py
│   ├── dependency_checker.py
│   ├── decorators.py
├── data/
│   └── bloatware.json          # Universal-Bloatware-Liste
└── docs/
    └── MODULES.md
```

---

## Pluginsystem

### Konzept

`PluginManager` durchsucht automatisch `plugins/`, lädt bekannten Plugin-Typen und erstellt das dynamische Menü. Unterstützt werden:

- moderne Klasse via `PluginBase`
- Legacy-Fallback via Modul `setup()`

### Eigenschaften

Jedes Plugin kann Eigenschaften bereitstellen:

- `name`
- `description`
- `version`
- `author`
- `destructive`

### Basisbeispiel

```python
from core.plugin_base import PluginBase

class MeinPlugin(PluginBase):
    @property
    def name(self):
        return "Mein Plugin"

    @property
    def description(self):
        return "Kurzbeschreibung"

    @property
    def destructive(self):
        return False

    def run(self, device_manager, adb, config):
        pass
```

### Sicherheitslogik

Plugins mit `destructive = True` erfordern eine zusätzliche Bestätigung vor dem Start.

---

## Module und Plugins

### Telemetrie/Basics

- Geräteinformationen, Model-Identifikation, Android-Property-Mapping
- App-Auflistung, Berechtigungs-Inspektion, Export-Komponenten

### Medien/Steuerung

- Screenshot, Bildschirmaufnahme
- Interaktive Taps und Texteingabe
- Dateimanager
- Remote-Tastatur in Web-UI

### System

- Backup-Routinen
- dumpsys-GUI
- Logcat-Stream
- Developer-Optionen
- WhatsApp-Backup-Modul

### Sicherheit/Audit/Recon

- CVE-Scanner
- IntentMapper
- Universal-Bloatware-Scan über `data/bloatware.json`
- Permission-Audit
- Exportierte Activities/Receivers/Services/Providers

### KI-Agent

Dispatch über `ai_agent_plugin.py`; Plugin-Zuordnung per natürlicher Sprache.

### Plugin-Module

| Modul/Plugin | Zweck |
|---|---|
| `PhoneSploit Pro` | ADB TCP/IP-Aktivierung, Reboot-Modi, Termux-Prüfung, Paket-/Intent-Audit |
| `AndroidHack BackDoor` | ADB-Statuscheck, APK-Info via dumpsys, exportierte Komponenten, Berechtigungsaudit |
| `AndroRAT` | Device-Info-Export, Standort/Telefonie-Status, Sensorliste, Report-Export |
| `CVE Scanner` | CVE/Security-Audit-Payloads |
| `IntentMapper` | Intent-Mapping/-Analyse |
| `App Debloater` | Bloatware-Scan |
| `Custom Command` | Eigene ADB-Shell-Kommandos |
| `Hardware Monitor` | Hardware-Metriken |

---

## KI-Agent / NL Schnittstelle

- Modul: `plugins/ai_agent_plugin.py`
- Eingabe: natürliche Sprache in TUI oder Web-UI
- Dispatch auf konkrete Plugin-Klassen: `PhoneSploitProPlugin`, `AndroidHackBackdoorPlugin`, `AndroRATPlugin`, plus Scanner/Mapper/Debloat-Workflows
- Rückgabeformat: strukturierter Bericht/Status

---

## OCR/Vision

Nutzt Tesseract und Pillow über `VisionService`:

- Ganzwort- und Mehrwortsuche auf Screenshots
- Trefferbewertung nach Konfidenz und Genauigkeit
- Deduplizierung
- Annotation exportierbar als Bild

---

## Web-UI Absegnung

Technologien:

- FastAPI + Uvicorn
- Tailwind-CSS-Frontend
- Interaktiver Screenshot, Klick/Tap-Mapping, Logcat-Livestream, Statistik-Cards

Schutz:

- Optionaler Bearer-Token über `POSEIDON_API_TOKEN`
- UTF-8-sicherer Logging-Stream
- Lebenszyklus-Management für ADB-Server

---

## Sicherheitsprinzipien

- Eingabesanitizer in `utils/cli_safety.py`
- Klare destruktive Kennzeichnung aller riskanten Tools
- Bestätigungsprompt vor gefährlichen Aktionen
- Keine festen Anmeldedaten
- `.env` wird nicht im Standard-Commit-Pfad abgelegt
- Pentest-Awareness-Demos, keine illegalen Persistenz-/Exfiltrationsaktionen

---

## Tests

```bash
pytest
python3 -m pytest
```

Abgedeckt unter anderem:

- Plugin-Registrierung
- Plugin-Menü-Abbruchverhalten
- App-Context-Init und Config-Merge
- CLI-Safety-Sanitizer
- i18n-/Lokalisierungshandling
- Gerätemanager-Verhalten
- Neue Plugin-Familien: PhoneSploit Pro, AndroidHack BackDoor, AndroRAT

---

## Mitwirken

1. Fork erstellen
2. Feature-Branch anlegen
3. Tests und Lint-Prüfungen durchführen
4. Pull Request eröffnen

---

## Lizenz

MIT
