# FAQ — difficult_dialogs

## What is difficult_dialogs?

A Python library for building structured, interactive debates using plain-text file-based argument definitions and pluggable policy engines.

---

## Data model

**Q: What is the hierarchy?**
`Statement` → `Premise` → `Argument`. Statements hold a claim and an `agreed` flag. A Premise is a group of statements plus Five-Ws metadata. An Argument is an ordered collection of premises with an intro and conclusion.

**Q: What are the Five-Ws fields?**
Each `Premise` carries `what`, `why`, `how`, `when`, `where` lists. These answer user questions during a debate without needing an LLM at runtime. Defined in `difficult_dialogs/premises.py`.

**Q: How is an argument stored on disk?**
One directory per argument. `intro.dialog` and `conclusion.conclusion` at the root. One subdirectory per premise, each containing `<name>.premise`, `<name>.support`, `<name>.source`, and any of the Five-Ws extension files (`.what`, `.why`, `.how`, `.when`, `.where`). See `Argument.load()` — `difficult_dialogs/arguments.py:108`.

---

## Policies

**Q: How many policies are there?**
10 total: `KnowItAllPolicy`, `SilentPolicy`, `SocraticPolicy`, `DebatePolicy`, `ExploratoryPolicy` (in `policy.py`) and `MaieuticPolicy`, `SkepticPolicy`, `TeacherPolicy`, `DebaterPolicy`, `MinimalistPolicy` (in `policies.py`).

**Q: What is the difference between `SocraticPolicy` and `MaieuticPolicy`?**
`SocraticPolicy` (policy.py) asks generic probing questions. `MaieuticPolicy` (policies.py) injects the argument's topic into question templates — more contextually grounded guided discovery.

**Q: How do I select a policy by name?**
`get_policy("teacher", argument)` — imported from `difficult_dialogs.policies`. Raises `InvalidPolicyError` for unknown names. See `policies.py:435`.

**Q: How does Five-Ws dispatch work at runtime?**
`BasePolicy._check_five_w(user_input)` — `policy.py:140`. Checks the lowercased input for `what/why/how/when/where` keywords against the current premise's lists. Returns a random answer if found, else `None`.

**Q: Can I run a policy as a generator (no UI loop)?**
`policy.run_sync()` is a Python generator using the coroutine-send protocol. `policy.stream(queue)` is an asyncio async generator that reads from an `asyncio.Queue`. Both delegate to `handle_input()`. Defined in `policy.py:195` and `policy.py:220`.

---

## CLI

**Q: What commands are available?**
`generate`, `validate`, `export`, `debate`, `list`. Run `python -m difficult_dialogs.cli --help`.

**Q: How do I run an interactive debate?**
`python -m difficult_dialogs.cli debate path/to/argument/ --policy teacher`

---

## LLM generation

**Q: Does difficult_dialogs require an LLM?**
No. LLM is optional — only needed for `generate` CLI command and `LLMEnhancer`. All debate logic runs offline.

**Q: What LLM servers are supported?**
Any OpenAI-compatible API (Llama.cpp, Ollama, LM Studio, OpenAI itself). Configured via `--server` flag or `ArgumentGenerator(base_url=...)`.

**Q: Why are so many API calls made per argument?**
By design — one call per concern (metadata, per-premise statements, Five-Ws, support, sources). This keeps each prompt small and within reach of smaller models.

---

## Export

**Q: What export formats are supported?**
JSON bundle (`export_to_json`, `export_library_to_json`) and SQLite (`LibraryDatabase`, `export_to_sqlite`). Defined in `difficult_dialogs/export.py`.

**Q: Does SQLite export preserve Five-Ws fields?**
Yes — `support` and `five_ws` tables were added. `get_argument()` restores all fields. See `export.py:200` (schema) and `export.py:400` (restore).
