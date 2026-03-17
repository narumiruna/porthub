# PortHub

PortHub is a local-first CLI tool for storing and retrieving Markdown context by hierarchical keys.

## MVP Scope

- Local filesystem storage only (`~/.porthub`).
- CLI-only workflows.
- Four commands: `set`, `get`, `search`, `list`.
- Exact match for `get`.
- Case-insensitive substring match for `search`.

## Install

```bash
uv sync
```

You can run commands either through `uv`:

```bash
uv run porthub --help
```

Or through the installed script:

```bash
porthub --help
```

## Usage

Set Markdown content:

```bash
porthub set python/typer "# Typer\nCLI framework for Python"
```

Get content by exact key:

```bash
porthub get python/typer
```

Search by key or content (case-insensitive):

```bash
porthub search typer
```

List all keys:

```bash
porthub list
```

## Skills

This repository includes a local skill for package-documentation retrieval workflows:

- Install:

```bash
npx skills add narumiruna/porthub
```

- Skill source: `skills/porthub/SKILL.md`

## Key Rules

A key is valid only when all rules pass:

1. It is not empty after trimming spaces.
2. It does not start or end with `/`.
3. It does not contain `//`.
4. It does not contain `..`.
5. It does not end with `.md`.

## Error Behavior

- Validation failures return non-zero exit code.
- `get` returns non-zero when a key is not found.
- `search` returns empty output with exit code `0` when no match exists.
