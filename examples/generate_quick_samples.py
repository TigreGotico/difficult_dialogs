#!/usr/bin/env python3
"""Quickly generate 5 sample arguments for demo purposes."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from difficult_dialogs.llm import ArgumentGenerator

LLM_URL = "http://192.168.1.200:8000"

# 5 diverse, high-interest topics
TOPICS = [
    ("Remote work increases productivity", "technology"),
    ("Vaccines are safe and effective", "science"),
    ("Exercise improves mental health", "health"),
    ("Universal basic income reduces poverty", "society"),
    ("Free will exists", "philosophy"),
]

def save_argument(arg, output_dir: Path) -> None:
    """Save argument to directory structure."""
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "intro.dialog").write_text(arg.intro)
    (output_dir / "conclusion.conclusion").write_text(arg.conclusion)
    
    for premise in arg.premises:
        pdir = output_dir / premise.name
        pdir.mkdir(exist_ok=True)
        (pdir / "description.premise").write_text("\n".join(s.text for s in premise.statements))
        if premise.support:
            (pdir / "support.support").write_text("\n".join(premise.support))
        if premise.sources:
            (pdir / "source.source").write_text("\n".join(premise.sources))
        if premise.what:
            (pdir / "what").write_text("\n".join(premise.what))
        if premise.why:
            (pdir / "why").write_text("\n".join(premise.why))
        if premise.how:
            (pdir / "how").write_text("\n".join(premise.how))

def main():
    print("=" * 70)
    print("Generating 5 Quick Sample Arguments")
    print("=" * 70)
    
    gen = ArgumentGenerator(LLM_URL, timeout=120.0)
    
    if not gen.client.health_check():
        print(f"✗ Server at {LLM_URL} not responding!")
        return
    
    print("✓ Server online\n")
    
    for i, (topic, category) in enumerate(TOPICS, 1):
        print(f"[{i}/5] Generating: {topic}")
        try:
            arg = gen.generate(topic=topic, stance="pro", depth=1, include_sources=False)
            slug = topic.lower().replace(" ", "_")[:40]
            save_argument(arg, Path(f"examples/sample_arguments/{category}/{slug}"))
            print(f"      ✓ Created with {len(arg.premises)} premises\n")
        except Exception as e:
            print(f"      ✗ Failed: {e}\n")
    
    print("=" * 70)
    print("Done! Arguments saved to examples/sample_arguments/")
    print("=" * 70)

if __name__ == "__main__":
    main()
