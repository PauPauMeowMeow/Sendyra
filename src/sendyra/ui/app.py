from __future__ import annotations

import flet as ft

from ..config import DEFAULT_PORT
from ..core.server import start_server
from .board_view import BoardView
from .peers_view import PeersView
from .share_view import ShareView
from .state import AppState


async def main(page: ft.Page) -> None:
    page.title = "Sendyra"
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.TEAL)

    state = AppState()

    runner, port = await start_server(
        state.board, state.device_id, state.device_name, DEFAULT_PORT
    )
    state.port = port
    await state.start_discovery()

    # Refresh once to show local board immediately while peers are discovered.
    await state.refresh()

    board_view = BoardView(page, state)
    share_view = ShareView(page, state)
    peers_view = PeersView(page, state)
    views: list[ft.Control] = [board_view, share_view, peers_view]

    content = ft.Container(content=board_view, expand=True)

    def on_nav_change(event: ft.ControlEvent) -> None:
        content.content = views[int(event.control.selected_index)]
        page.update()

    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        on_change=on_nav_change,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD, label="Board"),
            ft.NavigationBarDestination(icon=ft.Icons.SHARE, label="Share"),
            ft.NavigationBarDestination(icon=ft.Icons.DEVICES, label="Devices"),
        ],
    )
    page.appbar = ft.AppBar(
        title=ft.Text("Sendyra"),
        center_title=False,
        actions=[
            ft.IconButton(
                ft.Icons.REFRESH,
                tooltip="Refresh",
                on_click=lambda _: page.run_task(state.refresh),
            )
        ],
    )
    page.add(content)

    async def on_disconnect(_event) -> None:
        await state.stop()
        await runner.cleanup()

    page.on_disconnect = on_disconnect
    page.run_task(state.refresh_loop)
