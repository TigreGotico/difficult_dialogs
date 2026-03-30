# difficult_dialogs

Structured argumentation framework for guided multi-turn dialogs. Premises are declared in plain text files; a policy engine drives the conversation by presenting statements, offering support when a user disagrees, and citing sources.

Zero external dependencies. Pure Python 3.10+.

## Core concepts

| Class | Module | Role |
|---|---|---|
| `Statement` | `statements.py` | A sentence with a truth value (`True`/`False`). |
| `Premise` | `premises.py` | A named claim backed by a set of `Statement` objects. True iff all statements are true. |
| `Argument` | `arguments.py` | A collection of `Premise` objects with an intro and a conclusion. Loaded from a directory. |
| `BasePolicy` | `policy.py` | Drives a dialog loop: presents statements, collects agree/disagree feedback, advances premises. |
| `KnowItAllPolicy` | `policy.py` | Extends `BasePolicy`: replies with support statements on disagreement; falls back to sources or concedes. |

## File format

Arguments are directories. See [argument-format.md](argument-format.md) for full reference.

```
my_argument/
├── argument.intro        # Opening statement (optional)
├── argument.conclusion   # Closing statement (optional)
├── premise_1.premise     # Claim — each line is a Statement
├── premise_1.support     # Comebacks if user disagrees
├── premise_1.source      # Citations
├── premise_2.premise
└── ...
```

## Quick start

```python
from difficult_dialogs.arguments import Argument
from difficult_dialogs.policy import KnowItAllPolicy

arg = Argument(path="path/to/my_argument")
dialog = KnowItAllPolicy(arg)

dialog.start()          # speaks intro
while not dialog.finished:
    output = dialog._run_once()
    if output:
        print("BOT:", output)
        user_input = input("USER: ")
        if "y" in user_input.lower():
            dialog.agree()
        else:
            dialog.disagree()
dialog.end()            # speaks conclusion
```

### Async (threaded) loop

```python
dialog.run_async()

while True:
    if dialog.output:
        print("BOT:", dialog.output)
        if dialog.finished:
            break
        dialog.submit_input(input("USER: "))
dialog.stop()
```

## LLM grounding use case

The file-based format is naturally injectable into LLM prompts. Load the argument, call `arg.as_json()`, and pass the resulting structure as context to the LLM. The policy layer then acts as a constraint: the LLM generates natural language, the framework controls what claims are made and in what order.

## Navigation

- [argument-format.md](argument-format.md) — full file format reference
