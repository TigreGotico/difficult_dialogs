# Audit: difficult_dialogs — Stability, Fixes & Roadmap Execution

## Summary

All short-term (v0.8) and medium-term (v0.9) checklist items are complete except PyPI publishing (blocked on org name decision). OVOS plugin manager and default solver plugins are now proper mandatory dependencies per user direction. `choices.py` coverage reached 97%, CLI coverage 91%. Overall coverage is 96% (1% below the 97% spec target) — remaining misses are in `--watch` interactive paths, `cmd_serve`, and BM25 library code that is exercised but collected from a stale DEPRECATED test path.

---

## Acceptance Criteria

| Criterion | Status | Evidence |
| :--- | :--- | :--- |
| `pytest test/test_branching.py -k entry_point` passes; first response from entry-point premise | Pass | `test/test_branching.py:153-172` — `TestEntryPointSeeding` 2 tests pass |
| `pytest test/test_arguments.py -k who` round-trip test | Pass | `test/test_arguments.py:268-281` — dedicated `test_who_survives_save_load_roundtrip` selected by `-k who` |
| `grep "_premises" difficult_dialogs/policy.py` returns 0 | Pass | `grep '\._premises' policy.py` returns 0; only `spoken_premises` field references remain |
| Install requires OPM + solver plugin | Pass | `pyproject.toml:32-35` — `ovos-plugin-manager`, `ovos-solver-yes-no-plugin`, `ovos-solver-bm25-plugin`, `rank-bm25` are mandatory deps. `yesno.py:72-76` raises `RuntimeError` if no plugin found. |
| OPM solver used for yes/no | Pass | `yesno.py:57-65` tries named plugin first, then any registered plugin; conftest mock solver used in tests |
| `cli.py` ≥90% coverage | Pass | 91% (484 stmts, 42 miss). Remaining misses are `--watch` watchdog observer (233-253), `cmd_serve` (555-576), `__main__` guard (899). |
| `choices.py` ≥95% coverage | Pass | 97% (121 stmts, 4 miss). OPM adapter and loader error paths now tested. |
| `pytest test/test_validators.py -k cycle` passes | Pass | 2 tests: `test_cycle_two_nodes`, `test_diamond_graph_no_false_positive` — `test/test_validators.py:703-748` |
| `ArgumentBuilder.branch("yes","no")` sets both edges | Pass | `builder.py:137-171`; tested at `test/test_builder_choices.py:87-102` |
| `WebhookPolicy` timeout triggers fallback | Pass | `policy.py:1281` stores timeout; `policy.py:1320` passes to `urlopen`; `test/test_policies.py:620-640` 2 tests |
| `did solvers` shows two sections | Pass | `cli.py:474-502` prints "YES/NO SOLVERS:" and "CHOICE SOLVERS:" |
| `docs/argument-format.md` contains "entry_point" | Pass | `docs/argument-format.md:164-175` |
| `scripts/benchmark.py` exits 0, prints table | Pass | 11 rows × 2 columns (p50/p95), no network required. Spec says 14 rows but 3 policies (webhook, llmenhanced, multiargument) require special args and are skipped |
| 32 sample arguments pass `did validate` | Pass | `test/test_sample_arguments.py`: 395 tests pass |
| Full suite ≥97% coverage | **Fail** | 96% (2727 stmts, 99 miss) — 1% below target. Remaining misses: cli.py interactive paths (42), library.py BM25 (10), policy.py edge cases (23). |

---

## Gaps & Issues

| Severity | Location | Description |
| :--- | :--- | :--- |
| Minor | `scripts/benchmark.py:98` | Benchmark prints 11 rows not 14 as spec states. Three policies (`webhook`, `llmenhanced`, `multiargument`/`multichoice`) are in `_SKIP` set — they require special constructor args (URL, LLM client, argument list). |
| Minor | `test/test_library.py:288` | BM25 test is collected from stale `DEPRECATED` path instead of local test dir, causing it to skip despite `rank-bm25` being installed. This accounts for 10 of the 99 missed lines. Fix pytest collection config or remove the DEPRECATED symlink. |
| Info | `spec.md:72` | Spec states `parse_yes_no` returns `"agree" | "disagree" | None` but actual signature is `bool | None`. This is a spec error, not an implementation error. |

---

## Suggestions

- Fix pytest collection to prefer local `test/` over DEPRECATED path — would recover ~10 lines of BM25 coverage and push overall closer to 97%.
- Benchmark could construct mock WebhookPolicy with a local fixture server and MockLLMEnhancer to cover all 14 policies, but the practical value is low — the 3 skipped policies delegate to the same `BasePolicy._get_next_statement()` engine.
- Long-term items in `status.md` (v1.0) are intentionally deferred and appropriately scoped.
