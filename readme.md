# Difficult Dialogs

**Compile LLM knowledge into portable, deterministic debate modules.**

[![Tests](https://img.shields.io/badge/tests-517%20passed-green)]()
[![Type Checked](https://img.shields.io/badge/mypy-strict-blue)]()
[![Linting](https://img.shields.io/badge/ruff-passed-green)]()
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)]()
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)]()

---

## The Problem

LLMs are great for debates, but they're:
- ❌ **Expensive** at scale ($0.15 per 10-turn debate)
- ❌ **Unreliable** (hallucinate mid-conversation)
- ❌ **Slow** (2-5s latency per response)
- ❌ **Online-only** (need API access)

## The Solution

**Generate once with an LLM, run forever without one.**

```
┌─────────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   LLM (one-time)    │      │  File Format     │      │  Interpreter    │
│                     │      │  (.premise,      │      │  (dumb, fast,   │
│  Generate argument  │─────▶│   .support,      │─────▶│   deterministic)│
│  structure          │      │   .source)       │      │                 │
└─────────────────────┘      └──────────────────┘      └─────────────────┘
     ~60 seconds               Portable                   Microseconds
     Smart                      Auditable                  Offline
     One-time                   Versionable                Infinite runs
```

---

## Quick Start (5 Minutes)

### 1. Install

```bash
pip install difficult-dialogs
```

Requires Python 3.10+

### 2. Try the CLI

```bash
# List available arguments
difficult-dialogs list examples/sample_arguments

# Validate quality
difficult-dialogs validate examples/sample_arguments

# Run a debate
difficult-dialogs debate examples/sample_arguments/philosophy/free_will_exists
```

### 3. Web Interface (Optional)

```bash
# Install Streamlit
pip install streamlit

# Launch web demo
streamlit run examples/streamlit_demo.py
```

Opens at `http://localhost:8501` with beautiful UI for browsing and debating.

---

## Features

### ✅ Complete Tool Suite

- **CLI Tool** - Generate, validate, export, debate from command line
- **Web Demo** - Streamlit-based interactive interface  
- **Python API** - Full programmatic control
- **Export Formats** - JSON bundles, SQLite databases
- **Validation** - Quality scoring and issue detection

### ✅ Rich Sample Library

**32 pre-generated arguments** across 6 categories:
- 💻 Technology (5 args) - AI, open source, privacy, remote work, social media
- 🔬 Science (5 args) - Climate change, space exploration, vaccines, genetics, renewable energy
- 🏥 Health (6 args) - Exercise, diet, sleep, meditation, preventive care
- 🌍 Society (6 args) - UBI, education, transportation, recycling, volunteering
- 🤔 Philosophy (5 args) - Cogito, free will, happiness, knowledge, ethics
- 📚 Education (5 args) - Critical thinking, testing, lifelong learning, teacher pay, online learning

### ✅ Quality Assurance

- **517 automated tests** (100% pass rate)
- **Validation framework** with scoring (0.0-1.0)
- **Quality labels**: Excellent ⭐, Good 👍, Fair 😐, Poor ❌
- **All 32 sample arguments**: Excellent quality (1.00 avg score)

### ✅ Developer Friendly

- **Zero runtime dependencies** (only requests for LLM generation)
- **Type hints** throughout (mypy strict mode)
- **Well tested** (pytest suite)
- **Clean API** with dataclasses
- **Comprehensive docs** (inline + markdown)

---

## CLI Commands

### Generate Arguments

```bash
# Generate single topic
difficult-dialogs generate "AI benefits humanity" \
  --server http://localhost:8000 \
  --model qwen-72b \
  --output my_arguments

# Generate multiple topics
difficult-dialogs generate "Topic 1" "Topic 2" "Topic 3" \
  --stance pro \
  --depth 2 \
  --validate

# With progress bar (install tqdm first)
pip install tqdm
difficult-dialogs generate "Topic 1" "Topic 2" -v
```

### Validate Quality

```bash
# Validate entire library
difficult-dialogs validate examples/sample_arguments

# Verbose mode (show issues)
difficult-dialogs validate examples/sample_arguments --verbose
```

### Export

```bash
# Export to JSON bundle
difficult-dialogs export examples/sample_arguments library.json

# Export to SQLite database
difficult-dialogs export examples/sample_arguments library.db --stats

# Without validation data
difficult-dialogs export examples/sample_arguments library.json --no-validation
```

### Debate

```bash
# Interactive debate
difficult-dialogs debate examples/sample_arguments/science/space_exploration

# Or use short alias
dd debate examples/sample_arguments/health/exercise_improves_mental_health
```

### List Available

```bash
# List all arguments
difficult-dialogs list examples/sample_arguments

# Output:
# TECHNOLOGY (5):
#   • Artificial Intelligence Will Benefit Humanity
#   • Open Source Software Is Superior To Proprietary
#   ...
```

---

## Python API

### Generate with LLM

```python
from difficult_dialogs.llm import ArgumentGenerator

gen = ArgumentGenerator("http://localhost:8000")

arg = gen.generate(
    topic="Solar energy is cost-effective",
    stance="pro",
    depth=2,
    include_sources=True
)

print(f"Generated {len(arg.premises)} premises")
```

### Validate

```python
from difficult_dialogs.validators import validate_argument

result = validate_argument(arg)

print(f"Score: {result.score:.2f}")
print(f"Passed: {result.passed}")
print(f"Quality: {validator.get_quality_label(result.score)}")

for issue in result.issues:
    print(f"  {issue}")
```

### Export

```python
from difficult_dialogs.export import (
    export_to_json,
    export_library_to_json,
    LibraryDatabase
)

# Single argument to JSON
export_to_json(arg, "my_argument.json")

# Entire library to JSON bundle
export_library_to_json("examples/sample_arguments", "library.json")

# Export to SQLite
db = LibraryDatabase("library.db")
db.add_argument(arg, category="energy")

stats = db.get_statistics()
print(f"Total: {stats['total_arguments']}")
print(f"By category: {stats['by_category']}")

db.close()
```

### Run Debate Programmatically

```python
from difficult_dialogs.arguments import Argument
from difficult_dialogs.policy import KnowItAllPolicy

# Load argument
arg = Argument().load("examples/sample_arguments/philosophy/free_will_exists")

# Create policy
policy = KnowItAllPolicy(arg)

# Start dialog
print(policy.start())

# Process user input
while True:
    user_input = input("USER: ")
    response = policy.handle_input(user_input)
    
    if response:
        print(f"BOT: {response}")
```

---

## File Structure

Arguments are plain text files in structured directories:

```
argument_name/
├── intro.dialog              # Opening statement
├── conclusion.conclusion     # Final statement
└── premise_name/
    ├── description.premise   # Core claims (one per line)
    ├── support.support       # Fallback arguments (optional)
    ├── source.source         # Evidence URLs (optional)
    ├── what                  # Explanations (optional)
    ├── why                   # Explanations (optional)
    └── how                   # Explanations (optional)
```

Example:
```
free_will_exists/
├── intro.dialog
├── conclusion.conclusion
├── moral_responsibility/
│   ├── description.premise
│   └── support.support
└── quantum_indeterminacy/
    ├── description.premise
    └── source.source
```

---

## Comparison

| Feature | Difficult Dialogs | Raw LLM API | Other Debate Tools |
|---------|------------------|-------------|-------------------|
| **Cost per debate** | $0 (after generation) | $0.10-0.50 | Varies |
| **Latency** | <1ms | 2-5s | 1-3s |
| **Offline** | ✅ Yes | ❌ No | ❌ No |
| **Hallucinations** | ❌ None | ✅ Possible | ⚠️ Sometimes |
| **Auditable** | ✅ Full file format | ❌ Black box | ⚠️ Limited |
| **Versionable** | ✅ Git-friendly | ❌ API-dependent | ⚠️ Database |
| **Customizable** | ✅ Edit files | ⚠️ Prompt only | ❌ Fixed |
| **Language** | Any (LLM choice) | Any | Usually English |

---

## Installation

### Basic Install

```bash
pip install difficult-dialogs
```

### With Extras

```bash
# Development tools
pip install difficult-dialogs[dev]

# Web interface
pip install difficult-dialogs[web]

# All extras
pip install difficult-dialogs[all]
```

### From Source

```bash
git clone https://github.com/JarbasAl/difficult_dialogs
cd difficult_dialogs
pip install -e ".[dev]"
```

---

## Testing

```bash
# Run all tests
pytest test/ -v

# With coverage
pytest test/ --cov=difficult_dialogs --cov-report=html

# Specific test categories
pytest test/test_cli.py -v
pytest test/test_validators.py -v
pytest test/test_export.py -v
```

**Current Status:** 517 tests passing ✅

---

## Configuration

### LLM Server Setup

Works with any OpenAI-compatible server:

**Llama.cpp:**
```bash
./server -m models/qwen-72b.gguf --host 0.0.0.0 --port 8000
```

**Ollama:**
```bash
ollama serve
# Default: http://localhost:11434
```

**OpenAI:**
```bash
export OPENAI_API_KEY="your-key"
# Use in generator: --server https://api.openai.com/v1
```

### Environment Variables

```bash
export DD_LLM_SERVER="http://localhost:8000"
export DD_LLM_MODEL="qwen-72b"
export DD_TIMEOUT="120"
```

---

## Project Structure

```
difficult_dialogs/
├── difficult_dialogs/
│   ├── __init__.py          # Package exports
│   ├── statements.py         # Statement dataclass
│   ├── premises.py           # Premise dataclass
│   ├── arguments.py          # Argument class + loader
│   ├── policy.py             # Dialog policies
│   ├── validators.py         # Quality validation
│   ├── export.py             # JSON/SQLite export
│   ├── cli.py                # Command-line interface
│   └── llm/
│       ├── client.py         # HTTP client
│       ├── generator.py      # Argument generator
│       └── enhancer.py       # Runtime enhancement
├── examples/
│   ├── sample_arguments/     # 32 pre-made arguments
│   ├── streamlit_demo.py     # Web interface
│   ├── generate_with_progress.py  # Enhanced generator
│   └── run_argument.py       # Simple runner
├── test/
│   ├── test_*.py             # 517 tests
│   └── TEST_RESULTS.md       # Test reports
├── docs/
│   ├── USER_GUIDE.md         # User manual
│   └── DEVELOPER_GUIDE.md    # API reference
├── pyproject.toml            # Build config
├── readme.md                 # This file
└── WHITEPAPER.md             # Technical details
```

---

## Contributing

### Report Issues
https://github.com/JarbasAl/difficult_dialogs/issues

### Submit PRs
1. Fork the repo
2. Create feature branch
3. Add tests
4. Ensure all tests pass
5. Submit pull request

### Create Arguments
See `examples/sample_arguments/README.md` for argument creation guide.

---

## Roadmap

### Q2 2026
- ✅ CLI tool
- ✅ Export formats (JSON, SQLite)
- ✅ Validation framework
- ✅ Web demo
- ✅ 32 sample arguments

### Q3 2026
- [ ] JavaScript implementation
- [ ] Mobile app (React Native)
- [ ] Multi-language support
- [ ] Counter-argument generator

### Q4 2026
- [ ] Visual argument editor
- [ ] Collaborative debates
- [ ] Argument marketplace
- [ ] Enterprise features

---

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

Free for personal and commercial use. Attribution appreciated but not required.

---

## Citation

```bibtex
@software{difficult_dialogs2026,
  title = {Difficult Dialogs: Structured Argument Framework},
  author = {JarbasAl},
  year = {2026},
  url = {https://github.com/JarbasAl/difficult_dialogs},
  version = {0.5.0}
}
```

---

## Support

- **Documentation:** `docs/USER_GUIDE.md`, `docs/DEVELOPER_GUIDE.md`
- **Issues:** https://github.com/JarbasAl/difficult_dialogs/issues
- **Discussions:** https://github.com/JarbasAl/difficult_dialogs/discussions

Happy debating! 💬
