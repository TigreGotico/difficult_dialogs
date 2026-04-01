#!/usr/bin/env python3
"""Command-line interface for difficult_dialogs.

Provides commands for generating, validating, exporting, and debating arguments.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from datetime import timedelta


def cmd_generate(args: argparse.Namespace) -> int:
    """Generate arguments using LLM."""
    from difficult_dialogs.llm import ArgumentGenerator
    from difficult_dialogs.validators import validate_argument, ArgumentValidator
    
    print(f"🔌 Connecting to {args.server}...")
    
    generator = ArgumentGenerator(
        base_url=args.server,
        model=args.model,
        timeout=args.timeout
    )
    
    if not generator.client.health_check():
        print(f"❌ Error: Server not responding at {args.server}")
        return 1
    
    print(f"✓ Server online ({args.model})")
    print()
    
    # Parse topics
    topics = [(t.strip(), args.stance) for t in args.topics]
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate with progress
    generated = 0
    failed = 0
    skipped = 0
    
    validator = ArgumentValidator() if args.validate else None
    
    for i, (topic, stance) in enumerate(topics, 1):
        slug = topic.lower().replace(" ", "_").replace("'", "")[:50]
        arg_dir = output_dir / slug
        
        print(f"[{i}/{len(topics)}] {topic[:60]}...", end=" ", flush=True)
        
        # Check if exists
        if arg_dir.exists() and (arg_dir / "intro.dialog").exists():
            if not args.force:
                print("⊘ skipped (already exists)")
                skipped += 1
                continue
        
        try:
            # Generate
            arg = generator.generate(
                topic=topic,
                stance=stance,
                depth=args.depth,
                include_sources=not args.no_sources,
                include_counterarguments=args.counter
            )
            
            # Save to both file format and JSON bundle
            arg.save(arg_dir)
            from difficult_dialogs.export import export_to_json
            export_to_json(arg, arg_dir / "argument.json")
            
            generated += 1
            
            if validator:
                result = validator.validate(arg)
                quality = validator.get_quality_label(result.score)
                print(f"✓ {len(arg.premises)} premises, Score: {result.score:.2f} ({quality})")
            else:
                print(f"✓ {len(arg.premises)} premises")
                
        except Exception as e:
            failed += 1
            print(f"✗ {e}")
    
    # Summary
    print()
    print("=" * 60)
    print(f"Generated: {generated}/{len(topics)}")
    if skipped > 0:
        print(f"Skipped:  {skipped}/{len(topics)}")
    if failed > 0:
        print(f"Failed:   {failed}/{len(topics)}")
    print(f"Output:   {output_dir.absolute()}")
    
    return 0 if failed == 0 else 1



def cmd_validate(args: argparse.Namespace) -> int:
    """Validate arguments."""
    from difficult_dialogs.validators import validate_directory, ArgumentValidator
    
    path = Path(args.path)
    
    if not path.exists():
        print(f"❌ Error: Path not found: {path}")
        return 1
    
    print(f"Validating arguments in {path}...")
    print()
    
    results = validate_directory(path)
    
    if not results:
        print("No arguments found.")
        return 1
    
    validator = ArgumentValidator()
    
    # Group by quality
    excellent = [(n, r) for n, r in results if r.passed and r.score >= 0.9]
    good = [(n, r) for n, r in results if r.passed and r.score >= 0.7]
    fair = [(n, r) for n, r in results if r.passed and r.score >= 0.5]
    failed = [(n, r) for n, r in results if not r.passed]
    
    print("QUALITY DISTRIBUTION:")
    print(f"  ⭐ Excellent: {len(excellent)}")
    print(f"  👍 Good:      {len(good)}")
    print(f"  😐 Fair:      {len(fair)}")
    print(f"  ❌ Failed:    {len(failed)}")
    print()
    
    avg_score = sum(r.score for _, r in results) / len(results)
    print(f"Average Score: {avg_score:.2f} ({validator.get_quality_label(avg_score)})")
    print(f"Pass Rate: {(len(results) - len(failed)) / len(results) * 100:.1f}%")
    print()
    
    if failed and args.verbose:
        print("FAILED ARGUMENTS:")
        for name, result in failed[:10]:
            print(f"\n  {name}:")
            for issue in result.issues[:3]:
                print(f"    {issue}")
        if len(failed) > 10:
            print(f"  ...and {len(failed) - 10} more")
    
    return 0 if len(failed) == 0 else 1


def cmd_export(args: argparse.Namespace) -> int:
    """Export arguments to JSON or SQLite."""
    from difficult_dialogs.export import (
        export_library_to_json,
        export_to_sqlite,
        LibraryDatabase
    )
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"❌ Error: Input path not found: {input_path}")
        return 1
    
    format_type = args.format or output_path.suffix[1:]
    
    print(f"Exporting arguments to {format_type.upper()}...")
    
    if format_type == "json":
        result_path = export_library_to_json(
            input_path,
            output_path,
            include_validation=not args.no_validation
        )
        print(f"✓ Exported to {result_path}")
        
    elif format_type == "sqlite" or format_type == "db":
        db = export_to_sqlite(
            input_path,
            output_path,
            include_validation=not args.no_validation
        )
        
        stats = db.get_statistics()
        print(f"✓ Exported {stats['total_arguments']} arguments to {output_path}")
        
        if args.stats:
            print()
            print("STATISTICS:")
            print(f"  Total arguments: {stats['total_arguments']}")
            print(f"  Categories: {', '.join(k or 'uncategorized' for k in stats['by_category'].keys())}")
            if stats['validation']['validated_count'] > 0:
                print(f"  Avg validation score: {stats['validation']['average_score']:.2f}")
        
        db.close()
    else:
        print(f"❌ Error: Unknown format '{format_type}'. Use 'json' or 'sqlite'.")
        return 1
    
    return 0


def cmd_debate(args: argparse.Namespace) -> int:
    """Run interactive debate with an argument."""
    from difficult_dialogs.arguments import Argument
    from difficult_dialogs.policy import get_policy, POLICY_REGISTRY

    arg_path = Path(args.argument)

    if not arg_path.exists():
        print(f"❌ Error: Argument not found: {arg_path}")
        return 1

    # Load argument
    try:
        argument = Argument().load(arg_path)
    except Exception as e:
        print(f"❌ Error loading argument: {e}")
        return 1

    policy_name = args.policy or "knowitall"

    print(f"ARGUMENT: {argument.name}")
    print(f"POLICY:   {policy_name}")
    print("=" * 60)
    print()

    # Create policy
    try:
        policy = get_policy(policy_name, argument)
    except Exception as e:
        print(f"❌ {e}")
        return 1
    
    # Start dialog
    print(f"BOT: {policy.start()}")
    print()
    
    # Interactive loop
    try:
        while not policy.state.finished:
            user_input = input("USER: ").strip()

            if user_input.lower() in ('quit', 'exit', 'q'):
                print(f"\nBOT: {policy.end()}")
                break

            response = policy.handle_input(user_input)

            if response:
                print(f"BOT: {response}")

            if policy.state.finished:
                print(f"\nBOT: {policy.end()}")
                break

    except EOFError:
        print(f"\n\nBOT: {policy.end()}")

    # Optional transcript save
    if getattr(args, "save_transcript", None):
        from difficult_dialogs.export import export_transcript_to_markdown
        out = Path(args.save_transcript)
        export_transcript_to_markdown(policy, output_path=out)
        print(f"\nTranscript saved to {out}")

    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List available arguments."""
    from difficult_dialogs.arguments import Argument
    
    search_path = Path(args.path)
    
    if not search_path.exists():
        print(f"❌ Error: Path not found: {search_path}")
        return 1
    
    print(f"Available arguments in {search_path}:")
    print()
    
    count = 0
    categories = {}
    
    for intro_file in search_path.rglob("intro.dialog"):
        arg_dir = intro_file.parent
        
        # Determine category
        rel_path = arg_dir.relative_to(search_path)
        category = rel_path.parts[0] if len(rel_path.parts) > 1 else "uncategorized"
        
        if category not in categories:
            categories[category] = []
        
        categories[category].append(arg_dir.name.replace("_", " ").title())
        count += 1
    
    for category, args_list in sorted(categories.items()):
        print(f"{category.upper()} ({len(args_list)}):")
        for arg_name in sorted(args_list):
            print(f"  • {arg_name}")
        print()
    
    print(f"Total: {count} arguments")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    """Start the FastAPI REST server."""
    try:
        import uvicorn
    except ImportError:
        print("❌ uvicorn is required to run the server.")
        print("   Install with: pip install difficult-dialogs[server]")
        return 1

    print(f"🚀 Starting Difficult Dialogs API server on http://{args.host}:{args.port}")
    print("   Press Ctrl+C to stop.\n")

    uvicorn.run(
        "difficult_dialogs.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="difficult-dialogs",
        description="Generate, validate, export, and debate structured arguments."
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Generate command
    gen_parser = subparsers.add_parser(
        "generate",
        aliases=["gen", "g"],
        help="Generate arguments using LLM"
    )
    gen_parser.add_argument(
        "topics",
        nargs="+",
        help="Topics to generate arguments for"
    )
    gen_parser.add_argument(
        "-s", "--server",
        default="http://localhost:8000",
        help="LLM server URL (default: http://localhost:8000)"
    )
    gen_parser.add_argument(
        "-m", "--model",
        default="default",
        help="Model name (default: default)"
    )
    gen_parser.add_argument(
        "-o", "--output",
        default="./generated_arguments",
        help="Output directory (default: ./generated_arguments)"
    )
    gen_parser.add_argument(
        "--stance",
        choices=["pro", "con"],
        default="pro",
        help="Argument stance (default: pro)"
    )
    gen_parser.add_argument(
        "-d", "--depth",
        type=int,
        default=1,
        help="Argument depth/premises (default: 1)"
    )
    gen_parser.add_argument(
        "--no-sources",
        action="store_true",
        help="Don't include sources"
    )
    gen_parser.add_argument(
        "--counter",
        action="store_true",
        help="Include counterarguments"
    )
    gen_parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Overwrite existing arguments"
    )
    gen_parser.add_argument(
        "-v", "--validate",
        action="store_true",
        help="Validate generated arguments"
    )
    gen_parser.add_argument(
        "-t", "--timeout",
        type=float,
        default=120.0,
        help="Timeout per generation in seconds (default: 120)"
    )
    gen_parser.set_defaults(func=cmd_generate)
    
    # Validate command
    val_parser = subparsers.add_parser(
        "validate",
        aliases=["val", "v"],
        help="Validate argument quality"
    )
    val_parser.add_argument(
        "path",
        help="Path to arguments directory"
    )
    val_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed validation issues"
    )
    val_parser.set_defaults(func=cmd_validate)
    
    # Export command
    exp_parser = subparsers.add_parser(
        "export",
        aliases=["exp", "e"],
        help="Export arguments to JSON or SQLite"
    )
    exp_parser.add_argument(
        "input",
        help="Input directory with arguments"
    )
    exp_parser.add_argument(
        "output",
        help="Output file path"
    )
    exp_parser.add_argument(
        "-f", "--format",
        choices=["json", "sqlite", "db"],
        help="Export format (auto-detected from extension if not specified)"
    )
    exp_parser.add_argument(
        "--no-validation",
        action="store_true",
        help="Don't include validation data"
    )
    exp_parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics after export"
    )
    exp_parser.set_defaults(func=cmd_export)
    
    # Debate command
    deb_parser = subparsers.add_parser(
        "debate",
        aliases=["deb", "d", "run"],
        help="Run interactive debate"
    )
    deb_parser.add_argument(
        "argument",
        help="Path to argument directory"
    )
    deb_parser.add_argument(
        "-p", "--policy",
        default="knowitall",
        choices=[
            "knowitall", "silent", "socratic", "debate", "exploratory",
            "maieutic", "skeptic", "teacher", "debater", "minimalist",
            "adaptive",
        ],
        help="Dialog policy to use (default: knowitall)"
    )
    deb_parser.add_argument(
        "--save-transcript",
        metavar="FILE",
        help="Save the conversation transcript to a Markdown file after the session ends",
    )
    deb_parser.set_defaults(func=cmd_debate)
    
    # List command
    list_parser = subparsers.add_parser(
        "list",
        aliases=["ls", "l"],
        help="List available arguments"
    )
    list_parser.add_argument(
        "path",
        nargs="?",
        default="./examples/sample_arguments",
        help="Path to search (default: ./examples/sample_arguments)"
    )
    list_parser.set_defaults(func=cmd_list)

    # Serve command
    serve_parser = subparsers.add_parser(
        "serve",
        aliases=["server", "api"],
        help="Start the FastAPI REST server"
    )
    serve_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to listen on (default: 8080)"
    )
    serve_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    serve_parser.set_defaults(func=cmd_serve)

    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
