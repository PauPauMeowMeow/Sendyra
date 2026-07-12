from __future__ import annotations

import asyncio
from dataclasses import dataclass

from ..config import DEFAULT_PORT, data_dir, get_identity
from ..core.board import LocalBoard
from ..core.discovery import Discovery
from ..core.models import BoardItem, Peer
from ..core.peers import PeerRegistry

REFRESH_INTERVAL = 3.0


@dataclass
class DisplayItem:
    item: BoardItem
    owner_name: str
    peer: Peer | None  # None for own items


class AppState:
    """Application state shared between views: local board, peers, aggregated items."""

    def __init__(self):
        self.device_id, self.device_name = get_identity()
        self.board = LocalBoard(data_dir())
        self.registry = PeerRegistry()
        self.discovery: Discovery | None = None
        self.port: int = DEFAULT_PORT
        self.display_items: list[DisplayItem] = []
        self.on_change: list = []  # callbacks invoked after refresh

    async def start_discovery(self) -> None:
        self.discovery = Discovery(
            self.device_id,
            self.device_name,
            self.port,
            on_peer_added=self.registry.add,
            on_peer_removed=self.registry.remove,
        )
        await self.discovery.start()

    async def stop(self) -> None:
        if self.discovery is not None:
            await self.discovery.stop()

    def _notify(self) -> None:
        for callback in self.on_change:
            callback()

    async def refresh(self) -> None:
        boards = await self.registry.fetch_all_boards()
        items: list[DisplayItem] = [
            DisplayItem(item=i, owner_name=self.device_name, peer=None)
            for i in self.board.items
        ]
        peer_map = {p.id: p for p in self.registry.peers}
        for peer_id, peer_items in boards.items():
            peer = peer_map.get(peer_id)
            if peer is None:
                continue
            items.extend(
                DisplayItem(item=i, owner_name=peer.name, peer=peer)
                for i in peer_items
            )
        items.sort(key=lambda d: d.item.created, reverse=True)
        self.display_items = items
        self._notify()

    async def refresh_loop(self) -> None:
        while True:
            try:
                await self.refresh()
            except Exception:
                pass
            await asyncio.sleep(REFRESH_INTERVAL)
