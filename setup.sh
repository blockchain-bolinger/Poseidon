#!/bin/bash

# ============================================================================
# Poseidon - System Setup Script
# Installiert alle notwendigen System-Abhängigkeiten für Linux (Debian/Ubuntu)
# ============================================================================

# Farben für die Ausgabe
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}          Poseidon - System Abhängigkeiten Setup            ${NC}"
echo -e "${GREEN}============================================================${NC}"

# Prüfen auf Root/Sudo-Rechte
if [ "$EUID" -ne 0 ]; then
  echo -e "${YELLOW}[!] Bitte führen Sie dieses Skript mit sudo aus oder geben Sie Ihr Passwort gleich ein.${NC}"
fi

# 1. System-Pakete aktualisieren
echo -e "\n${GREEN}[1/4] Aktualisiere Paketlisten...${NC}"
sudo apt update

# 2. Notwendige Binärdateien installieren
echo -e "\n${GREEN}[2/4] Installiere System-Tools (adb, scrcpy, ffmpeg, nmap, net-tools, tcpdump, tesseract-ocr)...${NC}"
sudo apt install -y adb scrcpy ffmpeg nmap net-tools tcpdump tesseract-ocr

# 3. USB-Berechtigungen einrichten (Benutzer zur plugdev Gruppe hinzufügen)
echo -e "\n${GREEN}[3/4] Richte USB-Berechtigungen ein...${NC}"
sudo usermod -aG plugdev $USER
echo -e "${YELLOW}[i] Hinweis: Damit die USB-Rechte aktiv werden, müssen Sie sich evtl. einmal aus- und einloggen.${NC}"

# 4. Python-Abhängigkeiten sicherstellen
echo -e "\n${GREEN}[4/4] Installiere Python-Abhängigkeiten...${NC}"
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtuelle Umgebung gefunden, nutze venv/bin/pip...${NC}"
    ./venv/bin/pip install -r requirements.txt
else
    echo -e "${YELLOW}Keine venv gefunden, nutze system-pip...${NC}"
    pip install -r requirements.txt || pip3 install -r requirements.txt
fi

echo -e "\n${GREEN}============================================================${NC}"
echo -e "${GREEN}🎉 Setup abgeschlossen!${NC}"
echo -e "Sie können Poseidon nun mit ${YELLOW}python3 main.py${NC} starten."
echo -e "${GREEN}============================================================${NC}"
