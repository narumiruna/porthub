import multiprocessing
import threading
import time
from pathlib import Path

import pytest

from porthub import core


@pytest.fixture()
def root(tmp_path: Path) -> Path:
    return tmp_path / "store"


def _process_write_worker(
    root_path: str, key: str, content: str, start_event: multiprocessing.synchronize.Event
) -> None:
    start_event.wait()
    core.write_key(root=Path(root_path), key=key, content=content)


def test_storage_root_prefers_explicit_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PORTHUB_HOME", str(tmp_path / "env-store"))
    assert core.storage_root(root=tmp_path / "explicit").as_posix().endswith("/explicit")


def test_storage_root_uses_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    env_root = tmp_path / "env-store"
    monkeypatch.setenv("PORTHUB_HOME", str(env_root))
    assert core.storage_root() == env_root


def test_write_and_read_key_roundtrip(root: Path) -> None:
    normalized = core.write_key(root=root, key="python/typer", content="content")
    assert normalized == "python/typer"
    key, content = core.read_key(root=root, key="python/typer")
    assert key == "python/typer"
    assert content == "content"


@pytest.mark.parametrize(
    "key",
    ["python/troubleshooting", "machinelearning/svm", "lessons/python/typer"],
)
def test_validate_key_allows_descriptive_hierarchical_keys(key: str) -> None:
    assert core.validate_key(key) == key


@pytest.mark.parametrize("key", [".locks", ".locks/foo", "foo/.locks/bar"])
def test_validate_key_rejects_reserved_locks_segment(key: str) -> None:
    with pytest.raises(ValueError, match="reserved segment"):
        core.validate_key(key)


def test_read_key_raises_on_missing_key(root: Path) -> None:
    with pytest.raises(core.KeyNotFoundError):
        core.read_key(root=root, key="python/missing")


def test_search_modes(root: Path) -> None:
    core.write_key(root=root, key="python/typer", content="CLI framework")
    core.write_key(root=root, key="docs/guide", content="Use typer for apps")

    assert core.search_keys(root=root, query="typer", mode="all") == ["docs/guide", "python/typer"]
    assert core.search_keys(root=root, query="typer", mode="key") == ["python/typer"]
    assert core.search_keys(root=root, query="typer", mode="content") == ["docs/guide"]


def test_search_limit(root: Path) -> None:
    core.write_key(root=root, key="a/one", content="typer")
    core.write_key(root=root, key="b/two", content="typer")
    core.write_key(root=root, key="c/three", content="typer")
    assert len(core.search_keys(root=root, query="typer", mode="content", limit=2)) == 2


def test_validate_search_mode_rejects_invalid() -> None:
    with pytest.raises(ValueError, match="Mode must be one of"):
        core.validate_search_mode("invalid")


def test_write_key_concurrent_same_key_process_safe(root: Path) -> None:
    key = "python/typer"
    contents = [f"payload-{index}-" * 100 for index in range(6)]
    ctx = multiprocessing.get_context("spawn")
    start_event = ctx.Event()
    processes = [
        ctx.Process(target=_process_write_worker, args=(str(root), key, content, start_event)) for content in contents
    ]
    for process in processes:
        process.start()
    start_event.set()
    for process in processes:
        process.join(timeout=10)
        assert process.exitcode == 0
    _, content = core.read_key(root=root, key=key)
    assert content in contents


def test_write_key_concurrent_different_keys_process_safe(root: Path) -> None:
    entries = [(f"python/pkg{index}", f"value-{index}") for index in range(5)]
    ctx = multiprocessing.get_context("spawn")
    start_event = ctx.Event()
    processes = [
        ctx.Process(target=_process_write_worker, args=(str(root), key, value, start_event)) for key, value in entries
    ]
    for process in processes:
        process.start()
    start_event.set()
    for process in processes:
        process.join(timeout=10)
        assert process.exitcode == 0
    for key, value in entries:
        _, stored = core.read_key(root=root, key=key)
        assert stored == value


def test_write_key_last_write_wins(root: Path) -> None:
    key = "python/typer"
    barrier = threading.Barrier(2)

    def writer(content: str, delay_seconds: float) -> None:
        barrier.wait()
        if delay_seconds > 0:
            time.sleep(delay_seconds)
        core.write_key(root=root, key=key, content=content)

    first = threading.Thread(target=writer, args=("first", 0.0))
    second = threading.Thread(target=writer, args=("second", 0.05))
    first.start()
    second.start()
    first.join(timeout=5)
    second.join(timeout=5)
    assert not first.is_alive()
    assert not second.is_alive()
    _, final_content = core.read_key(root=root, key=key)
    assert final_content == "second"
