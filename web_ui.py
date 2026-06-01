#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import uvicorn
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from core.device_manager import DeviceManager
from core.adb_handler import ADBHandler
from services.vision_service import VisionService

app = FastAPI(title="Poseidon Web Remote Dashboard")

# Global variables for hardware interaction
config = {}
device_manager = None
adb = None
vision = None

def init_runtime():
    global config, device_manager, adb, vision
    # Load settings
    config_path = BASE_DIR / "config.json"
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            config = {}
    
    # Defaults
    if "global" not in config:
        config["global"] = {
            "screenshot_path": "./screenshots",
            "log_path": "./logs",
            "backup_path": "./backups"
        }
    
    # Ensure folders exist
    Path(config["global"].get("screenshot_path", "./screenshots")).mkdir(parents=True, exist_ok=True)
    Path(config["global"].get("log_path", "./logs")).mkdir(parents=True, exist_ok=True)
    Path(config["global"].get("backup_path", "./backups")).mkdir(parents=True, exist_ok=True)
    
    device_manager = DeviceManager(config)
    adb = ADBHandler(device_manager)
    vision = VisionService(device_manager, adb, screenshot_dir=config["global"].get("screenshot_path", "./screenshots"))

# Request models
class TapRequest(BaseModel):
    x: int
    y: int

class TextRequest(BaseModel):
    text: str

class KeycodeRequest(BaseModel):
    keycode: int

@app.on_event("startup")
def startup_event():
    init_runtime()

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    html_content = """
    <!DOCTYPE html>
    <html lang="de" class="dark">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🌊 Poseidon - Web Remote Controller</title>
        <!-- Tailwind CSS CDN -->
        <script src="https://cdn.tailwindcss.com"></script>
        <!-- Font Awesome -->
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <!-- Google Font -->
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
        <script>
            tailwind.config = {
                darkMode: 'class',
                theme: {
                    extend: {
                        fontFamily: {
                            sans: ['Outfit', 'sans-serif'],
                        },
                        colors: {
                            glow: '#00f2fe',
                            deepbg: '#0b0f19',
                            cardbg: 'rgba(20, 27, 45, 0.7)',
                        }
                    }
                }
            }
        </script>
        <style>
            body {
                background: radial-gradient(circle at 50% 50%, #152238 0%, #0b0f19 100%);
                font-family: 'Outfit', sans-serif;
            }
            .glass {
                background: rgba(17, 25, 40, 0.75);
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            .glow-effect:hover {
                box-shadow: 0 0 20px rgba(0, 242, 254, 0.4);
                border-color: rgba(0, 242, 254, 0.6);
            }
            /* Custom Scrollbar */
            ::-webkit-scrollbar {
                width: 6px;
            }
            ::-webkit-scrollbar-track {
                background: rgba(0, 0, 0, 0.2);
            }
            ::-webkit-scrollbar-thumb {
                background: rgba(0, 242, 254, 0.3);
                border-radius: 3px;
            }
            ::-webkit-scrollbar-thumb:hover {
                background: rgba(0, 242, 254, 0.6);
            }
        </style>
    </head>
    <body class="text-white min-h-screen flex flex-col pb-6">

        <!-- Navigation Header -->
        <header class="w-full glass py-4 px-6 border-b border-white/10 flex justify-between items-center z-10">
            <div class="flex items-center space-x-3">
                <span class="text-3xl">🌊</span>
                <div>
                    <h1 class="text-xl font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-[#00f2fe] to-[#4facfe]">
                        POSEIDON
                    </h1>
                    <p class="text-xs text-white/50 tracking-widest uppercase">ADB Web Controller</p>
                </div>
            </div>
            <div class="flex items-center space-x-4">
                <div id="deviceStatus" class="flex items-center space-x-2 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-3 py-1 rounded-full text-xs font-semibold">
                    <span class="relative flex h-2 w-2">
                        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                        <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                    </span>
                    <span id="deviceName">Warte auf Verbindung...</span>
                </div>
                <button onclick="refreshData()" class="glass hover:bg-white/10 p-2 rounded-full transition duration-300" title="Daten aktualisieren">
                    <i class="fa-solid fa-arrows-rotate text-glow"></i>
                </button>
            </div>
        </header>

        <!-- Main Dashboard Container -->
        <main class="flex-grow max-w-7xl w-full mx-auto px-4 md:px-6 py-6 grid grid-cols-1 lg:grid-cols-12 gap-6">

            <!-- Linke Spalte: Screenshot & Remote Buttons (5 Cols) -->
            <section class="lg:col-span-5 flex flex-col space-y-4">
                <div class="glass rounded-2xl p-4 flex flex-col items-center">
                    <h2 class="text-sm font-semibold uppercase tracking-wider text-white/50 mb-3 w-full flex justify-between items-center">
                        <span><i class="fa-solid fa-mobile-screen-button text-glow mr-1"></i> Live Screen</span>
                        <span class="text-xs lowercase text-white/40">Klick zum Tippen</span>
                    </h2>
                    
                    <!-- Screen Container with Interactive Image -->
                    <div class="relative max-h-[600px] w-full flex justify-center bg-black/40 rounded-xl overflow-hidden border border-white/5">
                        <img id="screenshotImg" src="/api/screenshot?t=0" alt="Android Screen" 
                             class="object-contain cursor-crosshair max-h-[500px]" 
                             onclick="handleScreenClick(event)" />
                        <!-- Loading spinner on update -->
                        <div id="screenLoader" class="absolute inset-0 bg-black/60 flex items-center justify-center hidden">
                            <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-glow"></div>
                        </div>
                    </div>

                    <!-- Navigation Keys Bar -->
                    <div class="w-full grid grid-cols-4 gap-2 mt-4">
                        <button onclick="sendKeycode(4)" class="glass hover:bg-white/10 py-2.5 rounded-xl flex flex-col items-center transition duration-300 glow-effect" title="Zurück">
                            <i class="fa-solid fa-chevron-left text-glow"></i>
                            <span class="text-[10px] mt-1 text-white/60">Zurück</span>
                        </button>
                        <button onclick="sendKeycode(3)" class="glass hover:bg-white/10 py-2.5 rounded-xl flex flex-col items-center transition duration-300 glow-effect" title="Home">
                            <i class="fa-solid fa-house text-glow"></i>
                            <span class="text-[10px] mt-1 text-white/60">Home</span>
                        </button>
                        <button onclick="sendKeycode(187)" class="glass hover:bg-white/10 py-2.5 rounded-xl flex flex-col items-center transition duration-300 glow-effect" title="Kürzliche Apps">
                            <i class="fa-solid fa-bars text-glow"></i>
                            <span class="text-[10px] mt-1 text-white/60">Recents</span>
                        </button>
                        <button onclick="sendKeycode(26)" class="glass hover:bg-white/10 py-2.5 rounded-xl flex flex-col items-center bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 transition duration-300" title="Power">
                            <i class="fa-solid fa-power-off text-red-400"></i>
                            <span class="text-[10px] mt-1 text-red-300/80">Power</span>
                        </button>
                    </div>
                </div>

                <!-- Text-Eingabe Panel -->
                <div class="glass rounded-2xl p-4">
                    <h3 class="text-sm font-semibold uppercase tracking-wider text-white/50 mb-3">
                        <i class="fa-regular fa-keyboard text-glow mr-1"></i> Tastatur-Eingabe
                    </h3>
                    <div class="flex space-x-2">
                        <input type="text" id="keyboardText" placeholder="Text auf Gerät eingeben..." 
                               class="flex-grow bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-sm focus:outline-none focus:border-glow transition"
                               onkeydown="if(event.key === 'Enter') sendText()"/>
                        <button onclick="sendText()" class="bg-gradient-to-r from-glow to-[#4facfe] hover:opacity-90 px-4 py-2 rounded-xl text-black font-semibold text-sm transition">
                            Senden
                        </button>
                    </div>
                </div>
            </section>

            <!-- Rechte Spalte: Stats, OCR und Logcat (7 Cols) -->
            <section class="lg:col-span-7 flex flex-col space-y-6">

                <!-- Device Metrics Card -->
                <div class="glass rounded-2xl p-5">
                    <h3 class="text-sm font-semibold uppercase tracking-wider text-white/50 mb-4">
                        <i class="fa-solid fa-gauge-high text-glow mr-1"></i> Geräte-Statistiken
                    </h3>
                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
                        <div class="bg-black/30 p-3 rounded-xl border border-white/5 flex flex-col">
                            <span class="text-xs text-white/40">Modell</span>
                            <span id="statModel" class="text-sm font-semibold mt-1 truncate">-</span>
                        </div>
                        <div class="bg-black/30 p-3 rounded-xl border border-white/5 flex flex-col">
                            <span class="text-xs text-white/40">Akku-Ladung</span>
                            <span id="statBattery" class="text-sm font-semibold mt-1 text-emerald-400">-</span>
                        </div>
                        <div class="bg-black/30 p-3 rounded-xl border border-white/5 flex flex-col">
                            <span class="text-xs text-white/40">Akku-Temp</span>
                            <span id="statTemp" class="text-sm font-semibold mt-1 text-amber-400">-</span>
                        </div>
                        <div class="bg-black/30 p-3 rounded-xl border border-white/5 flex flex-col">
                            <span class="text-xs text-white/40">Laufzeit</span>
                            <span id="statUptime" class="text-sm font-semibold mt-1 truncate">-</span>
                        </div>
                    </div>
                </div>

                <!-- OCR / Vision Card -->
                <div class="glass rounded-2xl p-5">
                    <h3 class="text-sm font-semibold uppercase tracking-wider text-white/50 mb-3">
                        <i class="fa-solid fa-eye text-glow mr-1"></i> OCR Vision Textsuche
                    </h3>
                    <div class="flex space-x-2 mb-3">
                        <input type="text" id="ocrQuery" placeholder="Wort oder Phrase auf Bildschirm suchen..." 
                               class="flex-grow bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-sm focus:outline-none focus:border-glow transition"
                               onkeydown="if(event.key === 'Enter') runOcr()"/>
                        <button onclick="runOcr()" class="bg-glow hover:opacity-90 text-black px-4 py-2 rounded-xl font-semibold text-sm transition">
                            Scannen
                        </button>
                    </div>
                    <!-- OCR Results Output -->
                    <div id="ocrOutput" class="text-xs text-white/50 bg-black/30 rounded-xl p-3 border border-white/5 hidden max-h-32 overflow-y-auto">
                        <!-- Dynamic matches -->
                    </div>
                </div>

                <!-- Logcat Card -->
                <div class="glass rounded-2xl p-5 flex-grow flex flex-col min-h-[300px]">
                    <div class="flex justify-between items-center mb-3">
                        <h3 class="text-sm font-semibold uppercase tracking-wider text-white/50">
                            <i class="fa-solid fa-terminal text-glow mr-1"></i> Logcat Live Stream
                        </h3>
                        <div class="flex space-x-2">
                            <button onclick="clearLogcatUI()" class="text-xs text-white/40 hover:text-white/80 transition">
                                <i class="fa-solid fa-trash-can mr-1"></i> Leeren
                            </button>
                        </div>
                    </div>
                    <!-- Log output console -->
                    <div id="logcatConsole" class="flex-grow bg-black/50 border border-white/10 rounded-xl p-4 font-mono text-[11px] text-white/80 overflow-y-auto max-h-[350px] space-y-1">
                        <div class="text-white/40">[System] Logcat wird geladen...</div>
                    </div>
                </div>

            </section>
        </main>

        <footer class="text-center text-xs text-white/30 mt-6">
            Poseidon ADB Suite - Web Client & Remote API.
        </footer>

        <!-- Scripts -->
        <script>
            // Elements
            const screenshotImg = document.getElementById('screenshotImg');
            const screenLoader = document.getElementById('screenLoader');
            const deviceName = document.getElementById('deviceName');
            const deviceStatus = document.getElementById('deviceStatus');
            const logcatConsole = document.getElementById('logcatConsole');

            // Stats Elements
            const statModel = document.getElementById('statModel');
            const statBattery = document.getElementById('statBattery');
            const statTemp = document.getElementById('statTemp');
            const statUptime = document.getElementById('statUptime');

            // OCR Elements
            const ocrQuery = document.getElementById('ocrQuery');
            const ocrOutput = document.getElementById('ocrOutput');

            // Refresh Screen (Screenshot cache-busting timestamp)
            function refreshScreen() {
                screenLoader.classList.remove('hidden');
                const timestamp = new Date().getTime();
                screenshotImg.src = `/api/screenshot?t=${timestamp}`;
            }

            screenshotImg.onload = function() {
                screenLoader.classList.add('hidden');
            };

            screenshotImg.onerror = function() {
                screenLoader.classList.add('hidden');
                console.error("Screenshot konnte nicht geladen werden.");
            };

            // Click Interaction
            async function handleScreenClick(event) {
                const img = event.target;
                const rect = img.getBoundingClientRect();
                
                // Get click relative to image boundaries
                const clickX = event.clientX - rect.left;
                const clickY = event.clientY - rect.top;
                
                // Scale according to actual device resolution
                const trueWidth = img.naturalWidth;
                const trueHeight = img.naturalHeight;
                
                if (!trueWidth || !trueHeight) return;
                
                const deviceX = Math.round((clickX / rect.width) * trueWidth);
                const deviceY = Math.round((clickY / rect.height) * trueHeight);
                
                console.log(`Tapping at: X=${deviceX}, Y=${deviceY}`);
                
                // Send API post
                screenLoader.classList.remove('hidden');
                try {
                    const response = await fetch('/api/tap', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ x: deviceX, y: deviceY })
                    });
                    const resData = await response.json();
                    if (resData.status === 'ok') {
                        // Immediately refresh screenshot after tapping
                        setTimeout(refreshScreen, 400);
                    } else {
                        alert("Tippen fehlgeschlagen: " + resData.detail);
                        screenLoader.classList.add('hidden');
                    }
                } catch (e) {
                    console.error("Fehler beim Senden des Tap-Events", e);
                    screenLoader.classList.add('hidden');
                }
            }

            // Keycodes sending
            async function sendKeycode(code) {
                screenLoader.classList.remove('hidden');
                try {
                    const response = await fetch('/api/keycode', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ keycode: code })
                    });
                    await response.json();
                    setTimeout(refreshScreen, 400);
                } catch (e) {
                    console.error(e);
                    screenLoader.classList.add('hidden');
                }
            }

            // Text input sending
            async function sendText() {
                const input = document.getElementById('keyboardText');
                const val = input.value.trim();
                if (!val) return;
                
                screenLoader.classList.remove('hidden');
                try {
                    const response = await fetch('/api/text', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ text: val })
                    });
                    await response.json();
                    input.value = "";
                    setTimeout(refreshScreen, 600);
                } catch (e) {
                    console.error(e);
                    screenLoader.classList.add('hidden');
                }
            }

            // OCR Scanning
            async function runOcr() {
                const val = ocrQuery.value.trim();
                if (!val) return;
                
                ocrOutput.classList.remove('hidden');
                ocrOutput.innerHTML = `<span class="text-glow animate-pulse"><i class="fa-solid fa-spinner animate-spin"></i> OCR läuft für "${val}"...</span>`;
                
                try {
                    const response = await fetch(`/api/ocr?query=${encodeURIComponent(val)}`);
                    const data = await response.json();
                    
                    if (data.count === 0) {
                        ocrOutput.innerHTML = `<span class="text-red-400">Keine Treffer gefunden für "${val}".</span>`;
                    } else {
                        let html = `<div class="font-semibold text-white mb-1">Gefundene Treffer (${data.count}):</div><div class="space-y-1">`;
                        data.matches.forEach(m => {
                            html += `
                                <div class="flex justify-between items-center bg-white/5 px-2 py-1 rounded border border-white/5">
                                    <span>"${m.text}" (Konfidenz: ${m.confidence.toFixed(1)}%)</span>
                                    <button onclick="triggerTap(${m.left + Math.round(m.width/2)}, ${m.top + Math.round(m.height/2)})" class="text-glow hover:underline">
                                        Tippen (${m.left + Math.round(m.width/2)}, ${m.top + Math.round(m.height/2)})
                                    </button>
                                </div>
                            `;
                        });
                        html += `</div>`;
                        ocrOutput.innerHTML = html;
                    }
                } catch (e) {
                    ocrOutput.innerHTML = `<span class="text-red-500">OCR-Fehler: ${e.message}</span>`;
                }
            }

            async function triggerTap(x, y) {
                screenLoader.classList.remove('hidden');
                try {
                    await fetch('/api/tap', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ x: x, y: y })
                    });
                    setTimeout(refreshScreen, 500);
                } catch (e) {
                    console.error(e);
                    screenLoader.classList.add('hidden');
                }
            }

            // Stats and Data fetching
            async function refreshData() {
                try {
                    const response = await fetch('/api/device');
                    const data = await response.json();
                    
                    if (data.connected) {
                        deviceName.innerText = data.serial;
                        deviceStatus.className = "flex items-center space-x-2 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-3 py-1 rounded-full text-xs font-semibold";
                        
                        statModel.innerText = data.model || "Unbekannt";
                        statBattery.innerText = data.battery_level ? `${data.battery_level}%` : "-";
                        statTemp.innerText = data.battery_temp ? `${data.battery_temp}°C` : "-";
                        statUptime.innerText = data.uptime || "-";
                    } else {
                        deviceName.innerText = "Kein Gerät verbunden";
                        deviceStatus.className = "flex items-center space-x-2 bg-red-500/10 text-red-400 border border-red-500/20 px-3 py-1 rounded-full text-xs font-semibold";
                        
                        statModel.innerText = "-";
                        statBattery.innerText = "-";
                        statTemp.innerText = "-";
                        statUptime.innerText = "-";
                    }
                } catch (e) {
                    console.error("Fehler beim Holen der Gerätedaten", e);
                }
                
                // Refresh logcat logs
                fetchLogcat();
            }

            // Logcat Polling
            async function fetchLogcat() {
                try {
                    const response = await fetch('/api/logcat');
                    const lines = await response.json();
                    
                    if (lines.length > 0) {
                        logcatConsole.innerHTML = "";
                        lines.forEach(l => {
                            const row = document.createElement('div');
                            row.className = "hover:bg-white/5 py-0.5 border-b border-white/5 leading-relaxed truncate";
                            
                            // Simple coloring classes for rows
                            if (l.includes(" E/") || l.includes("ERROR:") || l.includes("FATAL:")) {
                                row.classList.add("text-red-400");
                            } else if (l.includes(" W/") || l.includes("WARNING:")) {
                                row.classList.add("text-yellow-400");
                            } else if (l.includes(" I/") || l.includes("INFO:")) {
                                row.classList.add("text-green-400");
                            } else if (l.includes(" D/") || l.includes("DEBUG:")) {
                                row.classList.add("text-cyan-400");
                            }
                            row.innerText = l;
                            logcatConsole.appendChild(row);
                        });
                        // Scroll to bottom
                        logcatConsole.scrollTop = logcatConsole.scrollHeight;
                    }
                } catch(e) {
                    console.error("Fehler bei Logcat-Abfrage", e);
                }
            }

            function clearLogcatUI() {
                logcatConsole.innerHTML = '<div class="text-white/40">[System] Konsole geleert.</div>';
            }

            // Auto-refresh loops
            // Screen refresh every 6 seconds to save ADB resources
            setInterval(refreshScreen, 6000);
            
            // Stats & Logs refresh every 3 seconds
            setInterval(refreshData, 3000);

            // Run initial load
            window.onload = function() {
                refreshScreen();
                refreshData();
            };

        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/device")
async def get_device_info():
    serial = device_manager.get_current_device()
    if not serial:
        return {"connected": False}
    
    # Retrieve details via shell properties
    model = adb.get_device_property("ro.product.model", serial).strip()
    
    # Get battery level
    battery_level = None
    battery_temp = None
    bat_out, _, _ = adb.run_shell("dumpsys battery", serial)
    for line in bat_out.splitlines():
        if "level:" in line:
            try:
                battery_level = int(line.split(":")[-1].strip())
            except Exception:
                pass
        elif "temperature:" in line:
            try:
                # temperature is represented in tenths of degrees Centigrade (e.g. 350 = 35.0 C)
                battery_temp = float(line.split(":")[-1].strip()) / 10.0
            except Exception:
                pass

    # Uptime retrieval
    uptime_out, _, _ = adb.run_shell("uptime", serial)
    
    return {
        "connected": True,
        "serial": serial,
        "model": model,
        "battery_level": battery_level,
        "battery_temp": battery_temp,
        "uptime": uptime_out.strip()
    }

@app.get("/api/screenshot")
async def get_screenshot(t: Optional[str] = Query(None)):
    serial = device_manager.get_current_device()
    if not serial:
        raise HTTPException(status_code=400, detail="Kein Gerät verbunden")
        
    try:
        # Save preview to screenshot directory
        filename = "web_preview.png"
        target_path = vision.take_screenshot(serial=serial, filename=filename)
        return FileResponse(target_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Erstellen des Screenshots: {str(e)}")

@app.post("/api/tap")
async def post_tap(req: TapRequest):
    serial = device_manager.get_current_device()
    if not serial:
        raise HTTPException(status_code=400, detail="Kein Gerät verbunden")
        
    stdout, stderr, rc = adb.run_shell(f"input tap {req.x} {req.y}", serial=serial)
    if rc != 0:
        raise HTTPException(status_code=500, detail=f"Fehler beim Klicken: {stderr}")
    return {"status": "ok"}

@app.post("/api/text")
async def post_text(req: TextRequest):
    serial = device_manager.get_current_device()
    if not serial:
        raise HTTPException(status_code=400, detail="Kein Gerät verbunden")
    
    # Safe text transmission: escapes spaces for inputs
    # replace spaces with %s to allow adb input text to execute spaces
    safe_text = req.text.replace(" ", "%s")
    stdout, stderr, rc = adb.run_shell(f"input text '{safe_text}'", serial=serial)
    if rc != 0:
        raise HTTPException(status_code=500, detail=f"Fehler beim Texteingeben: {stderr}")
    return {"status": "ok"}

@app.post("/api/keycode")
async def post_keycode(req: KeycodeRequest):
    serial = device_manager.get_current_device()
    if not serial:
        raise HTTPException(status_code=400, detail="Kein Gerät verbunden")
        
    stdout, stderr, rc = adb.run_shell(f"input keyevent {req.keycode}", serial=serial)
    if rc != 0:
        raise HTTPException(status_code=500, detail=f"Fehler bei Tasten-Event: {stderr}")
    return {"status": "ok"}

@app.get("/api/logcat")
async def get_logcat_lines():
    serial = device_manager.get_current_device()
    if not serial:
        return []
    
    # Read last 50 logcat lines in dump mode
    stdout, _, _ = adb.run("logcat -d -t 50", serial=serial)
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    return lines

@app.get("/api/ocr")
async def get_ocr(query: str):
    serial = device_manager.get_current_device()
    if not serial:
        raise HTTPException(status_code=400, detail="Kein Gerät verbunden")
        
    try:
        # Take a snapshot and run OCR matching
        filename = "web_ocr_capture.png"
        target_path = vision.take_screenshot(serial=serial, filename=filename)
        matches = vision.find_text(query, target_path, min_confidence=20.0)
        return {
            "query": query,
            "count": len(matches),
            "matches": [m.to_dict() for m in matches]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR-Fehler: {str(e)}")

def main():
    print("============================================================")
    print("🌊 Starting Poseidon Web Remote Server on http://localhost:8000")
    print("   Press Ctrl+C to terminate the server.")
    print("============================================================")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    main()
