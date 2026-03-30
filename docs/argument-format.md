# Argument File Format

An argument is a directory. The directory name becomes the argument's description (underscores replaced with spaces). All files are plain UTF-8 text.

## Directory structure

```
argument_name/
├── argument.intro          # Optional. Opening statement (all lines concatenated).
├── argument.conclusion     # Optional. Closing statement (all lines concatenated).
├── <name>.premise          # One file per premise. Each line = one Statement.
├── <name>.support          # Optional. Comebacks for when the user disagrees with <name>.
├── <name>.source           # Optional. Citation lines for <name>.
├── <name>.what             # Optional. Answer to "what?" for <name>.
├── <name>.why              # Optional. Answer to "why?" for <name>.
├── <name>.when             # Optional. Answer to "when?" for <name>.
├── <name>.where            # Optional. Answer to "where?" for <name>.
└── <name>.how              # Optional. Answer to "how?" for <name>.
```

`<name>` is the premise identifier — the same stem must be used across all related files (`.premise`, `.support`, `.source`, `.what`, …).

## File types

### `.premise`

Each non-empty line is loaded as a separate `Statement` — `Premise.add_statement()`. Statements are presented in random order; no statement is repeated.

```
climate change is caused by human activity
global temperature has increased 1.1°C since pre-industrial times
CO₂ concentration is at its highest in 800,000 years
```

### `.support`

Comeback statements for when the user disagrees with the premise. Each line is loaded via `Premise.add_support_statement()`. Spoken by `KnowItAllPolicy.on_negative_feedback()` until exhausted.

```
97% of climate scientists agree on human causation
the IPCC report summarises thousands of peer-reviewed studies
```

### `.source`

Citation strings (URLs or free text). Each line is loaded via `Premise.add_source()`. Shown as a last resort when support is exhausted.

```
https://www.ipcc.ch/report/ar6/wg1/
https://climate.nasa.gov/evidence/
```

### `.intro` / `.conclusion`

All lines are concatenated into a single `Statement`. Spoken at the start (`dialog.start()`) and end (`dialog.end()`) of the session.

### `.what`, `.why`, `.when`, `.where`, `.how`

Lines loaded as statements answering the corresponding W-question. `KnowItAllPolicy.on_user_input()` detects these keywords in the user's utterance and speaks the matching statements.

## Example — `argument_template/`

Included in `examples/argument_template/`:

```
argument_template/
├── argument.conclusion
├── argument.intro
├── X.premise
├── X.source
├── X.support
├── X.what
├── X.when
├── X.where
├── X.why
├── X.how
└── Y.premise
```

## Example — `i_think_therefore_i_am/`

Three premises, each with support and a source:

```
i_think_therefore_i_am/
├── argument.intro
├── argument.conclusion
├── computers_process_information.premise
├── computers_process_information.source
├── computers_process_information.support
├── i_am_a_computer.premise
├── i_am_a_computer.source
├── i_am_a_computer.support
├── processing_information_is_thinking.premise
├── processing_information_is_thinking.source
└── processing_information_is_thinking.support
```

## Loading in Python

```python
from difficult_dialogs.arguments import Argument

arg = Argument(path="path/to/argument_name")
# arg.description == "argument name"
# arg.premises     — list of Premise objects
# arg.intro        — intro Statement
# arg.conclusion   — conclusion Statement
```

`Argument.load()` — `arguments.py:338` — iterates the directory and dispatches each file by extension.
