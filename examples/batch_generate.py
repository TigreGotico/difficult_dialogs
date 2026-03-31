#!/usr/bin/env python3
"""Generate a library of sample arguments for testing and demonstration."""
import sys
import json
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent.parent))

from difficult_dialogs.llm import ArgumentGenerator

# Configuration
LLM_URL = "http://192.168.1.200:8000"
MODEL_NAME = "qwen-72b"
CHECKPOINT_FILE = Path(".generation_checkpoint.json")
MAX_WORKERS = 3  # Parallel generations

# Topics organized by category
TOPICS = {
    "technology": [
        ("Artificial intelligence will benefit humanity", "pro"),
        ("Open source software is superior to proprietary", "pro"),
        ("Privacy is more important than convenience", "pro"),
        ("Remote work increases productivity", "pro"),
        ("Social media does more harm than good", "con"),
    ],
    "science": [
        ("Climate change requires immediate action", "pro"),
        ("Space exploration is worth the cost", "pro"),
        ("Vaccines are safe and effective", "pro"),
        ("Genetic engineering should be regulated", "pro"),
        ("Renewable energy can replace fossil fuels", "pro"),
    ],
    "health": [
        ("Regular exercise improves mental health", "pro"),
        ("A plant-based diet is healthier", "pro"),
        ("Sleep is essential for cognitive function", "pro"),
        ("Meditation reduces stress effectively", "pro"),
        ("Preventive care is better than treatment", "pro"),
    ],
    "society": [
        ("Universal basic income would reduce poverty", "pro"),
        ("Higher education should be free", "pro"),
        ("Cities should prioritize public transportation", "pro"),
        ("Recycling programs are effective", "pro"),
        ("Volunteering benefits both giver and receiver", "pro"),
    ],
    "philosophy": [
        ("I think therefore I am", "pro"),
        ("The ends justify the means", "con"),
        ("Free will exists", "pro"),
        ("Happiness is the highest good", "pro"),
        ("Knowledge is more valuable than pleasure", "pro"),
    ],
    "education": [
        ("Critical thinking should be taught in schools", "pro"),
        ("Standardized tests don't measure intelligence", "pro"),
        ("Lifelong learning is essential in modern society", "pro"),
        ("Teachers should be paid more", "pro"),
        ("Online learning is as effective as in-person", "pro"),
    ],
}


def save_argument(arg, output_dir: Path) -> None:
    """Save argument to directory structure."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write intro
    (output_dir / "intro.dialog").write_text(arg.intro)
    
    # Write conclusion
    (output_dir / "conclusion.conclusion").write_text(arg.conclusion)
    
    # Write premises
    for premise in arg.premises:
        premise_dir = output_dir / premise.name
        premise_dir.mkdir(exist_ok=True)
        
        # Write statements
        statements_text = "\n".join(s.text for s in premise.statements)
        (premise_dir / "description.premise").write_text(statements_text)
        
        # Write support
        if premise.support:
            support_text = "\n".join(premise.support)
            (premise_dir / "support.support").write_text(support_text)
        
        # Write sources
        if premise.sources:
            sources_text = "\n".join(premise.sources)
            (premise_dir / "source.source").write_text(sources_text)
        
        # Write Five Ws
        if premise.what:
            (premise_dir / "what").write_text("\n".join(premise.what))
        if premise.why:
            (premise_dir / "why").write_text("\n".join(premise.why))
        if premise.how:
            (premise_dir / "how").write_text("\n".join(premise.how))


def load_checkpoint() -> dict:
    """Load checkpoint data if exists."""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    return {"completed": [], "failed": []}


def save_checkpoint(completed: list, failed: list) -> None:
    """Save progress to checkpoint file."""
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({
            "completed": completed,
            "failed": failed,
            "timestamp": datetime.now().isoformat(),
            "total_completed": len(completed)
        }, f, indent=2)


def generate_single(topic_data: tuple, category: str, generator: ArgumentGenerator) -> dict:
    """Generate a single argument (for parallel execution)."""
    topic, stance = topic_data
    slug = topic.lower().replace(" ", "_").replace("'", "")[:50]
    # Use absolute path based on script location
    script_dir = Path(__file__).parent
    output_dir = script_dir / "sample_arguments" / category / slug
    
    # Skip if already exists and has intro
    if output_dir.exists() and (output_dir / "intro.dialog").exists():
        return {"status": "skipped", "topic": topic, "reason": "already exists"}
    
    try:
        arg = generator.generate(
            topic=topic,
            stance=stance,
            depth=1,
            include_sources=False,
            include_counterarguments=True
        )
        
        save_argument(arg, output_dir)
        return {
            "status": "success",
            "topic": topic,
            "premises": len(arg.premises),
            "path": str(output_dir)
        }
    except Exception as e:
        import traceback
        return {"status": "failed", "topic": topic, "error": f"{e}\n{traceback.format_exc()}"}


def main():
    """Generate all sample arguments."""
    print("=" * 70)
    print("Difficult Dialogs - Sample Argument Library Generator")
    print("=" * 70)
    print()
    
    # Check server
    print(f"Connecting to LLM server at {LLM_URL}...")
    test_gen = ArgumentGenerator(base_url=LLM_URL, model=MODEL_NAME, timeout=30.0)
    if not test_gen.client.health_check():
        print(f"ERROR: Server not responding!")
        return
    
    print("✓ Server is online!")
    print(f"Using {MAX_WORKERS} parallel workers")
    print()
    
    # Flatten all topics
    all_topics = []
    for category, topics in TOPICS.items():
        for topic_data in topics:
            all_topics.append((category, topic_data))
    
    total_topics = len(all_topics)
    print(f"Total topics to generate: {total_topics}")
    print()
    
    # No need to filter - generate_single will skip existing ones
    remaining = all_topics
    
    generated = 0
    failed = 0
    skipped = 0
    completed_slugs = []  # Track what we've successfully generated this run
    failed_slugs = []     # Track failures for checkpoint resume
    
    print(f"\n{'='*70}")
    print("Starting generation...")
    print(f"{'='*70}\n")
    
    # Create all category directories (use absolute path)
    script_dir = Path(__file__).parent
    base_dir = script_dir / "sample_arguments"
    for category in TOPICS.keys():
        (base_dir / category).mkdir(parents=True, exist_ok=True)
    
    # Generate with parallelism
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        
        # Submit initial batch
        for i, (category, topic_data) in enumerate(remaining[:MAX_WORKERS]):
            gen = ArgumentGenerator(base_url=LLM_URL, model=MODEL_NAME, timeout=180.0)
            future = executor.submit(generate_single, topic_data, category, gen)
            futures[future] = (category, topic_data)
        
        # Process as they complete
        pending_idx = MAX_WORKERS
        try:
            while futures:
                # Wait for at least one to complete
                done_futures = list(as_completed(futures, timeout=300.0))
                
                for done in done_futures:
                    result = done.result()
                    
                    # Update tracking
                    if result["status"] == "success":
                        generated += 1
                        completed_slugs.append(result["topic"].lower().replace(" ", "_").replace("'", "")[:50])
                        print(f"[{generated + skipped}/{total_topics}] ✓ {result['topic'][:50]} ({result['premises']} premises)", flush=True)
                    elif result["status"] == "skipped":
                        skipped += 1
                        print(f"[{generated + skipped}/{total_topics}] ⊘ {result['topic'][:50]} (already exists)", flush=True)
                    else:
                        failed += 1
                        failed_slugs.append(result["topic"].lower().replace(" ", "_").replace("'", "")[:50])
                        print(f"[{generated + skipped}/{total_topics}] ✗ {result['topic'][:50]}: {result.get('error', 'unknown')[:100]}", flush=True)
                    
                    # Remove completed future
                    del futures[done]
                    
                    # Submit next if available
                    if pending_idx < len(remaining):
                        category, topic_data = remaining[pending_idx]
                        gen = ArgumentGenerator(base_url=LLM_URL, model=MODEL_NAME, timeout=180.0)
                        future = executor.submit(generate_single, topic_data, category, gen)
                        futures[future] = (category, topic_data)
                        pending_idx += 1
                        print(f"Submitted next topic ({pending_idx}/{len(remaining)}): {topic_data[0][:40]}", flush=True)
                
                # Save checkpoint after batch
                save_checkpoint(completed_slugs, failed_slugs)
        except Exception as e:
            print(f"\nERROR in generation loop: {e}", flush=True)
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("GENERATION COMPLETE")
    print("=" * 70)
    print(f"Successfully generated: {generated}/{total_topics}")
    print(f"Failed: {failed}/{total_topics}")
    print(f"Skipped (already existed): {skipped}")
    print(f"\nArguments saved to: examples/sample_arguments/")
    print(f"\nCheckpoint saved to: {CHECKPOINT_FILE}")
    print(f"(Delete checkpoint file to regenerate all)")
    print("\nTo browse arguments:")
    print("  ls examples/sample_arguments/*/")
    print("\nTo test an argument:")
    print("  python examples/run_argument.py examples/sample_arguments/<category>/<topic>")


if __name__ == "__main__":
    main()
