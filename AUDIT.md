# Audit — difficult_dialogs

Evidence-based list of known issues, technical debt, and security considerations.

---

## Open Issues

### A-01 — `cmd_debate` does not call `policy.respond()` (uses `handle_input` directly)
**File:** `difficult_dialogs/cli.py:251`
**Severity:** Low
**Detail:** `cmd_debate` calls `policy.handle_input(user_input)` directly, bypassing
`policy.respond()` which also appends the user turn to `state.transcript`.
User turns therefore do not appear in the transcript when using the CLI.
**Fix:** Replace `policy.handle_input(user_input)` with `policy.respond(user_input)`.

### A-02 — `WebhookPolicy` has no timeout on HTTP calls
**File:** `difficult_dialogs/policy.py:WebhookPolicy`
**Severity:** Medium
**Detail:** The `requests.post` call in `WebhookPolicy.handle_input` uses the
default `requests` timeout (None — blocks forever). A slow or unreachable
webhook will hang the entire dialog loop.
**Fix:** Add `timeout=` parameter; expose it as a constructor argument.

### A-03 — `ArgumentLibrary.search` uses naïve token overlap scoring
**File:** `difficult_dialogs/library.py`
**Severity:** Info
**Detail:** Search scoring is simple token intersection.  Phrase order and
proximity are not considered, leading to poor ranking on short or ambiguous
queries.  Acceptable for v0.x; consider BM25 or vector embeddings for v1.

### A-04 — `export_to_sqlite` does not close connection on exception
**File:** `difficult_dialogs/export/sqlite.py`
**Severity:** Low
**Detail:** If `add_argument()` raises mid-export the `LibraryDatabase`
connection is not closed.  Use a context manager or try/finally.

### A-05 — No rate-limiting or session cap in `examples/server.py`
**File:** `examples/server.py`
**Severity:** Info (demo code)
**Detail:** The in-process `_sessions` dict has no size cap; a large number of
unclosed sessions will grow memory unbounded.  Acceptable for the demo; any
production deployment should add a TTL eviction layer.

---

## Resolved

| ID | Description | Fixed in |
|----|-------------|----------|
| R-01 | Six policy neutral branches unreachable due to `is_agreement(default=True)` | b211294 |
| R-02 | `server.py` shipped as library code, blurring library/demo boundary | b891b9e |
