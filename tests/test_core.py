from pathlib import Path

import pytest

from porthub import core


@pytest.fixture()
def root(tmp_path: Path) -> Path:
    return tmp_path / "store"


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
