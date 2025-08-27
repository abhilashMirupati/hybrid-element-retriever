"""CLI entrypoints for HER."""
import argparse
import json
import sys
import logging
from .cli_api import HybridClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main(argv=None):
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="her",
        description="Hybrid Element Retriever - Natural language UI automation"
    )
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Act command
    act_parser = subparsers.add_parser(
        "act",
        help="Execute an action on a page"
    )
    act_parser.add_argument(
        "--step",
        required=True,
        help="Natural language step to execute"
    )
    act_parser.add_argument(
        "--url",
        help="URL to navigate to before executing",
        default=None
    )
    act_parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode",
        default=True
    )
    act_parser.add_argument(
        "--timeout",
        type=int,
        help="Timeout in milliseconds",
        default=30000
    )
    
    # Query command
    query_parser = subparsers.add_parser(
        "query",
        help="Query for elements without executing"
    )
    query_parser.add_argument(
        "phrase",
        help="Search phrase for elements"
    )
    query_parser.add_argument(
        "--url",
        help="URL to navigate to before querying",
        default=None
    )
    query_parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode",
        default=True
    )
    
    # Parse arguments
    args = parser.parse_args(argv)
    
    try:
        # Create client
        client = HybridClient(
            auto_index=True,
            headless=args.headless if hasattr(args, 'headless') else True,
            timeout_ms=args.timeout if hasattr(args, 'timeout') else 30000
        )
        
        # Execute command
        if args.command == "act":
            result = client.act(args.step, url=args.url)
            print(json.dumps(result, indent=2))
        elif args.command == "query":
            results = client.query(args.phrase, url=args.url)
            print(json.dumps(results, indent=2))
        
        # Clean up
        client.close()
        
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()