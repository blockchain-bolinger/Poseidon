# Poseidon

Herstellerunabhängiges Android-Audit- und Steuerungsframework auf Basis von ADB. Poseidon kombiniert interaktive CLI, Plugin-System, generische Recon- und Audit-Payloads sowie einen KI-Agenten für natürliche Sprache.

## Warnhinweis

Dieses Tool ist für **legitime Sicherheitstests an eigenen oder autorisierten Geräten** gedacht. Nutzung auf fremden Geräten ohne ausdrückliche Zustimmung ist rechtswidrig.

## Features

- Interaktive Menüführung über Web-UI und TUI
- Herstellerunabhängige Erkennung von Geräteinformationen, Apps und Export-Komponenten
- Generische Audit- und CVE-Sichtprüfungen
- Recon für exportierte Activities, Receivers, Services und Provider
- Unversal-Bloatware-Scan über `data/bloatware.json`
- KI-Agent mit natürlicher Sprache als Eingabe
- Pluginsystem mit Destruktiv-Schutz und Bestätigungslogik
- Module: PhoneSploit Pro, AndroidHack BackDoor, AndroRAT

## Installation

```bash
git clone https://github.com/USERNAME/Poseidon.git
cd Poseidon
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m pytest
```

## Nutzung

### ADB vorbereiten

```bash
adb devices
```

### CLI / Web-UI starten

```bash
python3 main.py
python3 web_ui.py
```

## Plugin-Entwicklung

Plugins erben von `core.plugin_base.PluginBase` und registrieren sich automatisch über `core.plugin_manager.PluginManager`. Jedes Plugin sollte die Eigenschaften `name`, `description`, `version`, `author` und `destructive` bereitstellen.

```python
from core.plugin_base import PluginBase

class MeinePlugin(PluginBase):
    @property
    def name(self):
        return "Mein Plugin"
```

## Sicherheitsprinzipien

- Input-Sanitizer in `utils/cli_safety.py`
- Klar gekennzeichnete destruktive Plugins
- Bestätigungsprompt vor gefährlichen Aktionen
- Keine Hardcoded-Anmeldedaten; `.env` wird nicht committet

## Projektstruktur

```
Poseidon
├── core/
├── plugins/
├── modules/
├── utils/
├── data/
├── tests/
├── main.py
├── web_ui.py
├── README.md
└── pyproject.toml
```

## Mitwirken

1. Fork erstellen
2. Feature-Branch anlegen
3. Tests und Lint-Prüfungen durchführen
4. Pull Request eröffnen

## Lizenz

MIT
