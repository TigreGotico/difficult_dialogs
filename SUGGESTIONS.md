# Suggestions — difficult_dialogs

Agent proposals for future enhancements.  Not prioritised; discuss before implementing.

---

## S-01 — Fix A-01: route `cmd_debate` through `policy.respond()`

`cli.py:251` calls `handle_input` directly.  One-line fix: replace with
`policy.respond(user_input)`.  Will make `--save-transcript` capture user
turns correctly.

## S-02 — Add `timeout` to `WebhookPolicy`

Constructor: `WebhookPolicy(url, fallback, timeout=10.0)`.  Pass to
`requests.post(timeout=self.timeout)`.  Prevents indefinite hang on dead
webhooks.  Low-risk change.

## S-03 — `did replay FILE`

New CLI subcommand that reads a saved transcript JSON and replays it
non-interactively, printing each turn.  Useful for regression testing without
a live session.

## S-04 — `ArgumentLibrary.watch(callback)`

Use `watchdog` (optional dep) to inotify-watch the library root and call
`callback(event)` on `.dialog`/`.premise` file changes.  Enables hot-reload in
long-running servers.

## S-05 — BM25 search in `ArgumentLibrary`

Replace token-overlap scoring with BM25 (pure-Python `rank_bm25` package,
~2 KB).  Improves ranking on short queries.  Would require adding `rank_bm25`
as an optional dep.

## S-06 — WebSocket endpoint in `examples/server.py`

Add `GET /sessions/{id}/ws` — a WebSocket endpoint that streams bot responses
character-by-character for low-latency UX.  Useful for OVOS voice integration.

## S-07 — `Premise` i18n field

Add `translations: dict[str, dict[str, str]]` to `Premise` dataclass so
statements can be stored in multiple languages.  Needed for multi-language
support (see ROADMAP v0.8).

## S-09 — Auto-discover OPM choice solvers via `opm.agents.reranker`

`choices.py` defines `ChoiceSolverProtocol` but loads no plugins automatically.
Mirror `yesno.py`'s pattern exactly: add `_load_solver()` that tries the
`opm.agents.reranker` (or `opm.agents.multiple_choice`) entry-point group, falls
back to `_DefaultChoiceSolver` if nothing is installed.  OPM already has a
compatible `multiple_choice`/reranker plugin.  Would make `MultiChoicePolicy`
leverage semantic matching out-of-the-box with no user config.

## S-10 — `ArgumentBuilder.branch()` shorthand for two-way branches

`builder.on_agree("p_yes").on_disagree("p_no")` is verbose. A single
`.branch(on_agree="p_yes", on_disagree="p_no")` method would be cleaner.

## S-11 — Cycle detection in `ArgumentValidator`

If `on_agree`/`on_disagree` create a cycle (premise A → B → A) the dialog
loops forever. `ArgumentValidator` should detect cycles via DFS and report
them as `CRITICAL` severity issues.

## S-08 — `did score` shorthand

`did score ARG_DIR` prints a single line: `score: 87%  [GOOD]`.  Useful in CI
without parsing full `did validate` output.
