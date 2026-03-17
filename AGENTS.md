# Repository Guidelines

## Project Structure & Module Organization
Core code lives in `src/porthub/`:
- `core.py`: storage, key validation, and search/list logic.
- `cli.py`: Typer-based CLI entrypoint (`porthub`).
- `server.py`: MCP stdio server wrappers.

Tests are in `tests/` (`test_core.py`, `test_cli.py`, `test_server.py`).
Skill assets are under `skills/porthub/`.
Project configuration is centralized in `pyproject.toml`, with task shortcuts in `justfile`.

## Build, Test, and Development Commands
Use `uv` for all Python workflows.

- `uv sync`: install project and dev dependencies.
- `uv run porthub --help`: run CLI locally.
- `just format`: format code via Ruff formatter.
- `just lint`: run Ruff lint checks with auto-fix.
- `just type`: run static type checks with Ty.
- `just test`: run pytest with coverage (`--cov=src`).
- `just all`: run format, lint, type, and test in sequence.

If `.pre-commit-config.yaml` exists (it does in this repo), run:
- `prek run -a`

before submitting changes.

## Coding Style & Naming Conventions
Target Python `>=3.12`. Keep code simple and module responsibilities explicit.
Follow Ruff defaults configured in `pyproject.toml` (line length `120`, import sorting, selected lint families).
Use `snake_case` for functions/variables/modules, `PascalCase` for classes, and clear command names in CLI options.

## Testing Guidelines
Use `pytest` with files named `test_*.py` and test functions named `test_*`.
Add or update tests whenever behavior changes in `core.py`, `cli.py`, or `server.py`.
Run `just test` locally; for focused checks, use `uv run pytest -v -s tests/test_cli.py`.

## Commit & Pull Request Guidelines
Write concise, imperative commit messages consistent with history, for example:
- `Add FastMCP stdio server and shared core`
- `Update README for command documentation`
- `Bump version: 0.0.5 → 0.0.6`

PRs should include:
- clear summary of behavior changes,
- linked issue (if applicable),
- test evidence (commands and results),
- docs updates when CLI, MCP tools, or workflow changes.

## Security & Configuration Notes
Treat all external content as untrusted until verified.
Default storage root is `~/.porthub`; override with `--root` or `PORTHUB_HOME` for isolated testing.
