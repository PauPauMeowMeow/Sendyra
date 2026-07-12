from __future__ import annotations

import json
import socket
import uuid
from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "Sendyra"
DEFAULT_PORT = 53317
SERVICE_TYPE = "_sendyra._tcp.local."


def data_dir() -> Path:
    path = Path(user_data_dir(APP_NAME, appauthor=False))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _settings_path() -> Path:
    return data_dir() / "settings.json"


def load_settings() -> dict:
    path = _settings_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_settings(settings: dict) -> None:
    _settings_path().write_text(
        json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_identity() -> tuple[str, str]:
    """Return persistent (device_id, device_name)."""
    settings = load_settings()
    changed = False
    if "device_id" not in settings:
        settings["device_id"] = uuid.uuid4().hex
        changed = True
    if "device_name" not in settings:
        settings["device_name"] = socket.gethostname() or "Sendyra Device"
        changed = True
    if changed:
        save_settings(settings)
    return settings["device_id"], settings["device_name"]


def set_device_name(name: str) -> None:
    settings = load_settings()
    settings["device_name"] = name
    save_settings(settings)


def get_local_ip() -> str:
    """Best-effort detection of the LAN IP address."""
    try:
        from .android import get_wifi_ip

        ip = get_wifi_ip()
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
            if ip and not ip.startswith("127."):
                return ip
        except OSError:
            pass
        finally:
            sock.close()
    except Exception:
        pass

    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if ip and not ip.startswith("127.") and not ip.startswith("0.0.0.0"):
                return ip
    except OSError:
        pass

    return "127.0.0.1"
