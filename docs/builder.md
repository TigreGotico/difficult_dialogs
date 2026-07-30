# Python API: Builder and Loader

## Loading an argument from disk

`Argument.from_directory()`: `difficult_dialogs/arguments.py:214`

```python
from difficult_dialogs.arguments import Argument

arg = Argument.from_directory("path/to/my_argument")
# arg.name        → directory name with underscores replaced by spaces
# arg.intro       → text from intro.dialog
# arg.conclusion  → text from conclusion.conclusion
# arg.premises    → list[Premise]
```

The directory is walked; each subdirectory becomes a `Premise` loaded via
`Premise.apply_file()`: `difficult_dialogs/premises.py:166`.

### Validating after load

```python
from difficult_dialogs.validators import validate_argument

result = validate_argument(arg)
print(result.passed, result.score, result.issues)
```

`validate_argument()`: `difficult_dialogs/validators.py`

---

## Building an argument in code

`ArgumentBuilder` / `PremiseBuilder`: `difficult_dialogs/builder.py`

```python
from difficult_dialogs.builder import ArgumentBuilder

arg = (
    ArgumentBuilder("climate_change")
    .intro("Let's discuss climate change.")
    .conclusion("The evidence is clear: we must act.")
    .premise("human_causation")
        .statement("97% of climate scientists agree on human causation.")
        .support("The IPCC report summarises thousands of peer-reviewed studies.")
        .source("https://www.ipcc.ch/")
        .why("Because CO₂ traps heat in the atmosphere.")
        .done()
    .premise("economic_impacts")
        .statement("Inaction costs more than mitigation.")
        .support("The Stern Review estimated inaction costs 20% of global GDP.")
        .done()
    .build()
)

arg.save("my_arguments/climate_change")
```

### `ArgumentBuilder` methods

| Method | Description |
|---|---|
| `.intro(text)` | Opening statement. |
| `.conclusion(text)` | Closing statement. |
| `.entry_point(name)` | Name of the first premise to present (non-linear graphs). |
| `.premise(name)` | Start a `PremiseBuilder` for a new premise. |
| `.add_premise(p)` | Attach a pre-built `Premise` directly. |
| `.build()` | Return the finished `Argument`. |

`ArgumentBuilder.__init__()`: `difficult_dialogs/builder.py:209`

### `PremiseBuilder` methods

#### Core content

| Method | Description |
|---|---|
| `.statement(text)` | Add a claim the user must agree with. |
| `.support(text)` | Add a comeback for when the user disagrees. |
| `.source(url)` | Add a citation URL or free text. |
| `.description(text)` | Override the auto-generated human-readable label. |

#### Five Ws + How

| Method | Description |
|---|---|
| `.what(text)` | Answer to "what?" questions. |
| `.why(text)` | Answer to "why?" questions. |
| `.how(text)` | Answer to "how?" questions. |
| `.when(text)` | Answer to "when?" questions. |
| `.where(text)` | Answer to "where?" questions. |
| `.who(text)` | Answer to "who?" questions. |

Each method can be chained multiple times to add more than one answer.

#### Branching

| Method | Description |
|---|---|
| `.on_agree(premise_name)` | Jump to named premise when user agrees. |
| `.on_disagree(premise_name)` | Jump to named premise when user disagrees. |
| `.branch(on_agree=…, on_disagree=…)` | Set both edges in one call. |
| `.choice(text, outcome, next_premise, label)` | Add a multiple-choice option. |

`PremiseBuilder.branch()`: `difficult_dialogs/builder.py:137`

#### Navigation

| Method | Description |
|---|---|
| `.done()` | Finish this premise and return to `ArgumentBuilder`. |
| `.build()` | Return the finished `Premise` (also registers it). |

`PremiseBuilder.done()`: `difficult_dialogs/builder.py:177`

---

## Branching example

```python
from difficult_dialogs.builder import ArgumentBuilder

arg = (
    ArgumentBuilder("branching_demo")
    .intro("Let's explore.")
    .conclusion("Thanks for the discussion.")
    .premise("first_claim")
        .statement("Regular exercise improves mood.")
        .branch(on_agree="evidence", on_disagree="explain_mechanism")
        .done()
    .premise("explain_mechanism")
        .statement("Exercise releases endorphins which reduce stress hormones.")
        .support("Dozens of randomised trials confirm this effect.")
        .done()
    .premise("evidence")
        .statement("Meta-analyses covering 1 million participants support this.")
        .source("https://doi.org/10.1016/j.amepre.2019.02.013")
        .done()
    .build()
)
```

When the user agrees with `first_claim`, the dialog jumps to `evidence`.
When they disagree, it goes to `explain_mechanism`.
`Argument.next_premise()`: `difficult_dialogs/arguments.py:113`

---

## Merging arguments

```python
merged = Argument.merge(
    arg_a, arg_b,
    name="combined",
    intro="A combined view.",
    on_conflict="keep_first",   # or "keep_last" or "error"
)
```

`Argument.merge()`: `difficult_dialogs/arguments.py:413`

---

## Saving and round-tripping

```python
# Save to disk
arg.save("output/my_argument")

# Load back
arg2 = Argument.from_directory("output/my_argument")

# JSON round-trip
data = arg.to_dict()
arg3 = Argument.from_dict(data)
```

`Argument.save()`: `difficult_dialogs/arguments.py:246`

---
[← Policies](POLICIES.md) · [Home](index.md) · [Choice solver →](choice-solver.md)
