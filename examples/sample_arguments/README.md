# Sample Argument Library

A collection of 30 ready-to-run debate arguments for testing and demonstration.

---

## Quick Start

### Option 1: Command Line (Text-based)
```bash
# List all available arguments
ls examples/sample_arguments/

# Run an argument
python examples/run_argument.py examples/sample_arguments/<category>/<topic>

# Example
python examples/run_argument.py examples/sample_arguments/health/exercise_improves_mental_health
```

### Option 2: Web Interface (Recommended for Demos)
```bash
# Install Streamlit
pip install streamlit

# Launch web demo
streamlit run examples/streamlit_demo.py
```

This opens a beautiful web interface at `http://localhost:8501` where you can:
- Browse arguments by category
- Click through debates with Agree/Disagree buttons
- See real-time progress tracking
- View argument structure visually

---

## Available Arguments by Category

### 💻 Technology (5 arguments)
- Artificial intelligence will benefit humanity
- Open source software is superior to proprietary
- Privacy is more important than convenience
- Remote work increases productivity
- Social media does more harm than good

### 🔬 Science (5 arguments)
- Climate change requires immediate action
- Space exploration is worth the cost
- Vaccines are safe and effective
- Genetic engineering should be regulated
- Renewable energy can replace fossil fuels

### 🏥 Health (5 arguments)
- Regular exercise improves mental health
- A plant-based diet is healthier
- Sleep is essential for cognitive function
- Meditation reduces stress effectively
- Preventive care is better than treatment

### 🌍 Society (5 arguments)
- Universal basic income would reduce poverty
- Higher education should be free
- Cities should prioritize public transportation
- Recycling programs are effective
- Volunteering benefits both giver and receiver

### 🤔 Philosophy (5 arguments)
- I think therefore I am
- The ends justify the means
- Free will exists
- Happiness is the highest good
- Knowledge is more valuable than pleasure

### 📚 Education (5 arguments)
- Critical thinking should be taught in schools
- Standardized tests don't measure intelligence
- Lifelong learning is essential in modern society
- Teachers should be paid more
- Online learning is as effective as in-person

---

## Statistics

| Category | Arguments | Total Premises | Avg Complexity |
|----------|-----------|----------------|----------------|
| Technology | 5 | ~10 | Medium |
| Science | 5 | ~10 | Medium |
| Health | 5 | ~10 | Medium |
| Society | 5 | ~10 | Medium |
| Philosophy | 5 | ~10 | Medium |
| Education | 5 | ~10 | Medium |
| **Total** | **30** | **~60** | **-** |

*All arguments generated with LLM and ready for use.*

---

## Generate Your Own

Use the batch generator to create more arguments:

```bash
cd examples
python batch_generate.py
```

Configuration in `batch_generate.py`:
```python
LLM_URL = "http://192.168.1.200:8000"  # Your server
MODEL_NAME = "qwen-72b"                 # Your model
```

---

## File Structure

Each argument follows this format:

```
argument_name/
├── intro.dialog              # Opening statement
├── conclusion.conclusion     # Final statement
└── premise_name/
    ├── description.premise   # Core claims
    ├── support.support       # Fallback arguments
    ├── source.source         # Evidence URLs
    ├── what                  # Explanations
    ├── why                   # Explanations
    └── how                   # Explanations
```

---

## Usage Examples

### Simple Test Run

```bash
# Just see if it works
python examples/run_argument.py examples/sample_arguments/health/exercise_improves_mental_health
```

### Always Agree

```bash
echo -e "y\ny\ny\ny" | python examples/run_argument.py examples/sample_arguments/health/exercise_improves_mental_health
```

### Always Disagree

```bash
echo -e "n\nn\nn\nn" | python examples/run_argument.py examples/sample_arguments/health/exercise_improves_mental_health
```

### Mixed Responses

```bash
echo -e "y\nn\ny\nn" | python examples/run_argument.py examples/sample_arguments/health/exercise_improves_mental_health
```

---

## License

All sample arguments are provided under the same Apache 2.0 license as the main project.

Feel free to use, modify, and distribute for any purpose.

---

Happy debating!
