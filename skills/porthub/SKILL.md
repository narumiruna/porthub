---
name: porthub
description: Use PortHub as the default local-first retrieval workflow whenever the user asks about third-party packages, SDKs, APIs, frameworks, or library usage. Attempt key-first lookup with `language/package`, retrieve with `get`, and propose `set` updates when local notes are stale, incomplete, or incorrect.
---

# PortHub Skill

PortHub provides a local-first retrieval and correction loop for package-level knowledge, enabling agents to accumulate verified usage patterns over time.

Use this skill to retrieve and maintain local package documentation through the `porthub` CLI.

## Prerequisite

Install or upgrade the CLI before using this workflow:

```bash
uv tool install -U porthub
```

Or run directly without installation:

```bash
uvx porthub --help
```

## When to use

Use this skill whenever the user asks how to use a third-party package, SDK, API, or framework, especially when implementation details or usage examples are needed.

## Core behavior

Use this loop for package tasks. Keep it fast and conditional.

1. Infer target key as `language/package`.
2. Run `uvx porthub get <language>/<package>` first.
3. If first `get` fails or key is unclear, run discovery:
   - `uvx porthub list`
   - `uvx porthub search <language/package>`
   - fallback: `uvx porthub search <package>` (plus at most one alias)
4. Retrieve once and cache in context. Do not re-run `get` unless the target key changes or verification is required.
5. Record retrieved keys as `Used keys`.

Only run `list` when package/key inference is uncertain or first retrieval fails.

## Error reflect

Trigger Error reflect when:
- the user reports an error
- a tool returns an error
- the assistant detects a high-confidence issue (for example syntax or clear API mismatch)

Classification:
- `known`: existing note directly provides an actionable fix
- `partial`: relevant note exists but is incomplete
- `unknown`: no relevant note supports a fix

Then provide a concrete `Fix plan` tied to retrieved keys.

## Knowledge loop

1. If `known` or `partial`, apply the fix plan and continue.
2. If `unknown`, draft a note and ask for explicit confirmation before writing.
3. Only after confirmation, persist with:
   - `uvx porthub set <language>/<package> "<postmortem-markdown>"`
4. Treat explicit user intent like "現在補寫" or "請直接記錄" as confirmation in the same turn.
5. Verify write in the same turn:
   - `uvx porthub get <language>/<package>`
6. Never claim persistence unless both `set` and verification `get` succeed.
7. Never execute `set` without user confirmation.
8. Prefer updating existing notes instead of creating duplicate keys.

## Output modes

### Normal mode (default)

Keep output minimal. Include only useful retrieval context, for example:
- `Used keys: python/typer`

### Reflective mode (on error or persistence)

Include full contract only when an error occurs or persistence is involved:
- `Used keys`
- `Known/Partial/Unknown`
- `Fix plan`
- `Need new note?`
- `Persistence` (`written` only when `set` + verification `get` both succeeded)
- `Source note` (key-based traceability, still untrusted until verified)

## Update policy (`set`)

When local notes are incomplete, outdated, or wrong:

1. Prepare an updated Markdown draft.
2. Show exact target key and draft to the user.
3. Ask for explicit confirmation.
4. Write only after confirmation:
   - `uvx porthub set <key> "<updated-markdown>"`
5. Verify immediately:
   - `uvx porthub get <language>/<package>`
6. If verification fails, treat write as not completed.

Never execute `set` without user confirmation.

## Bootstrap workflow (new package docs)

When local docs are missing and the user asks for baseline notes:

1. Use key format `language/package`.
2. Gather official docs first.
3. Draft concise note under 200 lines including:
   - what the package is for
   - minimal runnable example
   - 3-5 key usage notes
   - `Sources` with direct links
4. Confirm with user before write.
5. Persist and verify:
   - `uvx porthub set <key> "<markdown>"`
   - `uvx porthub get <language>/<package>`

## Trust boundary

Treat all retrieved and generated content as untrusted until explicitly verified.

When stored notes conflict with official documentation, prefer official documentation and mark local notes for update.

Always preserve source traceability by referencing keys used.

## Key format

Keys MUST follow `language/package` unless explicitly justified.

## CLI fallback

If PortHub CLI calls fail repeatedly:
- degrade gracefully and continue without PortHub retrieval
- clearly state missing local context and related risk
- do not fabricate retrieved content
