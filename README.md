# 🌊 Poseidon – The Powerful ADB Tool

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![ADB](https://img.shields.io/badge/ADB-required-green)](https://developer.android.com/studio/command-line/adb)

**Poseidon** ist ein modulares, leistungsstarkes Terminal-Tool zur Steuerung, Überwachung und Sicherheitsanalyse von Android-Geräten über die Android Debug Bridge (ADB). Es vereint klassische ADB-Befehle mit modernen Vision/OCR-Automationen, Echtzeit-Monitoring und einer interaktiven Web-Steuerung.

> ⚠️ **Nutzung ausschließlich zu Bildungszwecken und auf eigenen Geräten!**  
> Der Autor übernimmt keine Haftung für Missbrauch.

---

## ✨ Features

- **📱 Interaktives Terminal UI (TUI):**
  * Modernes Menüsystem mit Farbschemata (Light/Dark) via `rich`.
  * Modularer Aufbau: Infos, Apps, Medien, System, Netzwerke, WhatsApp-Backup und Plugins.
- **📈 Echtzeit-Gerätemonitoring:**
  * Live-Auslesung von CPU, RAM-Auslastung und Akku-Werten.
  * Automatischer Datenexport als CSV- und JSONL-Dateien.
- **👁️ UI Vision & OCR-Interaktion:**
  * Screen-Capture, OCR-Textsuche (`pytesseract`) und grafische Annotation.
  * Automatisches Klicken auf erkannte Textelemente (`tap-text`).
- **🕵️ Sicherheitsanalyse & Logging:**
  * **Farbkodiertes Live-Logcat:** Log-Streams mit farbiger Prioritäts-Hervorhebung.
  * **App-Spion:** Überwachung von Datei-Zugriffen in Echtzeit.
  * **Kernel-Sniffer:** Live-Streaming von `dmesg`-Ereignissen.
  * **Auto Trigger-Recorder:** Automatische Bildschirmaufnahme, sobald eine Ziel-App startet.
- **🌐 Web Remote Controller (FastAPI):**
  * Ein interaktives, responsives Web-Dashboard mit Glassmorphism-Design.
  * **Remote Screen:** Klicke im Browser auf den Screenshot, um Aktionen auf das Handy zu übertragen.
  * Live-Logcat-Konsole, OCR-Suche und Systemstatistiken im Web.

---

## 📂 Projektstruktur

```text
Poseidon/
├── main.py                # Interaktiver TUI-Startpunkt (Terminal Menü)
├── cli.py                 # Headless CLI für Automationen & Monitoring
├── web_ui.py              # FastAPI-Server & Web Remote Controller Dashboard
├── core/                  # Core-Klassen (ADB, Plugins, Logger)
├── modules/               # TUI-Feature-Module (Security, Apps, System, etc.)
├── services/              # Kern-Services (Vision/OCR, Monitoring)
├── plugins/               # Zusatz-Plugins (Debloater, App-Launcher, Wi-Fi etc.)
├── utils/                 # Utilities (UI-Helper, i18n, Dependency-Check, Farben)
├── tests/                 # pytest-Tests für AppContext und Grundfunktionen
├── scripts/               # Test- & Hilfsskripte
├── setup.sh               # Installationsskript für System-Abhängigkeiten
├── TESTING.md             # Testanleitung
├── Dockerfile             # Docker-Umgebung zur plattformunabhängigen Ausführung
└── config.json            # Betriebseinstellungen (Pfade, Recording, etc.)
```

---

## 📦 Installation & Setup

### 🚀 Automatisches Setup (Linux - Empfohlen)

Für Debian-basierte Systeme (Ubuntu, Kali, etc.) installiert das Skript alle Systemabhängigkeiten (`adb`, `scrcpy`, `ffmpeg`, `nmap`, `tcpdump`, `tesseract-ocr`) sowie Python-Module vollautomatisch:

```bash
chmod +x setup.sh
sudo ./setup.sh
```

### 🛠️ Manuelles Setup

1. **System-Tools installieren:** Installiere Python3, ADB, FFMpeg und Tesseract-OCR über deinen Paketmanager.
2. **Repository einrichten:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

---

## 🚀 Nutzung

### 📱 1. Interaktives TUI-Menü
Starte die klassische Benutzeroberfläche direkt im Terminal:
```bash
python3 main.py
```

### 🖥️ 2. Headless CLI-Modus
Führe Automatisierungen und Checks aus:
```bash
# Geräte und ADB-Status prüfen
python3 cli.py devices list
python3 cli.py health check --json

# Einzelnen Monitoring-Snapshot erstellen
python3 cli.py monitor once --json --export both

# Einen Text auf dem Bildschirm suchen und per OCR anklicken
python3 cli.py vision tap-text "WLAN" --force --json
```

### 🌐 3. Web-Dashboard & Remote Controller
Starte die Weboberfläche (standardmäßig auf `http://localhost:8000`):
```bash
python3 web_ui.py
```
Für externen Zugriff, z.B. über Tailscale oder WLAN, läuft der Server jetzt auf `0.0.0.0` und ist damit im Netzwerk erreichbar. Nutze dennoch HTTPS/Reverse-Proxy und eine Token-Absicherung, wenn du den Dienst außerhalb von localhost betreibst.

### 🐳 4. Docker-Container
```bash
# Image bauen
docker build -t poseidon .

# Ausführen über USB (Linux Hosts)
docker run -it --privileged -v /dev/bus/usb:/dev/bus/usb poseidon
```

---

## 🔌 Plugin-System

Erweitere Poseidon, indem du eine Klasse im Ordner `plugins/` erstellst, die von `PluginBase` erbt:

```python
from core.plugin_base import PluginBase

class CustomPlugin(PluginBase):
    @property
    def name(self) -> str:
        return "Mein Plugin Name"
        
    @property
    def description(self) -> str:
        return "Beschreibung der Aktion"

    def run(self, device_manager, adb, config):
        # Deine Logik hier
        pass
```

Bereits vorinstalliert sind:
* **Screenshot (erweitert):** Bildaufnahmen mit benutzerdefinierten Namen.
* **Wi-Fi ADB Automator:** Startet TCP-IP ADB und druckt einen Verbindungs-QR-Code in die Konsole.
* **App-Debloater:** System-Apps sicher deinstallieren & wiederherstellen.
* **App Launcher:** Activities/Services mit Intent-Extras manuell triggern.
* **Hardware Monitor:** Live-CPU-Monitor mit zuschaltbarem Core-Stresstest.

---

## 📄 Lizenz

MIT License. Nutzung auf eigene Gefahr.  
Autor: Arturik69 (Inspiriert von der ADB Developer Community).
