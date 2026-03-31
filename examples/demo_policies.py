#!/usr/bin/env python3
"""Demo script showing all available dialog policies.

Run this to see how different policies handle the same argument differently.
"""
from pathlib import Path

from difficult_dialogs.arguments import Argument
from difficult_dialogs.policy import (
    KnowItAllPolicy,
    SilentPolicy,
    SocraticPolicy,
    DebatePolicy,
    ExploratoryPolicy,
)


def demo_policy(policy_name: str, policy, max_turns: int = 5) -> None:
    """Demonstrate a policy with simulated conversation.
    
    Args:
        policy_name: Name of the policy for display.
        policy: Policy instance to demo.
        max_turns: Maximum number of turns to simulate.
    """
    print(f"\n{'='*60}")
    print(f"POLICY: {policy_name}")
    print(f"{'='*60}\n")
    
    # Start the dialog
    intro = policy.start()
    print(f"BOT: {intro}")
    
    turns = 0
    while not policy.state.finished and turns < max_turns:
        # Alternate between agreement and disagreement
        if turns % 2 == 0:
            user_input = "yes"
            print(f"YOU: {user_input}")
        else:
            user_input = "no"
            print(f"YOU: {user_input}")
        
        response = policy.handle_input(user_input)
        
        if response:
            print(f"BOT: {response}")
        
        turns += 1
    
    if policy.state.finished:
        print("\n[Dialog completed]")
    else:
        print(f"\n[Demo stopped after {max_turns} turns]")


def main() -> None:
    """Run policy demonstrations."""
    # Load an example argument
    examples_dir = Path(__file__).parent
    cogito_dir = examples_dir / "i_think_therefore_i_am"
    
    if not cogito_dir.exists():
        print(f"Example directory not found: {cogito_dir}")
        print("Please ensure the i_think_therefore_i_am example exists.")
        return
    
    arg = Argument()
    arg.load(cogito_dir)
    
    print("\n" + "="*60)
    print("DIFFICULT DIALOGS - POLICY DEMONSTRATION")
    print("="*60)
    print(f"\nArgument: {arg.name}")
    print(f"Premises: {len(arg.premises)}")
    print("\nThis demo shows how different policies handle the same argument.")
    
    # Demo each policy
    policies = [
        ("KnowItAllPolicy", KnowItAllPolicy(arg)),
        ("SilentPolicy", SilentPolicy(arg)),
        ("SocraticPolicy", SocraticPolicy(arg)),
        ("DebatePolicy", DebatePolicy(arg)),
        ("ExploratoryPolicy", ExploratoryPolicy(arg)),
    ]
    
    for policy_name, policy in policies:
        demo_policy(policy_name, policy, max_turns=4)
    
    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)
    print("\nPolicy summaries:")
    print("- KnowItAllPolicy: Provides support & sources when you disagree")
    print("- SilentPolicy: Presents all statements without waiting for feedback")
    print("- SocraticPolicy: Asks probing questions to examine your reasoning")
    print("- DebatePolicy: Actively challenges your disagreements")
    print("- ExploratoryPolicy: Acknowledges multiple viewpoints neutrally")
    print("\nTry running the argument with different policies:")
    print("  python run_argument.py <path> --policy <policy_name>")


if __name__ == "__main__":
    main()
