import os
from utils.ui_helpers import wait_for_enter, confirm
from utils.ansi_colors import fg, style
from utils.file_utils import save_file, get_timestamp
from utils.cli_safety import sanitize_device_input
from utils.decorators import require_device
from core.logger import audit_logger

class AdvancedOps:
    def __init__(self, adb, serial, device_manager=None):
        self.adb = adb
        self.serial = serial
        self.device_manager = device_manager
        self.audit_log = "logs/audit.log"

    def _authorized(self) -> bool:
        if self.device_manager is None:
            return True
        if not self.serial:
            return False
        return self.device_manager.require_authorized_device(self.serial)

    def _log_audit(self, action, target):
        with open(self.audit_log, "a") as f:
            f.write(f"[AUDIT] {action} | Target: {target}\n")

    def ghost_clean(self):
        if not self._authorized():
            audit_logger.info("advanced_ops.ghost_clean denied serial=%s", self.serial)
            return
        audit_logger.info("advanced_ops.ghost_clean start serial=%s", self.serial)
        """Bereinigt Spuren von ADB-Artefakten."""
        print(f"{fg.CYAN}Bereinige System-Artefakte...{style.RESET}")
        self.adb.run_shell("rm -rf /data/local/tmp/*", self.serial)
        self.adb.run_shell("rm -rf /sdcard/Android/data/*/cache/*", self.serial)
        self._log_audit("GhostClean", "System/Cache")
        print("Bereinigung abgeschlossen.")

    def dump_ui_tree(self):
        if not self._authorized():
            audit_logger.info("advanced_ops.dump_ui_tree denied serial=%s", self.serial)
            return
        audit_logger.info("advanced_ops.dump_ui_tree start serial=%s", self.serial)
        """Extrahiert die komplette UI-Struktur als XML."""
        print("Erstelle UI-Dump...")
        self.adb.run_shell("uiautomator dump /sdcard/ui_dump.xml", self.serial)
        self.adb.run(f"pull /sdcard/ui_dump.xml ./ui_dump.xml", self.serial)
        self._log_audit("UIDump", "UI-Structure")
        print("UI-Dump nach ./ui_dump.xml extrahiert.")

    def list_hidden_intents(self, package):
        if not self._authorized():
            audit_logger.info("advanced_ops.list_hidden_intents denied serial=%s", self.serial)
            return
        audit_logger.info("advanced_ops.list_hidden_intents start serial=%s package=%s", self.serial, package)
        if not sanitize_device_input("package", package):
            print("Ungültiger Paketname.")
            wait_for_enter()
            return
        """Listet versteckte Intents einer App auf."""
        print(f"Suche versteckte Intents für {package}...")
        out, _, _ = self.adb.run_shell(f"dumpsys package {package} | grep -E 'intent-filter|action'", self.serial)
        print(out)
        self._log_audit("IntentScan", package)

    def set_device_identity(self, model, brand):
        if not self._authorized():
            audit_logger.info("advanced_ops.set_device_identity denied serial=%s", self.serial)
            return
        audit_logger.info("advanced_ops.set_device_identity start serial=%s model=%s brand=%s", self.serial, model, brand)
        safe_model = sanitize_device_input("model", model)
        safe_brand = sanitize_device_input("brand", brand)
        if not safe_model or not safe_brand:
            print("Ungültiger Model/Brand-Name.")
            wait_for_enter()
            return
        """Ändert die Identität des Geräts (erfordert Root)."""
        if not confirm("ACHTUNG: Erfordert Root. Wirklich build.prop überschreiben?"):
            return
        # Beispiel für ein Set-Command (muss remounted werden)
        self.adb.run_shell("mount -o remount,rw /system", self.serial)
        self.adb.run_shell(f"setprop ro.product.model '{safe_model}'", self.serial)
        self.adb.run_shell(f"setprop ro.product.brand '{safe_brand}'", self.serial)
        self._log_audit("IdentityChange", f"{safe_model}/{safe_brand}")
        print("Identity geändert (Reboot erforderlich).")
