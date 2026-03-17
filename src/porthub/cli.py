import sys
from pathlib import Path
from typing import Annotated

import typer

from porthub import core
from porthub.server import create_server

app = typer.Typer()

RootOption = Annotated[Path | None, typer.Option("--root", help="Override storage root.")]
SetFileOption = Annotated[Path | None, typer.Option("--file", help="Read value from file.")]
SetStdinOption = Annotated[bool, typer.Option("--stdin", help="Read value from stdin.")]
SearchKeyOnlyOption = Annotated[bool, typer.Option("--key-only", help="Search key names only.")]
SearchContentOnlyOption = Annotated[bool, typer.Option("--content-only", help="Search content only.")]
SearchLimitOption = Annotated[int | None, typer.Option("--limit", help="Maximum number of results.")]


def _raise_key_error(error: ValueError) -> None:
    raise typer.BadParameter(str(error), param_hint="key") from error


def _validate_search_flags(*, key_only: bool, content_only: bool, limit: int | None) -> None:
    if key_only and content_only:
        raise typer.BadParameter("Choose only one mode: --key-only or --content-only.", param_hint="query")
    if limit is not None and limit <= 0:
        raise typer.BadParameter("Limit must be greater than 0.", param_hint="limit")


@app.command("set")
def set_value(
    key: str,
    value: str | None = typer.Argument(None),
    file_path: SetFileOption = None,
    stdin: SetStdinOption = False,
    root: RootOption = None,
) -> None:
    try:
        normalized_key = core.validate_key(key)
    except ValueError as error:
        _raise_key_error(error)

    provided_sources = int(value is not None) + int(file_path is not None) + int(stdin)
    if provided_sources != 1:
        raise typer.BadParameter(
            "Provide exactly one content source: positional value, --file, or --stdin.",
            param_hint="value",
        )

    if file_path is not None:
        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError as error:
            typer.echo(f"Failed to read file '{file_path}': {error}", err=True)
            raise typer.Exit(code=1) from error
    elif stdin:
        content = sys.stdin.read()
    else:
        assert value is not None
        content = value

    try:
        core.write_key(root=core.storage_root(root=root), key=normalized_key, content=content)
    except OSError as error:
        typer.echo(f"Failed to write key '{normalized_key}': {error}", err=True)
        raise typer.Exit(code=1) from error


@app.command()
def get(key: str, root: RootOption = None) -> None:
    try:
        normalized_key = core.validate_key(key)
    except ValueError as error:
        _raise_key_error(error)
    try:
        _, content = core.read_key(root=core.storage_root(root=root), key=normalized_key)
    except core.KeyNotFoundError:
        typer.echo(f"Key '{normalized_key}' not found.", err=True)
        raise typer.Exit(code=1) from None
    except OSError as error:
        typer.echo(f"Failed to read key '{normalized_key}': {error}", err=True)
        raise typer.Exit(code=1) from error
    typer.echo(content, nl=False)


@app.command()
def search(
    query: str,
    key_only: SearchKeyOnlyOption = False,
    content_only: SearchContentOnlyOption = False,
    limit: SearchLimitOption = None,
    root: RootOption = None,
) -> None:
    normalized_query = query.strip()
    if not normalized_query:
        raise typer.BadParameter("Query must not be empty.", param_hint="query")
    _validate_search_flags(key_only=key_only, content_only=content_only, limit=limit)

    mode = "all"
    if key_only:
        mode = "key"
    if content_only:
        mode = "content"

    for key in core.search_keys(root=core.storage_root(root=root), query=normalized_query, mode=mode, limit=limit):
        typer.echo(key)


@app.command("list")
def list_keys(
    root: RootOption = None,
) -> None:
    for key in core.list_keys_from_root(core.storage_root(root=root)):
        typer.echo(key)


@app.command()
def server(
    root: RootOption = None,
    name: Annotated[str, typer.Option("--name", help="MCP server name.")] = "PortHub",
) -> None:
    mcp = create_server(name=name, root=core.storage_root(root=root))
    mcp.run(transport="stdio")
