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

**Oversight:** Full automated test suite (552 tests) passed after each commit.
Human review required before merging or publishing.
