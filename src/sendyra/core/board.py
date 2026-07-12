from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from .models import BoardItem

TEXT_PREVIEW_LEN = 80


class LocalBoard:
    """Stores this device's published items: texts in JSON, files on disk."""

    def __init__(self, base_dir: Path):
        self._dir = base_dir
        self._files_dir = base_dir / "files"
        self._files_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = base_dir / "board.json"
        self._items: dict[str, BoardItem] = {}
        self._load()

    def _load(self) -> None:
        if not self._index_path.exists():
            return
        try:
            raw = json.loads(self._index_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        for entry in raw:
            item = BoardItem.from_dict(entry)
            if item.kind == "file" and not self.file_path(item.id).exists():
                continue
            self._items[item.id] = item

    def _save(self) -> None:
        data = [item.to_dict() for item in self._items.values()]
        self._index_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @property
    def items(self) -> list[BoardItem]:
        return sorted(self._items.values(), key=lambda i: i.created, reverse=True)

    def get(self, item_id: str) -> BoardItem | None:
        return self._items.get(item_id)

    def file_path(self, item_id: str) -> Path:
        item = self._items.get(item_id)
        name = item.name if item else "file"
        return self._files_dir / item_id / name

    def add_text(self, text: str) -> BoardItem:
        text = text.strip()
        preview = text.splitlines()[0][:TEXT_PREVIEW_LEN] if text else ""
        item = BoardItem(id=uuid.uuid4().hex, kind="text", name=preview, text=text)
        self._items[item.id] = item
        self._save()
        return item

    def add_file(self, source_path: str | Path) -> BoardItem:
        source = Path(source_path)
        item_id = uuid.uuid4().hex
        target_dir = self._files_dir / item_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / source.name
        shutil.copy2(source, target)
        item = BoardItem(
            id=item_id, kind="file", name=source.name, size=target.stat().st_size
        )
        self._items[item.id] = item
        self._save()
        return item

    def remove(self, item_id: str) -> None:
        item = self._items.pop(item_id, None)
        if item is None:
            return
        if item.kind == "file":
            shutil.rmtree(self._files_dir / item_id, ignore_errors=True)
        self._save()
