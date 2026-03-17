from pathlib import Path

from mcp.server.fastmcp import FastMCP

from porthub import core


def _success(**payload: object) -> dict[str, object]:
    return {"ok": True, "error": None, **payload}


def _failure(code: str, message: str) -> dict[str, object]:
    return {"ok": False, "error": {"code": code, "message": message}}


def _register_get_tool(mcp: FastMCP, *, root: Path) -> None:
    @mcp.tool()
    def porthub_get(key: str) -> dict[str, object]:
        try:
            normalized_key, content = core.read_key(root=root, key=key)
        except ValueError as error:
            return _failure("invalid_key", str(error))
        except core.KeyNotFoundError as error:
            return _failure("key_not_found", f"Key '{error.args[0]}' not found.")
        except OSError as error:
            return _failure("io_error", f"Failed to read key '{key}': {error}")
        return _success(key=normalized_key, content=content)


def _register_set_tool(mcp: FastMCP, *, root: Path) -> None:
    @mcp.tool()
    def porthub_set(key: str, value: str) -> dict[str, object]:
        try:
            normalized_key = core.write_key(root=root, key=key, content=value)
        except ValueError as error:
            return _failure("invalid_key", str(error))
        except OSError as error:
            return _failure("io_error", f"Failed to write key '{key}': {error}")
        return _success(key=normalized_key, written=True)


def _register_search_tool(mcp: FastMCP, *, root: Path) -> None:
    @mcp.tool()
    def porthub_search(query: str, mode: str = "all", limit: int | None = None) -> dict[str, object]:
        try:
            validated_mode = core.validate_search_mode(mode)
            matches = core.search_keys(root=root, query=query, mode=validated_mode, limit=limit)
        except ValueError as error:
            message = str(error)
            if "Mode must" in message:
                return _failure("invalid_mode", message)
            if "Limit must" in message:
                return _failure("invalid_limit", message)
            return _failure("invalid_query", message)
        except OSError as error:
            return _failure("io_error", f"Failed to search query '{query}': {error}")
        return _success(query=query.strip(), mode=validated_mode, limit=limit, matches=matches)


def _register_list_tool(mcp: FastMCP, *, root: Path) -> None:
    @mcp.tool()
    def porthub_list() -> dict[str, object]:
        try:
            keys = core.list_keys_from_root(root)
        except OSError as error:
            return _failure("io_error", f"Failed to list keys: {error}")
        return _success(keys=keys)


def create_server(*, name: str, root: Path) -> FastMCP:
    mcp = FastMCP(name, json_response=True)
    _register_get_tool(mcp, root=root)
    _register_set_tool(mcp, root=root)
    _register_search_tool(mcp, root=root)
    _register_list_tool(mcp, root=root)
    return mcp
