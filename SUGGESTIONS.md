# SUGGESTIONS — difficult_dialogs

Agent proposals for potential improvements. Not committed to the roadmap.

## High Value

### Wire LLMEnhancer into a policy
`LLMEnhancer` (`llm/enhancer.py`) can rephrase pre-approved statements for variety. An `LLMEnhancedPolicy(base_policy, enhancer)` wrapper would call `enhancer.rephrase(response)` on every bot turn, giving natural language variety without changing the argument structure.

### `dd generate` CLI command
Expose `ArgumentGenerator` (`llm/generator.py`) as `dd generate --topic "..." --url http://localhost:8000 --out ./arguments`. Would let non-programmers create arguments from the command line.

### `who` field in ArgumentGenerator
`_generate_explanations()` (`llm/generator.py`) covers five fields but skips `who`. Add `who` to the prompt and call `premise.add_who()` in `_generate_premise()`.

## Medium Value

### SSRF protection for WebhookPolicy
Validate that `webhook_url` is not a loopback/private address before making requests. Add an `allowed_hosts` parameter.

### Rate limiting / auth for `server.py`
The FastAPI server (`server.py`) has no authentication. Add optional `api_key` header verification and per-IP rate limiting.

### Batch LLM calls in ArgumentGenerator
Merge the three per-premise LLM calls (support, sources, explanations) into one structured call to reduce latency and token cost.

## Low Value

### `ArgumentLibrary.reload()` shorthand
`lib.scan(reload=True)` is slightly verbose. A `lib.reload()` alias would be more discoverable.

### `PolicyState` diff utility
A `state.diff(other_state)` that returns what changed between two saved states — useful for replaying or auditing sessions.
