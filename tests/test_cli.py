from pathlib import Path

import pytest
from typer.testing import CliRunner

from porthub.cli import app


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("HOME", str(tmp_path))
    return tmp_path


@pytest.mark.parametrize(
    ("invalid_key",),
    [
        ("",),
        ("   ",),
        ("/python/typer",),
        ("python/typer/",),
        ("python//typer",),
        ("python/../typer",),
        ("python/typer.md",),
    ],
)
def test_set_rejects_invalid_keys(runner: CliRunner, isolated_home: Path, invalid_key: str) -> None:
    result = runner.invoke(app, ["set", invalid_key, "content"])
    assert result.exit_code != 0
    assert "Key must not" in result.output or "Key must" in result.output


@pytest.mark.parametrize(
    ("invalid_key",),
    [
        ("",),
        ("   ",),
        ("/python/typer",),
        ("python/typer/",),
        ("python//typer",),
        ("python/../typer",),
        ("python/typer.md",),
    ],
)
def test_get_rejects_invalid_keys(runner: CliRunner, isolated_home: Path, invalid_key: str) -> None:
    result = runner.invoke(app, ["get", invalid_key])
    assert result.exit_code != 0
    assert "Key must not" in result.output or "Key must" in result.output


def test_set_creates_and_overwrites_file(runner: CliRunner, isolated_home: Path) -> None:
    result_create = runner.invoke(app, ["set", "python/typer", "first"])
    assert result_create.exit_code == 0

    stored_path = isolated_home / ".porthub" / "python" / "typer.md"
    assert stored_path.read_text(encoding="utf-8") == "first"

    result_overwrite = runner.invoke(app, ["set", "python/typer", "second"])
    assert result_overwrite.exit_code == 0
    assert stored_path.read_text(encoding="utf-8") == "second"


def test_get_returns_exact_content(runner: CliRunner, isolated_home: Path) -> None:
    stored_path = isolated_home / ".porthub" / "python" / "typer.md"
    stored_path.parent.mkdir(parents=True, exist_ok=True)
    content = "# Typer\nCLI framework"
    stored_path.write_text(content, encoding="utf-8")

    result = runner.invoke(app, ["get", "python/typer"])
    assert result.exit_code == 0
    assert result.output == content


def test_get_missing_key_returns_non_zero(runner: CliRunner, isolated_home: Path) -> None:
    result = runner.invoke(app, ["get", "python/missing"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_search_matches_key_and_content_case_insensitive(
    runner: CliRunner,
    isolated_home: Path,
) -> None:
    root = isolated_home / ".porthub"
    (root / "zeta").mkdir(parents=True, exist_ok=True)
    (root / "zeta" / "alpha.md").write_text("nothing", encoding="utf-8")
    (root / "python").mkdir(parents=True, exist_ok=True)
    (root / "python" / "typer.md").write_text("CLI framework", encoding="utf-8")
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "guide.md").write_text("Use TyPeR for CLI apps", encoding="utf-8")

    result = runner.invoke(app, ["search", "typer"])
    assert result.exit_code == 0
    assert result.output.splitlines() == ["docs/guide", "python/typer"]


def test_search_returns_empty_output_when_no_match(runner: CliRunner, isolated_home: Path) -> None:
    root = isolated_home / ".porthub" / "python"
    root.mkdir(parents=True, exist_ok=True)
    (root / "click.md").write_text("decorators", encoding="utf-8")

    result = runner.invoke(app, ["search", "typer"])
    assert result.exit_code == 0
    assert result.output == ""


def test_search_rejects_empty_query(runner: CliRunner, isolated_home: Path) -> None:
    result = runner.invoke(app, ["search", "   "])
    assert result.exit_code != 0
    assert "must not be empty" in result.output.lower()


def test_list_returns_all_keys_sorted(runner: CliRunner, isolated_home: Path) -> None:
    root = isolated_home / ".porthub"
    (root / "zeta" / "alpha.md").parent.mkdir(parents=True, exist_ok=True)
    (root / "zeta" / "alpha.md").write_text("z", encoding="utf-8")
    (root / "python" / "typer.md").parent.mkdir(parents=True, exist_ok=True)
    (root / "python" / "typer.md").write_text("p", encoding="utf-8")
    (root / "docs" / "guide.md").parent.mkdir(parents=True, exist_ok=True)
    (root / "docs" / "guide.md").write_text("d", encoding="utf-8")

    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert result.output.splitlines() == ["docs/guide", "python/typer", "zeta/alpha"]


def test_list_returns_empty_output_when_root_missing(runner: CliRunner, isolated_home: Path) -> None:
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert result.output == ""


def test_list_returns_empty_output_when_no_markdown_files(runner: CliRunner, isolated_home: Path) -> None:
    root = isolated_home / ".porthub" / "python"
    root.mkdir(parents=True, exist_ok=True)
    (root / "notes.txt").write_text("not markdown", encoding="utf-8")

    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert result.output == ""
