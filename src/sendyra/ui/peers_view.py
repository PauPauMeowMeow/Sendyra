from __future__ import annotations

import flet as ft

from ..config import get_local_ip
from .state import AppState


class PeersView(ft.Column):
    """List of discovered devices on the local network."""

    def __init__(self, page: ft.Page, state: AppState):
        super().__init__(expand=True)
        self._page = page
        self._state = state
        self._list = ft.ListView(expand=True, spacing=8, padding=12)
        self.controls = [self._list]
        state.on_change.append(self._rebuild)
        self._rebuild()

    def _rebuild(self) -> None:
        controls: list[ft.Control] = [
            ft.ListTile(
                leading=ft.Icon(ft.Icons.COMPUTER, color=ft.Colors.PRIMARY),
                title=ft.Text(f"{self._state.device_name} (this device)"),
                subtitle=ft.Text(
                    f"http://{get_local_ip()}:{self._state.port} — "
                    "open in a browser on another device"
                ),
            )
        ]
        controls.extend(
            ft.ListTile(
                leading=ft.Icon(ft.Icons.DEVICES),
                title=ft.Text(peer.name),
                subtitle=ft.Text(f"{peer.host}:{peer.port}"),
            )
            for peer in self._state.registry.peers
        )
        if len(controls) == 1:
            controls.append(
                ft.Container(
                    ft.Text(
                        "No other devices found. Make sure Sendyra is "
                        "running on them and all devices are on the same network.",
                        color=ft.Colors.OUTLINE,
                    ),
                    padding=24,
                )
            )
        self._list.controls = controls
        if self.page is not None:
            self.update()
