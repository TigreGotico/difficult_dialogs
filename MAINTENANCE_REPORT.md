# MAINTENANCE REPORT — difficult_dialogs

Chronological audit log of AI-assisted changes.

---

## 2026-03-31 — Phase 2 revival (Claude Sonnet 4.6)

**AI Model:** Claude Sonnet 4.6
**Oversight:** Human review of all commits before push.

### Actions Taken

| Area | Change |
|---|---|
| `premises.py` | Added `who` field (6th W), `add_who()`, `apply_file` dispatch, `to/from_dict` |
| `policy.py` | `_check_five_w` now handles `who`; added `TranscriptEntry`, `PolicyState.to_dict/from_dict`, `AdaptivePolicy`, `WebhookPolicy`, `MultiArgumentPolicy` |
| `arguments.py` | Added `Argument.merge()` classmethod |
| `builder.py` | New module — `ArgumentBuilder` and `PremiseBuilder` fluent API |
| `library.py` | New module — `ArgumentLibrary` keyword search index |
| `server.py` | New module — FastAPI REST server with session store |
| `export/transcript.py` | New module — Markdown and JSON transcript export |
| `cli.py` | Added `dd serve` command; `AdaptivePolicy` wired to debate choices |
| `__init__.py` | Exported all new public classes |
| `docs/` | Created `index.md`, `argument-format.md`, `USER_GUIDE.md`, `DEVELOPER_GUIDE.md`, `POLICIES.md`; all URLs updated to TigreGotico |
| `pyproject.toml` | Added `[server]` extra (`fastapi`, `uvicorn`); removed stdlib `sqlite3` from extras |
| Tests | 785 tests passing; added suites for premises, policy, builder, multi-argument, server, export, library |

### Coverage

| Module | Coverage |
|---|---|
| `statements.py` | 100% |
| `premises.py` | 100% |
| `arguments.py` | 100% |
| `builder.py` | 100% |
| `policy.py` | 99% |
| `library.py` | 91% |
| `server.py` | 98% |
| `validators.py` | 100% |
| `llm/` | 99% |

---

## 2026-03-31 — Phase 1 revival (Claude Sonnet 4.6)

**AI Model:** Claude Sonnet 4.6
**Oversight:** Human review.

### Actions Taken

- Added type hints throughout all modules
- Wrote 42 initial unit tests
- Created `/docs` skeleton
- Migrated packaging to `pyproject.toml`
