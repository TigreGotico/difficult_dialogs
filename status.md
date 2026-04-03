# Status: Visualization, Graph Export & Library Improvements

## Checklist

- [x] Extract graph data model — `GraphData`, `GraphNode`, `GraphEdge` in `difficult_dialogs/graph.py`; add `Argument.to_graph()` method
- [x] Add Mermaid, DOT, and JSON renderers — `difficult_dialogs/export/graph.py` with `to_mermaid()`, `to_dot()`, `to_graph_json()`
- [x] Add `did graph` CLI command — `cmd_graph()` with `--format mermaid|dot|json` and `--output FILE`
- [x] Add `did stats` CLI command — `cmd_stats()` showing premise/statement/edge counts, depth, branching factor
- [x] Add CSV export — `difficult_dialogs/export/csv.py` with `export_to_csv()` and `export_library_to_csv()`; wired into `did export --format csv`
- [x] Add timestamp to TranscriptEntry — `timestamp: float | None` field; populated in start/respond/run_sync/end; serialization and export updated
- [x] Add CooperativePolicy — acknowledges disagreement, advances instead of looping; registered in POLICY_REGISTRY as "cooperative"
- [x] Export new symbols from `__init__.py` — GraphData/Node/Edge, renderers, export_to_csv, CooperativePolicy in `__all__`
- [x] Tests for all new features — test_graph.py (32), test_csv_export.py (9), test_cooperative_policy.py (10), test_transcript_timestamp.py (9), CLI graph/stats/csv (10)
- [ ] Update docs and FAQ — `did graph`/`did stats` in cli.md; graph export in argument-format.md; FAQ entries for visualization and CSV

## Blockers

<!-- populated by /implement-task if something is stuck -->
