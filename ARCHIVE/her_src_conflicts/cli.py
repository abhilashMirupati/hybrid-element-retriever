# archived duplicate of src/her/cli.py
#!/usr/bin/env python
"""Command-line interface for HER framework."""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Optional, List

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.logging import RichHandler

from her.cli_api import HybridClient

# Set up rich console
console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
def cli(debug: bool):
    """HER - Hybrid Element Retriever CLI
    
    Production-ready web element location framework.
    """
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        

@cli.command()
@click.argument('phrase')
@click.option('--url', '-u', help='URL to query')
@click.option('--headless/--headed', default=True, help='Run browser in headless mode')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.option('--cache-dir', type=click.Path(), help='Cache directory')
def query(phrase: str, url: Optional[str], headless: bool, output: str, cache_dir: Optional[str]):
    """Query for an element using natural language.
    
    Example:
        her query "add to cart button" -u https://example.com
    """
    async def run():
        client = HybridClient(
            headless=headless,
            cache_dir=Path(cache_dir) if cache_dir else None
        )
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("Initializing...", total=None)
                await client.initialize()
                
                if url:
                    progress.update(task, description=f"Navigating to {url}...")
                    
                progress.update(task, description="Querying element...")
                result = await client.query(phrase, url)
                
            if output == 'json':
                console.print_json(result.to_json())
            else:
                # Table output
                table = Table(title=f"Query: '{phrase}'")
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="green")
                
                table.add_row("Success", "✅" if result.success else "❌")
                table.add_row("Selector", result.selector or "N/A")
                table.add_row("Strategy", result.strategy)
                table.add_row("Confidence", f"{result.confidence:.3f}")
                
                if result.verification:
                    table.add_row("Unique", "✅" if result.verification.get('unique') else "❌")
                    table.add_row("Visible", "✅" if result.verification.get('visible') else "❌")
                    table.add_row("Count", str(result.verification.get('count', 0)))
                    
                if result.metadata:
                    table.add_row("Semantic Score", f"{result.metadata.get('semantic_score', 0):.3f}")
                    table.add_row("Heuristic Score", f"{result.metadata.get('heuristic_score', 0):.3f}")
                    table.add_row("Explanation", result.metadata.get('explanation', ''))
                    
                if result.timing:
                    table.add_row("Total Time", f"{result.timing.get('total', 0):.3f}s")
                    
                console.print(table)
                
                if result.alternatives:
                    console.print("\n[yellow]Alternative selectors:[/yellow]")
                    for alt in result.alternatives:
                        console.print(f"  • {alt}")
                        
        finally:
            await client.close()
            
    asyncio.run(run())
    

@cli.command()
@click.argument('steps', nargs=-1, required=True)
@click.option('--url', '-u', required=True, help='URL to start from')
@click.option('--headless/--headed', default=True, help='Run browser in headless mode')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.option('--cache-dir', type=click.Path(), help='Cache directory')
def act(steps: List[str], url: str, headless: bool, output: str, cache_dir: Optional[str]):
    """Execute action steps on a page.
    
    Example:
        her act "click login button" "type user@example.com in email field" -u https://example.com
    """
    async def run():
        client = HybridClient(
            headless=headless,
            cache_dir=Path(cache_dir) if cache_dir else None
        )
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("Initializing...", total=None)
                await client.initialize()
                
                progress.update(task, description=f"Navigating to {url}...")
                
                results = []
                for i, step in enumerate(steps, 1):
                    progress.update(task, description=f"Step {i}/{len(steps)}: {step[:50]}...")
                    
                    # First step includes URL, others don't
                    step_url = url if i == 1 else None
                    result = await client.act(step, step_url)
                    results.append(result)
                    
                    if not result.success:
                        console.print(f"[red]Step {i} failed: {result.error}[/red]")
                        break
                        
            if output == 'json':
                output_data = [r.to_json() for r in results]
                console.print_json(json.dumps(output_data, indent=2))
            else:
                # Table output
                table = Table(title="Action Results")
                table.add_column("Step", style="cyan")
                table.add_column("Action", style="yellow")
                table.add_column("Success", style="green")
                table.add_column("Selector", style="blue")
                table.add_column("Time", style="magenta")
                
                for i, (step, result) in enumerate(zip(steps, results), 1):
                    table.add_row(
                        str(i),
                        result.action,
                        "✅" if result.success else "❌",
                        result.selector[:50] + "..." if len(result.selector) > 50 else result.selector,
                        f"{result.timing.get('total', 0):.2f}s"
                    )
                    
                console.print(table)
                
                # Show post-action details
                for i, result in enumerate(results, 1):
                    if result.post_action:
                        console.print(f"\n[yellow]Step {i} post-action state:[/yellow]")
                        for key, value in result.post_action.items():
                            if value:
                                console.print(f"  • {key}: {value}")
                                
        finally:
            await client.close()
            
    asyncio.run(run())
    

@cli.command()
@click.option('--cache-dir', type=click.Path(), help='Cache directory')
def stats(cache_dir: Optional[str]):
    """Show framework statistics."""
    async def run():
        client = HybridClient(
            headless=True,
            cache_dir=Path(cache_dir) if cache_dir else None
        )
        
        try:
            await client.initialize()
            stats = await client.get_stats()
            
            # Main stats table
            table = Table(title="HER Framework Statistics")
            table.add_column("Component", style="cyan")
            table.add_column("Metric", style="yellow")
            table.add_column("Value", style="green")
            
            # Session stats
            if 'session' in stats:
                session = stats['session']
                table.add_row("Session", "Total Snapshots", str(session.get('total_snapshots', 0)))
                table.add_row("Session", "Cache Hit Rate", f"{session.get('cache_hit_rate', 0):.2%}")
                table.add_row("Session", "Route Changes", str(session.get('route_changes', 0)))
                table.add_row("Session", "Reindex Count", str(session.get('reindex_count', 0)))
                
            # Cache stats
            if 'cache' in stats:
                cache = stats['cache']
                table.add_row("Cache", "Total Items", str(cache.get('total_items', 0)))
                table.add_row("Cache", "Hit Rate", f"{cache.get('hit_rate', 0):.2%}")
                table.add_row("Cache", "Evictions", str(cache.get('evictions', 0)))
                
            # Embedder stats
            if 'embedder' in stats:
                embedder = stats['embedder']
                table.add_row("Embedder", "Cache Size", str(embedder.get('cache_size', 0)))
                table.add_row("Embedder", "Using Fallback", "Yes" if embedder.get('using_fallback') else "No")
                
            # Healing stats
            if 'healing' in stats:
                healing = stats['healing']
                table.add_row("Self-Heal", "Total Healed", str(healing.get('total_healed', 0)))
                table.add_row("Self-Heal", "Unique Failures", str(healing.get('unique_failures', 0)))
                
            # Promotion stats
            if 'promotion' in stats:
                promotion = stats['promotion']
                table.add_row("Promotion", "Total Entries", str(promotion.get('total_entries', 0)))
                table.add_row("Promotion", "Avg Confidence", f"{promotion.get('avg_confidence', 0):.3f}")
                table.add_row("Promotion", "High Confidence", str(promotion.get('high_confidence_count', 0)))
                
            console.print(table)
            
        finally:
            await client.close()
            
    asyncio.run(run())
    

@cli.command()
@click.option('--output', '-o', type=click.Path(), default='requirements.txt', help='Output file')
def freeze(output: str):
    """Export requirements for reproducibility."""
    import pkg_resources
    
    installed_packages = [d for d in pkg_resources.working_set]
    requirements = []
    
    for package in installed_packages:
        if package.project_name not in ['pip', 'setuptools', 'wheel']:
            requirements.append(f"{package.project_name}=={package.version}")
            
    requirements.sort()
    
    with open(output, 'w') as f:
        f.write('\n'.join(requirements))
        
    console.print(f"[green]Requirements exported to {output}[/green]")
    console.print(f"Total packages: {len(requirements)}")
    

@cli.command()
def version():
    """Show HER version."""
    from her import __version__
    console.print(f"HER version: [cyan]{__version__}[/cyan]")
    
    # Check component availability
    checks = [
        ("Playwright", "playwright"),
        ("ONNX Runtime", "onnxruntime"),
        ("Transformers", "transformers"),
        ("NumPy", "numpy"),
        ("SciPy", "scipy"),
    ]
    
    table = Table(title="Component Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Version", style="yellow")
    
    for name, module_name in checks:
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', 'unknown')
            table.add_row(name, "✅ Installed", version)
        except ImportError:
            table.add_row(name, "❌ Not installed", "N/A")
            
    console.print(table)
    

def main():
    """Main entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if '--debug' in sys.argv:
            console.print_exception()
        sys.exit(1)
        

if __name__ == '__main__':
    main()