"""
Command-line entry point to run Auto Description Retrieval tasks.

Usage:
    python main.py scrape_description <vdp_url>
    python main.py test_llm
"""
import os
from dotenv import load_dotenv
import argparse
import json
from client.llm_client import LLMClient

from core.main_functions.scrape_description import scrape_description
from core.main_functions.determine_vpd_search_paths import determine_vpd_search_paths

load_dotenv()
PRINT_DEBUG_COMMENTS = bool(os.getenv("PRINT_DEBUG_COMMENTS", False))

def main() -> None:
    # Get argument parsers
    parser = argparse.ArgumentParser(description="Run Auto Description Retrieval tasks.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Get "scrape_description" parameters
    scrape_parser = subparsers.add_parser("scrape_description", help="Fetch and process vehicle description.")
    scrape_parser.add_argument("vdp_url", type=str, help="The VDP URL to process.")\

    # Get "determine_vpd_search_paths" parameters
    determine_vpd_search_paths_parser = subparsers.add_parser(
        "determine_vpd_search_paths",
        help="Determine location of description in HTML."
    )
    determine_vpd_search_paths_parser.add_argument("vdp_url", type=str, help="The VDP URL to process.")\

    # demo_scrape_description parameters (no arguments)
    demo_parser = subparsers.add_parser(
        "demo_scrape_description", help="Run a demo scrape on sample URLs from JSON."
    )

    # Initalize the LLM client (with env settings) and test it
    llm_client = LLMClient()
    llm_client.test_connection()

    # Grab arguments from the parser
    args = parser.parse_args()

    if args.command == "scrape_description":
        if PRINT_DEBUG_COMMENTS:
            print(
                f"--- DEBUG, PULLING DESCRIPTION FROM URL ---\n",
                f"`{args.vdp_url}`",
                "\n----------------------------------------------------------------\n"
            )
        
        description, token_count = scrape_description(
            vdp_url = args.vdp_url,
            llm_client = llm_client,
            print_debug_comments=PRINT_DEBUG_COMMENTS,
        )
        
        if PRINT_DEBUG_COMMENTS:
            print(f"--- DEBUG, QUERY COMPLETE USING {token_count} TOKENS ---\n")
        
        return description
    
    elif args.command == "demo_scrape_description":
        # Load the demo URLs from JSON
        with open("tests/demo_urls.json", "r") as f:
            url_data = json.load(f)
            print("Loaded demo urls:", url_data, "\n-------------------------------\n")

        for section, urls in url_data.items():
            banner = f"\n{'='*10} {section.upper()} {'='*10}\n"
            print(banner)

            for url in urls:
                print(f"Scraping =={section.upper()}== URL: `{url}`")

                try:
                    description, token_count = scrape_description(
                        vdp_url=url,
                        llm_client=llm_client,
                        print_debug_comments=PRINT_DEBUG_COMMENTS,
                    )
                    print(f"Response ({token_count} tokens):\n{description}\n")
                    print("=========================================================\n")
                except Exception as e:
                    print(f"ERROR scraping URL `{url}`: {e}\n")
    
    elif args.command == "determine_vpd_search_paths":
        description, token_count = determine_vpd_search_paths(
            vdp_url = args.vdp_url,
            llm_client = llm_client
        )
        
        if PRINT_DEBUG_COMMENTS:
            print(f"--- DEBUG, QUERY COMPLETE USING {token_count} TOKENS ---\n")
        
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
