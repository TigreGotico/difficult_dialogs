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
A: Yes — two levels of convenience. Quick file persistence: `policy.save_state("session.json")` / `policy.load_state("session.json")` (`BasePolicy.save_state` — `policy.py`). For key-value stores (Redis, DB): `PolicyState.to_dict()` / `PolicyState.from_dict()` produce JSON-safe dicts; restore with `policy.restore_state(state_dict)`.

**Q: Can I switch the active policy mid-conversation?**
A: Yes. `AdaptivePolicy.set_policy(new_policy_instance)` transfers all state and activates the new policy immediately (`policy.py:AdaptivePolicy.set_policy`).

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
A: `did serve --host 0.0.0.0 --port 8080` — dynamically loads `examples/server.py` (FastAPI demo app, not part of the library).

**Q: How do I list available CLI commands?**
A: `did --help`.

**Q: Can I run a debate non-interactively (from a script or CI)?**
A: Yes. Use `did debate ARG_DIR --input-file turns.txt` where `turns.txt` has one user turn per line. Output goes to stdout.

**Q: How do I validate argument quality?**
A: `ArgumentValidator` (importable from `difficult_dialogs`) scores arguments and returns a `ValidationResult` with per-issue severity. Also available via CLI: `did validate ARG_DIR`.

**Q: How do I use a custom yes/no solver (e.g. for non-English)?**
A: Call `set_solver(my_solver)` or `configure(plugin_name)` from `difficult_dialogs` at startup to replace the default OPM plugin.
