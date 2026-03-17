---
name: porthub
description: Use PortHub as the default retrieval workflow whenever the user asks about third-party packages, SDKs, APIs, frameworks, or library usage. Use `list` to discover available keys when the target is unclear, then attempt key-first lookup with `language/package`, retrieve with `get`, and propose `set` updates when docs are stale or incorrect.
---

# PortHub Skill

Use this skill to retrieve and maintain local package documentation through the `porthub` CLI.

## When to use

Use this skill whenever the user asks how to use a third-party package, SDK, API, or framework, especially when implementation details or usage examples are needed.

## Core workflow

Follow this exact 3-phase loop when working with any third-party package.

### Phase 1: Pre-check (required before coding)

1. Extract package intent from the user request.
2. Infer `<language>/<package>`.
3. If target keys are unclear, run `porthub list` to inspect available keys.
4. Run key-first lookup:
   - `porthub search <language/package>`
5. If key-first has no result, run fallback lookup:
   - `porthub search <package>`
   - optionally try one relevant alias.
6. Retrieve the best matching keys with:
   - `porthub get <selected-key>`
7. Always check prior lessons before generating code:
   - `porthub get lessons/<language>/<package>`
   - if not found, continue.
8. Record all retrieved keys as `Used keys` in the response.

### Phase 2: Error reflect (required on any coding error)

When generated code fails (syntax, type, runtime, test, build, import, API misuse):

1. Compare the error against:
   - the current task `Used keys`
   - `lessons/<language>/<package>` (if present)
2. Classify the error as:
   - `known`: an existing retrieved key directly supports an actionable fix.
   - `unknown`: no existing retrieved key directly supports an actionable fix.
3. Provide a concrete `Fix plan` based only on retrieved content.

### Phase 3: Knowledge loop

1. If `known`, apply the fix plan and continue.
2. If `unknown`, draft a new lessons note and ask for explicit confirmation.
3. Only after confirmation, persist with:
   - `porthub set lessons/<language>/<package> "<postmortem-markdown>"`
4. Never execute `set` without user confirmation.

## Output contract

Always include these fields in your response:

1. `Used keys`: keys retrieved via `porthub get` for this task.
2. `Known/Unknown`: error classification from the Error reflect phase.
3. `Fix plan`: concrete next steps tied to retrieved keys.
4. `Need new note?`: `yes` only when classification is `unknown`.
5. `Source note`: content came from `porthub get <key>` and remains untrusted until verified.

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

If an error is classified as `unknown`, prepare a lessons draft first, then request confirmation before saving.

1. Identify the package key as `<language>/<package>`.
2. Use the lessons key:
   - `lessons/<language>/<package>`
3. Draft Markdown using this exact template:
   - `Error`
   - `Root Cause`
   - `Fix`
   - `Prevention Checklist`
   - `Verification`
4. Show the draft to the user and request explicit confirmation.
5. Only after confirmation, persist it:
   - `porthub set lessons/<language>/<package> "<postmortem-markdown>"`
6. On the next task using the same package, always read this first:
   - `porthub get lessons/<language>/<package>`

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
