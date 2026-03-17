import os
import sys
import tempfile
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer()

ROOT_DIR_NAME = ".porthub"
RootOption = Annotated[Path | None, typer.Option("--root", help="Override storage root.")]
SetFileOption = Annotated[Path | None, typer.Option("--file", help="Read value from file.")]
SetStdinOption = Annotated[bool, typer.Option("--stdin", help="Read value from stdin.")]
SearchKeyOnlyOption = Annotated[bool, typer.Option("--key-only", help="Search key names only.")]
SearchContentOnlyOption = Annotated[bool, typer.Option("--content-only", help="Search content only.")]
SearchLimitOption = Annotated[int | None, typer.Option("--limit", help="Maximum number of results.")]


def storage_root(*, root: Path | None = None) -> Path:
    if root is not None:
        return root.expanduser()
    env_root = os.environ.get("PORTHUB_HOME")
    if env_root:
        return Path(env_root).expanduser()
    return Path.home() / ROOT_DIR_NAME


def validate_key(key: str) -> str:
    normalized = key.strip()
    if not normalized:
        msg = "Key must not be empty."
        raise ValueError(msg)
    if normalized.startswith("/") or normalized.endswith("/"):
        msg = "Key must not start or end with '/'."
        raise ValueError(msg)
    if "//" in normalized:
        msg = "Key must not contain '//'."
        raise ValueError(msg)
    if ".." in normalized:
        msg = "Key must not contain '..'."
        raise ValueError(msg)
    if normalized.endswith(".md"):
        msg = "Key must not end with '.md'."
        raise ValueError(msg)
    return normalized


def key_to_path(root: Path, key: str) -> Path:
    return root / f"{key}.md"


def list_keys_from_root(root: Path) -> list[str]:
    if not root.exists():
        return []
    keys: list[str] = []
    for md_path in root.rglob("*.md"):
        if not md_path.is_file():
            continue
        key = md_path.relative_to(root).with_suffix("").as_posix()
        keys.append(key)
    return sorted(keys)


def _raise_key_error(error: ValueError) -> None:
    raise typer.BadParameter(str(error), param_hint="key") from error


def _validate_search_flags(*, key_only: bool, content_only: bool, limit: int | None) -> None:
    if key_only and content_only:
        raise typer.BadParameter("Choose only one mode: --key-only or --content-only.", param_hint="query")
    if limit is not None and limit <= 0:
        raise typer.BadParameter("Limit must be greater than 0.", param_hint="limit")


def _search_key_content_match(
    *,
    md_path: Path,
    key: str,
    query_lower: str,
    key_only: bool,
    content_only: bool,
) -> bool:
    key_match = (not content_only) and query_lower in key.lower()
    if key_match:
        return True

    should_read_content = not key_only and (content_only or not key_match)
    if not should_read_content:
        return False

    try:
        content = md_path.read_text(encoding="utf-8")
    except OSError:
        return False
    return query_lower in content.lower()


@app.command("set")
def set_value(
    key: str,
    value: str | None = typer.Argument(None),
    file_path: SetFileOption = None,
    stdin: SetStdinOption = False,
    root: RootOption = None,
) -> None:
    try:
        normalized_key = validate_key(key)
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

    resolved_root = storage_root(root=root)
    path = key_to_path(resolved_root, normalized_key)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            delete=False,
        ) as tmp_file:
            tmp_file.write(content)
            temp_path = Path(tmp_file.name)
        temp_path.replace(path)
    except OSError as error:
        typer.echo(f"Failed to write key '{normalized_key}': {error}", err=True)
        raise typer.Exit(code=1) from error


@app.command()
def get(key: str, root: RootOption = None) -> None:
    try:
        normalized_key = validate_key(key)
    except ValueError as error:
        _raise_key_error(error)
    resolved_root = storage_root(root=root)
    path = key_to_path(resolved_root, normalized_key)
    if not path.is_file():
        typer.echo(f"Key '{normalized_key}' not found.", err=True)
        raise typer.Exit(code=1)
    try:
        content = path.read_text(encoding="utf-8")
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

    resolved_root = storage_root(root=root)
    query_lower = normalized_query.lower()
    matches: set[str] = set()
    for key in list_keys_from_root(resolved_root):
        md_path = key_to_path(resolved_root, key)
        if not md_path.exists():
            continue
        if _search_key_content_match(
            md_path=md_path,
            key=key,
            query_lower=query_lower,
            key_only=key_only,
            content_only=content_only,
        ):
            matches.add(key)
        if limit is not None and len(matches) >= limit:
            break
    for key in sorted(matches):
        typer.echo(key)


@app.command("list")
def list_keys(
    root: RootOption = None,
) -> None:
    for key in list_keys_from_root(storage_root(root=root)):
        typer.echo(key)
