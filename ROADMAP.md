# Roadmap — difficult_dialogs

## v0.6 — API Completeness *(in progress)*

- [x] Export all missing public symbols from `__init__.py`
      (`ArgumentValidator`, `ValidationResult`, `ValidationSeverity`,
      `ValidationIssue`, `export_transcript_to_markdown`,
      `export_transcript_to_json`, `ArgumentGenerator`, `LLMEnhancer`,
      `LLMClient`)
- [x] `BasePolicy.save_state(path)` / `load_state(path)` — file-based session
      persistence
- [x] `AdaptivePolicy.set_policy(policy)` — manual policy override
- [x] `did debate --input-file FILE` — non-interactive / CI-friendly debate runs
- [x] Rename CLI entrypoint `dd` → `did` (avoids conflict with system `dd`)
- [x] `py.typed` PEP 561 marker — type checkers treat package as fully typed
- [x] Document `BasePolicy.stream()` async usage in USER_GUIDE.md

## v0.7 — Developer Experience

- [x] `did replay FILE` — step through a saved transcript non-interactively,
      useful for regression tests
- [x] `did score ARG_DIR` — one-line quality score (no full validate output)
- [x] `ArgumentLibrary.watch(callback)` — hot-reload index on filesystem change
      (requires `watchdog`)
- [x] `progress()` in REST server `GET /sessions/{id}` response
- [x] WebSocket endpoint in `examples/server.py` for streaming dialog

## v0.8 — Multi-language & Solver Ecosystem

- [ ] Solver auto-discovery via `opm.agents.yesno` entry points (scaffolding
      already present in `yesno.py`)
- [x] Language routing in `BasePolicy` — pass `lang` through to `parse_yes_no`
- [x] `Premise` i18n: `translations: dict[str, dict[str, list[str]]]` field
      for statement text in multiple locales; locale-specific file format

## v1.0 — Stable Public API

- [ ] Semantic versioning guarantee on all symbols in `__all__`
- [ ] `ArgumentDiff` / `ArgumentMerge` high-level UX (`diff()` and `merge()`
      primitives exist in `arguments.py` but have no standalone API surface)
- [x] Formal plugin spec for custom policies via entry-point group
      `difficult_dialogs.policies`
- [x] `did debate --watch` — reload argument file on change without restarting
      the CLI session
