from __future__ import annotations

import asyncio
from pathlib import Path

import aiohttp

from .models import BoardItem, Peer

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)
DOWNLOAD_TIMEOUT = aiohttp.ClientTimeout(total=None, sock_connect=10, sock_read=60)


class PeerRegistry:
    """Tracks discovered peers and fetches their boards over HTTP."""

    def __init__(self):
        self._peers: dict[str, Peer] = {}
        self._lock = asyncio.Lock()

    @property
    def peers(self) -> list[Peer]:
        return sorted(self._peers.values(), key=lambda p: p.name.lower())

    def add(self, peer: Peer) -> None:
        self._peers[peer.id] = peer

    def remove(self, peer_id: str) -> None:
        self._peers.pop(peer_id, None)

    async def fetch_board(self, peer: Peer) -> list[BoardItem]:
        async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
            async with session.get(f"{peer.base_url}/api/board") as resp:
                resp.raise_for_status()
                data = await resp.json()
        return [BoardItem.from_dict(entry) for entry in data.get("items", [])]

    async def fetch_all_boards(self) -> dict[str, list[BoardItem]]:
        """Returns {peer_id: items}. Unreachable peers are kept in the registry
        so they can be retried on the next refresh; mDNS remove_service handles
        permanent removal."""
        peers = list(self._peers.values())
        results = await asyncio.gather(
            *(self.fetch_board(p) for p in peers), return_exceptions=True
        )
        boards: dict[str, list[BoardItem]] = {}
        for peer, result in zip(peers, results):
            if not isinstance(result, BaseException):
                boards[peer.id] = result
        return boards

    async def download_file(
        self, peer: Peer, item: BoardItem, target_path: str | Path
    ) -> Path:
        target = Path(target_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        async with aiohttp.ClientSession(timeout=DOWNLOAD_TIMEOUT) as session:
            async with session.get(peer.item_url(item.id)) as resp:
                resp.raise_for_status()
                with target.open("wb") as fh:
                    async for chunk in resp.content.iter_chunked(1 << 16):
                        fh.write(chunk)
        return target
