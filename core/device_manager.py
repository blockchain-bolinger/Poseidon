import subprocess
from typing import List, Optional
from core.logger import logger

class DeviceManager:
    def __init__(self, config=None, device_manager=None, adb=None):
        self.config = config if config is not None else {}
        self.current_serial = None
        self.devices = []
        self.device_config = {}
        self._device_manager = device_manager
        self._adb = adb
        logger.info("DeviceManager initialisiert.")

    def refresh_devices(self) -> List[str]:
        if self._adb is None:
            logger.debug("DeviceManager.refresh_devices fallback ohne ADBHandler.")
            return []

        result = self._adb.run("devices", timeout=10)
        if not result[2] == 0:
            logger.warning("adb devices fehlgeschlagen.")
            return []

        devices = []
        raw_stdout = result[0] or ""
        for line in raw_stdout.splitlines()[1:]:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("List of devices attached"):
                continue
            if "offline" in stripped:
                continue
            serial = stripped.split()[0]
            devices.append(serial)

        self.devices = devices
        logger.debug(f"Geräteliste aktualisiert: {devices}")
        if self.current_serial and self.current_serial not in devices:
            logger.warning(f"Zuvor ausgewähltes Gerät {self.current_serial} nicht mehr verbunden.")
            self.current_serial = None
        return devices

    def select_device(self) -> Optional[str]:
        devices = self.refresh_devices()
        if not devices:
            print("Keine Geräte gefunden.")
            return None
        if len(devices) == 1:
            serial = devices[0]
            self.current_serial = serial
            print(f"Einziges Gerät ausgewählt: {serial}")
            logger.info("Gerät automatisch ausgewählt: %s", serial)
            return serial
        print("Mehrere Geräte verfügbar:")
        for idx, serial in enumerate(devices, 1):
            print(f"{idx}. {serial}")
        try:
            choice = int(input("Bitte wählen: ")) - 1
            if 0 <= choice < len(devices):
                serial = devices[choice]
                self.current_serial = serial
                logger.info("Gerät manuell ausgewählt: %s", serial)
                return serial
            print("Ungültige Auswahl.")
            logger.warning("Ungültige Geräteauswahl getroffen (Index %s).", choice + 1)
            return None
        except Exception:
            print("Ungültige Eingabe.")
            logger.warning("Ungültige Eingabe bei Geräteauswahl.")
            return None

    def require_authorized_device(self, serial: Optional[str] = None) -> bool:
        serial = serial or self.get_current_device()
        if not serial:
            print("Kein Gerät ausgewählt.")
            logger.warning("Autorisierungscheck: kein Gerät ausgewählt.")
            return False
        if serial in self.refresh_devices():
            return True
        self.current_serial = None
        print("Gerät nicht mehr verbunden.")
        logger.warning("Autorisierungscheck fehlgeschlagen für Serial %s.", serial)
        return False

    def get_current_device(self) -> Optional[str]:
        """Gibt die Seriennummer des aktuell ausgewählten Geräts zurück."""
        if not self.current_serial:
            self.select_device()
        return self.current_serial

    def get_current_serial(self) -> Optional[str]:
        """Alias für get_current_device (für Kompatibilität)."""
        return self.get_current_device()

    def disconnect_all(self):
        """Trennt alle ADB-Verbindungen."""
        subprocess.run(["adb", "disconnect"], capture_output=True)
        self.current_serial = None
        self.devices = []
