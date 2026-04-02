# Status: Visualization, Graph Export & Library Improvements

## Checklist

- [x] Extract graph data model — `GraphData`, `GraphNode`, `GraphEdge` in `difficult_dialogs/graph.py`; add `Argument.to_graph()` method
- [x] Add Mermaid, DOT, and JSON renderers — `difficult_dialogs/export/graph.py` with `to_mermaid()`, `to_dot()`, `to_graph_json()`
- [ ] Add `did graph` CLI command — `cmd_graph()` with `--format mermaid|dot|json` and `--output FILE`
- [ ] Add `did stats` CLI command — `cmd_stats()` showing premise/statement/edge counts, depth, branching factor
- [ ] Add CSV export — `difficult_dialogs/export/csv.py` with `export_to_csv()` and `export_library_to_csv()`; wire into `did export --format csv`
- [ ] Add timestamp to TranscriptEntry — `timestamp: float | None` field; populate in `start()`/`respond()`/`run_sync()`; update serialization and transcript export
- [ ] Add CooperativePolicy — new policy class; acknowledges disagreement, seeks common ground, moves forward; register in POLICY_REGISTRY
- [ ] Export new symbols from `__init__.py` — graph types, CSV export, CooperativePolicy added to `__all__`
- [ ] Tests for all new features — `test_graph.py`, `test_csv_export.py`, `test_cooperative_policy.py`, timestamp tests, CLI graph/stats tests
- [ ] Update docs and FAQ — `did graph`/`did stats` in cli.md; graph export in argument-format.md; FAQ entries for visualization and CSV

## Blockers

<!-- populated by /implement-task if something is stuck -->
