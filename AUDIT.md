# AUDIT — difficult_dialogs

Known issues, technical debt, and security notes. All citations include `file.py:LINE`.

---

## Open Issues

### `export.py:123-124` — load warning silently swallowed
`export_library_to_json` catches all exceptions and prints a warning instead of propagating. Bad arguments are silently skipped with no way for callers to detect partial failures.
- **Severity**: Low
- **File**: `difficult_dialogs/export.py:123`

### `export.py:365-368` — `_get_argument_id` returns 0 on miss
When an argument name is not found, `_get_argument_id` returns `0`. Callers that use the return value as a database key will silently associate data with a non-existent row.
- **Severity**: Medium
- **File**: `difficult_dialogs/export.py:365`

### `validators.py:209` — unreachable duplicate-premise-name branch
`_validate_premises` checks for duplicate names in `premise_names` list, but `_premises` is a dict — keys are unique by construction. The duplicate check can never fire unless `_premises` is mutated directly.
- **Severity**: Low (dead code)
- **File**: `difficult_dialogs/validators.py:205`

### `arguments.py:207` — dead `continue` in `_load_legacy_format` (removed)
Legacy format was dropped in refactor. No longer present.

### `policy.py:58` — abstract method body is `pass`
`BasePolicy.handle_input` uses `pass` instead of `raise NotImplementedError`. Subclasses that forget to implement it will silently return `None` instead of raising.
- **Severity**: Low
- **File**: `difficult_dialogs/policy.py:58`

---

## Technical Debt

~~Dual policy modules~~ — resolved: all 10 policy classes, `POLICY_REGISTRY`, and `get_policy` merged into `policy.py`; `policies.py` deleted.

### `export.py` size
At 589 lines, `export.py` mixes SQLite schema management, CRUD, JSON serialization, and validation. Should be split into `export/json.py`, `export/sqlite.py`, and `export/validator_bridge.py`.

### `cli.py:cmd_generate` depends on live LLM
`cmd_generate` has no dry-run or offline mode. Integration tests must mock the entire `ArgumentGenerator` stack. Consider a `--dry-run` flag that validates server connectivity only.

### No input sanitization in `cli.py:cmd_debate`
`user_input` from `input()` is passed directly to `handle_input()`. For multi-user or web deployments this is fine (all local), but worth noting for any future web exposure.

---

## Security Notes

- All file reads in `Argument.load()` use `Path.read_text()` — no shell execution, no injection risk.
- `LLMClient` uses `urllib.request` with explicit `Content-Type` header and JSON encoding — no shell command exposure.
- SQLite export uses parameterized queries throughout (`?` placeholders) — no SQL injection risk.
- LLM-generated content is stored as plain text and never executed — no prompt injection execution risk.
