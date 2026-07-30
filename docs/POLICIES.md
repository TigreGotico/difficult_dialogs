# Dialog Policies

All policies inherit from `BasePolicy`: `difficult_dialogs/policy.py:92`.

A policy is instantiated with an `Argument` and drives the conversation by
implementing `handle_input(user_input) -> str | None`.

---

## Quick selection

| Policy name | CLI flag | Best for |
|---|---|---|
| `knowitall` | `--policy knowitall` | Default. Persuades with evidence on disagreement. |
| `silent` | `--policy silent` | One-way presentations, ignores user input. |
| `socratic` | `--policy socratic` | Probing questions on disagreement, no direct counter-arguments. |
| `debate` | `--policy debate` | Challenges disagreement with pre-loaded support, advances after 2 challenges. |
| `exploratory` | `--policy exploratory` | Acknowledges complexity, neutral on disagreement. |
| `maieutic` | `--policy maieutic` | Guided discovery, starts with open topic question. |
| `skeptic` | `--policy skeptic` | Challenges every claim, stress-tests arguments. |
| `teacher` | `--policy teacher` | Patient educator, emphasises examples and step-by-step explanation. |
| `debater` | `--policy debater` | Aggressive counterarguments, adversarial training. |
| `minimalist` | `--policy minimalist` | Brief and direct, truncates responses ≥ 100 chars. |
| `adaptive` | `--policy adaptive` | Starts as `KnowItAllPolicy`, switches to `ExploratoryPolicy` after 3 consecutive disagreements. |
| `multichoice` | Python only | Presents labelled A/B/C options when a `.choices` file is present. |

`POLICY_REGISTRY`: `difficult_dialogs/policy.py:1711`

---

## Policy behaviour details

### `KnowItAllPolicy`

On disagreement: serves support statements one-by-one until exhausted, then shows sources.
On Five-Ws questions (`what`, `why`, `how`, `when`, `where`, `who`): answers from the matching premise field.
`KnowItAllPolicy.handle_input()`: `difficult_dialogs/policy.py:439`

### `SilentPolicy`

Returns the next statement regardless of user input.
`SilentPolicy.handle_input()`: `difficult_dialogs/policy.py:510`

### `SocraticPolicy`

On clear disagreement: asks a random question from `SOCRATIC_QUESTIONS` (8 built-in prompts).
On clear agreement: advances to next statement.
On ambiguous input: also asks a question.
`SocraticPolicy.handle_input()`: `difficult_dialogs/policy.py:568`

### `DebatePolicy`

On disagreement: prefixes support with a random `CHALLENGE_RESPONSES` phrase. After 2 challenges
on the same premise with no support remaining, advances.
`DebatePolicy.handle_input()`: `difficult_dialogs/policy.py:659`

### `ExploratoryPolicy`

On disagreement: picks a random neutral acknowledgment, then appends support or sources if available.
`ExploratoryPolicy.handle_input()`: `difficult_dialogs/policy.py:755`

### `MaieuticPolicy`

Opens with a question about the topic (`INTRO_QUESTIONS`). On agreement: presents next statement.
On disagreement: asks a skeptical question (`DISAGREEMENT_QUESTIONS`). Overrides `start()` to
replace the intro with an open question.
`MaieuticPolicy.handle_input()`: `difficult_dialogs/policy.py:835`

### `SkepticPolicy`

On agreement: presents a challenge phrase without advancing. On disagreement: advances and prefixes
the next statement with a counter-phrase.
`SkepticPolicy.handle_input()`: `difficult_dialogs/policy.py:906`

### `TeacherPolicy`

On `?` in user input: peeks at the next statement (without consuming it) and wraps it with a
`TRANSITION_PHRASES` intro. On agreement: advances with a `SUMMARY_PHRASES` prefix. On
disagreement: says "Let me clarify:" and re-peeks the same statement.
`TeacherPolicy.handle_input()`: `difficult_dialogs/policy.py:966`

### `DebaterPolicy`

On inputs longer than 10 characters: treats as debate and prefixes a counter-statement with an
attack phrase. Short inputs are parsed as yes/no.
`DebaterPolicy.handle_input()`: `difficult_dialogs/policy.py:1048`

### `MinimalistPolicy`

Truncates Five-Ws answers to 100 chars and statements to 100 chars.
`MinimalistPolicy.handle_input()`: `difficult_dialogs/policy.py:1092`

### `AdaptivePolicy`

Delegates to `initial_policy` (default `KnowItAllPolicy`). Counts consecutive disagreements, on
reaching `switch_threshold` (default 3) transfers the full session state to `fallback_policy`
(default `ExploratoryPolicy`) without repeating premises.

```python
from difficult_dialogs.policy import AdaptivePolicy, SkepticPolicy, SocraticPolicy

policy = AdaptivePolicy(
    arg,
    initial_policy=SkepticPolicy,
    fallback_policy=SocraticPolicy,
    switch_threshold=2,
)
```

`AdaptivePolicy`: `difficult_dialogs/policy.py:1121`

### `MultiChoicePolicy`

When the current premise has a `.choices` file, appends the formatted option menu to the
statement text and waits for the user to select an option. Matching is performed by
`parse_choice()`: `difficult_dialogs/choices.py:352`: using the active choice solver
(offline label/prefix matcher by default, or an OPM plugin if installed). If the user's
input does not match any option, the menu is re-presented.

When no `.choices` are defined for the current premise, falls back to `KnowItAllPolicy`
yes/no behaviour.

```python
from difficult_dialogs.arguments import Argument
from difficult_dialogs.policy import MultiChoicePolicy

arg = Argument.from_directory("my_argument")
policy = MultiChoicePolicy(arg)
print(policy.start())
```

`MultiChoicePolicy.handle_input()`: `difficult_dialogs/policy.py:1565`

### `WebhookPolicy`

Forwards every turn to an external HTTP endpoint (POST JSON). Falls back to
`KnowItAllPolicy` on any network failure. Not available via the CLI `--policy` flag
because it requires a `webhook_url` constructor argument.

Payload:
```json
{
  "argument": "<name>",
  "user_input": "<text>",
  "current_premise": "<name or null>",
  "transcript": [{"role": "bot|user", "text": "…"}]
}
```

Expected response: `{"response": "<text>"}`.

`WebhookPolicy`: `difficult_dialogs/policy.py:1245`

---

## Common base interface

Every policy provides:

| Method | Description |
|---|---|
| `start() -> str` | Reset state, honour `entry_point`, return intro. `BasePolicy.start()`: `policy.py:130` |
| `respond(user_input) -> str \| None` | Record turn in transcript, then call `handle_input()`. Prefer over calling `handle_input` directly. `BasePolicy.respond()`: `policy.py:167` |
| `end() -> str` | Set `state.finished = True`, return conclusion. `BasePolicy.end()`: `policy.py:143` |
| `progress() -> (int, int)` | `(premises_covered, total_premises)`. `BasePolicy.progress()`: `policy.py:154` |
| `save_state(path)` | Persist `PolicyState` to a JSON file. `BasePolicy.save_state()`: `policy.py:309` |
| `load_state(path)` | Restore from a JSON file written by `save_state()`. `BasePolicy.load_state()`: `policy.py:319` |
| `restore_state(state)` | Restore from a `PolicyState` or raw dict (for Redis / key-value stores). `BasePolicy.restore_state()`: `policy.py:329` |
| `run_sync() -> Generator` | Coroutine-send protocol: `next(gen)` → intro, `gen.send(text)` → response. `BasePolicy.run_sync()`: `policy.py:352` |
| `stream(queue) -> AsyncGenerator` | Async variant, reads user messages from an `asyncio.Queue`. `BasePolicy.stream()`: `policy.py:391` |

---

## Plugin policies

Third-party policies can be registered under the `difficult_dialogs.policies`
entry-point group. They are discovered at import time and added to `POLICY_REGISTRY`.

```toml
# pyproject.toml
[project.entry-points."difficult_dialogs.policies"]
my_policy = "my_package.policy:MyPolicy"
```

`_load_plugin_policies()`: `difficult_dialogs/policy.py:1729`

---

## Creating a custom policy

```python
from difficult_dialogs.policy import BasePolicy

class ConfirmPolicy(BasePolicy):
    """Asks for confirmation before advancing each statement."""

    def handle_input(self, user_input: str) -> str | None:
        lower = user_input.strip().lower()
        if lower in ("yes", "y", "ok", "sure"):
            result = self._get_next_statement()
            if result is None:
                self.state.finished = True
                return str(self.argument.conclusion)
            _, statement = result
            return f"{statement}\n\nDo you want to continue? (yes/no)"
        return "Please confirm before we continue. (yes/no)"
```

The helper methods available to all subclasses:

| Method | Description |
|---|---|
| `_get_next_statement()` | Advance and mark as spoken. Returns `(premise_name, text)` or `None`. |
| `_peek_next_statement()` | Same but does not mark as spoken. |
| `_get_support()` | Return one unused support statement for the current premise. |
| `_get_sources()` | Return list of source citations for the current premise. |
| `_check_five_w(user_input)` | Return an answer if input contains a Five-Ws keyword. |

---
[← Argument format](argument-format.md) · [Home](index.md) · [Builder →](builder.md)
