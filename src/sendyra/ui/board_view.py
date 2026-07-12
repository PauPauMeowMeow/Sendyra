from __future__ import annotations

import datetime
from pathlib import Path

import flet as ft

from ..config import data_dir
from .state import AppState, DisplayItem


def _format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def _format_time(timestamp: float) -> str:
    return datetime.datetime.fromtimestamp(timestamp).strftime("%d.%m %H:%M")


class BoardView(ft.Column):
    """Aggregated board: own items plus items of every discovered peer."""

    def __init__(self, page: ft.Page, state: AppState):
        super().__init__(expand=True)
        self._page = page
        self._state = state
        self._list = ft.ListView(expand=True, spacing=8, padding=12)
        self._save_picker = ft.FilePicker(on_result=self._on_save_result)
        self._pending_download: DisplayItem | None = None
        page.overlay.append(self._save_picker)
        self.controls = [self._list]
        state.on_change.append(self._rebuild)
        self._rebuild()

    def _snack(self, message: str) -> None:
        self._page.open(ft.SnackBar(ft.Text(message)))

    def _rebuild(self) -> None:
        self._list.controls = [
            self._build_card(entry) for entry in self._state.display_items
        ] or [
            ft.Container(
                ft.Text(
                    "The board is empty. Publish a text or a file on the Share tab.",
                    color=ft.Colors.OUTLINE,
                ),
                padding=24,
                alignment=ft.alignment.center,
            )
        ]
        if self.page is not None:
            self.update()

    def _build_card(self, entry: DisplayItem) -> ft.Card:
        item = entry.item
        is_own = entry.peer is None
        is_text = item.kind == "text"

        actions: list[ft.Control] = []
        if is_text:
            actions.append(
                ft.IconButton(
                    ft.Icons.COPY,
                    tooltip="Copy text",
                    on_click=lambda _, e=entry: self._copy_text(e),
                )
            )
        elif not is_own:
            actions.append(
                ft.IconButton(
                    ft.Icons.DOWNLOAD,
                    tooltip="Download file",
                    on_click=lambda _, e=entry: self._download(e),
                )
            )
        if is_own:
            actions.append(
                ft.IconButton(
                    ft.Icons.DELETE_OUTLINE,
                    tooltip="Delete",
                    on_click=lambda _, e=entry: self._delete(e),
                )
            )

        subtitle = f"{entry.owner_name} · {_format_time(item.created)}"
        if not is_text:
            subtitle += f" · {_format_size(item.size)}"

        body: ft.Control
        if is_text:
            body = ft.Text(item.text, max_lines=6, overflow=ft.TextOverflow.ELLIPSIS)
        else:
            body = ft.Text(item.name, weight=ft.FontWeight.BOLD)

        return ft.Card(
            content=ft.Container(
                ft.Row(
                    [
                        ft.Icon(
                            ft.Icons.NOTES if is_text else ft.Icons.INSERT_DRIVE_FILE,
                            color=ft.Colors.PRIMARY,
                        ),
                        ft.Column(
                            [body, ft.Text(subtitle, size=12, color=ft.Colors.OUTLINE)],
                            spacing=4,
                            expand=True,
                        ),
                        ft.Row(actions, spacing=0),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=12,
            )
        )

    def _copy_text(self, entry: DisplayItem) -> None:
        self._page.set_clipboard(entry.item.text)
        self._snack("Text copied to clipboard")

    def _delete(self, entry: DisplayItem) -> None:
        self._state.board.remove(entry.item.id)
        self._page.run_task(self._state.refresh)

    def _download(self, entry: DisplayItem) -> None:
        self._pending_download = entry
        if self._page.platform in (ft.PagePlatform.ANDROID, ft.PagePlatform.IOS):
            target = data_dir() / "downloads" / entry.item.name
            self._page.run_task(self._do_download, entry, target)
        else:
            self._save_picker.save_file(file_name=entry.item.name)

    def _on_save_result(self, event: ft.FilePickerResultEvent) -> None:
        entry = self._pending_download
        self._pending_download = None
        if entry is None or not event.path:
            return
        self._page.run_task(self._do_download, entry, Path(event.path))

    async def _do_download(self, entry: DisplayItem, target: Path) -> None:
        assert entry.peer is not None
        self._snack(f"Downloading {entry.item.name}…")
        try:
            await self._state.registry.download_file(entry.peer, entry.item, target)
            self._snack(f"Saved: {target}")
        except Exception as exc:
            self._snack(f"Download failed: {exc}")
