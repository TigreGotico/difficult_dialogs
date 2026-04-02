# Status: difficult_dialogs Roadmap

## Checklist

### SHORT TERM — Stability & Correctness (v0.8 patch)

- [x] Verify & test `entry_point` seeding — add regression test with two premises; assert first spoken text matches `entry_point` premise, not insertion-order first
- [x] Fix `.who` persistence — already fixed in prior commit; added round-trip assertion to test_save_load_roundtrip
- [x] Fix private attribute access in `MultiChoicePolicy` — already fixed in prior commits; no `_premises` access in policy.py
- [x] Make `ovos-solver-yes-no-plugin` optional — added _BuiltinYesNoSolver regex fallback; demoted to [ovos] extra; removed unused requests dep
- [x] Raise CLI test coverage from 70% → 90% — added 13 new CLI tests; fixed ValidationSeverity comparison bug and ArgumentBuilder kwargs bug
- [x] Add cycle-detection to `ArgumentValidator` — already implemented; added diamond-graph false-positive test
- [ ] Document `entry_point` in `docs/argument-format.md` and `FAQ.md`

### MEDIUM TERM — DX & Publishability (v0.9)

- [ ] Publish to PyPI — align org name, run release workflow, tag v0.9.0
- [ ] OPM choice-solver auto-discovery — mirror `yesno._load_solver()` in `choices.py`; update `did solvers` output
- [ ] `ArgumentBuilder.branch()` shorthand — add method, update docs, add tests
- [ ] Add `timeout` parameter to `WebhookPolicy` — prevent hang on dead endpoints; add test
- [ ] Latency benchmark script — `scripts/benchmark.py`; 100 turns × 14 policies; print p50/p95

### LONG TERM — Stable API & Ecosystem (v1.0+)

- [ ] Stable 1.0 API guarantee — audit `__all__`, add `DeprecationWarning` to removed symbols, write migration guide
- [ ] High-level `ArgumentDiff` / `ArgumentMerge` UX — expose as top-level functions; add `did merge` CLI subcommand; add docs and tests
- [ ] Voice integration guide — `docs/OVOS_INTEGRATION.md`; example skill in `examples/ovos_skill.py`
- [ ] RAG / retrieval layer — `ArgumentLibrary.retrieve(query, top_k)` across premises; optional dep on `rank_bm25` or embeddings
- [ ] LMS / classroom export — `export_to_scorm()` or self-contained HTML debate exercise

## Blockers

<!-- populated by /implement-task if something is stuck -->
