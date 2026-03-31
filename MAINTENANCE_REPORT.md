# Maintenance Report

Audit log of AI-assisted changes to this repository.

---

## 2026-03-31

**AI Model:** claude-sonnet-4-6

### Changes

1. **fix: remove redundant `Statement.__post_init__`** (`statements.py`)
   - `field(default=True, init=False)` already sets `agreed`; the `__post_init__`
     that re-set it to `True` was a no-op that misled readers about initialization order.

2. **feat: wire Five-Ws to `BasePolicy._check_five_w`** (`policy.py`)
   - Added shared helper `_check_five_w(user_input)` to `BasePolicy`.  Iterates
     all five keyword→premise field mappings (`what/why/how/when/where`) and
     returns `random.choice()` from the first match.
   - All four policies in `policy.py` (`KnowItAllPolicy`, `SocraticPolicy`,
     `DebatePolicy`, `ExploratoryPolicy`) now dispatch 5W questions at the top of
     `handle_input` before entering agree/disagree logic.
   - Previously only `KnowItAllPolicy` handled `what/why/how`; `when` and `where`
     were silently ignored by every policy.

3. **refactor: rename `policies.SocraticPolicy` → `MaieuticPolicy`; fix
   `POLICY_REGISTRY`; export all policies** (`policies.py`, `__init__.py`)
   - `SocraticPolicy` existed in both `policy.py` and `policies.py` — a silent
     name collision.  The `policies.py` variant overrides `start()` and injects
     the argument topic into question templates; it is a distinct "guided
     discovery" style renamed to `MaieuticPolicy`.
   - `POLICY_REGISTRY` lambdas were broken (chained string manipulation +
     `__import__` calls); replaced with direct imports.
   - All 10 policy classes now accessible from the top-level package via
     `get_policy()` and `POLICY_REGISTRY`.
   - Version bumped 0.4.0 → 0.5.0.

4. **refactor: factor out `Argument._apply_file_to_premise`** (`arguments.py`)
   - `_load_legacy_format` and `_load_premise` each duplicated a ~50-line dispatch
     block mapping file suffixes to `Premise.add_*` methods.  Extracted into a
     single static method with a `_DISPATCH` dict; new suffix→method mappings now
     require one edit instead of two.

5. **fix: typo `LLLMEnhancer` → `LLMEnhancer` in `llm/__init__.__all__`** (`llm/__init__.py`)
   - Triple-L typo meant `LLMEnhancer` was absent from `__all__` under the correct name.

6. **feat: complete Five-Ws generation; add `Argument.save()`; fix JSON fence stripping**
   (`llm/client.py`, `llm/generator.py`, `arguments.py`)
   - `generate_json` markdown fence stripping now handles any opening fence line (not just
     `` ```json ``), including `` ```python ``, `` ``` ``, etc.
   - `_generate_explanations` now requests all five keys (what/why/how/when/where); previously
     `when` and `where` were never requested and therefore always absent.
   - `_generate_premise` wired to call `add_when`/`add_where` via a dispatch loop.
   - Added `Argument.save(path)` — writes the argument to the plain-text directory format.
     Round-trip verified: build in memory → `save()` → `load()` → all fields intact.

7. **fix: scope contradiction detection; add `_validate_five_ws`; save() tests**
   (`validators.py`, `test_arguments.py`, `test_validators.py`)
   - Contradiction detection now checks only within-premise statement pairs.  Cross-premise
     polarity differences (e.g. "always" in premise 1, "never" in premise 2) are normal and
     were causing false positives.
   - Added `_validate_five_ws()`: INFO-level notice for each premise missing any 5W field.
   - Added 7 tests for `Argument.save()` and contradiction/five-ws validator behaviour.

8. **refactor: replace `_save_argument_files` with `arg.save()`; add `--policy` to debate; remove dead `DebaterPolicy.opposition`**
   (`cli.py`, `policies.py`)
   - CLI's `_save_argument_files` duplicated `Argument.save()` but omitted all 5W files; replaced.
   - `debate` subcommand now accepts `-p/--policy` with all 10 policy names as choices.
   - `DebaterPolicy.opposition` parameter stored but never read; removed to avoid misleading callers.

9. **feat: add `support` and `five_ws` tables to SQLite schema** (`export.py`)
   - `LibraryDatabase.add_argument` was silently discarding support arguments and all 5W content.
     An argument exported to SQLite and re-loaded via `get_argument()` would be missing all
     5W answers, making it unusable for interactive debates.
   - Added `support` and `five_ws` tables; `get_argument` now restores all fields on load.
   - 2 new tests: `test_support_persisted_in_sqlite`, `test_five_ws_persisted_in_sqlite`.

10. **feat: `run_sync`/`stream` delegate to `handle_input`; typed exceptions; dead code removed**
    (`policy.py`, `exceptions.py`, `arguments.py`, `policies.py`, `__init__.py`)
    - `run_sync` and `stream` hardcoded KnowItAll-style logic; 5W dispatch and all
      policy-specific behaviour were bypassed in generator mode.  Rewritten to call
      `self.handle_input()`.  `run_async()` removed — it was a broken stub.
      `policy.py` coverage 75% → 94%.
    - `exceptions.py` was fully orphaned (defined, never raised, never exported).
      Replaced with four typed exceptions: `ArgumentLoadError`, `ArgumentSaveError`,
      `InvalidPolicyError`, `MissingStatementError`. All exported from package root.
    - Dead `Argument.__post_init__` branch removed (`path` is `init=False`, always `None`).
    - Tests updated to catch new exception types; 6 new tests for `run_sync`/`stream`.

**Oversight:** Full automated test suite (571 tests) passed after each commit.
Human review required before merging or publishing.

---

## 2026-03-31 (continued)

**AI Model:** claude-sonnet-4-6

### Changes

11. **test: fill policies.py coverage gaps to 96%** (`test/test_policies.py`)
    - 18 new tests across 6 new test classes covering uncovered branches:
      `MaieuticPolicy` neutral-input and 5W dispatch, `SkepticPolicy` counter-premise
      and default skepticism, `TeacherPolicy` example/fallback paths,
      `DebaterPolicy` disagree double-down and attack-only, `MinimalistPolicy`
      no-statements disagree and exhausted conclusion paths.
    - policies.py 73% → 96%; suite 571 → 589 passing.

12. **test: fill validators.py to 99%, premises.py to 100%** (`test/test_validators.py`, `test/test_premises.py`)
    - Added `how`/`when`/`where` fields to `test_from_dict_roundtrip` — premises.py 89% → 100%.
    - 26 new tests covering `ValidationIssue.__str__` for all four severities,
      "Fair"/"Poor"/"Good" quality label branches, short-statement INFO,
      long-intro INFO, many-statements WARNING, brief-description INFO,
      duplicate-statements ERROR, empty-premise-name ERROR, invalid-URL WARNING,
      `validate_directory` load-failure path.
    - validators.py 89% → 99%; suite 589 → 605 passing.

13. **test: fill export.py coverage gaps to 95%** (`test/test_export.py`)
    - 5 new tests: `ArgumentEncoder` fallback, `get_argument()` None path,
      `list_arguments()` category filter, `export_to_sqlite` with validation,
      `export_library_to_json` skip-bad-dirs.
    - export.py 93% → 95%; suite 605 → 610 passing.

14. **test: fill policy.py coverage gaps to 99%** (`test/test_policy.py`)
    - 15 new tests: `BasePolicy._get_support`/`_get_sources`/`_check_five_w`
      null-return and stale-premise paths; 5W dispatch returns in `SocraticPolicy`,
      `DebatePolicy`, `ExploratoryPolicy`, `KnowItAllPolicy`; neutral-advance
      fallbacks; `KnowItAllPolicy` sources path; `run_sync` None-response break.
    - policy.py 94% → 99%; suite 610 → 623 passing.

15. **fix+test: cli.py 0% → 99%** (`difficult_dialogs/cli.py`, `test/test_cli.py`)
    - 26 new tests calling `cmd_validate`, `cmd_export`, `cmd_list`, `cmd_debate`,
      `cmd_generate` (mocked LLM) directly for coverage.
    - **Bug fixed:** `cli.py:194` — stats `--stats` flag crashed with `TypeError`
      when any argument had no category (None key in `by_category` dict).
      Fixed: `k or 'uncategorized'` in the join.
    - **Bug fixed:** `cli.py:234` — `get_policy()` raises `InvalidPolicyError`
      (not `ValueError`); except clause widened to `Exception`.
    - Total coverage 82% → 89%; suite 623 → 649 passing.

16. **test: LLM module tests — client/generator/enhancer 18-26% → 94-100%**
    (`test/test_llm.py`, new file)
    - 31 new tests covering `LLMClient.generate` (with/without model, system prompt,
      stop sequences), `generate_json` (fence stripping, schema, invalid-JSON error),
      `health_check` (200 OK, /v1/models fallback, both endpoints fail),
      `ArgumentGenerator.generate` pipeline (premises, sources, no-sources/no-counter,
      server-unreachable, error fallbacks), `_slugify`, `LLMEnhancer.rephrase`
      (cache hit, too-different fallback, exception fallback), `explain`,
      `summarize_exchange`, `clear_cache`, `_is_too_different`.
    - llm/client.py 26% → 100%, llm/generator.py 23% → 99%,
      llm/enhancer.py 18% → 94%, llm/__init__.py 0% → 100%.
    - Total coverage 89% → **98%**; suite 649 → **680 passing**.

**Oversight:** Full automated test suite (680 tests) passed after each commit.
Human review required before merging or publishing.
