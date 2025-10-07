"""
Command-line entry point to run Auto Description Retrieval tasks.

Usage:
    python main.py scrape_description <vdp_url>
    python main.py test_llm
"""
import os
import argparse
from dotenv import load_dotenv
from client.llm_client import LLMClient

from core.main_functions.scrape_description import scrape_description

load_dotenv()

def main() -> None:
    # Get argument parsers
    parser = argparse.ArgumentParser(description="Run Auto Description Retrieval tasks.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Get "scrape_description" parameters
    scrape_parser = subparsers.add_parser("scrape_description", help="Fetch and process vehicle description.")
    scrape_parser.add_argument("vdp_url", type=str, help="The VDP URL to process.")\

    # Initalize the LLM client and ensure current config / connection work
    llm_client = LLMClient()
    llm_client.test_connection()

    # Grab arguments from the parser
    args = parser.parse_args()

    if args.command == "scrape_description":
        description, token_count = scrape_description(
            vdp_url = args.vdp_url,
            llm_client = llm_client
        )
        
        if os.getenv("PRINT_TOKEN_COUNT", False):
            print(f"- query complete using {token_count} tokens")
        
        return description


if __name__ == "__main__":
    import sys
    try:
        result = main()
        print(result) # Print result for CLI or Terminal use
    except Exception as e:
        # Display the type of exception + message
        print(f"[{type(e).__name__}] {e}", file=sys.stderr)
        sys.exit(1)  # exit code signals failure to shell
