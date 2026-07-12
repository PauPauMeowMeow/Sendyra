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

    # Show a spinner while the server and discovery are starting.
    loading = ft.Container(
        content=ft.Column(
            [
                ft.ProgressRing(scale=2, color=ft.Colors.TEAL),
                ft.Text("Starting Sendyra…", size=16),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
        expand=True,
    )
    page.add(loading)

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

    page.remove(loading)
    page.add(content)

    async def on_disconnect(_event) -> None:
        await state.stop()
        await runner.cleanup()

    def on_lifecycle_change(event: ft.AppLifecycleStateChangeEvent) -> None:
        # When the app returns to foreground, re-announce and refresh so
        # Android devices pick up new peers after being suspended.
        if event.state == ft.AppLifecycleState.RESUME:
            page.run_task(state.refresh)
            if state.discovery is not None:
                page.run_task(state.discovery.re_announce)

    page.on_disconnect = on_disconnect
    page.on_app_lifecycle_state_change = on_lifecycle_change
    page.run_task(state.refresh_loop)
