# Difficult Dialogs - Developer API Reference

**Version:** 0.5.0
**For:** Python developers building on Difficult Dialogs

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Classes](#core-classes)
3. [LLM Integration](#llm-integration)
4. [Policy System](#policy-system)
5. [Advanced Topics](#advanced-topics)
6. [Testing](#testing)
7. [Contributing](#contributing)

---

## Architecture Overview

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│  (Your code: custom policies, integrations, UIs)            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Policy Layer                            │
│  BasePolicy → KnowItAllPolicy, SilentPolicy, CustomPolicy  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Argument Layer                            │
│  Argument → Premise → Statement                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   File System Layer                          │
│  Plain text files in structured directories                 │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                   LLM Generation Layer                       │
│  ArgumentGenerator, LLMClient, LLMEnhancer                  │
└─────────────────────────────────────────────────────────────┘
```

### Module Structure

```
difficult_dialogs/
├── __init__.py          # Public API exports
├── version.py           # OVOS version block + __version__
├── statements.py        # Statement dataclass
├── premises.py          # Premise dataclass
├── arguments.py         # Argument class + file I/O
├── policy.py            # Policy ABC + 10 concrete implementations
├── policies.py          # POLICY_REGISTRY helpers
├── validators.py        # Argument validation utilities
├── cli.py               # CLI entry point (dd / difficult-dialogs)
├── exceptions.py        # Custom exceptions
├── export/
│   ├── __init__.py
│   ├── json.py          # JSON export
│   ├── sqlite.py        # SQLite export
│   └── markdown.py      # Markdown export
└── llm/
    ├── __init__.py
    ├── client.py        # HTTP client for LLM APIs
    └── generator.py     # Argument generation
```

---

## Core Classes

### Statement

The atomic unit of dialog.

```python
from difficult_dialogs import Statement
```

#### API

```python
class Statement:
    """A statement that can be agreed or disagreed with.
    
    Attributes:
        text (str): The text content.
        agreed (bool): Whether user has agreed (default: True).
    """
    
    def agree(self) -> None:
        """Mark as agreed."""
    
    def disagree(self) -> None:
        """Mark as disagreed."""
    
    def __bool__(self) -> bool:
        """Return agreement state."""
    
    def __str__(self) -> str:
        """Return text content."""
    
    def __eq__(self, other: object) -> bool:
        """Equality based on text."""
    
    def __hash__(self) -> int:
        """Hash based on text for set/dict usage."""
```

#### Usage Examples

```python
# Create statement
stmt = Statement("Pizza contains vegetables")

# Check agreement
if stmt:  # True by default
    print("User agrees")

# Change state
stmt.disagree()
assert not stmt  # Now False

stmt.agree()
assert stmt  # Back to True

# Use in collections
statement_set = {stmt, Statement("other")}
assert stmt in statement_set

# Hash for dict keys
statement_map = {stmt: "metadata"}
```

---

### Premise

A collection of statements forming a logical claim.

```python
from difficult_dialogs import Premise
```

#### API

```python
class Premise:
    """A premise containing statements that must all be agreed upon.
    
    Attributes:
        name (str): Identifier for this premise.
        description (str): Human-readable description.
        statements (list[Statement]): Core claims.
        support (list[str]): Fallback arguments.
        sources (list[str]): Evidence URLs.
        what (list[str]): "What" explanations.
        why (list[str]): "Why" explanations.
        how (list[str]): "How" explanations.
        when (list[str]): Timing context.
        where (list[str]): Location context.
    """
    
    @property
    def is_true(self) -> bool:
        """True if all statements are agreed."""
    
    @property
    def is_complete(self) -> bool:
        """True if has at least one statement."""
    
    def add_statement(self, text: str) -> Premise:
        """Add a statement. Returns self for chaining."""
    
    def add_support(self, text: str) -> Premise:
        """Add support argument. Returns self for chaining."""
    
    def add_source(self, url: str) -> Premise:
        """Add source URL. Returns self for chaining."""
    
    def add_what(self, text: str) -> Premise:
        """Add "what" explanation."""
    
    def add_why(self, text: str) -> Premise:
        """Add "why" explanation."""
    
    def add_how(self, text: str) -> Premise:
        """Add "how" explanation."""
    
    def add_when(self, text: str) -> Premise:
        """Add timing context."""
    
    def add_where(self, text: str) -> Premise:
        """Add location context."""
    
    def get_next_statement(self, cache: set[str]) -> Statement | None:
        """Get next unspoken statement."""
    
    def get_support(self, cache: set[str]) -> str | None:
        """Get unused support argument."""
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Premise:
        """Create from dictionary."""
```

#### Usage Examples

```python
# Create premise with builder pattern
premise = (
    Premise(name="health_benefits", description="Vegetables are nutritious")
    .add_statement("Vegetables contain vitamins")
    .add_statement("Vitamins support immune function")
    .add_support("Studies show reduced disease risk")
    .add_source("https://nutrition.gov/vegetables")
    .add_why("Because they contain essential nutrients")
)

# Check truth value
if premise:  # True if all statements agreed
    print("Premise accepted")

# Get next statement (for policies)
cache: set[str] = set()
next_stmt = premise.get_next_statement(cache)
if next_stmt:
    print(f"Present: {next_stmt.text}")
    cache.add(next_stmt.text)

# Serialization
data = premise.to_dict()
premise2 = Premise.from_dict(data)
```

---

### Argument

A complete debate with intro, conclusion, and premises.

```python
from difficult_dialogs import Argument
```

#### API

```python
class Argument:
    """An argument composed of multiple premises.
    
    Attributes:
        name (str): Identifier for this argument.
        intro (str): Opening statement.
        conclusion (str): Closing statement.
        path (Path | None): Source directory if loaded from disk.
    """
    
    @property
    def premises(self) -> list[Premise]:
        """List of all premises."""
    
    @property
    def premise_names(self) -> list[str]:
        """List of premise names."""
    
    @property
    def is_true(self) -> bool:
        """True if all premises are agreed."""
    
    @property
    def is_complete(self) -> bool:
        """True if has at least one premise."""
    
    def add_premise(self, premise: Premise) -> Argument:
        """Add a premise. Returns self for chaining."""
    
    def get_premise(self, name: str) -> Premise | None:
        """Get premise by name."""
    
    def get_next_premise(self, cache: set[str]) -> Premise | None:
        """Get next unspoken premise."""
    
    def load(self, path: str | Path) -> Argument:
        """Load from directory. Returns self for chaining."""
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Argument:
        """Create from dictionary."""
```

#### Usage Examples

```python
from pathlib import Path
from difficult_dialogs import Argument, Premise

# Method 1: Programmatic creation
arg = (
    Argument(
        name="exercise_benefits",
        intro="Regular exercise improves both physical and mental health.",
        conclusion="Start with just 10 minutes a day."
    )
    .add_premise(
        Premise(name="physical", description="Exercise strengthens the body")
        .add_statement("Improves cardiovascular health")
        .add_statement("Builds muscle mass")
    )
    .add_premise(
        Premise(name="mental", description="Exercise improves mental health")
        .add_statement("Reduces stress hormones")
        .add_statement("Releases endorphins")
    )
)

# Method 2: Load from files
arg = Argument()
arg.load(Path("arguments/exercise_benefits"))

# Iterate over premises
for premise in arg.premises:
    print(f"{premise.name}: {len(premise.statements)} statements")

# Serialization
data = arg.to_dict()
with open("argument.json", "w") as f:
    json.dump(data, f)

arg2 = Argument.from_dict(data)
```

---

## LLM Integration

### LLMClient

Low-level HTTP client for OpenAI-compatible APIs.

```python
from difficult_dialogs.llm import LLMClient
```

#### API

```python
class LLMClient:
    """HTTP client for OpenAI-compatible APIs.
    
    Args:
        base_url (str): Server URL (e.g., "http://localhost:8000")
        model (str | None): Model name (optional)
        timeout (float): Request timeout in seconds
    """
    
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stop: list[str] | None = None
    ) -> LLMResponse:
        """Generate text from a prompt."""
    
    def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
        schema: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Generate structured JSON output."""
    
    def health_check(self) -> bool:
        """Check if server is reachable."""
```

#### Usage Examples

```python
from difficult_dialogs.llm import LLMClient

# Initialize client
client = LLMClient(
    base_url="http://192.168.1.200:8000",
    model="qwen-72b",
    timeout=120.0
)

# Simple generation
response = client.generate("Explain quantum entanglement in 2 sentences")
print(response.text)
print(f"Model: {response.model}")
print(f"Tokens used: {response.usage}")

# Structured generation
schema = {
    "type": "object",
    "properties": {
        "claims": {"type": "array", "items": {"type": "string"}},
        "sources": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["claims", "sources"]
}

data = client.generate_json(
    prompt="List 3 claims about solar energy with sources",
    system_prompt="Respond only with valid JSON",
    schema=schema
)

print(f"Claims: {data['claims']}")
print(f"Sources: {data['sources']}")

# Health check
if client.health_check():
    print("Server is online")
else:
    print("Server is unreachable")
```

---

### ArgumentGenerator

High-level argument generation.

```python
from difficult_dialogs.llm import ArgumentGenerator
```

#### API

```python
class ArgumentGenerator:
    """Generates structured arguments using an LLM.
    
    Args:
        base_url (str): LLM server URL
        model (str | None): Model name
        timeout (float): Generation timeout
    """
    
    def generate(
        self,
        topic: str,
        stance: str = "pro",
        depth: int = 2,
        include_sources: bool = True,
        include_counterarguments: bool = True,
        language: str = "en"
    ) -> Argument:
        """Generate a complete argument structure."""
```

#### Usage Examples

```python
from difficult_dialogs.llm import ArgumentGenerator
from pathlib import Path

# Initialize generator
gen = ArgumentGenerator(
    base_url="http://localhost:8000",
    model="qwen-72b",
    timeout=300.0
)

# Generate argument
arg = gen.generate(
    topic="Universal basic income would reduce poverty",
    stance="pro",
    depth=2,
    include_sources=True,
    include_counterarguments=True,
    language="en"
)

# Save to disk — Argument.save() writes the full subdirectory structure
arg.save("arguments/ubi_poverty")
print(f"Generated argument with {len(arg.premises)} premises")
```

---

### LLMEnhancer

Runtime enhancement of pre-approved content.

```python
from difficult_dialogs.llm import LLMEnhancer
```

#### API

```python
class LLMEnhancer:
    """Enhances pre-written arguments with natural phrasing.
    
    Args:
        base_url (str): LLM server URL
        model (str | None): Model name
    """
    
    def rephrase(
        self,
        text: str,
        context: str | None = None,
        style: str = "conversational"
    ) -> str:
        """Rephrase while preserving meaning."""
    
    def explain(
        self,
        concept: str,
        question_type: str = "why"
    ) -> str | None:
        """Generate explanation for a concept."""
    
    def summarize_exchange(
        self,
        user_statements: list[str],
        bot_statements: list[str]
    ) -> str:
        """Summarize the debate so far."""
    
    def clear_cache(self) -> None:
        """Clear rephrasing cache."""
```

#### Usage Examples

```python
from difficult_dialogs.llm import LLMEnhancer

enhancer = LLMEnhancer(base_url="http://localhost:8000")

# Rephrase for variety
original = "Computers process information"
rephrased = enhancer.rephrase(
    original,
    context="Explaining AI to beginners",
    style="friendly"
)
print(rephrased)
# "At their core, computers are designed to handle and manipulate data"

# Different styles
formal = enhancer.rephrase(original, style="formal")
casual = enhancer.rephrase(original, style="conversational")
academic = enhancer.rephrase(original, style="academic")

# Generate explanations
explanation = enhancer.explain(
    "photosynthesis",
    question_type="why"
)
print(explanation)
# "Photosynthesis occurs because plants need to convert sunlight into usable energy"

# Summarize debate
summary = enhancer.summarize_exchange(
    user_statements=["But isn't that expensive?", "What about maintenance?"],
    bot_statements=[
        "Solar panels have decreased 90% in cost since 2010",
        "Maintenance costs are minimal, about $20/year"
    ]
)
print(summary)
# "The user expressed concerns about costs, while the bot presented data on price reductions and low maintenance expenses"

# Cache management
enhancer.clear_cache()  # Clear cached rephrasings
```

---

## Policy System

### BasePolicy

Abstract base class for all policies.

```python
from difficult_dialogs import BasePolicy
```

#### API

```python
class BasePolicy(ABC):
    """Abstract base class for dialog policies.
    
    Subclasses must implement handle_input().
    """
    
    def __init__(self, argument: Argument) -> None:
        """Initialize with an argument."""
    
    @abstractmethod
    def handle_input(self, user_input: str) -> str | None:
        """Process user input and return response."""
    
    def start(self) -> str:
        """Start dialog, return intro."""

    def end(self) -> str:
        """End dialog, set finished=True, return conclusion."""

    def agree(self) -> None:
        """Mark current premise as agreed."""
    
    def disagree(self) -> None:
        """Mark current premise as disagreed."""
    
    @property
    def state(self) -> PolicyState:
        """Current dialog state."""
```

#### Implementing Custom Policy

```python
from difficult_dialogs import BasePolicy, Argument

class EmpatheticPolicy(BasePolicy):
    """Policy that acknowledges user feelings."""
    
    def handle_input(self, user_input: str) -> str | None:
        # Detect emotional content
        if any(word in user_input.lower() for word in ["frustrated", "angry", "upset"]):
            return "I understand this topic can be frustrating. Let's take it step by step."
        
        # Normal processing
        if user_input.lower().startswith(('y', 'yes')):
            self.agree()
            return self._advance()
        else:
            self.disagree()
            return self._handle_disagreement()
    
    def _advance(self) -> str | None:
        result = self._get_next_statement()
        if result is None:
            self.state.finished = True
            return self.argument.conclusion
        _, statement = result
        return f"{statement}\nDo you agree?"
    
    def _handle_disagreement(self) -> str:
        support = self._get_support()
        if support:
            return f"I hear your concern. Consider: {support}"
        return "That's a valid perspective. Let's continue."

# Usage
arg = Argument()
arg.load(Path("arguments/sensitive_topic"))
policy = EmpatheticPolicy(arg)
```

### KnowItAllPolicy

Default policy with support arguments.

```python
from difficult_dialogs import KnowItAllPolicy
```

#### Features

- Presents statements from premises
- Provides support arguments when user disagrees
- Cites sources when available
- Handles "what", "why", "how" questions

#### Usage

```python
from difficult_dialogs import Argument, KnowItAllPolicy

arg = Argument()
arg.load(Path("arguments/climate_change"))

policy = KnowItAllPolicy(arg)
policy.start()

while not policy.state.finished:
    user_input = input("USER: ")
    response = policy.handle_input(user_input)
    if response:
        print(f"BOT: {response}")
```

### SilentPolicy

One-way presentation without waiting for feedback.

```python
from difficult_dialogs import SilentPolicy
```

#### Usage

```python
from difficult_dialogs import Argument, SilentPolicy

arg = Argument()
arg.load(Path("arguments/lecture"))

policy = SilentPolicy(arg)

while not policy.state.finished:
    response = policy.handle_input("")
    if response:
        print(response)
```

---

## Advanced Topics

### Type Hints

Full type hints throughout:

```python
from difficult_dialogs import Argument, Premise, Statement
from difficult_dialogs.policy import BasePolicy, PolicyState
from typing import Generator, AsyncGenerator

def create_argument() -> Argument:
    ...

def run_dialog(policy: BasePolicy) -> Generator[str, str, None]:
    ...

async def stream_dialog(policy: BasePolicy) -> AsyncGenerator[str, None]:
    ...
```

### Error Handling

```python
from difficult_dialogs.arguments import Argument
from difficult_dialogs.exceptions import ArgumentLoadError

arg = Argument()

try:
    arg.load("/nonexistent/path")
except ArgumentLoadError as e:
    print(f"Could not load argument: {e}")

from difficult_dialogs.llm.generator import ArgumentGenerator

gen = ArgumentGenerator("http://invalid-url:8000")

try:
    arg = gen.generate("topic")
except RuntimeError as e:
    print(f"LLM server unreachable: {e}")
except ValueError as e:
    print(f"LLM returned invalid JSON: {e}")
```

### Testing Your Code

```python
import pytest
from pathlib import Path
from difficult_dialogs import Argument, Premise, Statement
from difficult_dialogs.policy import KnowItAllPolicy

def test_argument_creation():
    arg = Argument(
        name="test",
        intro="Hello",
        conclusion="Goodbye"
    )
    arg.add_premise(
        Premise(name="p1", description="Test premise")
        .add_statement("Statement 1")
        .add_statement("Statement 2")
    )
    
    assert arg.name == "test"
    assert len(arg.premises) == 1
    assert arg.is_true  # All statements agreed by default

def test_argument_loading():
    arg = Argument()
    arg.load(Path("examples/i_think_therefore_i_am"))

    assert arg.is_complete
    assert len(arg.premises) > 0

def test_policy_dialog():
    arg = Argument()
    arg.load(Path("examples/i_think_therefore_i_am"))
    
    policy = KnowItAllPolicy(arg)
    intro = policy.start()
    
    assert intro != ""
    assert not policy.state.finished
    
    response = policy.handle_input("yes")
    assert response is not None

def test_sync_policy():
    arg = Argument()
    arg.load(Path("examples/i_think_therefore_i_am"))

    policy = KnowItAllPolicy(arg)
    policy.start()

    gen = policy.run_sync()
    response = next(gen)
    assert response is not None
```

---

## Contributing

### Development Setup

```bash
# Clone repository
git clone https://github.com/TigreGotico/difficult_dialogs
cd difficult_dialogs

# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest test/ -v

# Type checking
uv run mypy difficult_dialogs/

# Linting
uv run ruff check difficult_dialogs/ test/
```

### Code Style

- **Type hints:** Required for all public APIs
- **Docstrings:** Google style for all public classes/methods
- **Formatting:** ruff auto-format
- **Testing:** pytest with >80% coverage

### Pull Request Process

1. Fork the repository
2. Create feature branch (`git checkout -b feature/my-feature`)
3. Make changes with tests
4. Ensure all checks pass (`pytest`, `mypy`, `ruff`)
5. Submit PR with clear description

### Reporting Issues

Use GitHub Issues with:
- Clear title
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS
- Minimal code example if possible

---

## Support

- **Documentation:** `/docs/` directory
- **API Reference:** This document
- **Issues:** https://github.com/TigreGotico/difficult_dialogs/issues
- **Discussions:** https://github.com/TigreGotico/difficult_dialogs/discussions

Happy coding!
