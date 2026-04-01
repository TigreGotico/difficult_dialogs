# CLI Reference

The `dd` (or `difficult-dialogs`) command is the primary entry point.

`main()` — `difficult_dialogs/cli.py:624`

---

## Commands

### `dd debate` — run an interactive dialog

```
dd debate <argument-dir> [options]
```

Loads an argument directory, creates the named policy, and starts an interactive
turn-by-turn session. Type `quit`, `exit`, or `q` to end early.

| Flag | Default | Description |
|---|---|---|
| `-p` / `--policy` | `knowitall` | Policy name (see table below). |
| `--save-transcript FILE` | — | Write conversation to a Markdown file when the session ends. |
| `--input-file FILE` | — | Read user turns from a file (one per line); useful for CI scripting. |
| `--watch` | off | Reload the argument directory on any file change without restarting the session. Requires `watchdog`; falls back to 1-second polling if absent. |

Policy names accepted by `--policy`: `knowitall`, `silent`, `socratic`, `debate`,
`exploratory`, `maieutic`, `skeptic`, `teacher`, `debater`, `minimalist`, `adaptive`.

`cmd_debate()` — `difficult_dialogs/cli.py:206`

---

### `dd replay` — replay a saved transcript

```
dd replay <transcript.json>
```

Prints a saved JSON transcript to stdout. Accepts both a raw list of
`{"role", "text"}` entries and a full state dict (as saved by
`--save-transcript` or `export_transcript_to_json`).

`cmd_replay()` — `difficult_dialogs/cli.py:376`

---

### `dd diff` — compare two argument directories

```
dd diff <argument-a-dir> <argument-b-dir>
```

Shows added/removed premises and changed statements between two argument
directories. Exits 0 if identical, 1 if differences exist.

`cmd_diff()` — `difficult_dialogs/cli.py:415`, `Argument.diff()` — `difficult_dialogs/arguments.py:366`

---

### `dd validate` — quality report

```
dd validate <path> [-v]
```

Scans `<path>` recursively for argument directories (looks for `intro.dialog`)
and prints a quality distribution. Exit code 1 if any argument fails.

Add `-v` / `--verbose` to list failure reasons for each failed argument.

`cmd_validate()` — `difficult_dialogs/cli.py:102`

---

### `dd score` — single-argument quality score

```
dd score <argument-dir>
```

Prints a one-line score and label (`EXCELLENT` / `GOOD` / `FAIR` / `POOR`).
Exit code 2 if the argument fails validation.

`cmd_score()` — `difficult_dialogs/cli.py:344`

---

### `dd list` — browse a library

```
dd list [path]
```

Walks `<path>` (default: `./examples/sample_arguments`) and lists all arguments
grouped by top-level subdirectory category.

`cmd_list()` — `difficult_dialogs/cli.py:496`

---

### `dd solvers` — list installed choice solver plugins

```
dd solvers
```

Lists all entry points registered under `opm.solver.multiple_choice`.
Exits 1 if none are installed and prints the install command for the default plugin.

`cmd_solvers()` — `difficult_dialogs/cli.py:474`

---

### `dd new` — interactive argument wizard

```
dd new [-o DIR]
```

Interactive prompt-driven wizard to create a new argument without an LLM.
Saves the result to `<DIR>/<slugified-name>/`.

`cmd_new()` — `difficult_dialogs/cli.py:568`

---

### `dd generate` — LLM-generate an argument

```
dd generate <topic> [options]
```

Requires an OpenAI-compatible LLM server. Calls `ArgumentGenerator.generate()`
and saves the result to `--output`.

| Flag | Default | Description |
|---|---|---|
| `-s` / `--server` | `http://localhost:8000` | LLM server URL. |
| `-m` / `--model` | `default` | Model name. |
| `-o` / `--output` | `./generated_arguments` | Output directory. |
| `--stance` | `pro` | `pro` or `con`. |
| `-d` / `--depth` | `1` | Complexity (1 = simple, 3 = complex). |
| `--no-sources` | off | Skip source URL generation. |
| `--counter` | off | Include counterarguments in support. |
| `-f` / `--force` | off | Overwrite existing arguments. |
| `-v` / `--validate` | off | Print quality score after generation. |
| `-t` / `--timeout` | `120.0` | Per-generation timeout (seconds). |

---

### `dd export` — export to JSON or SQLite

```
dd export <input-dir> <output-file> [options]
```

Format is inferred from the output file extension (`.json` or `.db`/`.sqlite`)
unless overridden with `-f`.

---

### `dd serve` — start the REST API server

```
dd serve [--host HOST] [--port PORT]
```

Starts the FastAPI server from `examples/server.py`. Requires `fastapi` and `uvicorn`.
Default bind: `127.0.0.1:8080`.
