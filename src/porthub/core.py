import hashlib
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import IO
from typing import Literal

ROOT_DIR_NAME = ".porthub"
LOCKS_DIR_NAME = ".locks"
SearchMode = Literal["all", "key", "content"]


class KeyNotFoundError(FileNotFoundError):
    """Raised when a key does not exist in storage."""


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
    if any(segment == LOCKS_DIR_NAME for segment in normalized.split("/")):
        msg = f"Key must not use reserved segment '{LOCKS_DIR_NAME}'."
        raise ValueError(msg)
    return normalized


def key_to_path(root: Path, key: str) -> Path:
    return root / f"{key}.md"


def _lock_path_for_key(root: Path, key: str) -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return root / LOCKS_DIR_NAME / f"{digest}.lock"


def _lock_file(file_obj: IO[bytes]) -> None:
    if os.name == "nt":
        import msvcrt

        file_obj.seek(0)
        file_obj.write(b"\0")
        file_obj.flush()
        file_obj.seek(0)
        msvcrt.locking(file_obj.fileno(), msvcrt.LK_LOCK, 1)
        return

    import fcntl

    fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX)


def _unlock_file(file_obj: IO[bytes]) -> None:
    if os.name == "nt":
        import msvcrt

        file_obj.seek(0)
        msvcrt.locking(file_obj.fileno(), msvcrt.LK_UNLCK, 1)
        return

    import fcntl

    fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)


@contextmanager
def _acquire_key_lock(*, root: Path, key: str) -> Iterator[None]:
    lock_path = _lock_path_for_key(root, key)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock_file:
        _lock_file(lock_file)
        try:
            yield
        finally:
            _unlock_file(lock_file)


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


def write_key(*, root: Path, key: str, content: str) -> str:
    normalized_key = validate_key(key)
    with _acquire_key_lock(root=root, key=normalized_key):
        path = key_to_path(root, normalized_key)
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
    return normalized_key


def read_key(*, root: Path, key: str) -> tuple[str, str]:
    normalized_key = validate_key(key)
    path = key_to_path(root, normalized_key)
    if not path.is_file():
        raise KeyNotFoundError(normalized_key)
    content = path.read_text(encoding="utf-8")
    return normalized_key, content


def validate_search_mode(mode: str) -> SearchMode:
    lowered = mode.strip().lower()
    if lowered not in {"all", "key", "content"}:
        msg = "Mode must be one of: all, key, content."
        raise ValueError(msg)
    return lowered  # type: ignore[return-value]


def search_keys(*, root: Path, query: str, mode: SearchMode = "all", limit: int | None = None) -> list[str]:
    normalized_query = query.strip()
    if not normalized_query:
        msg = "Query must not be empty."
        raise ValueError(msg)
    if limit is not None and limit <= 0:
        msg = "Limit must be greater than 0."
        raise ValueError(msg)

    query_lower = normalized_query.lower()
    key_only = mode == "key"
    content_only = mode == "content"
    matches: set[str] = set()
    for key in list_keys_from_root(root):
        md_path = key_to_path(root, key)
        if not md_path.exists():
            continue
        key_match = (not content_only) and query_lower in key.lower()
        if key_match:
            matches.add(key)
        should_read_content = not key_only and (content_only or not key_match)
        if should_read_content:
            try:
                content = md_path.read_text(encoding="utf-8")
            except OSError:
                continue
            if query_lower in content.lower():
                matches.add(key)
        if limit is not None and len(matches) >= limit:
            break
    return sorted(matches)
