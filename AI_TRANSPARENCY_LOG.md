# AI Transparency Log — difficult_dialogs

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
