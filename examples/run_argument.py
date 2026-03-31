#!/usr/bin/env python3
"""Simple example running an argument with user interaction."""
import sys
from pathlib import Path

from difficult_dialogs import Argument, KnowItAllPolicy


def main():
    """Run an argument with user interaction."""
    # Get path from command line or use default
    if len(sys.argv) > 1:
        arg_path = Path(sys.argv[1])
    else:
        arg_path = Path(__file__).parent / "i_think_therefore_i_am"
    
    if not arg_path.exists():
        print(f"ERROR: Argument path not found: {arg_path}")
        sys.exit(1)
    
    arg = Argument()
    arg.load(arg_path)
    
    print(f"ARGUMENT: {arg.name}")
    print("=" * 50)
    
    policy = KnowItAllPolicy(arg)
    
    # Start dialog
    intro = policy.start()
    if intro:
        print(f"\nBOT: {intro}")
    
    while not policy.state.finished:
        try:
            user_input = input("\nUSER: ").strip()
            if not user_input:
                continue
            
            response = policy.handle_input(user_input)
            if response:
                print(f"\nBOT: {response}")
                
        except KeyboardInterrupt:
            print("\n\nInterrupted!")
            break
    
    print("\n" + "=" * 50)
    print("Dialog complete.")


if __name__ == "__main__":
    main()
