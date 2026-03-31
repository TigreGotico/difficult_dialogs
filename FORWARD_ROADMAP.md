# difficult_dialogs — Forward Roadmap

**Status**: Revival in progress  
**Philosophy**: Break things. No backwards compatibility. No legacy baggage.

---

## Vision

A modern argumentation framework for structured dialog management. The core insight remains valid: separate **what to argue** (file-based argument definitions) from **how to argue** (policy engines). But the implementation needs a ground-up rewrite for 2026+.

### Key Differentiator

The file-based argument format is the unique UX:
```
my_argument/
├── intro.dialog
├── premise_name/
│   ├── description.premise
│   ├── statement_1.dialog
│   ├── support.support
│   └── source.source
└── conclusion.conclusion
```

Human-readable, version-controllable, LLM-injectable. This stays.

---

## Phase 0 — Cleanup (immediate)

**Goal**: Remove dead weight, establish baseline.

- [ ] Delete `setup.py` (already have `pyproject.toml`)
- [ ] Remove old examples that don't work (`examples/i_think_therefore_i_am` uses outdated format)
- [ ] Strip out `threading`-based async (replace with proper `asyncio`)
- [ ] Remove unused methods and properties across all modules
- [ ] Consolidate duplicate logic between `Argument` and `BasePolicy`
- [ ] Delete `ROADMAP.md` and `MAINTENANCE_REPORT.md` (this file replaces them)

---

## Phase 1 — Core Rewrite (week 1)

**Goal**: Working prototype with clean API.

### 1.1 Data Layer

```python
# statements.py - simplified
@dataclass
class Statement:
    text: str
    agreed: bool = False
    
    def __bool__(self) -> bool:
        return self.agreed
```

```python
# premises.py - simplified  
@dataclass
class Premise:
    name: str
    description: str
    statements: list[Statement]
    support: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        return all(bool(s) for s in self.statements)
```

```python
# arguments.py - loading logic
class Argument:
    def __init__(self, path: str | Path): ...
    def load(self) -> None: ...  # validate structure, raise on error
    def start(self) -> str: ...
    def next(self) -> str | None: ...
    def support(self) -> str | None: ...
    def end(self) -> str: ...
```

### 1.2 Policy Layer

```python
# policy.py - ABC + implementations
from abc import ABC, abstractmethod

class Policy(ABC):
    def __init__(self, argument: Argument): ...
    
    @abstractmethod
    async def handle_input(self, user_input: str) -> str: ...
    
    async def run(self) -> None: ...  # main loop
```

Key changes:
- Make `Policy` an ABC with clear extension points
- Replace `threading` with `asyncio`
- Remove `run_async()` / `stop()` / `_async_thread` mess
- Single `async run()` method

### 1.3 Validation

- [ ] Argument folder validation on load (clear errors)
- [ ] No silent failures like current implementation
- [ ] Type hints everywhere (Python 3.10+ features)

---

## Phase 2 — Developer Experience (week 2)

**Goal**: Make it pleasant to use.

### 2.1 API Design

```python
# Clean synchronous API for simple cases
from difficult_dialogs import Argument, KnowItAllPolicy

arg = Argument("my_argument")
policy = KnowItAllPolicy(arg)

for response in policy.run():
    print(f"BOT: {response}")
    user = input("USER: ")
    policy.submit(user)
```

```python
# Async API for integrations
async with KnowItAllPolicy(arg) as policy:
    async for response in policy.stream():
        await bot.send(response)
```

### 2.2 Testing

- [ ] 80%+ coverage minimum
- [ ] Test-driven development for new features
- [ ] Property-based testing for edge cases

### 2.3 Documentation

- [ ] `docs/getting-started.md` — 5 minute tutorial
- [ ] `docs/argument-format.md` — complete file format reference
- [ ] `docs/policies.md` — how to write custom policies
- [ ] `docs/api.md` — auto-generated from type hints

---

## Phase 3 — Modern Features (week 3+)

**Goal**: Earn your keep in 2026.

### 3.1 LLM Integration (optional)

```python
# LLM-powered phrasing
from difficult_dialogs.llm import LLMPolicy

def llm_fn(context: dict, statement: str) -> str:
    # Call your LLM here
    return generated_text

policy = LLMPolicy(arg, llm_fn)
```

Features:
- Use argument structure as grounding/prompts
- LLM generates natural phrasing instead of verbatim file text
- Maintain constraint layer (argument structure) while freeing language

### 3.2 Validation & Consistency

```python
# Check logical consistency
arg.validate()  # raises if premises contradict

# Add metadata
Premise(
    name="example",
    tags=["philosophy", "existence"],
    confidence=0.9
)
```

### 3.3 Export/Import

```python
# Round-trip support
arg.to_json()
Argument.from_json(data)

arg.to_dict()
Argument.from_dict(data)
```

---

## Non-Goals

These will **not** be implemented:

- Backwards compatibility with old file formats
- Support for Python < 3.10
- YAML/JSON argument formats (the whole point is plain text files)
- Database backends
- GUI tools
- Web interface

---

## Success Criteria

The project is "ready" when:

1. [ ] All tests pass (80%+ coverage)
2. [ ] Type checker passes (mypy strict mode)
3. [ ] Linter passes (ruff/flake8)
4. [ ] Documentation is complete
5. [ ] Example arguments work end-to-end
6. [ ] Published to PyPI as `difficult-dialogs`

---

## File Format Reference

Preserved exactly as-is (this is the key differentiator):

```
argument_folder/
├── intro.dialog          # Opening statement
├── premise_name/
│   ├── description.premise   # The claim being made
│   ├── statement_1.dialog    # Supporting statements
│   ├── statement_2.dialog
│   ├── support.support       # Fallback arguments
│   └── source.source         # Evidence URLs
├── another_premise/
│   └── ...
└── conclusion.conclusion     # Final statement
```

**Do not replace with YAML or JSON.** The format is the feature.

---

## Notes

- Author: JarbasAl (original creator)
- Revival: Starting from scratch, keeping only what works
- License: Apache 2.0 (unchanged)
