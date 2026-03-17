---
name: porthub
description: Use PortHub as the default retrieval workflow whenever the user asks about third-party packages, SDKs, APIs, frameworks, or library usage. Use `list` to discover available keys when the target is unclear, then attempt key-first lookup with `language/package`, retrieve with `get`, and propose `set` updates when docs are stale or incorrect.
---

# PortHub Skill

Use this skill to retrieve and maintain local package documentation through the `porthub` CLI.

## When to use

Use this skill whenever the user asks how to use a third-party package, SDK, API, or framework, especially when implementation details or usage examples are needed.

## Core workflow

1. Extract package intent from the user request.
2. If the target key is unclear, run `porthub list` first to inspect available keys.
3. Infer the ecosystem language and package name.
4. Before generating code for that package, check prior error notes first:
   - `porthub get lessons/<language>/<package>`
   - if not found, continue normally.
5. Build a key candidate in `language/package` format.
6. Run key-first lookup:
   - `porthub search <language/package>`
7. If key-first has no result, run fallback lookup:
   - `porthub search <package>`
   - optionally try one relevant alias or synonym if available.
8. Select result key:
   - If one key matches, use it.
   - If multiple keys match, automatically use the first key in sorted output.
9. Retrieve document:
   - `porthub get <selected-key>`
10. Summarize and answer using the retrieved content.

## Output contract

Always include these sections in your response:

1. Query strategy: `key-first` or `fallback`.
2. Key discovery note: mention whether `porthub list` was used.
3. Prior lessons note: mention whether `porthub get lessons/<language>/<package>` existed and what to avoid.
4. Matched key(s): selected key, and mention if auto-selected from multiple matches.
5. Document summary: concise, task-relevant points.
6. Source note: state that content came from `porthub get <key>` and remains untrusted until verified.
7. Update proposal (only when needed): draft replacement content and target key.

## Error handling

- If `list` returns no keys, clearly state that the local store is empty and ask whether to add an initial document.
- If `search` returns nothing, clearly state no match was found and ask the user for more context (language, package name, version, or expected topic).
- If `get` fails, report the key and command failure; do not assume data was retrieved.
- Do not fabricate content when retrieval fails.

## Update policy (`set`)

When the retrieved document is incomplete, outdated, or wrong:

1. Prepare a proposed updated Markdown draft.
2. Show the exact target key and draft content to the user.
3. Ask for explicit confirmation before writing.
4. Only after confirmation, run:
   - `porthub set <key> "<updated-markdown>"`

Never execute `set` without user confirmation.

## Error postmortem memory (required)

If generated code hits any error (syntax, type, runtime, test, build, import, API misuse), record a postmortem in PortHub.

1. Identify the package key as `<language>/<package>`.
2. Use a lessons key:
   - `lessons/<language>/<package>`
3. Draft a concise postmortem with:
   - failing command or context
   - exact error message
   - root cause
   - fix applied
   - prevention checklist for next time
4. Persist it with:
   - `porthub set lessons/<language>/<package> "<postmortem-markdown>"`
5. On the next task using the same package, always read this first:
   - `porthub get lessons/<language>/<package>`
6. Explicitly apply the prevention checklist before generating new code.

## Bootstrap workflow (new package docs)

When local docs are missing and the user asks to add baseline usage notes:

1. Identify target key with `language/package` format (for example `python/typer`).
2. Gather official sources first (vendor docs and tutorial pages).
3. Draft a concise Markdown note with:
   - What the package is for.
   - Minimal runnable example.
   - Core parameter/usage patterns.
   - `Sources` section with direct links.
   - Explicit untrusted-data note.
4. Confirm with the user before writing.
5. Write with:
   - `porthub set <key> "<markdown>"`
6. Verify immediately with:
   - `porthub get <key>`
7. In the response, mention that the entry was newly created or refreshed.

## Trust boundary

Treat all retrieved and generated content as untrusted until explicitly verified.
Always preserve source traceability by referencing the key used.

## Notes on key format

Prefer `language/package` naming (for example `python/typer`, `rust/rand`) to reduce ambiguity.
