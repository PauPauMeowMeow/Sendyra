"""Smoke test: board + HTTP API without GUI. Run: python tests/smoke_test.py"""
import asyncio
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import aiohttp

from sendyra.core.board import LocalBoard
from sendyra.core.server import start_server


async def run() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        board = LocalBoard(Path(tmp))
        text_item = board.add_text("hello from smoke test")

        file_source = Path(tmp) / "sample.txt"
        file_source.write_text("file payload", encoding="utf-8")
        file_item = board.add_file(file_source)

        runner, port = await start_server(board, "testid", "testdev", 53317)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://127.0.0.1:{port}/api/info") as resp:
                    assert resp.status == 200, resp.status
                    info = await resp.json()
                    assert info["id"] == "testid"

                async with session.get(f"http://127.0.0.1:{port}/api/board") as resp:
                    assert resp.status == 200
                    data = await resp.json()
                    assert len(data["items"]) == 2, data

                async with session.get(
                    f"http://127.0.0.1:{port}/api/item/{text_item.id}"
                ) as resp:
                    assert await resp.text() == "hello from smoke test"

                async with session.get(
                    f"http://127.0.0.1:{port}/api/item/{file_item.id}"
                ) as resp:
                    assert await resp.read() == b"file payload"

                async with session.get(f"http://127.0.0.1:{port}/") as resp:
                    assert resp.status == 200

                async with session.get(
                    f"http://127.0.0.1:{port}/api/item/missing"
                ) as resp:
                    assert resp.status == 404
        finally:
            await runner.cleanup()

        board.remove(file_item.id)
        assert len(board.items) == 1

    print("Smoke test OK")


if __name__ == "__main__":
    asyncio.run(run())
