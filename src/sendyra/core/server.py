from __future__ import annotations

import html

from aiohttp import web

from .. import __version__
from .board import LocalBoard

MAX_PORT_ATTEMPTS = 10


def create_app(board: LocalBoard, device_id: str, device_name: str) -> web.Application:
    app = web.Application()

    async def info(_request: web.Request) -> web.Response:
        return web.json_response(
            {"id": device_id, "name": device_name, "version": __version__}
        )

    async def get_board(_request: web.Request) -> web.Response:
        return web.json_response({"items": [i.to_dict() for i in board.items]})

    async def get_item(request: web.Request) -> web.StreamResponse:
        item = board.get(request.match_info["id"])
        if item is None:
            raise web.HTTPNotFound(text="Item not found")
        if item.kind == "text":
            return web.Response(text=item.text, content_type="text/plain")
        path = board.file_path(item.id)
        if not path.exists():
            raise web.HTTPNotFound(text="File not found")
        return web.FileResponse(
            path,
            headers={
                "Content-Disposition": f'attachment; filename="{item.name}"'
            },
        )

    async def index(_request: web.Request) -> web.Response:
        rows = []
        for item in board.items:
            if item.kind == "text":
                rows.append(
                    f"<li><pre>{html.escape(item.text)}</pre></li>"
                )
            else:
                size_mb = item.size / (1024 * 1024)
                rows.append(
                    f'<li><a href="/api/item/{item.id}">{html.escape(item.name)}</a>'
                    f" ({size_mb:.1f} MB)</li>"
                )
        body = (
            "<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<title>Sendyra — {html.escape(device_name)}</title>"
            "<style>body{font-family:sans-serif;max-width:720px;margin:2rem auto;"
            "padding:0 1rem}pre{background:#f4f4f4;padding:.5rem;border-radius:6px;"
            "white-space:pre-wrap}</style></head><body>"
            f"<h1>Sendyra — {html.escape(device_name)}</h1>"
            f"<ul>{''.join(rows) or '<p>The board is empty</p>'}</ul>"
            "</body></html>"
        )
        return web.Response(text=body, content_type="text/html")

    app.router.add_get("/api/info", info)
    app.router.add_get("/api/board", get_board)
    app.router.add_get("/api/item/{id}", get_item)
    app.router.add_get("/", index)
    return app


async def start_server(
    board: LocalBoard, device_id: str, device_name: str, preferred_port: int
) -> tuple[web.AppRunner, int]:
    """Start the HTTP server, trying successive ports if busy. Returns (runner, port)."""
    app = create_app(board, device_id, device_name)
    runner = web.AppRunner(app)
    await runner.setup()
    last_error: OSError | None = None
    for port in range(preferred_port, preferred_port + MAX_PORT_ATTEMPTS):
        site = web.TCPSite(runner, host="0.0.0.0", port=port)
        try:
            await site.start()
            return runner, port
        except OSError as exc:
            last_error = exc
    await runner.cleanup()
    raise RuntimeError(f"Could not bind any port: {last_error}")
