import asyncio
import os
from pathlib import Path

from mcp import ClientSession
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client


def test_mcp_server_stdio_smoke(tmp_path: Path) -> None:
    async def _run() -> None:
        store_root = tmp_path / "mcp-store"
        params = StdioServerParameters(
            command="uv",
            args=["run", "porthub", "server", "--root", str(store_root), "--name", "PortHubTest"],
            env=os.environ.copy(),
        )

        async with (
            stdio_client(params) as (read_stream, write_stream),
            ClientSession(read_stream, write_stream) as session,
        ):
            await session.initialize()

            tools = await session.list_tools()
            tool_names = sorted(tool.name for tool in tools.tools)
            assert tool_names == ["porthub_get", "porthub_list", "porthub_search", "porthub_set"]

            set_result = await session.call_tool("porthub_set", {"key": "python/typer", "value": "hello"})
            assert set_result.structuredContent is not None
            assert set_result.structuredContent["ok"] is True
            assert set_result.structuredContent["key"] == "python/typer"

            get_result = await session.call_tool("porthub_get", {"key": "python/typer"})
            assert get_result.structuredContent is not None
            assert get_result.structuredContent["ok"] is True
            assert get_result.structuredContent["content"] == "hello"

            search_result = await session.call_tool("porthub_search", {"query": "typer", "mode": "key"})
            assert search_result.structuredContent is not None
            assert search_result.structuredContent["ok"] is True
            assert search_result.structuredContent["matches"] == ["python/typer"]

            list_result = await session.call_tool("porthub_list", {})
            assert list_result.structuredContent is not None
            assert list_result.structuredContent["ok"] is True
            assert list_result.structuredContent["keys"] == ["python/typer"]

    asyncio.run(_run())
