# CLI Reference

The `did` (or `difficult-dialogs`) command is the primary entry point.

`main()`: `difficult_dialogs/cli.py:624`

---

## Commands

### `did debate`: run an interactive dialog

```
did debate <argument-dir> [options]
```

Loads an argument directory, creates the named policy, and starts an interactive
turn-by-turn session. Type `quit`, `exit`, or `q` to end early.

| Flag | Default | Description |
|---|---|---|
| `-p` / `--policy` | `knowitall` | Policy name (see table below). |
| `--save-transcript FILE` | none | Write conversation to a Markdown file when the session ends. |
| `--input-file FILE` | none | Read user turns from a file (one per line); useful for CI scripting. |
| `--watch` | off | Reload the argument directory on any file change without restarting the session. Requires `watchdog`; falls back to 1-second polling if absent. |

Policy names accepted by `--policy`: `knowitall`, `silent`, `socratic`, `debate`,
`exploratory`, `maieutic`, `skeptic`, `teacher`, `debater`, `minimalist`, `adaptive`.

`cmd_debate()`: `difficult_dialogs/cli.py:206`

---

### `did replay`: replay a saved transcript

```
did replay <transcript.json>
```

Prints a saved JSON transcript to stdout. Accepts both a raw list of
`{"role", "text"}` entries and a full state dict (as saved by
`--save-transcript` or `export_transcript_to_json`).

`cmd_replay()`: `difficult_dialogs/cli.py:376`

---

### `did diff`: compare two argument directories

```
did diff <argument-a-dir> <argument-b-dir>
```

Shows added/removed premises and changed statements between two argument
directories. Exits 0 if identical, 1 if differences exist.

`cmd_diff()`: `difficult_dialogs/cli.py:415`, `Argument.diff()`: `difficult_dialogs/arguments.py:366`

---

### `did validate`: quality report

```
did validate <path> [-v]
```

Scans `<path>` recursively for argument directories (looks for `intro.dialog`)
and prints a quality distribution. Exit code 1 if any argument fails.

Add `-v` / `--verbose` to list failure reasons for each failed argument.

`cmd_validate()`: `difficult_dialogs/cli.py:102`

---

### `did score`: single-argument quality score

```
did score <argument-dir>
```

Prints a one-line score and label (`EXCELLENT` / `GOOD` / `FAIR` / `POOR`).
Exit code 2 if the argument fails validation.

`cmd_score()`: `difficult_dialogs/cli.py:344`

---

### `did list`: browse a library

```
did list [path]
```

Walks `<path>` (default: `./examples/sample_arguments`) and lists all arguments
grouped by top-level subdirectory category.

`cmd_list()`: `difficult_dialogs/cli.py:496`

---

### `did solvers`: list installed choice solver plugins

```
did solvers
```

Lists all entry points registered under `opm.solver.multiple_choice`.
Exits 1 if none are installed and prints the install command for the default plugin.

`cmd_solvers()`: `difficult_dialogs/cli.py:474`

---

### `did new`: interactive argument wizard

```
did new [-o DIR]
```

Interactive prompt-driven wizard to create a new argument without an LLM.
Saves the result to `<DIR>/<slugified-name>/`.

`cmd_new()`: `difficult_dialogs/cli.py:568`

---

### `did generate`: LLM-generate an argument

```
did generate <topic> [options]
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

### `did export`: export to JSON or SQLite

```
did export <input-dir> <output-file> [options]
```

Format is inferred from the output file extension (`.json` or `.db`/`.sqlite`)
unless overridden with `-f`.

---

### `did graph`: render premise graph

```
did graph <argument-dir> [--format mermaid|dot|json] [--output FILE]
```

Renders the premise graph of an argument. Default format is **Mermaid**
(renders in GitHub, GitLab, Obsidian).

| Flag | Default | Description |
|------|---------|-------------|
| `--format` / `-f` | `mermaid` | Output format: `mermaid`, `dot` (Graphviz), or `json` |
| `--output` / `-o` | stdout | Write to file instead of stdout |

Examples:

```bash
did graph examples/sample_arguments/philosophy/free_will_exists
did graph my_arg/ --format dot | dot -Tsvg > graph.svg
did graph my_arg/ --format json --output graph.json
```

---

### `did stats`: structural statistics

```
did stats <path>
```

Prints structural metrics for a single argument or an entire library directory:
premise count, statement count, explicit edge count, max graph depth, branching
factor, choice count, and translation language count.

```bash
did stats examples/sample_arguments          # whole library
did stats examples/sample_arguments/science  # one category
```

---

### `did serve`: start the REST API server

```
did serve [--host HOST] [--port PORT]
```

Starts the FastAPI server from `examples/server.py`. Requires `fastapi` and `uvicorn`.
Default bind: `127.0.0.1:8080`.

---
[← Choice solver](choice-solver.md) · [Home](index.md) · [Graphs →](GRAPHS.md)
