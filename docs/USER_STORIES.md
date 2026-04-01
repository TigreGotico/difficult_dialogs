# User Stories — difficult_dialogs

Developer-perspective stories for the `difficult_dialogs` library.  Each story
identifies the downstream use case, the relevant API, and any gap that was
found and addressed.

---

## US-01 — Embed a structured debate in a chatbot

> As a chatbot developer, I want to load an argument file and feed user
> messages through a policy so my bot can hold a structured persuasive dialog
> without calling an LLM.

**API path:** `Argument.from_directory(path)` → `get_policy(name, arg)` →
`policy.start()` / `policy.respond(user_input)`

**Async variant:** `async for response in policy.stream(input_queue):` —
`BasePolicy.stream` (`policy.py`) accepts an `AsyncGenerator` of user strings
and yields bot responses.

```python
import asyncio
from difficult_dialogs import Argument, get_policy

arg = Argument.from_directory("examples/i_think_therefore_i_am")
policy = get_policy("socratic", arg)
print(policy.start())

async def run(input_stream):
    async for response in policy.stream(input_stream):
        print("BOT:", response)
```

**Gap addressed:** `stream()` was undocumented; added to USER_GUIDE.md.

---

## US-02 — Build an argument programmatically at runtime

> As an app developer, I want to construct arguments in code (not from files)
> so I can generate them from a database or API response.

**API path:** `ArgumentBuilder` / `PremiseBuilder` (`builder.py`)

```python
from difficult_dialogs import ArgumentBuilder

arg = (
    ArgumentBuilder("Free will exists")
    .intro("Let's explore free will.")
    .conclusion("Free will is real.")
    .premise("Deliberation is real")
        .statement("Humans deliberate before acting.")
        .why("Deliberation implies choice.")
        .source("https://plato.stanford.edu/entries/freewill/")
        .done()
    .build()
)
```

**Gap addressed:** `ArgumentBuilder`, `PremiseBuilder` now exported from
`difficult_dialogs.__init__`.

---

## US-03 — Persist and resume a debate session

> As a web developer, I want to save a session's state to disk and restore it
> in the next request so my stateless API can host multi-turn debates.

**API path:** `policy.save_state(path)` / `policy.load_state(path)` —
`BasePolicy` (`policy.py`)

```python
# Request 1 — save
policy.start()
policy.respond("I disagree")
policy.save_state("/tmp/session_42.json")

# Request 2 — restore
policy2 = get_policy("knowitall", arg)
policy2.load_state("/tmp/session_42.json")
reply = policy2.respond("Tell me more")
```

For key-value stores: `policy.state.to_dict()` / `policy.restore_state(d)`.

**Gap addressed:** `save_state` / `load_state` added to `BasePolicy`.

---

## US-04 — Validate an argument before publishing

> As a content team member, I want to validate an argument's quality score
> before it goes live so I can catch missing sources or weak premises.

**API path:** `ArgumentValidator` → `ValidationResult` (`validators.py`)

```python
from difficult_dialogs import ArgumentValidator, ValidationSeverity

validator = ArgumentValidator()
result = validator.validate(arg)
print(f"Score: {result.score:.0%}  Passed: {result.passed}")
for issue in result.issues:
    if issue.severity >= ValidationSeverity.WARNING:
        print(f"  [{issue.severity.name}] {issue.message}")
```

CLI equivalent: `did validate examples/i_think_therefore_i_am`

**Gap addressed:** `ArgumentValidator`, `ValidationResult`, `ValidationSeverity`,
`ValidationIssue` now exported from package root.

---

## US-05 — Search a library of arguments by topic

> As a debate app developer, I want to search my argument library by keyword
> so I can surface the most relevant argument for a user's topic.

**API path:** `ArgumentLibrary` / `SearchResult` (`library.py`)

```python
from difficult_dialogs import ArgumentLibrary

lib = ArgumentLibrary("examples/sample_arguments").scan()
results = lib.search("climate change", limit=5)
for r in results:
    print(r.argument.name, r.score, r.matched_fields)
```

**Gap addressed:** `ArgumentLibrary`, `SearchResult` now exported from root.

---

## US-06 — Switch policies mid-conversation

> As a tutoring app developer, I want to switch from a teacher policy to a
> Socratic one if the student seems confident.

**API path:** `AdaptivePolicy.set_policy(new_instance)` (`policy.py`)

```python
from difficult_dialogs import AdaptivePolicy, SocraticPolicy

policy = AdaptivePolicy(arg)
policy.start()
# … several turns later …
policy.set_policy(SocraticPolicy(arg))  # transfer state, activate immediately
```

Automatic switching: `AdaptivePolicy` also auto-switches after
`switch_threshold` consecutive disagreements.

**Gap addressed:** `set_policy` added to `AdaptivePolicy`.

---

## US-07 — Export a session transcript for audit

> As a compliance engineer, I want to export session transcripts in JSON and
> Markdown so I can store structured records of AI-assisted debates.

**API path:** `export_transcript_to_markdown(policy)` /
`export_transcript_to_json(policy)` (`export/transcript.py`)

```python
from difficult_dialogs import export_transcript_to_markdown, export_transcript_to_json

md = export_transcript_to_markdown(policy, title="Session 2024-01-01")
data = export_transcript_to_json(policy)
```

CLI: `did debate ARG_DIR --save-transcript session.md`

**Gap addressed:** Both functions now exported from package root.

---

## US-08 — Generate an argument from a topic with a local LLM

> As a developer using Ollama locally, I want to generate a structured
> argument from a topic string to bootstrap content.

**API path:** `ArgumentGenerator` (`llm/generator.py`)

```python
from difficult_dialogs import ArgumentGenerator

gen = ArgumentGenerator(base_url="http://localhost:11434/v1", model="llama3")
arg = gen.generate("Renewable energy can replace fossil fuels", stance="for")
arg.save("generated/renewable_energy")
```

CLI: `did generate "Renewable energy" --server http://localhost:11434/v1`

**Gap addressed:** `ArgumentGenerator`, `LLMEnhancer`, `LLMClient` now
exported from package root.

---

## US-09 — Run a debate non-interactively (scripted / CI)

> As a CI pipeline developer, I want to pipe pre-written turns into
> `did debate` and capture the output so I can regression-test argument files.

**CLI:** `did debate ARG_DIR --input-file turns.txt`

`turns.txt` example:
```
yes
no
I'm not sure about that
yes
```

**Gap addressed:** `--input-file FILE` added to `debate` subcommand (`cli.py`).

---

## US-10 — Chain multiple arguments into a curriculum

> As an e-learning developer, I want to sequence three arguments so my course
> flows naturally.

**API path:** `MultiArgumentPolicy` (`policy.py`)

```python
from difficult_dialogs import MultiArgumentPolicy, Argument

policy = MultiArgumentPolicy([
    (Argument.from_directory("intro"), "silent"),
    (Argument.from_directory("core"), "teacher"),
    (Argument.from_directory("advanced"), "socratic"),
])
policy.start()
```

**Gap addressed:** `MultiArgumentPolicy` now exported from package root;
documented in USER_GUIDE.md.

---

## US-11 — Use a custom yes/no solver for another language

> As a Spanish-language app developer, I want to plug in a Spanish yes/no
> solver so the dialog policies detect agreement correctly.

**API path:** `set_solver(solver)` / `configure(plugin_name)` (`yesno.py`)

```python
from difficult_dialogs import set_solver

class SpanishSolver:
    def match_yes_or_no(self, text, lang="es-ES"):
        return True if "sí" in text.lower() else (False if "no" in text.lower() else None)

set_solver(SpanishSolver())
```

**Gap addressed:** `set_solver`, `configure`, `parse_yes_no` already exported;
confirmed and documented here.

---

## US-12 — Add auth to the REST server demo

> As a backend developer, I want to add API-key auth to `examples/server.py`
> before deploying publicly.

**Location:** `examples/server.py` — demo app, not part of the library.

```python
# Add to examples/server.py to enable API-key auth:
from fastapi import Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

API_KEY = "changeme"
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_token(key: str = Security(api_key_header)):
    if key != API_KEY:
        raise HTTPException(status_code=403)

# Then add `dependencies=[Depends(verify_token)]` to app routes that need auth.
```

**Gap addressed:** Comment block added to `examples/server.py`.
