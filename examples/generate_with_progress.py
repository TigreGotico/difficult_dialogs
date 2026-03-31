#!/usr/bin/env python3
"""Enhanced argument generator with progress bar, ETA, and retry logic."""
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import tqdm for progress bars, fall back to simple text if not available
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("Note: Install 'tqdm' for better progress display: pip install tqdm")

from difficult_dialogs.llm import ArgumentGenerator
from difficult_dialogs.validators import validate_argument, ArgumentValidator

# Configuration
LLM_URL = "http://192.168.1.200:8000"
MODEL_NAME = "qwen-72b"
OUTPUT_DIR = Path(__file__).parent / "sample_arguments"
MAX_RETRIES = 2
TIMEOUT = 120.0  # seconds per generation


class ProgressBar:
    """Simple progress bar fallback if tqdm not available."""
    
    def __init__(self, total: int, desc: str = ""):
        self.total = total
        self.current = 0
        self.desc = desc
        self.start_time = time.time()
    
    def update(self, n: int = 1) -> None:
        self.current += n
    
    def set_description(self, desc: str) -> None:
        self.desc = desc
    
    def close(self) -> None:
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass
    
    def format_progress(self) -> str:
        """Format progress as text string."""
        elapsed = time.time() - self.start_time
        pct = (self.current / self.total * 100) if self.total > 0 else 0
        eta_seconds = (elapsed / self.current * (self.total - self.current)) if self.current > 0 else 0
        eta = timedelta(seconds=int(eta_seconds))
        
        bar_width = 30
        filled = int(bar_width * self.current / self.total) if self.total > 0 else 0
        bar = "█" * filled + "░" * (bar_width - filled)
        
        return f"{self.desc}: [{bar}] {self.current}/{self.total} ({pct:.0f}%) ETA: {eta}"


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


def generate_with_retry(
    generator: ArgumentGenerator,
    topic: str,
    stance: str,
    max_retries: int = MAX_RETRIES
) -> tuple[Optional[Any], Optional[str]]:
    """Generate argument with retry logic.
    
    Args:
        generator: ArgumentGenerator instance.
        topic: Topic to generate.
        stance: 'pro' or 'con'.
        max_retries: Maximum number of retry attempts.
        
    Returns:
        Tuple of (Argument or None, error message or None).
    """
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                print(f"    Retry {attempt}/{max_retries}...")
            
            arg = generator.generate(
                topic=topic,
                stance=stance,
                depth=1,
                include_sources=False,
                include_counterarguments=True
            )
            
            return arg, None
            
        except Exception as e:
            last_error = str(e)
            print(f"    Attempt {attempt + 1} failed: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff
    
    return None, last_error


def main():
    """Generate arguments with enhanced UX."""
    print("=" * 80)
    print("Difficult Dialogs - Enhanced Argument Generator")
    print("=" * 80)
    print()
    
    # Topics to generate
    topics = [
        ("Remote work increases productivity", "technology", "pro"),
        ("Artificial intelligence benefits humanity", "technology", "pro"),
        ("Climate change requires immediate action", "science", "pro"),
        ("Exercise improves mental health", "health", "pro"),
        ("Universal basic income reduces poverty", "society", "pro"),
        ("Free will exists", "philosophy", "pro"),
        ("Critical thinking should be taught in schools", "education", "pro"),
    ]
    
    # Check server
    print(f"Connecting to LLM server at {LLM_URL}...")
    test_gen = ArgumentGenerator(base_url=LLM_URL, model=MODEL_NAME, timeout=10.0)
    
    if not test_gen.client.health_check():
        print(f"❌ ERROR: Server not responding at {LLM_URL}")
        print("Make sure your LLM server is running.")
        return
    
    print(f"✓ Server online ({MODEL_NAME})")
    print()
    
    # Initialize progress
    ProgressClass = tqdm if HAS_TQDM else ProgressBar
    pbar = ProgressClass(total=len(topics), desc="Generating")
    
    # Statistics
    generated = 0
    failed = 0
    skipped = 0
    validation_scores = []
    
    generator = ArgumentGenerator(base_url=LLM_URL, model=MODEL_NAME, timeout=TIMEOUT)
    validator = ArgumentValidator()
    
    start_time = time.time()
    
    for i, (topic, category, stance) in enumerate(topics, 1):
        slug = topic.lower().replace(" ", "_").replace("'", "")[:50]
        output_dir = OUTPUT_DIR / category / slug
        
        # Update progress description
        if HAS_TQDM:
            pbar.set_description(f"[{i}/{len(topics)}] {topic[:50]}")
        else:
            print(f"\n[{i}/{len(topics)}] {topic}")
        
        # Check if already exists
        if output_dir.exists() and (output_dir / "intro.dialog").exists():
            skipped += 1
            pbar.update(1)
            continue
        
        # Generate with retry
        arg, error = generate_with_retry(generator, topic, stance)
        
        if arg is None:
            failed += 1
            print(f"  ❌ Failed after {MAX_RETRIES} retries: {error}")
            pbar.update(1)
            continue
        
        # Save argument
        save_argument(arg, output_dir)
        
        # Validate
        result = validator.validate(arg)
        validation_scores.append(result.score)
        
        quality_label = validator.get_quality_label(result.score)
        
        # Report success
        print(f"  ✓ Generated: {len(arg.premises)} premises, Score: {result.score:.2f} ({quality_label})")
        
        generated += 1
        pbar.update(1)
    
    pbar.close()
    
    # Final statistics
    elapsed = time.time() - start_time
    avg_score = sum(validation_scores) / len(validation_scores) if validation_scores else 0
    
    print()
    print("=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)
    print(f"Time elapsed: {timedelta(seconds=int(elapsed))}")
    print(f"Successfully generated: {generated}/{len(topics)}")
    print(f"Skipped (already existed): {skipped}/{len(topics)}")
    print(f"Failed: {failed}/{len(topics)}")
    print()
    print(f"Quality Metrics:")
    print(f"  Average score: {avg_score:.2f}")
    print(f"  Quality: {validator.get_quality_label(avg_score)}")
    print()
    print(f"Arguments saved to: {OUTPUT_DIR}")
    print()
    
    if failed > 0:
        print(f"⚠️  {failed} argument(s) failed to generate.")
        print("   You can retry by running this script again.")
        print()
    
    print("To view arguments:")
    print(f"  ls {OUTPUT_DIR}/*/")
    print()
    print("To test an argument:")
    print(f"  python examples/run_argument.py {OUTPUT_DIR}/<category>/<topic>")
    print()


if __name__ == "__main__":
    main()
