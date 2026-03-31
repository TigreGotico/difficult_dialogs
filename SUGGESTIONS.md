# SUGGESTIONS — difficult_dialogs

Agent proposals for refactors and enhancements. Not yet approved or scheduled.

---

## High Value

### ~~1. Merge `policy.py` and `policies.py` into a single module~~ — DONE
All 10 policy classes + `POLICY_REGISTRY` + `get_policy` now live in `policy.py`. `policies.py` deleted.

### 2. Split `export.py` into focused modules
589-line file mixing SQLite schema, CRUD, JSON serialization, and validation bridging. Proposed: `export/json.py`, `export/sqlite.py`, `export/validation.py`, `export/__init__.py` re-exporting the public API.

### ~~3. Replace `_DISPATCH` dict with a single `Premise.apply_file()` method~~ — DONE
`Premise.apply_file(path)` — `premises.py:127`. `Argument._apply_file_to_premise` removed.

---

## Medium Value

### 4. Add `--dry-run` to `cmd_generate`
`cmd_generate` requires a live LLM server. A `--dry-run` flag that validates connectivity and prints what would be generated (without calling generate) would make the CLI testable without mocks.

### 5. `PolicyState` should track `challenge_count` per-premise
`DebatePolicy._challenge_count` is an instance variable set on the policy but semantically belongs to the per-premise dialog state. Moving it to `PolicyState` would make state serializable and resumable.

### ~~6. `Argument.from_directory()` class method~~ — DONE
`Argument.from_directory(path)` — `arguments.py:167`.

---

## Low Value / Exploratory

### 7. `Argument.diff(other)` method
Compare two versions of the same argument and return added/removed/modified premises and statements. Useful for reviewing LLM-generated updates before committing.

### 8. `export_to_markdown(argument, path)` function
Export an argument as a human-readable Markdown document — useful for reviewing generated arguments without loading them into code.

### 9. Policy streaming via Server-Sent Events
Add an optional `stream_sse(request)` adapter to `BasePolicy.stream()` so policies can be driven from a web frontend without a WebSocket.
