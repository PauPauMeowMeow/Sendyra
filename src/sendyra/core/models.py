from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class BoardItem:
    id: str
    kind: str  # "text" | "file"
    name: str = ""  # file name for files, short preview for texts
    text: str = ""  # full text for text items
    size: int = 0  # file size in bytes
    created: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BoardItem":
        return cls(
            id=data["id"],
            kind=data["kind"],
            name=data.get("name", ""),
            text=data.get("text", ""),
            size=int(data.get("size", 0)),
            created=float(data.get("created", 0)),
        )


@dataclass
class Peer:
    id: str
    name: str
    host: str
    port: int

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def item_url(self, item_id: str) -> str:
        return f"{self.base_url}/api/item/{item_id}"
