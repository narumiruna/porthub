# PortHub MVP Specification

## Purpose

Define the minimum viable product (MVP) for PortHub: a local CLI tool that stores and retrieves Markdown context by hierarchical keys.

## Product Goal

PortHub must let a user:
1. Save Markdown content under a key.
2. Read Markdown content by exact key.
3. Search keys and content with a plain substring query.

## In Scope

- Local filesystem storage only.
- CLI interface only.
- Hierarchical keys such as `python/typer`.
- Markdown payloads stored as `.md` files.
- Commands: `set`, `get`, `search`.

## Out of Scope

- Cloud sync or remote API.
- Multi-user access control.
- Metadata, versioning, or history.
- Full-text indexing engine.
- Prefix aggregation on `get`.

## Storage Model

- Root directory: `~/.porthub/`.
- Key-to-path mapping: `<key>` -> `~/.porthub/<key>.md`.
- Parent directories must be created automatically when needed.

Example mappings:
- `python/typer` -> `~/.porthub/python/typer.md`
- `rust/clap` -> `~/.porthub/rust/clap.md`

## Key Rules

A key is valid only when all rules pass:
1. It is not empty after trimming spaces.
2. It does not start or end with `/`.
3. It does not contain `//`.
4. It does not contain `..`.
5. It does not end with `.md`.

Invalid keys must fail fast with a clear CLI error.

## Command Behavior

### `porthub set <key> <value>`

- Validate key.
- Resolve target file path.
- Create parent directories if missing.
- Overwrite existing file content atomically.
- Exit code `0` on success.

### `porthub get <key>`

- Validate key.
- Read exact mapped file only.
- Print raw Markdown content without wrappers.
- If file does not exist, return a not-found error with non-zero exit code.

### `porthub search <query>`

- Reject empty query.
- Scan all `~/.porthub/**/*.md` files.
- Match when query is a substring of either:
  - the normalized key, or
  - file content.
- Return matched keys, one per line, sorted ascending.
- Return empty output with exit code `0` when no match exists.

## Error Handling

- Validation and not-found cases must produce deterministic, human-readable messages.
- Internal I/O failures must return non-zero exit code.
- No silent fallback behavior is allowed.

## Security and Trust Boundary

- Stored and retrieved content is untrusted input.
- PortHub must not execute stored content.
- PortHub only reads and writes files within `~/.porthub/`.

## Acceptance Criteria

The MVP is complete only when all criteria pass:
1. `set` creates and overwrites mapped `.md` files correctly.
2. `get` returns exact content for existing keys and proper errors for missing keys.
3. `search` returns deterministic key lists based on substring matches.
4. Invalid keys are rejected consistently across all commands.
5. Behavior is covered by automated tests for happy path and failure cases.

## Future Work (Post-MVP)

- Prefix aggregation (`get python` -> aggregated children).
- Metadata fields (tags, source, timestamps).
- Faster search backend.
