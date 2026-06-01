# ============================================================================
# Poseidon - Dockerfile
# ============================================================================
# Basis-Image: Python 3.10-slim für Stabilität und Paket-Kompatibilität
FROM python:3.10-slim

# Umgebungsvariablen setzen
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System-Abhängigkeiten installieren
# adb, tesseract-ocr, ffmpeg, nmap, net-tools und tcpdump
RUN apt-get update && apt-get install -y --no-install-recommends \
    android-tools-adb \
    tesseract-ocr \
    ffmpeg \
    nmap \
    net-tools \
    tcpdump \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis erstellen
WORKDIR /app

# Python-Abhängigkeiten kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Den gesamten Projektcode in das Image kopieren
COPY . .

# Standard-Verzeichnisse für Runtime-Dateien erstellen
RUN mkdir -p logs backups screenshots plugins

# Standard-Port für Poseidon Web-GUI (falls verwendet)
EXPOSE 8000

# Standard-Befehl beim Starten des Containers
# Ermöglicht das Starten des interaktiven TUI oder Überschreiben per CLI
CMD ["python", "main.py"]

# ============================================================================
# 📖 ANLEITUNG ZUM BAUEN & RUNNEN
# ============================================================================
#
# 1. Image bauen:
#    docker build -t poseidon .
#
# 2. Container ausführen (Option A: Direkt über USB - Linux Hosts):
#    docker run -it --privileged -v /dev/bus/usb:/dev/bus/usb poseidon
#
# 3. Container ausführen (Option B: ADB-Server des Hosts mitnutzen - Cross-Platform):
#    Auf dem PC/Host den ADB-Server im Netzwerkmodus starten:
#       adb kill-server
#       adb -a nodaemon server start
#    Dann den Container starten und die Host-IP übergeben (z.B. 172.17.0.1):
#       docker run -it -e ADB_SERVER_SOCKET=tcp:172.17.0.1:5037 poseidon
#
# 4. Web-GUI ausführen (wenn Tool 5 implementiert ist):
#    docker run -it -p 8000:8000 -e ADB_SERVER_SOCKET=tcp:172.17.0.1:5037 poseidon python main.py --web
# ============================================================================
