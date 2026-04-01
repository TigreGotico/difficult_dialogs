# Choice Solver (OPM Plugin)

When a premise has a `.choices` file, user input must be matched to one of the
labelled options. `parse_choice()` — `difficult_dialogs/choices.py:352` — does this matching.

---

## Default offline solver

With no plugin installed, matching is done entirely offline by `_DefaultChoiceSolver` —
`difficult_dialogs/choices.py:119`. Resolution order:

1. Exact label match (case-insensitive, e.g. `"A"`, `"b"`).
2. Input starts with label followed by punctuation or space (e.g. `"a)"`, `"a."`).
3. 1-based integer index (e.g. `"1"` selects option A).
4. Case-insensitive prefix of the option text (≥ 3 characters).

Returns `None` if no option matches. `MultiChoicePolicy` re-presents the menu on `None`.

---

## OPM semantic solver (optional)

Install `ovos-solver-bm25-plugin` to enable BM25-based semantic matching for
free-text inputs that the offline matcher cannot resolve:

```bash
pip install ovos-solver-bm25-plugin
```

The plugin is discovered automatically at import time via the
`opm.solver.multiple_choice` entry-point group. When installed, the offline
matcher still runs first; the OPM solver is only called for inputs that produce
no offline match.

`_OPMChoiceSolverAdapter.match_choice()` — `difficult_dialogs/choices.py:202`

### List installed solvers

```bash
dd solvers
```

Or in Python:

```python
from difficult_dialogs.choices import list_solvers
print(list_solvers())
# {'ovos-choice-solver-bm25': 'ovos_bm25_solver.choices:BM25ChoiceSolver'}
```

`list_solvers()` — `difficult_dialogs/choices.py:331`

---

## Changing the active solver

### Select a different OPM plugin

```python
from difficult_dialogs.choices import configure

configure("my-opm-reranker-plugin")   # entry-point name
# Solver is reloaded on next parse_choice() call
```

`configure()` — `difficult_dialogs/choices.py:315`

### Inject a custom solver at runtime

```python
from difficult_dialogs.choices import set_solver, ChoiceOption

class MyChoiceSolver:
    def match_choice(
        self,
        text: str,
        options: list[ChoiceOption],
        lang: str,
    ) -> ChoiceOption | None:
        # your matching logic
        ...

from difficult_dialogs.choices import set_solver
set_solver(MyChoiceSolver())
```

`set_solver()` — `difficult_dialogs/choices.py:299`

The solver must implement `ChoiceSolverProtocol` — `difficult_dialogs/choices.py:88`.

---

## Passing a solver directly to MultiChoicePolicy

```python
from difficult_dialogs.policy import MultiChoicePolicy

policy = MultiChoicePolicy(arg, choice_solver=MyChoiceSolver())
```

`MultiChoicePolicy.__init__()` — `difficult_dialogs/policy.py:1536`
