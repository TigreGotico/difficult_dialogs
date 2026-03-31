#!/usr/bin/env python3
"""Quick test of LLM argument generation."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from difficult_dialogs.llm.client import LLMClient
from difficult_dialogs.llm.generator import ArgumentGenerator

LLM_URL = "http://192.168.1.200:8000"

print("Testing LLM integration...")
print(f"Server: {LLM_URL}")
print()

# Test 1: Simple generation
print("Test 1: Simple text generation")
client = LLMClient(LLM_URL)
try:
    response = client.generate("What is 2+2? Answer in one word.")
    print(f"✓ Response: {response.text}")
except Exception as e:
    print(f"✗ Failed: {e}")

print()

# Test 2: JSON generation
print("Test 2: Structured JSON generation")
try:
    data = client.generate_json(
        prompt="List 3 fruits",
        schema={"type": "object", "properties": {"fruits": {"type": "array", "items": {"type": "string"}}}}
    )
    print(f"✓ JSON: {data}")
except Exception as e:
    print(f"✗ Failed: {e}")

print()

# Test 3: Full argument generation
print("Test 3: Generate complete argument (this may take 30-60s)")
topic = "Solar energy is cost-effective"
print(f"Topic: {topic}")

try:
    generator = ArgumentGenerator(LLM_URL, timeout=120.0)
    
    print("Generating structure...")
    arg = generator.generate(
        topic=topic,
        stance="pro",
        depth=1,  # Keep it simple for testing
        include_sources=False,  # Skip sources for speed
        include_counterarguments=True
    )
    
    print(f"✓ Generated argument!")
    print(f"  Name: {arg.name}")
    print(f"  Intro: {arg.intro[:80]}...")
    print(f"  Premises: {len(arg.premises)}")
    
    for p in arg.premises:
        print(f"    - {p.name}: {len(p.statements)} statements, {len(p.support)} support")
    
    # Save it
    output_dir = Path("examples/generated_test")
    output_dir.mkdir(exist_ok=True)
    
    (output_dir / "intro.dialog").write_text(arg.intro)
    (output_dir / "conclusion.conclusion").write_text(arg.conclusion)
    
    for premise in arg.premises:
        pdir = output_dir / premise.name
        pdir.mkdir(exist_ok=True)
        (pdir / "description.premise").write_text("\n".join(s.text for s in premise.statements))
        if premise.support:
            (pdir / "support.support").write_text("\n".join(premise.support))
    
    print(f"\n✓ Saved to: {output_dir}")
    print(f"\nTo test: python examples/run_argument.py --path {output_dir}")
    
except Exception as e:
    print(f"✗ Failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("Done!")
