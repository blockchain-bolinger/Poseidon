from __future__ import annotations

import json
import shlex
import shutil
import subprocess
import uuid
import webbrowser
from pathlib import Path
from typing import Iterable, Sequence
from urllib import error, request


def normalize_command(command: str | Sequence[str]) -> list[str]:
    if isinstance(command, (list, tuple)):
        return [str(part) for part in command if str(part).strip()]
    if not command:
        return []
    return shlex.split(str(command))


def command_available(command: str | Sequence[str]) -> bool:
    parts = normalize_command(command)
    if not parts:
        return False
    exe = parts[0]
    return Path(exe).expanduser().exists() or shutil.which(exe) is not None


def command_display(command: str | Sequence[str]) -> str:
    return " ".join(normalize_command(command))


def run_command(command: str | Sequence[str], cwd: str | Path | None = None, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    parts = normalize_command(command)
    if not parts:
        raise ValueError("Leerer Befehl")
    return subprocess.run(
        parts,
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def spawn_command(command: str | Sequence[str], cwd: str | Path | None = None) -> subprocess.Popen[str]:
    parts = normalize_command(command)
    if not parts:
        raise ValueError("Leerer Befehl")
    return subprocess.Popen(
        parts,
        cwd=str(cwd) if cwd is not None else None,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        text=True,
    )


def open_url(url: str) -> bool:
    return webbrowser.open(url, new=2)


FRIDA_PROCESS_PRESETS = [
    ("Discovery", ["-U"], "Prozessliste auf dem verbundenen Gerät"),
    ("Spawn attach", ["-U", "-f", "<package-or-binary>", "--no-pause"], "App spawnen und anhalten"),
    ("Attach target", ["-U", "-n", "<process-name>"], "An einen laufenden Prozess anhängen"),
]

OBJECTION_PRESETS = [
    ("Explore", ["-g", "<package>", "explore"], "Interaktive Analyse-Shell"),
    ("Run command", ["-g", "<package>", "run", "<objection-command>"], "Einzelnen Objection-Befehl ausführen"),
    ("Device info", ["-g", "<package>", "device", "info"], "Geräte- und Kontextinfos"),
]


def mobsf_multipart_body(field_name: str, filename: str, content: bytes, boundary: str | None = None) -> tuple[bytes, str]:
    boundary = boundary or f"----Poseidon{uuid.uuid4().hex}"
    lines = [
        f"--{boundary}",
        f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"',
        "Content-Type: application/vnd.android.package-archive",
        "",
    ]
    body = "\r\n".join(lines).encode("utf-8") + b"\r\n" + content + b"\r\n" + f"--{boundary}--\r\n".encode("utf-8")
    return body, boundary


def mobsf_upload_and_scan(apk_path: str | Path, base_url: str, api_key: str, timeout: int = 120) -> dict:
    apk_path = Path(apk_path).expanduser()
    if not apk_path.exists():
        raise FileNotFoundError(f"APK nicht gefunden: {apk_path}")

    base = str(base_url).rstrip("/")
    upload_url = f"{base}/api/v1/upload"
    scan_url = f"{base}/api/v1/scan"

    data = apk_path.read_bytes()
    body, boundary = mobsf_multipart_body("file", apk_path.name, data)

    headers = {
        "Authorization": api_key,
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Accept": "application/json",
    }
    req = request.Request(upload_url, data=body, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            upload_raw = resp.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        raise RuntimeError(f"MobSF Upload fehlgeschlagen: HTTP {exc.code} {exc.reason}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"MobSF Upload fehlgeschlagen: {exc.reason}") from exc

    upload_json = json.loads(upload_raw)
    scan_hash = upload_json.get("hash") or upload_json.get("file_sha256") or upload_json.get("file_name")
    if not scan_hash:
        raise RuntimeError(f"MobSF Upload lieferte keinen Hash: {upload_json}")

    scan_payload = json.dumps({"hash": scan_hash})
    scan_req = request.Request(
        scan_url,
        data=scan_payload.encode("utf-8"),
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(scan_req, timeout=timeout) as resp:
            scan_raw = resp.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        raise RuntimeError(f"MobSF Scan fehlgeschlagen: HTTP {exc.code} {exc.reason}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"MobSF Scan fehlgeschlagen: {exc.reason}") from exc

    try:
        scan_json = json.loads(scan_raw)
    except json.JSONDecodeError:
        scan_json = {"raw": scan_raw}

    return {
        "upload": upload_json,
        "scan": scan_json,
        "hash": scan_hash,
        "upload_url": upload_url,
        "scan_url": scan_url,
    }
