# Argument File Format

An argument is a directory. The directory name becomes the argument's name
(underscores replaced with spaces). All files are plain UTF-8 text.

## Directory structure

```
argument_name/
├── intro.dialog              # Optional. Opening statement (all lines concatenated).
├── conclusion.conclusion     # Optional. Closing statement.
└── premise_name/             # One subdirectory per premise.
    ├── premise_name.premise   # Required. Each non-empty line = one Statement.
    ├── premise_name.support   # Optional. Comebacks when user disagrees.
    ├── premise_name.source    # Optional. Citation URLs.
    ├── premise_name.what      # Optional. Answer to "what?"
    ├── premise_name.why       # Optional. Answer to "why?"
    ├── premise_name.how       # Optional. Answer to "how?"
    ├── premise_name.when      # Optional. Answer to "when?"
    ├── premise_name.where     # Optional. Answer to "where?"
    ├── premise_name.who       # Optional. Answer to "who?" (who is affected / who are the authorities)
    ├── premise_name.choices   # Optional. Multiple-choice options (see below).
    ├── premise_name.on_agree  # Optional. Name of the premise to jump to on agreement.
    └── premise_name.on_disagree  # Optional. Name of the premise to jump to on disagreement.
```

The subdirectory name is the premise identifier. All files inside must share
that same stem (e.g. directory `moral_responsibility/` contains
`moral_responsibility.premise`, `moral_responsibility.support`, etc.).

A premise is only loaded if it has at least one `.premise` file with content
(`Premise.is_complete` — `premises.py`).

## File types

### `.premise`

Each non-empty line is loaded as a separate `Statement` via `Premise.add_statement()`.

```
climate change is caused by human activity
global temperature has increased 1.1°C since pre-industrial times
CO₂ concentration is at its highest in 800,000 years
```

### `.support`

Comeback statements for when the user disagrees. Each line loaded via
`Premise.add_support()`. Spoken by `KnowItAllPolicy` until exhausted.

```
97% of climate scientists agree on human causation
the IPCC report summarises thousands of peer-reviewed studies
```

### `.source`

Citation strings (URLs or free text). Each line loaded via `Premise.add_source()`.
Shown as a last resort when support is exhausted.

```
https://www.ipcc.ch/report/ar6/wg1/
https://climate.nasa.gov/evidence/
```

### `intro.dialog` / `conclusion.conclusion`

All lines concatenated into a single string. Spoken at the start and end of
the session via `BasePolicy.start()` and when `PolicyState.finished` is set.

### `.what`, `.why`, `.how`, `.when`, `.where`, `.who`

Lines loaded as contextual explanation fields (the "Five Ws + How").  Policies
that implement `_check_five_w()` detect these keywords in the user's utterance
and return a random matching line from the current premise.

### `.choices` — Multiple-choice options

One option per non-empty line. Used by `MultiChoicePolicy` to present a labelled
menu to the user instead of (or in addition to) yes/no.

Format: `LABEL) text [outcome_keyword] [-> next_premise_name]`

- `LABEL)` — single alphanumeric identifier (auto-assigned A, B, C… if omitted).
- `[outcome_keyword]` — optional `[agree]`, `[disagree]`, `[clarify]`, or `[skip]`.
  Default outcomes by position: A=agree, B=agree, C=disagree, D=clarify.
- `-> next_premise_name` — optional jump target; overrides `on_agree`/`on_disagree`
  for this specific choice.

```
A) I agree completely -> economic_angle
B) I agree with reservations
C) I disagree [disagree]
D) I need more context [clarify]
```

Loaded via `Premise.apply_file()` → `parse_choices_file()` — `choices.py`.
Stored in `Premise.choices: list[ChoiceOption]` — `premises.py`.

### `.on_agree` / `.on_disagree` — Branching edges

Single-line files containing the **name** of the premise to visit next when the
user agrees or disagrees with this premise. If absent, the argument falls back to
linear insertion-order traversal (backwards-compatible with existing arguments).

```
# human_causation.on_agree
economic_impacts

# human_causation.on_disagree
scientific_consensus_explained
```

Together, `.on_agree`, `.on_disagree`, and `.choices` turn a flat argument into a
**directed graph** (dialogue tree). The traversal is implemented in
`Argument.next_premise()` — `arguments.py`.

## Example — `i_think_therefore_i_am/`

```
i_think_therefore_i_am/
├── intro.dialog
├── conclusion.conclusion
├── computers_process_information/
│   ├── computers_process_information.premise
│   ├── computers_process_information.source
│   └── computers_process_information.support
├── i_am_a_computer/
│   ├── i_am_a_computer.premise
│   ├── i_am_a_computer.source
│   └── i_am_a_computer.support
└── thinking_is_information_processing/
    ├── thinking_is_information_processing.premise
    ├── thinking_is_information_processing.source
    └── thinking_is_information_processing.support
```

## Loading in Python

```python
from difficult_dialogs.arguments import Argument

# Idiomatic — classmethod
arg = Argument.from_directory("path/to/argument_name")

# Equivalent instance method
arg = Argument().load("path/to/argument_name")

# arg.name         — "argument name" (underscores → spaces)
# arg.intro        — opening string
# arg.conclusion   — closing string
# arg.premises     — list[Premise]
```

`Argument.load()` — `arguments.py:112` — iterates subdirectories and calls
`Premise.apply_file()` — `premises.py:127` — for each file, dispatching by
extension.

## Saving

```python
arg.save("path/to/output_dir")   # writes full directory structure
```

`Argument.save()` — `arguments.py:198`.

## Exporting

```python
from difficult_dialogs.export import export_to_json, export_to_markdown, export_to_sqlite

export_to_json(arg, "argument.json")
md = export_to_markdown(arg, "argument.md")   # human-readable review doc
db = export_to_sqlite("arguments/", "library.db")
```
