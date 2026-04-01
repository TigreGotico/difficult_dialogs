# AI Transparency Log — difficult_dialogs

## 2026-04-01 — Session: multiple-choice input and branching argument graphs

**AI Model:** claude-sonnet-4-6

**Actions Taken:**

| Commit | Description |
|--------|-------------|
| 27d2c39 | feat: add choices.py — ChoiceOption, ChoiceSolverProtocol, parse_choice() |
| 45d9b27 | feat: extend Premise with choices, on_agree, on_disagree fields |
| 40d70e5 | feat: add entry_point and next_premise() graph traversal to Argument |
| ad4218d | feat: wire branching into BasePolicy._get_next_statement(); add MultiChoicePolicy |
| ac6f8eb | feat: extend ArgumentBuilder/PremiseBuilder with choice/branching fluent methods |
| c17c9d3 | feat: export new symbols from \_\_init\_\_.py |
| 5ea9550 | test: 71 new tests covering choices, branching, MultiChoicePolicy, builder |
| *(this commit)* | docs: argument-format, POLICIES, FAQ, SUGGESTIONS, AI log |

**Oversight:** Human review of all commits before push; full test suite (961 tests) run after each commit.

**Notes:**
- `Argument._premises` was already a `dict[str, Premise]` — no data model migration needed.
- `BasePolicy._get_next_statement()` now prefers `Argument.next_premise()` for graph edges before falling back to `get_next_premise()` (linear); fully backwards-compatible.
- `MultiChoicePolicy` uses offline label/prefix matching by default; accepts a pluggable `ChoiceSolverProtocol` for OPM reranker integration (S-09).

---

## 2026-04-01 — Session: revival, policy fixes, server refactor, user stories

**AI Model:** claude-sonnet-4-6

**Actions Taken:**

| Commit | Description |
|--------|-------------|
| 9a56fc7 | Phase 1 revival — type hints, 42 unit tests, docs |
| b211294 | Fix: use `parse_yes_no` directly so neutral input reaches all policy branches |
| fc3c108 | Feat: add `dd new` wizard, `progress()` method, `--save-transcript` to `dd debate` |
| b891b9e | Refactor: move `server.py` from library package to `examples/` |
| *(this session)* | Exports audit, `save_state`/`load_state`, `AdaptivePolicy.set_policy`, `--input-file` CLI flag, rename `dd`→`did`, user stories, roadmap, maintenance docs |

**Oversight:** Human review of all commits before push; tests run after each commit batch.

**Notes:**
- Neutral-input dead-code fix (b211294) required architectural change: six policies switched from `is_agreement(default=True)` to `parse_yes_no()` so `None` intent is a distinct reachable branch.
- Server moved to `examples/` to clarify library vs. demo boundary; `cmd_serve` now loads it dynamically via `importlib.util`.
- `dd` entrypoint renamed to `did` to avoid collision with the POSIX `dd` utility.
