import tempfile
from pathlib import Path

import typer

app = typer.Typer()

ROOT_DIR_NAME = ".porthub"


def storage_root() -> Path:
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


def key_to_path(key: str) -> Path:
    return storage_root() / f"{key}.md"


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


@app.command("set")
def set_value(key: str, value: str) -> None:
    try:
        normalized_key = validate_key(key)
    except ValueError as error:
        _raise_key_error(error)
    path = key_to_path(normalized_key)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            delete=False,
        ) as tmp_file:
            tmp_file.write(value)
            temp_path = Path(tmp_file.name)
        temp_path.replace(path)
    except OSError as error:
        typer.echo(f"Failed to write key '{normalized_key}': {error}", err=True)
        raise typer.Exit(code=1) from error


@app.command()
def get(key: str) -> None:
    try:
        normalized_key = validate_key(key)
    except ValueError as error:
        _raise_key_error(error)
    path = key_to_path(normalized_key)
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
def search(query: str) -> None:
    normalized_query = query.strip()
    if not normalized_query:
        raise typer.BadParameter("Query must not be empty.", param_hint="query")
    root = storage_root()
    query_lower = normalized_query.lower()
    matches: set[str] = set()
    for key in list_keys_from_root(root):
        md_path = key_to_path(key)
        if not md_path.exists():
            continue
        key_match = query_lower in key.lower()
        if key_match:
            matches.add(key)
            continue
        try:
            content = md_path.read_text(encoding="utf-8")
        except OSError:
            continue
        if query_lower in content.lower():
            matches.add(key)
    for key in sorted(matches):
        typer.echo(key)


@app.command("list")
def list_keys() -> None:
    for key in list_keys_from_root(storage_root()):
        typer.echo(key)
