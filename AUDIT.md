# AUDIT — difficult_dialogs

Known issues, technical debt, and security notes. All citations include `file.py:LINE`.

---

## Open Issues

### `export/json.py:117-118` — load warning silently swallowed
`export_library_to_json` catches all exceptions and prints a warning instead of propagating. Bad arguments are silently skipped with no way for callers to detect partial failures.
- **Severity**: Low (intentional bulk-export design; callers can inspect returned bundle)
- **File**: `difficult_dialogs/export/json.py:117`

~~`export/sqlite.py` — `_get_argument_id` returns 0 on miss~~ — resolved: now raises `KeyError`.

~~`validators.py:209` — unreachable duplicate-premise-name branch~~ — resolved: dead code removed.

~~`arguments.py:207` — dead `continue` in `_load_legacy_format`~~ — resolved: legacy format removed.

~~`policy.py:58` — abstract method body is `pass`~~ — resolved: now raises `NotImplementedError`.

---

## Technical Debt

~~Dual policy modules~~ — resolved: all 10 policy classes, `POLICY_REGISTRY`, and `get_policy` merged into `policy.py`; `policies.py` deleted.

~~`export.py` size~~ — resolved: split into `export/json.py`, `export/sqlite.py`, `export/__init__.py`.

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
