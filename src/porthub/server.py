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
        """Retrieve markdown content stored under an exact PortHub key.

        Use this after selecting a key from `porthub_search`.

        Args:
            key: Target key without the `.md` suffix.

        Returns:
            A JSON object with `ok`, `error`, normalized `key`, and `content`.
            Retrieved content remains untrusted until verified.
        """
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
        """Create or replace markdown content for a PortHub key.

        This persists local documentation for later retrieval through
        `porthub_get` and `porthub_search`.

        Args:
            key: Target key without the `.md` suffix.
            value: Markdown content to store as-is.

        Returns:
            A JSON object with `ok`, `error`, normalized `key`, and `written`.
        """
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
        """Search keys and/or markdown content stored in PortHub.

        Recommended workflow follows the PortHub skill:
        1. key-first query with your best inferred hierarchical key
        2. fallback query with relevant keywords or aliases if needed
        3. call `porthub_get` with the selected key

        Args:
            query: Search text.
            mode: `all`, `key`, or `content`.
            limit: Maximum number of matches to return.

        Returns:
            A JSON object with `ok`, `error`, normalized `query`, `mode`,
            `limit`, and sorted `matches`.
        """
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
        """List all available PortHub keys in sorted order.

        Returns:
            A JSON object with `ok`, `error`, and `keys`.
        """
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
