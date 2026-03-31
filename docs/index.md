# difficult_dialogs

Structured argumentation framework for guided multi-turn dialogs. Premises are
declared in plain text files; a pluggable policy engine drives the conversation
by presenting statements, offering support when a user disagrees, and citing sources.

Zero external runtime dependencies. Pure Python 3.10+.

## Core concepts

| Class | Module | Role |
|---|---|---|
| `Statement` | `statements.py` | A sentence with an agreed/disagreed truth value. |
| `Premise` | `premises.py` | A named claim backed by `Statement` objects. True iff all statements agreed. |
| `Argument` | `arguments.py` | A collection of `Premise` objects with intro and conclusion. Loaded from a directory. |
| `BasePolicy` | `policy.py` | Abstract base for dialog loops: presents statements, collects feedback, advances premises. |
| `PolicyState` | `policy.py` | Serializable session state (spoken premises/statements, challenge count, finished flag). |

10 concrete policies ship in `policy.py`: `KnowItAllPolicy`, `SilentPolicy`, `SocraticPolicy`,
`DebatePolicy`, `ExploratoryPolicy`, `MaieuticPolicy`, `SkepticPolicy`, `TeacherPolicy`,
`DebaterPolicy`, `MinimalistPolicy`.

## File format

Arguments are directories with one subdirectory per premise. See [argument-format.md](argument-format.md).

```
my_argument/
├── intro.dialog              # Opening statement
├── conclusion.conclusion     # Closing statement
└── premise_name/
    ├── premise_name.premise  # Core claims (one per line)
    ├── premise_name.support  # Fallback comebacks (optional)
    ├── premise_name.source   # Citation URLs (optional)
    ├── premise_name.what     # Five-Ws explanations (optional)
    ├── premise_name.why
    ├── premise_name.how
    ├── premise_name.when
    └── premise_name.where
```

## Quick start

```python
from difficult_dialogs.arguments import Argument
from difficult_dialogs.policy import KnowItAllPolicy

arg = Argument.from_directory("path/to/my_argument")
policy = KnowItAllPolicy(arg)

print(policy.start())

gen = policy.run_sync()
response = next(gen)
while response:
    print("BOT:", response)
    try:
        response = gen.send(input("USER: "))
    except StopIteration:
        break
```

## Export

```python
from difficult_dialogs.export import export_to_json, export_to_markdown

export_to_json(arg, "argument.json")
md = export_to_markdown(arg)           # returns string; optionally writes file
diff = arg.diff(updated_arg)           # {meta, added_premises, removed_premises, modified_premises}
```

## Navigation

- [argument-format.md](argument-format.md) — full file format reference
- [USER_GUIDE.md](USER_GUIDE.md) — end-user manual
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) — API reference
- [POLICIES.md](POLICIES.md) — policy reference
