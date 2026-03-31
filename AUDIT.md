# AUDIT — difficult_dialogs

Known issues, technical debt, and security notes. All citations include `file.py:LINE`.

## Open Issues

### ArgumentGenerator does not populate `who` field
- `llm/generator.py:_generate_premise` — `_generate_explanations()` returns a dict with keys `what/why/how/when/where` but not `who`. The `who` field added to `Premise` (`premises.py:43`) is never populated by LLM generation.
- **Severity:** Low (feature gap, not a bug)
- **Fix:** Add `who` to the system prompt in `_generate_explanations()` and call `premise.add_who()`.

### `library.py` partial coverage (91%)
- Lines 94, 120-121, 161, 192, 205, 221, 235 — edge cases (empty directory, malformed argument, category boundary) not yet tested.
- **Severity:** Low

### `cli.py` serve error path untested (95%)
- Lines 309-325, 522 — `cmd_serve()` import-error branch (FastAPI not installed) and version subcommand.
- **Severity:** Low

### `policy.py` async path partially untested (99%)
- Lines 802-803, 817-818 — `run_async()` generator edge cases.
- **Severity:** Negligible

### `docs/DEVELOPER_GUIDE.md` module list stale
- Lists `policies.py` as a module (`DEVELOPER_GUIDE.md:62`) — this file does not exist. Should list `builder.py` and `library.py` instead.
- **Severity:** Docs only

## Security Notes

- `WebhookPolicy` (`policy.py`) makes outbound HTTP requests to a caller-supplied URL. No SSRF protection. Only use in trusted environments.
- `server.py` session store is in-process dict — no authentication, no rate limiting. Not production-ready without a reverse proxy.
- `llm/client.py` trusts LLM JSON responses directly — `generate_json()` raises `ValueError` on bad JSON but does not sanitize content before it reaches callers.

## Technical Debt

- `ArgumentGenerator._generate_premise()` (`llm/generator.py`) calls the LLM three times per premise (support, sources, explanations). Could be batched into one call.
- `LLMEnhancer` is not wired to any built-in policy. It exists as a standalone utility but has no `LLMEnhancedPolicy` integration.
- `export/sqlite.py` uses raw string SQL construction in places — should use parameterized queries throughout.
