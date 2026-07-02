from services.monitoring_service import MonitoringService
from services.monitoring_service import MonitoringService

from core.app import AppContext

CONTEXT = AppContext()

def build_monitoring_service(config):
    return MonitoringService(
        CONTEXT.device_manager,
        CONTEXT.adb,
        poseidon_version=config.get("version", "5.0-dev"),
        export_dir=config.get("global", {}).get("log_path", "./logs"),
    )


def show_menu(device_manager, adb, config):
    export_dir = config.get("global", {}).get("log_path", "./logs")
    service = build_monitoring_service(config)

    while True:
        print_header("Geräte-Monitoring", "Gerätemetriken mit Export")
        print("1. Einmalige Snapshot-Erfassung")
        print("2. Snapshot + CSV-Export")
        print("3. Snapshot + JSONL-Export")
        print("4. Snapshot + beide Exporte")
        print("0. Zurück")

        choice = menu_prompt("Option wählen", range(0, 5))
        if choice == 0:
            break

        metrics = service.collect_once()
        data = metrics.to_dict()

        print("-" * 50)
        for key, value in data.items():
            print(f"{key}: {value}")

        if choice == 2:
            path = service.export_csv(metrics)
            print(f"CSV exportiert nach: {path}")
        elif choice == 3:
            path = service.export_jsonl(metrics)
            print(f"JSONL exportiert nach: {path}")
        elif choice == 4:
            csv_path = service.export_csv(metrics)
            jsonl_path = service.export_jsonl(metrics)
            print(f"CSV exportiert nach: {csv_path}")
            print(f"JSONL exportiert nach: {jsonl_path}")

        wait_for_enter()
