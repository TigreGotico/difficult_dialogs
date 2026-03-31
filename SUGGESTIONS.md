# SUGGESTIONS — difficult_dialogs

Agent proposals for refactors and enhancements. Not yet approved or scheduled.

---

## High Value

### 1. Merge `policy.py` and `policies.py` into a single module
The split between `policy.py` (5 policies) and `policies.py` (5 more) is arbitrary and confuses imports. A single `difficult_dialogs/policies/` package with one class per file and an `__init__.py` re-exporting all 10 + `POLICY_REGISTRY` + `get_policy` would eliminate the confusion.

### 2. Split `export.py` into focused modules
589-line file mixing SQLite schema, CRUD, JSON serialization, and validation bridging. Proposed: `export/json.py`, `export/sqlite.py`, `export/validation.py`, `export/__init__.py` re-exporting the public API.

### 3. Replace `_DISPATCH` dict with a single `Premise.apply_file()` method
`arguments.py:_apply_file_to_premise` is a static method that maps file suffixes to `Premise.add_*` methods. This dispatch belongs on `Premise` itself — `premise.apply_file(path)`. Keeps `Argument` focused on structure, `Premise` focused on content.

---

## Medium Value

### 4. Add `--dry-run` to `cmd_generate`
`cmd_generate` requires a live LLM server. A `--dry-run` flag that validates connectivity and prints what would be generated (without calling generate) would make the CLI testable without mocks.

### 5. `PolicyState` should track `challenge_count` per-premise
`DebatePolicy._challenge_count` is an instance variable set on the policy but semantically belongs to the per-premise dialog state. Moving it to `PolicyState` would make state serializable and resumable.

### 6. `Argument.from_directory()` class method
A `@classmethod` version of `load()` that returns a new `Argument` (instead of mutating self) would be more idiomatic:
```python
arg = Argument.from_directory("path/to/arg")
```
The current pattern `Argument().load(path)` is unusual.

---

## Low Value / Exploratory

### 7. `Argument.diff(other)` method
Compare two versions of the same argument and return added/removed/modified premises and statements. Useful for reviewing LLM-generated updates before committing.

### 8. `export_to_markdown(argument, path)` function
Export an argument as a human-readable Markdown document — useful for reviewing generated arguments without loading them into code.

### 9. Policy streaming via Server-Sent Events
Add an optional `stream_sse(request)` adapter to `BasePolicy.stream()` so policies can be driven from a web frontend without a WebSocket.
