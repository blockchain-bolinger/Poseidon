# Poseidon Module

Module erweitern die Kernfunktionen um spezialisierte Audit- und Steuerungs-Workflows.
Alle Module respektieren den Legal-Frame: ausschließlich eigene/autorisiertete Geräte.

## PhoneSploit Pro
Plugin: `plugins/phonesploit_pro.py`
- ADB TCP/IP-Aktivierung
- Reboot-Modi
- Termux-Prüfung/-Remote
- Paket- und Intent-Audit

## AndroidHack BackDoor
Plugin: `plugins/androidhack_backdoor.py`
- ADB-Aktivierung prüfen
- APK-Info via `dumpsys package`
- Exportierte Komponenten
- Berechtigungsaudit
- Diagnose-Code

## AndroRAT
Plugin: `plugins/androrat.py`
- Device-Info-Export
- Standort/Telefonie-Status
- Sensorliste
- Report-Export

## Begrenzungen
Module führen keine Persistenz-, Exfiltrations- oder Stealth-Aktionen aus.
Sie sind Awareness- und Audit-Tools für autorisierte Umgebungen.
