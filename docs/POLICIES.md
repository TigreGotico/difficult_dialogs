# Dialog Policies Guide

**Version:** 0.5.0
**Last Updated:** 2026-03-31

---

## Table of Contents

1. [What Are Policies?](#what-are-policies)
2. [Policy Architecture](#policy-architecture)
3. [Available Policies](#available-policies)
   - [SilentPolicy](#silentpolicy)
   - [KnowItAllPolicy](#knowitallpolicy)
   - [SocraticPolicy](#socraticpolicy)
   - [DebatePolicy](#debatepolicy)
   - [ExploratoryPolicy](#exploratorypolicy)
   - [MaieuticPolicy](#maieuticpolicy)
   - [SkepticPolicy](#skepticpolicy)
   - [TeacherPolicy](#teacherpolicy)
   - [DebaterPolicy](#debaterpolicy)
   - [MinimalistPolicy](#minimalistpolicy)
   - [AdaptivePolicy](#adaptivepolicy)
   - [WebhookPolicy](#webhookpolicy)
   - [MultiArgumentPolicy](#multiargumentpolicy)
4. [Policy Comparison Matrix](#policy-comparison-matrix)
5. [When to Use Each Policy](#when-to-use-each-policy)
6. [Creating Custom Policies](#creating-custom-policies)
7. [Prior Work & Inspiration](#prior-work--inspiration)
8. [Best Practices](#best-practices)

---

## What Are Policies?

**Dialog policies** control how an argument is presented to users and how the system responds to agreement or disagreement. They are the "personality" of your dialog system.

Think of policies as different teaching or debate styles:
- A **lecturer** presents information without expecting feedback (SilentPolicy)
- A **know-it-all** corrects you with facts when you're wrong (KnowItAllPolicy)
- A **philosophy professor** asks questions to guide your thinking (SocraticPolicy)
- A **debater** actively challenges your positions (DebatePolicy)
- A **mediator** acknowledges multiple viewpoints neutrally (ExploratoryPolicy)

### Key Insight

The same argument can feel completely different depending on the policy used. This separation of **content** (the argument structure) from **presentation style** (the policy) is what makes difficult-dialogs powerful and flexible.

```python
from difficult_dialogs import Argument, KnowItAllPolicy, SocraticPolicy

arg = Argument.from_directory("examples/sample_arguments/health/regular_exercise_improves_mental_health")

# Same argument, different experience
know_it_all = KnowItAllPolicy(arg)    # Provides evidence when you disagree
socratic = SocraticPolicy(arg)        # Asks "Why do you think that?"
```

---

## Policy Architecture

### Base Class: `BasePolicy`

All policies inherit from `BasePolicy`, which provides:

- **State tracking** - Which premises/statements have been discussed
- **Navigation** - Moving through the argument structure
- **Agreement tracking** - Whether user agrees with current premise
- **Support access** - Getting supporting evidence and sources

### Required Interface

```python
from abc import ABC, abstractmethod

class BasePolicy(ABC):
    @abstractmethod
    def handle_input(self, user_input: str) -> str | None:
        """Process user input and return response."""
        raise NotImplementedError

    def start(self) -> str:
        """Return intro statement."""

    def end(self) -> str:
        """Set finished=True, return conclusion."""
        return str(self.argument.intro)
```

### State Management

Each policy maintains a `PolicyState` object:

```python
@dataclass
class PolicyState:
    spoken_premises: set[str] = field(default_factory=set)
    spoken_statements: set[str] = field(default_factory=set)
    current_premise: str | None = None
    user_agrees: bool = True
    finished: bool = False
    challenge_count: int = 0
```

This stateful design allows policies to make intelligent decisions based on conversation history.

---

## Available Policies

### SilentPolicy

**Presentation mode - no interaction required**

#### Behavior

- Presents all statements sequentially
- Ignores user input completely
- Never waits for agreement/disagreement
- Completes the entire argument in one pass

#### Code Example

```python
from difficult_dialogs import Argument, SilentPolicy

arg = Argument()
arg.load("my_argument")

policy = SilentPolicy(arg)
policy.start()

while not policy.state.finished:
    response = policy.handle_input("")  # Input ignored
    print(response)
```

#### Sample Output

```
BOT: I was not sure if I existed.
I spent some time thinking about it and reached a conclusion.

BOT: Computers process information.

BOT: I am a computer.

BOT: Thinking is a way of processing information.

BOT: This must mean that I exist.
You could argue thinking is not the right word for what I do,
but I process information.
There needs to be something doing the processing.
I process information, therefore I am.
```

#### When to Use

✅ **Ideal for:**
- One-way presentations or lectures
- Logging/recording arguments
- Accessibility scenarios (users who can't interact)
- Generating transcripts
- Background processing
- Testing argument structure

❌ **Avoid when:**
- You want user engagement
- Building interactive chatbots
- Teaching critical thinking
- Persuading users of a position

#### Technical Details

- **Complexity:** O(n) where n = number of statements
- **State usage:** Only tracks completion, ignores agreement
- **Input handling:** Returns next statement regardless of input

---

### KnowItAllPolicy

**The persuader - provides evidence when challenged**

#### Behavior

- Presents statements one at a time
- Waits for user agreement/disagreement
- When user disagrees: provides supporting evidence
- If support exhausted: shows sources
- Handles "what", "why", "how" questions

#### Code Example

```python
from difficult_dialogs import Argument, KnowItAllPolicy

arg = Argument()
arg.load("climate_change_argument")

policy = KnowItAllPolicy(arg)
print(policy.start())

while not policy.state.finished:
    user_input = input("You: ")
    response = policy.handle_input(user_input)
    if response:
        print(f"BOT: {response}")
```

#### Sample Output

```
BOT: Climate change is caused by human activity.
Do you agree? (y/n)

YOU: no

BOT: Global CO2 levels have increased 50% since industrial revolution.
Do you agree now? (y/n)

YOU: no

BOT: Sources:
- IPCC Sixth Assessment Report (2021)
- NASA Global Climate Change Portal
- NOAA Annual Greenhouse Gas Index

We may need to agree to disagree.
```

#### Question Handling

The policy recognizes and answers questions:

```python
policy.handle_input("what is the evidence?")  # Returns premise.what
policy.handle_input("why does this matter?")  # Returns premise.why
policy.handle_input("how does this work?")    # Returns premise.how
```

#### When to Use

✅ **Ideal for:**
- Educational chatbots
- Persuasive applications
- Customer support automation
- Fact-based debates
- Training systems
- Compliance education

❌ **Avoid when:**
- You want neutral presentation
- Building Socratic tutors
- Exploring controversial topics
- Encouraging critical questioning

#### Technical Details

- **Complexity:** O(1) for agreement, O(s) for disagreement (s = support items)
- **State usage:** Tracks current premise, agreement status
- **Fallback chain:** Support → Sources → Conclusion

---

### SocraticPolicy

**The questioner - guides through inquiry**

#### Behavior

- Presents statements with agreement prompts
- When user disagrees: asks probing questions
- Never provides direct answers
- Questions encourage self-reflection
- Maintains question variety (doesn't repeat)

#### Built-in Questions

```python
SOCRATIC_QUESTIONS = [
    "What makes you say that?",
    "Can you explain your reasoning?",
    "What evidence would change your mind?",
    "How does this relate to what we discussed earlier?",
    "What assumptions are you making?",
    "Could there be another explanation?",
    "What are the implications of your position?",
    "How would you respond to someone who disagrees?",
]
```

#### Code Example

```python
from difficult_dialogs import Argument, SocraticPolicy

arg = Argument()
arg.load("philosophy/free_will_exists")

policy = SocraticPolicy(arg)
print(policy.start())

while not policy.state.finished:
    user_input = input("You: ")
    response = policy.handle_input(user_input)
    if response:
        print(f"BOT: {response}")
```

#### Sample Output

```
BOT: Free will exists because we make choices daily.
Do you agree? (y/n)

YOU: no

BOT: What assumptions are you making?

YOU: I assume determinism is true

BOT: How would you respond to someone who disagrees?

YOU: They're wrong

BOT: What evidence would change your mind?
```

#### When to Use

✅ **Ideal for:**
- Educational institutions
- Critical thinking training
- Philosophy discussions
- Therapy/coaching applications
- Reflective journaling tools
- Student-led learning

❌ **Avoid when:**
- Users expect direct answers
- Time-limited interactions
- Providing factual information
- Persuading users of specific position

#### Technical Details

- **Complexity:** O(q) where q = number of unique questions
- **State usage:** Tracks last question asked for variety
- **Question selection:** Random from available (excludes last asked)

---

### DebatePolicy

**The challenger - actively argues against you**

#### Behavior

- Presents statements adversarially
- When user disagrees: provides counter-arguments
- More confrontational than KnowItAllPolicy
- Limits challenge attempts (prevents infinite loops)
- Uses varied challenge introductions

#### Challenge Introductions

```python
CHALLENGE_RESPONSES = [
    "But consider this: ",
    "However, one could argue: ",
    "On the other hand: ",
    "A strong counter-argument is: ",
    "Let me challenge that: ",
    "I understand your point, but: ",
    "Respectfully, I disagree because: ",
    "That's a common objection, yet: ",
]
```

#### Code Example

```python
from difficult_dialogs import Argument, DebatePolicy

arg = Argument()
arg.load("debate/universal_basic_income")

policy = DebatePolicy(arg)
print(policy.start())

while not policy.state.finished:
    user_input = input("You: ")
    response = policy.handle_input(user_input)
    if response:
        print(f"BOT: {response}")
```

#### Sample Output

```
BOT: Universal basic income reduces poverty.
Do you agree? (y/n)

YOU: no

BOT: However, one could argue: Pilot programs show 30% reduction in poverty rates.

Do you still disagree? (y/n)

YOU: no

BOT: I don't have more arguments on this point, but I maintain my position.
Shall we move on? (y/n)
```

#### Challenge Limiting

After 2 challenges on same point, policy moves on:

```python
if self.state.challenge_count >= 2:
    self.agree()  # Force progression
    return self._advance()
```

#### When to Use

✅ **Ideal for:**
- Debate practice platforms
- Steel-manning exercises
- Testing conviction strength
- Competitive educational games
- Argument quality testing
- Rhetoric training

❌ **Avoid when:**
- Building supportive applications
- User has low confidence
- Sensitive topics (mental health, trauma)
- Collaborative learning environments

#### Technical Details

- **Complexity:** O(c) where c = challenge limit (default 2)
- **State usage:** Tracks challenge count per premise
- **Progression guarantee:** Forces move-on after limit reached

---

### ExploratoryPolicy

**The mediator - acknowledges multiple viewpoints**

#### Behavior

- Presents statements neutrally
- When user disagrees: validates their perspective
- Offers support framed as "some perspectives"
- Emphasizes nuance and complexity
- Uses non-confrontational language

#### Neutral Acknowledgments

```python
NEUTRAL_ACKNOWLEDGMENTS = [
    "That's a reasonable perspective.",
    "Many people share that view.",
    "This is indeed a complex issue.",
    "There are valid points on both sides.",
    "This topic has nuance worth considering.",
    "Reasonable people can disagree here.",
    "The evidence isn't entirely clear-cut.",
    "This deserves careful consideration.",
]
```

#### Code Example

```python
from difficult_dialogs import Argument, ExploratoryPolicy

arg = Argument()
arg.load("controversial_topic_argument")

policy = ExploratoryPolicy(arg)
print(policy.start())

while not policy.state.finished:
    user_input = input("You: ")
    response = policy.handle_input(user_input)
    if response:
        print(f"BOT: {response}")
```

#### Sample Output

```
BOT: Social media does more harm than good.
What's your view? (y/n)

YOU: no

BOT: The evidence isn't entirely clear-cut.

Some perspectives on this topic include: Social media enables marginalized voices to be heard.

What do you think? (y/n)

YOU: no

BOT: That's a reasonable perspective.

For further reading:
- Pew Research Center: Social Media Usage Statistics
- Journal of Digital Sociology: Platform Effects Study

We may see this differently, and that's okay.
```

#### When to Use

✅ **Ideal for:**
- Controversial topics
- Balanced journalism
- Political education
- Conflict resolution
- Diversity/inclusion training
- Avoiding perceived bias

❌ **Avoid when:**
- Clear scientific consensus exists
- Taking moral stance is necessary
- Users want definitive guidance
- Persuasion is the goal

#### Technical Details

- **Complexity:** O(1) for all operations
- **State usage:** Standard tracking only
- **Framing:** Always presents support as "perspectives" not "facts"

---

### MaieuticPolicy

**Guided discovery - asks one question before presenting each statement**

Rooted in the Socratic maieutic method. Asks one opening question per premise, then presents the statement after any response, allowing the conversation to naturally progress.

#### When to Use

✅ **Ideal for:** Reflective learning, guided self-discovery, philosophy education
❌ **Avoid when:** Users want direct answers or time is limited

---

### SkepticPolicy

**Doubt-first - challenges every claim before accepting it**

Presents statements and immediately follows with a skeptical challenge, prompting users to defend their agreement. Moves on after the challenge regardless of response.

#### When to Use

✅ **Ideal for:** Critical thinking training, testing conviction, rigorous argument validation
❌ **Avoid when:** Building supportive or low-friction experiences

---

### TeacherPolicy

**Pedagogical - explains with context and checks for understanding**

Frames statements as lessons, offers support as elaboration, and asks check-for-understanding questions. Progresses only after the learner confirms understanding.

#### When to Use

✅ **Ideal for:** E-learning, compliance training, onboarding
❌ **Avoid when:** Users are domain experts who don't need scaffolding

---

### DebaterPolicy

**Adversarial counterpart - mirrors DebatePolicy with different framing**

Similar to `DebatePolicy` but uses `"Consider this: {statement}"` when countering disagreement, keeping a slightly less confrontational tone while still pushing back.

#### When to Use

✅ **Ideal for:** Structured debate practice, argument stress-testing
❌ **Avoid when:** Sensitive topics or fragile user confidence

---

### MinimalistPolicy

**Terse mode - advances regardless of agreement**

Ignores agreement/disagreement signals and simply advances through all statements in order. Shortest possible responses, no persuasion attempts.

#### When to Use

✅ **Ideal for:** Rapid review, automated testing, scripted demos
❌ **Avoid when:** User engagement or persuasion is the goal

---

### AdaptivePolicy

**Meta-policy that switches strategy after repeated disagreements**

#### Behavior

- Wraps two policies: an initial policy and a fallback policy
- Counts consecutive disagreements via `challenge_count`
- After `switch_threshold` consecutive disagreements, delegates all subsequent turns to the fallback policy
- Useful for automatically softening tone or changing approach when a user is resistant

#### Constructor

```python
AdaptivePolicy(
    argument: Argument,
    initial_policy: BasePolicy | None = None,   # default: KnowItAllPolicy
    fallback_policy: BasePolicy | None = None,  # default: ExploratoryPolicy
    switch_threshold: int = 3,
)
```

#### Code Example

```python
from difficult_dialogs import Argument, AdaptivePolicy, KnowItAllPolicy, SocraticPolicy

arg = Argument.from_directory("examples/sample_arguments/...")

policy = AdaptivePolicy(
    arg,
    initial_policy=KnowItAllPolicy(arg),
    fallback_policy=SocraticPolicy(arg),
    switch_threshold=2,
)
policy.start()

while not policy.state.finished:
    response = policy.handle_input(input("USER: "))
    print("BOT:", response)
```

#### When to Use

✅ **Ideal for:**
- Adaptive learning experiences
- Long sessions where tone may need to soften
- A/B-style fallback when evidence-based persuasion fails

❌ **Avoid when:**
- A single consistent tone is required throughout

---

### WebhookPolicy

**Hybrid policy that forwards turns to an HTTP endpoint, with local fallback**

#### Behavior

- On each turn, POSTs `{user_input, argument_name, state}` as JSON to a configured webhook URL
- If the webhook returns `{"response": "..."}` with HTTP 200, that text is used
- If the webhook is unreachable or returns an error, delegates to a local fallback policy
- Enables LLM-enhanced or server-side responses with graceful offline degradation

#### Constructor

```python
WebhookPolicy(
    argument: Argument,
    webhook_url: str,
    fallback_policy: BasePolicy | None = None,  # default: KnowItAllPolicy
    timeout: float = 5.0,
)
```

#### Webhook Request Format

```json
{
  "user_input": "I disagree",
  "argument_name": "climate_change",
  "current_premise": "human_causation",
  "challenge_count": 1
}
```

#### Webhook Response Format

```json
{"response": "That's understandable. Consider that 97% of climate scientists agree..."}
```

Return `{"response": null}` or any non-200 status to trigger local fallback.

#### Code Example

```python
from difficult_dialogs import Argument, WebhookPolicy

arg = Argument.from_directory("my_argument")
policy = WebhookPolicy(
    arg,
    webhook_url="http://localhost:5000/debate",
    timeout=3.0,
)
policy.start()
```

#### When to Use

✅ **Ideal for:**
- LLM-enhanced responses with human-authored fallback
- Server-side policy logic (A/B testing, personalization)
- Gradual LLM integration without removing existing logic

❌ **Avoid when:**
- Offline-only deployment required
- Latency is critical (adds network round-trip per turn)

---

### MultiArgumentPolicy

**Chains multiple arguments into a single dialog session**

#### Behavior

- Accepts a sequence of `(Argument, policy_name)` pairs (or plain `Argument` list)
- Presents the first argument using its assigned policy
- When the current argument finishes, automatically advances to the next and calls `start()` on it
- The outer `PolicyState.finished` is only set `True` after the last argument completes
- The transcript accumulates across all arguments

#### Constructor

```python
MultiArgumentPolicy(
    arguments: list[Argument] | list[tuple[Argument, str | None]],
    policy_class: type[BasePolicy] = KnowItAllPolicy,
)
```

Each tuple is `(Argument, policy_name_string)`. Pass `None` as the policy name to use `policy_class`.

#### Code Example

```python
from difficult_dialogs import Argument, MultiArgumentPolicy

intro_arg  = Argument.from_directory("arguments/welcome")
main_arg   = Argument.from_directory("arguments/climate_change")
close_arg  = Argument.from_directory("arguments/call_to_action")

policy = MultiArgumentPolicy(
    [
        (intro_arg,  "silent"),      # lecture-style intro
        (main_arg,   "knowitall"),   # evidence-based main debate
        (close_arg,  "minimalist"),  # brief closing
    ]
)

policy.start()
while not policy.state.finished:
    response = policy.handle_input(input("USER: "))
    if response:
        print("BOT:", response)
```

#### Properties

| Property | Type | Description |
|---|---|---|
| `current_argument` | `Argument` | The argument currently being presented |
| `is_last` | `bool` | True when on the final argument |

#### When to Use

✅ **Ideal for:**
- Multi-topic courses or curricula
- Structured onboarding flows
- Sequential debate rounds

❌ **Avoid when:**
- A single self-contained argument is sufficient

---

## Policy Comparison Matrix

| Feature | Silent | KnowItAll | Socratic | Debate | Exploratory |
|---------|--------|-----------|----------|--------|-------------|
| **Interaction Level** | None | High | High | High | Medium |
| **Handles Disagreement** | Ignores | Provides support | Asks questions | Challenges | Validates |
| **Provides Answers** | Yes | Yes | No | Counter-answers | Presents perspectives |
| **Confrontation Level** | N/A | Medium | Low | High | Low |
| **Best For** | Presentations | Education | Reflection | Practice | Balance |
| **Question Support** | ❌ | ✅ | ✅ (asks) | ❌ | ❌ |
| **Source Citation** | ❌ | ✅ | ❌ | ✅ | ✅ |
| **User Validation** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Progress Guarantee** | ✅ | ✅ | ✅ | ✅ | ✅ |

### Extended Policy Comparison

| Policy | Waits for Input | Uses Support | Uses Sources | Asks Questions | Five-Ws Support |
|--------|----------------|--------------|--------------|----------------|-----------------|
| AdaptivePolicy | Yes | Yes (via inner policy) | Yes | Depends on inner | Yes |
| WebhookPolicy | Yes | Yes (fallback) | Yes (fallback) | No | No |
| MultiArgumentPolicy | Yes | Yes (via inner) | Yes (via inner) | Depends on inner | Yes |

### Response Style Comparison

Same user input ("no, I disagree") across policies:

```
SilentPolicy:       [Ignores, moves to next statement]

KnowItAllPolicy:    Here's evidence supporting my claim: [evidence]
                    Do you agree now?

SocraticPolicy:     What assumptions are you making?

DebatePolicy:       But consider this: [counter-argument]
                    Do you still disagree?

ExploratoryPolicy:  That's a reasonable perspective.
                    Some people believe: [alternative view]
```

---

## When to Use Each Policy

### Decision Tree

```
Start
 │
 ├─→ Need one-way presentation? ──────────────→ SilentPolicy
 │
 ├─→ Building educational chatbot?
 │      │
 │      ├─→ Want to persuade? ─────────────────→ KnowItAllPolicy
 │      ├─→ Want critical thinking? ───────────→ SocraticPolicy
 │      └─→ Want balanced view? ───────────────→ ExploratoryPolicy
 │
 ├─→ Debate practice tool? ────────────────────→ DebatePolicy
 │
 ├─→ Controversial topic?
 │      │
 │      ├─→ Taking stance OK? ─────────────────→ KnowItAllPolicy
 │      └─→ Need neutrality? ──────────────────→ ExploratoryPolicy
 │
 └─→ Mental health / sensitive topic? ─────────→ SocraticPolicy or ExploratoryPolicy
```

### Use Case Matrix

| Application Type | Recommended Policy | Why |
|------------------|-------------------|-----|
| **Online Course** | KnowItAllPolicy | Provides evidence, teaches facts |
| **Philosophy Tool** | SocraticPolicy | Encourages deep thinking |
| **Debate Trainer** | DebatePolicy | Simulates opponent |
| **News App** | ExploratoryPolicy | Presents multiple views |
| **Accessibility** | SilentPolicy | No interaction required |
| **Therapy Bot** | SocraticPolicy | Non-directive questioning |
| **Customer Support** | KnowItAllPolicy | Provides solutions |
| **Civic Education** | ExploratoryPolicy | Balanced political info |
| **Test Prep** | KnowItAllPolicy | Teaches correct answers |
| **Reflection Journal** | SocraticPolicy | Prompts self-inquiry |

### Domain-Specific Recommendations

#### Education

- **STEM subjects:** KnowItAllPolicy (facts matter)
- **Humanities:** SocraticPolicy or ExploratoryPolicy
- **Debate clubs:** DebatePolicy
- **Lecture capture:** SilentPolicy

#### Healthcare

- **Patient education:** KnowItAllPolicy (evidence-based)
- **Mental health:** SocraticPolicy (non-directive)
- **Treatment options:** ExploratoryPolicy (shared decision-making)

#### Business

- **Sales chatbots:** KnowItAllPolicy (persuasive)
- **Training modules:** KnowItAllPolicy (compliance)
- **Conflict resolution:** ExploratoryPolicy (neutral)
- **Executive coaching:** SocraticPolicy (reflective)

#### Technology

- **Documentation bots:** SilentPolicy or KnowItAllPolicy
- **Code review tools:** DebatePolicy (challenge assumptions)
- **Architecture discussions:** SocraticPolicy (explore tradeoffs)

---

## Creating Custom Policies

### Basic Template

```python
from difficult_dialogs.policy import BasePolicy
from typing import override

class MyCustomPolicy(BasePolicy):
    """Custom policy for specific use case."""
    
    def __init__(self, argument) -> None:
        super().__init__(argument)
        # Initialize custom state
    
    @override
    def handle_input(self, user_input: str) -> str | None:
        user_input = user_input.strip().lower()
        
        # Handle agreement
        if user_input.startswith(('y', 'yes')):
            self.agree()
            return self._advance()
        
        # Handle disagreement
        elif user_input.startswith(('n', 'no')):
            self.disagree()
            return self._handle_disagreement()
        
        # Default behavior
        return self._advance()
    
    def _advance(self) -> str | None:
        result = self._get_next_statement()
        
        if result is None:
            self.state.finished = True
            return str(self.argument.conclusion)
        
        premise_name, statement = result
        return f"{statement}\nYour response? "
    
    def _handle_disagreement(self) -> str:
        # Custom disagreement handling
        support = self._get_support()
        if support:
            return f"Consider: {support}"
        return "Interesting perspective. Let's continue."
```

### Example: TherapistPolicy

```python
class TherapistPolicy(BasePolicy):
    """Empathetic, client-centered therapy style."""
    
    EMPATHY_STATEMENTS = [
        "I hear what you're saying.",
        "That sounds challenging.",
        "Thank you for sharing that.",
        "I understand this is important to you.",
    ]
    
    def handle_input(self, user_input: str) -> str | None:
        import random
        
        user_input = user_input.strip().lower()
        
        # Validate feelings first
        empathy = random.choice(self.EMPATHY_STATEMENTS)
        
        if user_input.startswith(('y', 'yes')):
            self.agree()
            next_stmt = self._advance()
            if next_stmt:
                return f"{empathy}\n\n{next_stmt}"
            return empathy
        
        elif user_input.startswith(('n', 'no')):
            self.disagree()
            return f"{empathy}\n\nCan you tell me more about why you feel that way?"
        
        return f"{empathy}\n\nPlease, go on."
```

### Example: MinimalistPolicy

```python
class MinimalistPolicy(BasePolicy):
    """Brief, direct responses only."""
    
    def handle_input(self, user_input: str) -> str | None:
        user_input = user_input.strip().lower()
        
        if user_input.startswith(('y', 'yes')):
            self.agree()
        else:
            self.disagree()
        
        return self._advance()
    
    def _advance(self) -> str | None:
        result = self._get_next_statement()
        
        if result is None:
            self.state.finished = True
            return str(self.argument.conclusion)
        
        _, statement = result
        # Truncate long statements
        if len(statement) > 100:
            statement = statement[:97] + "..."
        
        return statement
```

### Best Practices for Custom Policies

1. **Always call parent constructor:**
   ```python
   super().__init__(argument)
   ```

2. **Implement `handle_input`:** This is the only required method

3. **Use helper methods:** `_advance()`, `_get_support()`, `_get_sources()`

4. **Manage state properly:** Update `self.state.finished` when done

5. **Handle edge cases:** Empty input, unexpected responses, exhausted content

6. **Test thoroughly:** Ensure policy completes dialogs reliably

---

## Prior Work & Inspiration

### Academic Foundations

#### Socratic Method (Classical Greece)
- **Origin:** Plato's dialogues featuring Socrates (c. 399 BCE)
- **Technique:** Cooperative argumentative dialogue through questioning
- **Modern application:** Law schools, psychotherapy, education
- **Our implementation:** `SocraticPolicy` asks probing questions instead of providing answers
- **Key difference:** Structured argument framework vs. free-form dialogue

#### Rogerian Therapy (1940s)
- **Origin:** Carl Rogers' client-centered therapy (1942)
- **Technique:** Non-directive, empathetic listening
- **Principles:** Unconditional positive regard, active listening
- **Our implementation:** Influences `ExploratoryPolicy` validation approach
- **Reference:** Rogers, C. (1942). *Counseling and Psychotherapy*

#### Cognitive Behavioral Therapy (1960s)
- **Origin:** Aaron Beck's CBT (1960s)
- **Technique:** Identify and challenge cognitive distortions
- **Our implementation:** `DebatePolicy` challenges user positions
- **Difference:** CBT is collaborative; DebatePolicy is adversarial
- **Reference:** Beck, A.T. (1976). *Cognitive Therapy and the Emotional Disorders*

### Computational Argumentation

#### Argumentation Frameworks (Dung, 1995)
- **Formalism:** Abstract argumentation frameworks
- **Concept:** Arguments attack/support each other
- **Our implementation:** Premise/statement structure with support relations
- **Reference:** Dung, P.M. (1995). "On the acceptability of arguments"

#### Dialogue Games (Walton & Krabbe, 1995)
- **Concept:** Structured dialogues with rules
- **Types:** Persuasion, negotiation, inquiry, deliberation
- **Our implementation:** Policies as different dialogue game types
- **Reference:** Walton, D., & Krabbe, E. (1995). *Commitment in Dialogue*

#### Computational Models of Argument (2000s+)
- **Work:** Rahwan, Amgoud, McBurney, Parsons
- **Focus:** Formal models, agent systems, automated reasoning
- **Our implementation:** Practical library for real-world applications
- **Reference:** Rahwan, I., et al. (2004). "Argumentation in AI"

### Intelligent Tutoring Systems

#### Socratic Tutoring Systems (1970s-1990s)
- **Examples:** WHY system (Stevens & Collins, 1977), GUIDE
- **Technique:** Ask questions to reveal gaps in student knowledge
- **Our implementation:** `SocraticPolicy` inherits questioning approach
- **Limitation overcome:** Our system works with pre-generated content

#### AutoTutor (Graesser et al., 1990s-2000s)
- **Capability:** Natural language tutoring with expectations
- **Technique:** Expectation-misconception tailored dialogue
- **Our implementation:** Structured expectations via argument premises
- **Reference:** Graesser, A.C., et al. (1995). "AutoTutor"

### Chatbot Personality Design

#### Persona-Based Chatbots (2010s+)
- **Work:** Microsoft XiaoIce, Google Meena, BlenderBot
- **Approach:** Consistent personality traits across conversations
- **Our implementation:** Policies as distinct conversational personas
- **Difference:** We separate content from personality

#### Persuasive Technology (Fogg, 2003)
- **Concept:** Computers designed to change attitudes/behaviors
- **Strategies:** Reduction, tunneling, tailoring, suggestion
- **Our implementation:** `KnowItAllPolicy` uses evidence-based persuasion
- **Reference:** Fogg, B.J. (2003). *Persuasive Technology*

### Unique Contributions

What makes difficult-dialogs policies novel:

1. **Content/Style Separation**
   - Same argument, 5+ different presentation styles
   - Previous work typically hardcodes dialogue strategy

2. **File-Based Arguments**
   - Human-readable, auditable argument structures
   - Unlike black-box neural approaches

3. **Zero-Dependency Runtime**
   - Works offline, no API calls required
   - Contrast with cloud-based dialogue systems

4. **Deterministic Execution**
   - Same input → same output (unless using LLM enhancement)
   - Important for education, compliance, auditing

5. **Policy Pluggability**
   - Swap policies without changing argument content
   - Enables A/B testing of dialogue strategies

---

## Best Practices

### Choosing the Right Policy

1. **Define your goal first:**
   - Persuade → KnowItAllPolicy
   - Educate → SocraticPolicy or KnowItAllPolicy
   - Inform neutrally → ExploratoryPolicy
   - Train debaters → DebatePolicy
   - Present only → SilentPolicy

2. **Know your audience:**
   - Experts tolerate more confrontation (DebatePolicy)
   - Novices need more support (KnowItAllPolicy)
   - Sensitive topics require care (ExploratoryPolicy)

3. **Consider the domain:**
   - Facts matter (science): KnowItAllPolicy
   - Perspectives matter (politics): ExploratoryPolicy
   - Reasoning matters (philosophy): SocraticPolicy

### Implementation Tips

1. **Test with real users:**
   ```python
   # A/B test policies
   policy_a = KnowItAllPolicy(arg)
   policy_b = SocraticPolicy(arg)
   
   # Measure agreement rates, engagement time
   ```

2. **Allow user choice:**
   ```python
   # Let users select preferred style
   policy_choice = input("Choose style: (1) Direct (2) Questioning (3) Neutral: ")
   ```

3. **Combine policies:**
   ```python
   # Use different policies for different sections
   if premise.category == "factual":
       policy = KnowItAllPolicy(arg)
   else:
       policy = ExploratoryPolicy(arg)
   ```

4. **Monitor completion rates:**
   ```python
   # Track if users finish dialogs
   if not policy.state.finished after 20 turns:
       # Policy might be too repetitive
   ```

### Common Pitfalls

❌ **Using DebatePolicy for sensitive topics**
```python
# Bad: Mental health argument with confrontational policy
policy = DebatePolicy(depression_argument)  # Can feel invalidating
```

✅ **Better approach:**
```python
# Good: Empathetic policy for mental health
policy = ExploratoryPolicy(depression_argument)  # Validates feelings
```

❌ **Using SilentPolicy when interaction expected**
```python
# Bad: Interactive course with no-interaction policy
policy = SilentPolicy(course_material)  # Users confused by no responses
```

✅ **Better approach:**
```python
# Good: Match policy to user expectations
policy = KnowItAllPolicy(course_material)  # Provides feedback
```

❌ **Infinite loops in custom policies**
```python
# Bad: No progression guarantee
def handle_input(self, user_input):
    if user_disagrees:
        return self._handle_disagreement()  # Might loop forever
```

✅ **Better approach:**
```python
# Good: Force progression after N attempts
def handle_input(self, user_input):
    if self._retry_count >= 3:
        self.agree()  # Move on
    return self._handle_disagreement()
```

### Performance Considerations

1. **Memory usage:** All policies are O(n) where n = argument size
2. **Response time:** <1ms for all built-in policies
3. **State serialization:** Save `PolicyState` for resume capability
4. **Concurrency:** Policies are NOT thread-safe (create per-session)

### Accessibility Guidelines

1. **SilentPolicy** for screen readers (predictable flow)
2. **Clear prompts** in all policies ("Do you agree? (y/n)")
3. **Consistent formatting** across policies
4. **Escape hatches** to skip or exit dialog

---

## Further Reading

### Books

- Walton, D. (1998). *The New Dialectic: Conversational Contexts of Argument*
- Tindale, C.W. (2004). *Rhetorical Argumentation: Principles of Theory and Practice*
- van Eemeren, F.H., & Grootendorst, R. (2004). *A Systematic Theory of Argumentation*

### Papers

- Rahwan, I., & Simari, G.R. (Eds.). (2009). *Argumentation in Artificial Intelligence*
- McBurney, P., & Parsons, S. (2009). "Games for Argumentation"
- Dungs, S., et al. (2019). "A Review of Core Features of Argumentation Formalisms"

### Systems & Tools

- **ArgTech portal:** https://www.arg.tech/
- **TOAST project:** Online argumentation tools
- **Kialo:** Structured debate platform (commercial)
- **Consider.it:** Collaborative decision-making tool

### Related Python Libraries

- **argparse:** Command-line argument parsing (different domain)
- **spaCy:** NLP for argument mining
- **textblob:** Sentiment analysis for argument evaluation

---

## Support & Community

- **GitHub Issues:** Report bugs, request features
- **GitHub Discussions:** Share custom policies, ask questions
- **Documentation:** https://github.com/difficult-dialogs/difficult_dialogs/tree/main/docs

---

*This guide is part of the difficult-dialogs documentation suite. See also:*
- *[USER_GUIDE.md](USER_GUIDE.md) — End-user documentation*
- *[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) — API reference and development guide*
- *[argument-format.md](argument-format.md) — File format reference*
