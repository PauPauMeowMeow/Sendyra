"""Android helpers: keep multicast enabled while using mDNS."""
from __future__ import annotations

import logging
import socket
import struct
from typing import Any


logger = logging.getLogger(__name__)


def _get_activity() -> Any | None:
    try:
        from jnius import autoclass
    except Exception:
        return None

    import os

    activity_host_class = os.environ.get("MAIN_ACTIVITY_HOST_CLASS_NAME")
    if not activity_host_class:
        return None
    try:
        activity_host = autoclass(activity_host_class)
        return activity_host.mActivity
    except Exception as exc:
        logger.debug("Could not get Android activity: %s", exc)
        return None


def acquire_multicast_lock() -> Any | None:
    """Acquire a WifiManager.MulticastLock so mDNS works on Android."""
    activity = _get_activity()
    if activity is None:
        return None
    try:
        Context = __import__("jnius").autoclass("android.content.Context")
        WifiManager = __import__("jnius").autoclass("android.net.wifi.WifiManager")
        wifi = activity.getSystemService(Context.WIFI_SERVICE)
        lock = wifi.createMulticastLock("sendyra")
        lock.setReferenceCounted(True)
        lock.acquire()
        logger.debug("Android multicast lock acquired")
        return lock
    except Exception as exc:
        logger.warning("Could not acquire Android multicast lock: %s", exc)
        return None


def release_multicast_lock(lock: Any | None) -> None:
    if lock is None:
        return
    try:
        lock.release()
    except Exception as exc:
        logger.warning("Could not release Android multicast lock: %s", exc)


def get_wifi_ip() -> str | None:
    """Return the WiFi IP address as reported by Android's WifiManager."""
    activity = _get_activity()
    if activity is None:
        return None
    try:
        Context = __import__("jnius").autoclass("android.content.Context")
        WifiManager = __import__("jnius").autoclass("android.net.wifi.WifiManager")
        wifi = activity.getSystemService(Context.WIFI_SERVICE)
        info = wifi.getConnectionInfo()
        if info is None:
            return None
        ip_int = info.getIpAddress()
        if ip_int == 0:
            return None
        return socket.inet_ntoa(struct.pack("<I", ip_int))
    except Exception as exc:
        logger.warning("Could not get Android WiFi IP: %s", exc)
        return None
