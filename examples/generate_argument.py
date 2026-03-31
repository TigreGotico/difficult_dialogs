#!/usr/bin/env python3
"""Generate an argument using a local LLM server."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from difficult_dialogs.llm import ArgumentGenerator


def main():
    """Generate a sample argument."""
    # Configuration - update these for your setup
    LLM_URL = "http://192.168.1.200:8000"
    MODEL_NAME = "qwen-72b"  # or None to use server default
    
    print("=" * 60)
    print("Difficult Dialogs - LLM Argument Generator")
    print("=" * 60)
    print()
    
    # Get topic from user
    topic = input("Enter a topic to argue about: ").strip()
    if not topic:
        topic = "Remote work increases productivity"
        print(f"Using default topic: {topic}")
    
    print()
    print(f"Connecting to LLM server at {LLM_URL}...")
    
    try:
        # Create generator
        generator = ArgumentGenerator(
            base_url=LLM_URL,
            model=MODEL_NAME,
            timeout=300.0
        )
        
        # Check server health
        print("Checking server health...")
        if not generator.client.health_check():
            print(f"ERROR: Server at {LLM_URL} is not responding!")
            print("Make sure llama.cpp server is running.")
            return
        
        print("Server is online!")
        print()
        
        # Generate argument
        print(f"Generating argument for: '{topic}'")
        print("This may take 30-60 seconds...")
        print()
        
        argument = generator.generate(
            topic=topic,
            stance="pro",
            depth=2,
            include_sources=True,
            include_counterarguments=True
        )
        
        # Save argument
        output_dir = Path(__file__).parent / "generated" / argument.name
        print(f"Saving to: {output_dir}")
        
        # Manually save since Argument doesn't have save method yet
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write intro
        (output_dir / "intro.dialog").write_text(argument.intro)
        
        # Write conclusion
        (output_dir / "conclusion.conclusion").write_text(argument.conclusion)
        
        # Write premises
        for premise in argument.premises:
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
        
        print()
        print("=" * 60)
        print("SUCCESS! Argument generated and saved.")
        print("=" * 60)
        print()
        print(f"Directory: {output_dir}")
        print(f"Premises: {len(argument.premises)}")
        print(f"Total statements: {sum(len(p.statements) for p in argument.premises)}")
        print()
        print("To run this argument:")
        print(f"  python examples/run_argument.py --path {output_dir}")
        print()
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"ERROR: {e}")
        print("=" * 60)
        print()
        print("Troubleshooting:")
        print("1. Make sure llama.cpp server is running")
        print("2. Check that the URL is correct")
        print("3. Verify the model is loaded")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
