# FAQ — difficult_dialogs

## General

**Q: What is difficult_dialogs?**
A: A structured, file-based argumentation framework. Arguments are stored as plain-text directories; pluggable policies drive turn-by-turn dialogs.

**Q: Does it require an LLM or internet connection?**
A: No. The core library (`policy.py`, `premises.py`, `arguments.py`) has zero runtime dependencies. LLM features in `difficult_dialogs/llm/` are opt-in.

**Q: What Python versions are supported?**
A: Python 3.10+.

## Arguments

**Q: How do I create an argument programmatically?**
A: Use `ArgumentBuilder` — `difficult_dialogs/builder.py`:
```python
from difficult_dialogs.builder import ArgumentBuilder
arg = (
    ArgumentBuilder("topic")
    .intro("Opening statement.")
    .premise("claim").statement("Evidence.").why("Reason.").done()
    .build()
)
```

**Q: What is the Five Ws + How system?**
A: Each premise supports six contextual fields: `what`, `why`, `how`, `when`, `where`, `who`. Policies that implement `_check_five_w()` detect these keywords in user input and return the matching answer from the current premise. Defined in `premises.py:Premise`.

**Q: What happens if a `.premise` file is empty?**
A: The premise is skipped — `Premise.is_complete` (`premises.py:56`) returns `False` and `Argument.load()` (`arguments.py`) will not add it.

## Policies

**Q: Which policy should I use?**
A: `KnowItAllPolicy` is the default for interactive persuasion. `SilentPolicy` for one-way presentation. `AdaptivePolicy` when you want the bot to soften its approach after repeated disagreements.

**Q: How do I chain multiple arguments into one session?**
A: Use `MultiArgumentPolicy` from `policy.py`:
```python
policy = MultiArgumentPolicy([(arg1, "knowitall"), (arg2, "silent")])
```

**Q: Can I save and restore a session?**
A: Yes. `PolicyState.to_dict()` / `PolicyState.from_dict()` (`policy.py:49-88`) produce JSON-safe dicts. Restore with `policy.restore_state(state_dict)`.

**Q: How do I run the dialog in a loop?**
A: Use `policy.run_sync()` — a generator that yields bot responses and accepts user input via `.send()`:
```python
gen = policy.run_sync()
response = next(gen)
while response:
    response = gen.send(input("USER: "))
```

## Export & Library

**Q: How do I export an argument?**
A: Use `difficult_dialogs.export`:
```python
from difficult_dialogs.export import export_to_json, export_to_markdown
export_to_json(arg, "argument.json")
md = export_to_markdown(arg)
```

**Q: How do I search across many arguments?**
A: Use `ArgumentLibrary` (`library.py`):
```python
from difficult_dialogs.library import ArgumentLibrary
lib = ArgumentLibrary("arguments/").scan()
results = lib.search("climate change")
```

## Server / CLI

**Q: How do I run the REST API?**
A: `dd serve --host 0.0.0.0 --port 8080` — starts a FastAPI server defined in `server.py`.

**Q: How do I list available CLI commands?**
A: `dd --help`.
