from __future__ import annotations

import asyncio
import socket
from typing import Callable

from zeroconf import InterfaceChoice, IPVersion, ServiceListener, ServiceInfo, Zeroconf
from zeroconf.asyncio import AsyncServiceBrowser, AsyncServiceInfo, AsyncZeroconf

from ..config import SERVICE_TYPE, get_local_ip
from .models import Peer


class Discovery(ServiceListener):
    """Announces this device via mDNS and discovers other Sendyra peers."""

    def __init__(
        self,
        device_id: str,
        device_name: str,
        port: int,
        on_peer_added: Callable[[Peer], None],
        on_peer_removed: Callable[[str], None],
    ):
        self._device_id = device_id
        self._device_name = device_name
        self._port = port
        self._on_peer_added = on_peer_added
        self._on_peer_removed = on_peer_removed
        self._azc: AsyncZeroconf | None = None
        self._browser: AsyncServiceBrowser | None = None
        self._service_info: ServiceInfo | None = None
        self._service_names: dict[str, str] = {}  # service name -> peer id

    async def start(self) -> None:
        self._azc = AsyncZeroconf(interfaces=InterfaceChoice.All, ip_version=IPVersion.V4Only)
        local_ip = get_local_ip()
        self._service_info = ServiceInfo(
            SERVICE_TYPE,
            f"{self._device_id}.{SERVICE_TYPE}",
            addresses=[socket.inet_aton(local_ip)],
            port=self._port,
            properties={"id": self._device_id, "name": self._device_name},
        )
        await self._azc.async_register_service(self._service_info)
        # Allow a short moment for the registration to be processed before browsing.
        await asyncio.sleep(0.5)
        self._browser = AsyncServiceBrowser(self._azc.zeroconf, SERVICE_TYPE, self)

    async def stop(self) -> None:
        if self._azc is None:
            return
        try:
            if self._browser is not None:
                await self._browser.async_cancel()
            if self._service_info is not None:
                await self._azc.async_unregister_service(self._service_info)
        finally:
            await self._azc.async_close()
            self._azc = None

    # -- ServiceListener callbacks (called on the asyncio event loop) --

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.create_task(self._resolve_service(zc, type_, name))

    async def _resolve_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = AsyncServiceInfo(type_, name)
        # Try a few times: mDNS address records may arrive shortly after the PTR announcement.
        for _ in range(2):
            if await info.async_request(zc, timeout=3000):
                break
            await asyncio.sleep(0.5)
        else:
            return
        props = {
            k.decode(): v.decode() if isinstance(v, bytes) else v
            for k, v in (info.properties or {}).items()
            if v is not None
        }
        peer_id = props.get("id", "")
        if not peer_id or peer_id == self._device_id:
            return
        addresses = info.parsed_addresses()
        if not addresses:
            return
        peer = Peer(
            id=peer_id,
            name=props.get("name", "Unknown"),
            host=addresses[0],
            port=info.port or 0,
        )
        self._service_names[name] = peer_id
        self._on_peer_added(peer)

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        # Service update may indicate an address/TXT change. Re-resolve and re-add.
        self.add_service(zc, type_, name)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        peer_id = self._service_names.pop(name, None)
        if peer_id:
            self._on_peer_removed(peer_id)
