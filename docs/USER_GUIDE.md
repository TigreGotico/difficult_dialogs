# Difficult Dialogs - Complete User Guide

**Version:** 0.5.0
**Last Updated:** 2026-03-31

---

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Quick Start (5 Minutes)](#quick-start-5-minutes)
4. [Understanding the File Format](#understanding-the-file-format)
5. [Creating Your First Argument](#creating-your-first-argument)
6. [Using the LLM Generator](#using-the-llm-generator)
7. [Running Debates](#running-debates)
8. [Advanced Features](#advanced-features)
9. [Troubleshooting](#troubleshooting)
10. [Examples](#examples)

---

## Introduction

### What is Difficult Dialogs?

Difficult Dialogs is a framework for creating **portable, deterministic debate bots** that can run without an LLM at inference time.

**The core idea:**
1. Use an LLM **once** to generate structured argument files
2. Run the debate **forever** with a lightweight interpreter
3. No API costs, no hallucinations, works offline

### When to Use This

✅ **Good use cases:**
- Educational debate tutors
- Patient education in healthcare
- Customer support FAQs
- Compliance-heavy domains (legal, finance)
- Offline/edge deployment
- High-volume applications (1000s of users/day)

❌ **Not suitable for:**
- Open-ended conversations
- Topics requiring real-time information
- Highly personalized interactions
- Creative writing or roleplay

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: GENERATION (One-time, uses LLM, ~30-60 seconds)  │
│                                                             │
│  You: "Generate an argument about vaccine safety"          │
│  LLM: Creates directory structure with premises, support   │
│       statements, sources, explanations                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: EXECUTION (Infinite, no LLM, microseconds)       │
│                                                             │
│  User: "Why should I trust vaccines?"                      │
│  Bot: Presents pre-approved arguments from files           │
│       Never hallucinates, always consistent, works offline │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Installation

### Requirements

- Python 3.10 or higher
- Access to an OpenAI-compatible LLM server (for generation only)
  - Local: Llama.cpp, Ollama, vLLM
  - Cloud: OpenAI API, Anthropic, etc.

### Install from PyPI

```bash
pip install difficult-dialogs
```

### Install from Source

```bash
git clone https://github.com/TigreGotico/difficult_dialogs
cd difficult_dialogs
uv pip install -e .
```

### Verify Installation

```bash
python -c "from difficult_dialogs import Argument; print('✓ Installed!')"
```

---

## Quick Start (5 Minutes)

### Step 1: Set Up Your LLM Server

If you have a local LLM server running (e.g., Llama.cpp):

```bash
# Example: Llama.cpp server
./server -m models/qwen-72b.gguf --host 0.0.0.0 --port 8000
```

Note your server URL (e.g., `http://localhost:8000`).

### Step 2: Generate an Argument

```bash
# Run the generator
python examples/generate_argument.py

# Enter your topic when prompted
Topic: Remote work increases productivity
```

This creates a directory like `examples/generated/remote_work_increases_productivity/`.

### Step 3: Run the Debate

```bash
# Run the generated argument
python examples/run_argument.py examples/generated/remote_work_increases_productivity
```

You'll see:
```
ARGUMENT: remote work increases productivity
==================================================

BOT: Remote work has fundamentally transformed how we approach productivity...

USER: why do you say that?
BOT: Studies show that remote workers report fewer distractions and higher job satisfaction.
Do you agree? (y/n)
```

**That's it!** You've created and run a debate bot in 5 minutes.

---

## Understanding the File Format

### Directory Structure

Arguments are stored as plain text files in a structured directory:

```
my_argument/
├── intro.dialog              # Opening statement (required)
├── conclusion.conclusion     # Final statement (required)
├── premise_name/             # Each premise is a subdirectory
│   ├── description.premise   # Main claim(s), one per line (required)
│   ├── support.support       # Fallback arguments (optional)
│   ├── source.source         # Evidence URLs (optional)
│   ├── what                  # "What" explanations (optional)
│   ├── why                   # "Why" explanations (optional)
│   ├── how                   # "How" explanations (optional)
│   ├── when                  # Timing context (optional)
│   └── where                 # Location context (optional)
└── another_premise/
    └── ...
```

### File Contents

Each file contains one statement per line:

**`description.premise`:**
```
Remote work reduces commute stress
Employees save 2+ hours daily by not commuting
Less stress leads to better mental health
```

**`support.support`:**
```
A Stanford study found 13% performance increase in remote workers
Companies report lower turnover rates for remote employees
Remote workers take fewer sick days
```

**`source.source`:**
```
https://news.stanford.edu/2015/02/17/work-from-home-effects-021715/
https://www.forbes.com/sites/bryanrobinson/2023/01/22/why-remote-workers-are-more-productive/
```

### Why Files Instead of JSON/YAML?

| Benefit | Explanation |
|---------|-------------|
| **Human-readable** | Anyone can edit with a text editor |
| **Git-friendly** | Clean diffs, easy versioning |
| **Modular** | Each file = single responsibility |
| **Composable** | Mix and match premises from different arguments |
| **Non-technical** | Subject matter experts can write without coding |

---

## Creating Your First Argument

### Method 1: Manual Creation (Recommended for Learning)

Let's create a simple argument manually:

#### Step 1: Create Directory Structure

```bash
mkdir -p arguments/pizza_is_healthy/{pizza_nutrients,moderation_key}
```

#### Step 2: Write Intro

Create `arguments/pizza_is_healthy/intro.dialog`:
```
Pizza often gets a bad reputation as unhealthy fast food.
However, when made with quality ingredients and consumed in moderation,
pizza can actually be part of a balanced diet.
Let me explain why.
```

#### Step 3: Write Conclusion

Create `arguments/pizza_is_healthy/conclusion.conclusion`:
```
So while pizza shouldn't be your only food,
it can absolutely fit into a healthy lifestyle.
The key is mindful ingredient choices and portion control.
Enjoy your slice!
```

#### Step 4: Create Premises

Create `arguments/pizza_is_healthy/pizza_nutrients/description.premise`:
```
Pizza provides essential nutrients
Tomato sauce contains lycopene and vitamins
Cheese offers calcium and protein
Vegetable toppings add fiber and antioxidants
```

Create `arguments/pizza_is_healthy/pizza_nutrients/support.support`:
```
A slice of vegetable pizza counts toward your daily vegetable intake
Homemade pizza lets you control sodium levels
Whole wheat crust adds complex carbohydrates
```

Create `arguments/pizza_is_healthy/pizza_nutrients/source.source`:
```
https://www.healthline.com/nutrition/is-pizza-healthy
https://www.webmd.com/food-recipes/features/can-pizza-be-healthy
```

#### Step 5: Add Second Premise

Create `arguments/pizza_is_healthy/moderation_key/description.premise`:
```
Portion control makes any food sustainable
Balance is more important than individual meals
Long-term habits matter more than occasional indulgence
```

Create `arguments/pizza_is_healthy/moderation_key/support.support`:
```
Nutritionists emphasize overall dietary patterns, not single foods
The Mediterranean diet includes bread and cheese regularly
Restrictive diets often fail, while flexible approaches succeed
```

#### Step 6: Test Your Argument

```bash
python examples/run_argument.py arguments/pizza_is_healthy
```

### Method 2: LLM Generation (Faster for Complex Topics)

See [Using the LLM Generator](#using-the-llm-generator) below.

---

## Using the LLM Generator

### Configuration

Edit `examples/generate_argument.py` to match your setup:

```python
LLM_URL = "http://192.168.1.200:8000"  # Your server URL
MODEL_NAME = "qwen-72b"                 # Your model name (or None for default)
```

### Basic Usage

```bash
python examples/generate_argument.py
```

You'll be prompted:
```
Enter a topic to argue about: Electric vehicles are better for the environment
```

### Advanced Options

For programmatic generation:

```python
from difficult_dialogs.llm import ArgumentGenerator

# Initialize generator
gen = ArgumentGenerator(
    base_url="http://localhost:8000",
    model="qwen-72b",
    timeout=300.0  # 5 minute timeout
)

# Generate argument
argument = gen.generate(
    topic="Electric vehicles reduce carbon emissions",
    stance="pro",                    # or "con"
    depth=2,                         # Complexity level (1-3)
    include_sources=True,            # Add citation URLs
    include_counterarguments=True,   # Anticipate objections
    language="en"                    # Language code
)

# Save to disk — Argument.save() handles all file naming automatically
argument.save("arguments/ev_better")
print(f"Generated argument saved to arguments/ev_better")
```

### Generation Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `topic` | str | required | The topic to argue about |
| `stance` | str | "pro" | "pro" or "con" |
| `depth` | int | 2 | Complexity (1=simple, 3=complex) |
| `include_sources` | bool | True | Generate source URLs |
| `include_counterarguments` | bool | True | Generate support statements |
| `language` | str | "en" | Language code |

### Tips for Better Generation

1. **Be specific with topics:**
   - ❌ "Climate change"
   - ✅ "Carbon taxes effectively reduce emissions"

2. **Choose appropriate depth:**
   - Depth 1: Simple FAQ (2-3 premises)
   - Depth 2: Standard debate (4-6 premises)
   - Depth 3: Complex argument (8-12 premises)

3. **Review generated content:**
   - Always review before deploying
   - Check sources are real URLs
   - Verify logical consistency
   - Edit for tone and accuracy

4. **Iterate:**
   - Generate multiple versions
   - Pick the best one
   - Manually refine

---

## Running Debates

### Interactive Mode

```bash
python examples/run_argument.py arguments/pizza_is_healthy
```

Example session:
```
ARGUMENT: pizza is healthy
==================================================

BOT: Pizza often gets a bad reputation as unhealthy fast food...

USER: but isn't pizza just junk food?
BOT: A slice of vegetable pizza counts toward your daily vegetable intake.
Do you agree? (y/n)

USER: n
BOT: Homemade pizza lets you control sodium levels.
Do you agree now? (y/n)

USER: y
BOT: Portion control makes any food sustainable.
Do you agree? (y/n)
```

### Programmatic Usage

```python
from pathlib import Path
from difficult_dialogs import Argument, KnowItAllPolicy

# Load argument
arg = Argument()
arg.load(Path("arguments/pizza_is_healthy"))

# Create policy
policy = KnowItAllPolicy(arg)

# Run dialog
print(f"BOT: {policy.start()}")

while not policy.state.finished:
    user_input = input("USER: ")
    
    # Handle special commands
    if user_input == "/quit":
        break
    elif user_input == "/sources":
        print("Sources available for current claim")
        continue
    
    response = policy.handle_input(user_input)
    if response:
        print(f"BOT: {response}")
```

### Embedding in Applications

#### Web Application (Flask Example)

```python
from flask import Flask, request, jsonify, session
from difficult_dialogs import Argument, KnowItAllPolicy

app = Flask(__name__)
app.secret_key = "your-secret-key"

# Load argument once at startup
ARGUMENT_PATH = Path("arguments/pizza_is_healthy")
argument = Argument()
argument.load(ARGUMENT_PATH)

@app.route('/start', methods=['POST'])
def start_debate():
    """Initialize a new debate session."""
    policy = KnowItAllPolicy(argument)
    session['policy_state'] = {
        'spoken_premises': list(policy.state.spoken_premises),
        'spoken_statements': list(policy.state.spoken_statements),
        'current_premise': policy.state.current_premise,
        'finished': False
    }
    return jsonify({'response': policy.start()})

@app.route('/chat', methods=['POST'])
def chat():
    """Process user message and get bot response."""
    user_input = request.json.get('message', '')
    
    # Recreate policy and restore state
    policy = KnowItAllPolicy(argument)
    # Restore state from session...
    
    response = policy.handle_input(user_input)
    
    return jsonify({
        'response': response,
        'finished': policy.state.finished
    })

if __name__ == '__main__':
    app.run(debug=True)
```

#### Discord Bot Example

```python
import discord
from discord.ext import commands
from difficult_dialogs import Argument, KnowItAllPolicy

bot = commands.Bot(command_prefix='!')

# Store active debates
debates = {}

@bot.event
async def on_ready():
    global default_argument
    default_argument = Argument()
    default_argument.load(Path("arguments/pizza_is_healthy"))
    print(f'{bot.user} is ready!')

@bot.command(name='debate')
async def start_debate(ctx, *, topic: str = None):
    """Start a debate on the specified topic."""
    debates[ctx.author.id] = KnowItAllPolicy(default_argument)
    policy = debates[ctx.author.id]
    
    await ctx.send(f"**Bot:** {policy.start()}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if message.author.id in debates:
        policy = debates[message.author.id]
        response = policy.handle_input(message.content)
        
        if response:
            await message.channel.send(f"**Bot:** {response}")
            
            if policy.state.finished:
                del debates[message.author.id]
    
    await bot.process_commands(message)

bot.run('YOUR_DISCORD_TOKEN')
```

---

## Advanced Features

### Hybrid Mode: LLM Enhancement

Add natural language variety while keeping structured arguments:

```python
from difficult_dialogs import Argument, KnowItAllPolicy
from difficult_dialogs.llm import LLMEnhancer

# Load argument
arg = Argument()
arg.load(Path("arguments/climate_change"))

# Create policy
policy = KnowItAllPolicy(arg)

# Attach LLM enhancer
enhancer = LLMEnhancer(base_url="http://localhost:8000")

# Custom policy with enhancement
class EnhancedPolicy(KnowItAllPolicy):
    def handle_input(self, user_input: str) -> str | None:
        response = super().handle_input(user_input)
        
        if response and self.state.current_premise:
            # Rephrase with LLM for variety
            enhanced = enhancer.rephrase(
                response,
                context=f"Debating: {self.argument.name}",
                style="conversational"
            )
            return enhanced
        
        return response

policy = EnhancedPolicy(arg)
```

### Custom Policies

Create your own dialog flow:

```python
from difficult_dialogs import BasePolicy

class SocraticPolicy(BasePolicy):
    """Policy that asks questions instead of making statements."""
    
    def handle_input(self, user_input: str) -> str | None:
        if user_input.lower().startswith(('y', 'yes', 'agree')):
            self.agree()
            return self._ask_followup()
        elif user_input.lower().startswith(('n', 'no', 'disagree')):
            self.disagree()
            return self._challenge_gently()
        else:
            return self._clarify()
    
    def _ask_followup(self) -> str:
        """Ask a follow-up question."""
        result = self._get_next_statement()
        if result is None:
            self.state.finished = True
            return self.argument.conclusion
        
        _, statement = result
        return f"Interesting. Can you tell me more about: {statement}?"
    
    def _challenge_gently(self) -> str:
        """Gently challenge disagreement."""
        support = self._get_support()
        if support:
            return f"I understand your skepticism. Consider this: {support}"
        
        sources = self._get_sources()
        if sources:
            return f"Here's some evidence: {'; '.join(sources[:2])}"
        
        self.agree()
        return "That's a valid perspective. Let's continue."
    
    def _clarify(self) -> str:
        """Ask for clarification."""
        return "Could you elaborate on what you mean?"
```

### Argument Composition

Import premises from other arguments:

```python
from difficult_dialogs import Argument

# Load base arguments
vaccines = Argument()
vaccines.load(Path("arguments/vaccine_safety"))

herd_immunity = Argument()
herd_immunity.load(Path("arguments/herd_immunity"))

# Combine into comprehensive argument
comprehensive = Argument(
    name="vaccination_is_important",
    intro="Vaccination protects both individuals and communities..."
)

# Import all premises from both arguments
for premise in vaccines.premises:
    comprehensive.add_premise(premise)

for premise in herd_immunity.premises:
    comprehensive.add_premise(premise)

# Save combined argument
output_dir = Path("arguments/vaccination_comprehensive")
output_dir.mkdir(parents=True, exist_ok=True)
# ... save logic
```

### Export Formats

#### JSON Bundle

```python
import json
from difficult_dialogs import Argument

arg = Argument()
arg.load(Path("arguments/my_topic"))

# Export to JSON
data = arg.to_dict()

with open("arguments/my_topic.json", "w") as f:
    json.dump(data, f, indent=2)

# Import from JSON
arg2 = Argument.from_dict(data)
```

#### SQLite Database

```python
import sqlite3
from difficult_dialogs import Argument

def export_to_sqlite(arg: Argument, db_path: str) -> None:
    """Export argument to SQLite database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS arguments (
            id INTEGER PRIMARY KEY,
            name TEXT,
            intro TEXT,
            conclusion TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS premises (
            id INTEGER PRIMARY KEY,
            argument_id INTEGER,
            name TEXT,
            description TEXT,
            FOREIGN KEY (argument_id) REFERENCES arguments(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS statements (
            id INTEGER PRIMARY KEY,
            premise_id INTEGER,
            text TEXT,
            type TEXT,
            FOREIGN KEY (premise_id) REFERENCES premises(id)
        )
    ''')
    
    # Insert data
    cursor.execute(
        'INSERT INTO arguments (name, intro, conclusion) VALUES (?, ?, ?)',
        (arg.name, arg.intro, arg.conclusion)
    )
    arg_id = cursor.lastrowid
    
    for premise in arg.premises:
        cursor.execute(
            'INSERT INTO premises (argument_id, name, description) VALUES (?, ?, ?)',
            (arg_id, premise.name, premise.description)
        )
        premise_id = cursor.lastrowid
        
        for stmt in premise.statements:
            cursor.execute(
                'INSERT INTO statements (premise_id, text, type) VALUES (?, ?, ?)',
                (premise_id, stmt.text, 'statement')
            )
        
        for support in premise.support:
            cursor.execute(
                'INSERT INTO statements (premise_id, text, type) VALUES (?, ?, ?)',
                (premise_id, support, 'support')
            )
    
    conn.commit()
    conn.close()
```

---

## Troubleshooting

### Common Issues

#### "Module not found" Error

```bash
python -c "from difficult_dialogs import Argument"
# ModuleNotFoundError: No module named 'difficult_dialogs'
```

**Solution:**
```bash
# Install the package
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH=/path/to/difficult_dialogs:$PYTHONPATH
```

#### LLM Server Not Responding

```
ERROR: Server at http://localhost:8000 is not responding
```

**Solutions:**
1. Verify server is running:
   ```bash
   curl http://localhost:8000/health
   ```
2. Check firewall settings
3. Ensure correct port and IP address
4. Restart the LLM server

#### Generated Arguments Are Empty

**Cause:** LLM returned malformed JSON or timed out.

**Solutions:**
1. Increase timeout in generator:
   ```python
   gen = ArgumentGenerator(base_url, timeout=600.0)  # 10 minutes
   ```
2. Use a larger/faster model
3. Reduce depth parameter:
   ```python
   arg = gen.generate(topic, depth=1)  # Simpler argument
   ```
4. Check LLM server logs for errors

#### Arguments Don't Load

```
FileNotFoundError: Argument path does not exist
```

**Check:**
1. Path is correct (absolute vs relative)
2. Directory exists
3. Required files present (`intro.dialog`, `conclusion.conclusion`, at least one `.premise`)

#### Policy Doesn't Advance

**Symptom:** Bot repeats the same statement.

**Cause:** Statement cache not clearing between sessions.

**Solution:**
```python
policy = KnowItAllPolicy(arg)
policy.start()  # Resets the cache
```

### Getting Help

- **Documentation:** `/docs/` directory
- **Issues:** https://github.com/TigreGotico/difficult_dialogs/issues
- **Discussions:** https://github.com/TigreGotico/difficult_dialogs/discussions

---

## Examples

### Example 1: Educational Debate Tutor

**Topic:** Photosynthesis explanation

```bash
# Generate
python examples/generate_argument.py
Topic: Photosynthesis is essential for life on Earth

# Review and edit generated files
vim arguments/photosynthesis_essential/*/*.premise

# Deploy in classroom
python examples/run_argument.py arguments/photosynthesis_essential
```

### Example 2: Healthcare Patient Education

**Topic:** Vaccine safety

```python
from difficult_dialogs.llm import ArgumentGenerator

gen = ArgumentGenerator("http://hospital-llm.internal:8000")

arg = gen.generate(
    topic="Childhood vaccines are safe and effective",
    stance="pro",
    depth=3,
    include_sources=True,
    language="en"
)

# Medical review required before deployment
arg.save("patient_ed/vaccine_safety")
```

### Example 3: Customer Support Bot

**Topic:** Product refund policy

```python
# Manually create argument for precise control
from difficult_dialogs import Argument, Premise

arg = Argument(
    name="refund_policy",
    intro="I can help you understand our refund policy.",
    conclusion="Is there anything else about refunds you'd like to know?"
)

premise = Premise(
    name="eligibility",
    description="Refunds are available within 30 days of purchase"
)
premise.add_statement("Purchase must be within last 30 days")
premise.add_statement("Product must be in original condition")
premise.add_statement("Digital products have different rules")
premise.add_support("We understand circumstances change")
premise.add_support("Our goal is customer satisfaction")
premise.add_source("https://example.com/terms#refunds")

arg.add_premise(premise)

# Integrate with support system
# ... (see embedding examples above)
```

### Example 4: Multi-Language Support

Generate the same argument in different languages:

```python
languages = ["en", "es", "fr", "de", "zh"]

for lang in languages:
    arg = gen.generate(
        topic="Regular exercise improves mental health",
        language=lang
    )
    arg.save(f"arguments/exercise_mental_{lang}")
```

### Example 5: A/B Testing Arguments

Create multiple versions to test effectiveness:

```python
# Version A: Emotional appeal
arg_a = gen.generate(
    topic="Donate to charity",
    stance="pro",
    depth=2
)
# Edit to emphasize emotional stories
arg_a.save("arguments/charity_emotional")

# Version B: Logical appeal
arg_b = gen.generate(
    topic="Donate to charity",
    stance="pro",
    depth=2
)
# Edit to emphasize data and impact metrics
arg_b.save("arguments/charity_logical")

# Track which version converts better
```

---

## Next Steps

Now that you've mastered the basics:

1. **Read the Developer Guide** (`docs/DEVELOPER_GUIDE.md`) for API details
2. **Explore Examples** (`examples/` directory) for working code
3. **Join Discussions** on GitHub to share your use cases

Happy debating!
