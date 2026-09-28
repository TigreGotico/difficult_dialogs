# Audit: Visualization, Graph Export & Library Improvements

## Summary

All 10 checklist items shipped. The implementation adds a graph data model (`graph.py`), three renderers (Mermaid/DOT/JSON), two new CLI commands (`did graph`, `did stats`), CSV export, transcript timestamps, CooperativePolicy, and a 31-argument gallery in `docs/GRAPHS.md`. 70 new tests across 6 files; 1059 total tests passing. Code quality is high — clean separation of concerns, consistent patterns, good test coverage. No critical issues found.

## Acceptance Criteria

| Criterion | Status | Evidence |
| :--- | :--- | :--- |
| `to_graph()` on linear 3-premise → 3 nodes, 2 fallback edges | Pass | `test/test_graph.py:TestBuildGraphLinear` (5 tests); verified: `nodes=3, edges=2, all_fallback=True` |
| `to_graph()` on branching → "agree"/"disagree" edges, `is_linear_fallback=False` | Pass | `test/test_graph.py:TestBuildGraphBranching` (4 tests) |
| `to_graph()` with `entry_point="p2"` → `graph.entry_point == "p2"` | Pass | `test/test_graph.py:TestBuildGraphEntryPoint::test_entry_point_set` |
| `to_mermaid()` contains `graph TD`, renders in Mermaid editor | Pass | `test/test_graph.py:TestMermaidRenderer::test_starts_with_graph_td`; `export/graph.py:47` |
| `to_dot()` contains `digraph {`, valid Graphviz | Pass | `test/test_graph.py:TestDOTRenderer::test_starts_with_digraph`; `export/graph.py:91` |
| `to_graph_json()` passes `json.dumps()`, has "nodes"/"edges" | Pass | `test/test_graph.py:TestJSONRenderer::test_json_serializable` + `test_has_nodes_and_edges` |
| `did graph` prints Mermaid, exits 0 | Pass | `test/test_cli.py:TestCmdGraph::test_graph_mermaid_default`; CLI verified manually |
| `did graph --format dot` prints DOT | Pass | `test/test_cli.py:TestCmdGraph::test_graph_dot_format` |
| `did graph /nonexistent` exits 1 | Pass | `test/test_cli.py:TestCmdGraph::test_graph_nonexistent_path` |
| `did stats` prints counts for library | Pass | `test/test_cli.py:TestCmdStats::test_stats_sample_arguments`; manual: `Arguments: 31, Premises: 65, Statements: 342` |
| `export_to_csv()` creates readable CSV with correct headers | Pass | `test/test_csv_export.py:TestExportToCSV` (6 tests) |
| `export_library_to_csv()` has `category` column | Pass | `test/test_csv_export.py:TestExportLibraryToCSV::test_has_category` |
| `did export --format csv` creates CSV | Pass | `test/test_cli.py:TestCmdExportCSV::test_export_csv_format` |
| `TranscriptEntry().timestamp` is `None` (backwards compat) | Pass | `test/test_transcript_timestamp.py:TestTimestampField::test_default_is_none` |
| After `start()`, transcript[0].timestamp is `float > 0` | Pass | `test/test_transcript_timestamp.py:TestTimestampPopulation::test_start_populates_timestamp` |
| After `respond()`, user+bot entries have float timestamps | Pass | `test/test_transcript_timestamp.py:TestTimestampPopulation::test_respond_populates_both` |
| `from_dict({"role":"bot","text":"hi"})` → timestamp=None | Pass | `test/test_transcript_timestamp.py:TestTimestampField::test_from_dict_missing_key` |
| `CooperativePolicy` in POLICY_REGISTRY, selectable via `get_policy` | Pass | `test/test_cooperative_policy.py:TestCooperativePolicyRegistration` (2 tests) |
| `CooperativePolicy.handle_input("no")` acknowledges + advances | Pass | `test/test_cooperative_policy.py:TestCooperativeDisagreement` (3 tests) |
| `did debate --policy cooperative` accepted by CLI | Pass | `cli.py:900` includes "cooperative" in choices list |
| All sample arguments pass `did validate` | Pass | `test_sample_arguments.py`: 408 passed (up from 395 — new branching argument) |
| `pytest` full suite passes | Pass | 1059 passed, 7 skipped, 0 failures |

## Gaps & Issues

| Severity | Location | Description |
| :--- | :--- | :--- |
| Minor | `graph.py:125-126` | Linear fallback edge generation scans all edges with `any(e.source == name ...)` — O(n×e) in the worst case. For arguments with <100 premises this is negligible, but could be optimized with a `set` lookup for large graphs. |
| Minor | `export/graph.py:61` | Mermaid diamond shape `{"{display}"}` uses curly braces for choice nodes. If `display` contains `}` characters (unlikely in premise names but possible), the Mermaid syntax would break. No sanitization of the display label for this edge case. |
| Minor | `cli.py:cmd_stats` | The BFS depth calculation at lines 636-647 uses `queue.pop(0)` which is O(n) on a list. For large graphs, `collections.deque` would be O(1). Negligible for current corpus sizes. |
| Minor | `docs/index.md:7` | Still says "Zero external runtime dependencies" — inaccurate since OPM+plugins are now mandatory deps. Stale from a prior state. |
| Minor | `docs/GRAPHS.md` | Generated file — will go stale as sample arguments change. No CI step or pre-commit hook to regenerate. Consider adding a `scripts/generate_graphs.py` for maintainability. |
| Info | `export/csv.py:18` | The `_COLUMNS` list includes `category` but `export_to_csv()` always writes an empty string for it. This is intentional (denormalized schema), but could confuse users expecting `export_to_csv` to not have a category column. |

## Suggestions

- Add a `scripts/generate_graphs.py` that regenerates `docs/GRAPHS.md` from the current sample arguments, so the gallery doesn't go stale.
- Consider adding `--include-fallback` flag to `did graph` for users who want to see implicit linear edges even on branching arguments.
- The `did stats` BFS could also report the number of leaf nodes (premises with no outgoing edges) — useful for understanding argument convergence.
- `export_to_csv` could accept an optional `columns` parameter to let callers select which fields to include, avoiding the always-empty `category` column for single-argument exports.
- CooperativePolicy's acknowledgment phrases are hardcoded English strings. For i18n, these should eventually come from `.dialog` files or a locale-specific phrase bank.
- The new branching sample argument (`should_ai_be_regulated`) is a great showcase. Consider adding 2-3 more branching examples across other categories to better demonstrate the visualization feature.
