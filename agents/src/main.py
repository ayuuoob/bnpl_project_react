"""
BNPL Analytics Agent - Main Entry Point

Provides CLI interface for running the agent.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def main():
    """Main entry point for the agent CLI."""
    # Load environment variables
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="BNPL Intelligent Analytics Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main --query "What was our GMV last month?"
  python -m src.main --demo
  python -m src.main --interactive
        """,
    )
    
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Run a single query",
    )
    
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demo queries",
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Start interactive mode",
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output",
    )
    
    args = parser.parse_args()
    
    # Set debug mode
    if args.debug:
        os.environ["DEBUG_MODE"] = "true"
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    # Run appropriate mode
    if args.demo:
        asyncio.run(run_demo())
    elif args.query:
        asyncio.run(run_single_query(args.query))
    elif args.interactive:
        asyncio.run(run_interactive())
    else:
        parser.print_help()


async def run_single_query(query: str):
    """Run a single query."""
    from .graph import run_query
    
    print(f"\n🔍 Query: {query}\n")
    print("-" * 60)
    
    response = await run_query(query)
    print(response)


async def run_demo():
    """Run demo queries."""
    from .graph import demo
    await demo()


async def run_interactive():
    """Run interactive REPL mode."""
    from .graph import run_query
    
    print("=" * 60)
    print("BNPL Analytics Agent - Interactive Mode")
    print("=" * 60)
    print("\nType your question and press Enter.")
    print("Type 'exit' or 'quit' to exit.")
    print("Type 'help' for example questions.\n")
    
    example_questions = [
        "What was our GMV last month vs previous month?",
        "How many active users do we have in the last 30 days?",
        "What is our late payment rate by cohort?",
        "Which merchants have the highest dispute rates?",
        "What is our checkout conversion rate?",
    ]
    
    while True:
        try:
            user_input = input("\n📊 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nGoodbye! 👋")
                break
            
            if user_input.lower() == "help":
                print("\n📋 Example questions:")
                for i, q in enumerate(example_questions, 1):
                    print(f"  {i}. {q}")
                continue
            
            # Check if user entered a number for example questions
            if user_input.isdigit():
                idx = int(user_input) - 1
                if 0 <= idx < len(example_questions):
                    user_input = example_questions[idx]
                    print(f"📊 Running: {user_input}")
            
            print("\n⏳ Analyzing...\n")
            response = await run_query(user_input)
            print("🤖 Agent:")
            print("-" * 40)
            print(response)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            if os.getenv("DEBUG_MODE"):
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    main()
