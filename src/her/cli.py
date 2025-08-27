"""CLI entrypoints for HER."""
import argparse
import json
import sys
import logging
from pathlib import Path
from typing import Optional

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
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Act command
    act_parser = subparsers.add_parser(
        "act",
        help="Execute an action on a page"
    )
    act_parser.add_argument(
        "step",
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
    act_parser.add_argument(
        "--output",
        help="Output format (json, text)",
        default="json",
        choices=["json", "text"]
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
    query_parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of results",
        default=10
    )
    query_parser.add_argument(
        "--output",
        help="Output format (json, text)",
        default="json",
        choices=["json", "text"]
    )
    
    # Cache command
    cache_parser = subparsers.add_parser(
        "cache",
        help="Manage embedding cache"
    )
    cache_parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear all cached embeddings"
    )
    cache_parser.add_argument(
        "--stats",
        action="store_true",
        help="Show cache statistics"
    )
    
    # Version command
    version_parser = subparsers.add_parser(
        "version",
        help="Show version information"
    )
    
    # If no command specified, show help
    if len(sys.argv if argv is None else argv) == 1:
        parser.print_help()
        return 0
    
    # Parse arguments
    args = parser.parse_args(argv)
    
    try:
        # Handle cache command
        if args.command == "cache":
            handle_cache_command(args)
            return 0
        
        # Handle version command
        if args.command == "version":
            print("Hybrid Element Retriever (HER) v0.1.0")
            return 0
        
        # Import here to avoid loading everything for simple commands
        from .cli_api import HybridClient
        
        # Create client for act/query commands
        if args.command in ["act", "query"]:
            client = HybridClient(
                auto_index=True,
                headless=args.headless,
                timeout_ms=args.timeout if hasattr(args, 'timeout') else 30000
            )
            
            try:
                # Execute command
                if args.command == "act":
                    result = client.act(args.step, url=args.url)
                    output_result(result, args.output)
                    
                elif args.command == "query":
                    results = client.query(args.phrase, url=args.url)
                    # Limit results if specified
                    if hasattr(args, 'limit') and args.limit > 0:
                        results = results[:args.limit]
                    output_result(results, args.output)
                
            finally:
                # Always clean up
                client.close()
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Command failed: {e}")
        if "--debug" in sys.argv:
            import traceback
            traceback.print_exc()
        return 1


def handle_cache_command(args):
    """Handle cache management commands."""
    from .config import get_embeddings_cache_dir, get_promotion_store_path
    
    if args.clear:
        # Clear embedding cache
        cache_dir = get_embeddings_cache_dir()
        if cache_dir.exists():
            import shutil
            shutil.rmtree(cache_dir)
            cache_dir.mkdir(parents=True, exist_ok=True)
            print("✓ Embedding cache cleared")
        
        # Clear promotion store
        promotion_path = get_promotion_store_path()
        if promotion_path.exists():
            promotion_path.unlink()
            print("✓ Promotion store cleared")
        
        print("Cache cleared successfully")
        
    elif args.stats:
        # Show cache statistics
        cache_dir = get_embeddings_cache_dir()
        promotion_path = get_promotion_store_path()
        
        stats = {
            "embedding_cache": {
                "path": str(cache_dir),
                "exists": cache_dir.exists()
            },
            "promotion_store": {
                "path": str(promotion_path),
                "exists": promotion_path.exists()
            }
        }
        
        if cache_dir.exists():
            # Count cache files
            cache_files = list(cache_dir.glob("*.db"))
            stats["embedding_cache"]["files"] = len(cache_files)
            stats["embedding_cache"]["size_mb"] = sum(
                f.stat().st_size for f in cache_files
            ) / (1024 * 1024)
        
        if promotion_path.exists():
            stats["promotion_store"]["size_kb"] = promotion_path.stat().st_size / 1024
            # Try to load and count promotions
            try:
                import json
                with open(promotion_path) as f:
                    promotions = json.load(f)
                    stats["promotion_store"]["entries"] = len(promotions)
            except Exception:
                stats["promotion_store"]["entries"] = "unknown"
        
        print(json.dumps(stats, indent=2))
    
    else:
        print("Use --clear to clear cache or --stats to show statistics")


def output_result(result, format="json"):
    """Output result in specified format."""
    if format == "json":
        # Ensure clean JSON output
        if isinstance(result, dict):
            # Remove None values and empty strings
            clean_result = {
                k: v for k, v in result.items() 
                if v is not None and v != ""
            }
            print(json.dumps(clean_result, indent=2, ensure_ascii=False))
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif format == "text":
        if isinstance(result, dict):
            # Format as human-readable text
            if "success" in result:
                status = "✓" if result.get("success") else "✗"
                print(f"{status} Action: {result.get('action', 'unknown')}")
                if result.get("error"):
                    print(f"  Error: {result['error']}")
                if result.get("duration_ms"):
                    print(f"  Duration: {result['duration_ms']}ms")
            else:
                for key, value in result.items():
                    if value is not None and value != "":
                        print(f"{key}: {value}")
        
        elif isinstance(result, list):
            for i, item in enumerate(result, 1):
                if isinstance(item, dict):
                    print(f"\n{i}. {item.get('selector', 'unknown')}")
                    print(f"   Score: {item.get('score', 0):.3f}")
                    if item.get('explanation'):
                        print(f"   {item['explanation']}")
                else:
                    print(f"{i}. {item}")
        
        else:
            print(result)


if __name__ == "__main__":
    sys.exit(main())