#!/usr/bin/env python
"""Functional validation runner for HER framework.

Runs end-to-end tests against ground truth fixtures.
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import statistics

from playwright.async_api import async_playwright, Page
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from her.cli_api import HybridClient

# Set up console and logging
console = Console()
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a single validation test."""
    fixture_name: str
    intent_id: str
    query: str
    success: bool
    matched_selector: str
    expected_selector: str
    strategy_match: bool
    uniqueness_match: bool
    cold_latency_ms: float
    warm_latency_ms: float
    cache_hit: bool
    error: Optional[str] = None
    details: Dict[str, Any] = None
    

@dataclass
class FixtureResult:
    """Result for a complete fixture."""
    name: str
    total_intents: int
    passed: int
    failed: int
    accuracy: float
    avg_cold_latency_ms: float
    avg_warm_latency_ms: float
    cache_hit_rate: float
    failures: List[str]
    

@dataclass
class OverallResults:
    """Overall validation results."""
    total_fixtures: int
    total_intents: int
    total_passed: int
    total_failed: int
    overall_accuracy: float
    ir_at_1: float
    median_cold_latency_ms: float
    median_warm_latency_ms: float
    overall_cache_hit_rate: float
    fixture_results: List[FixtureResult]
    validation_results: List[ValidationResult]
    

class FunctionalValidator:
    """Runs functional validation tests."""
    
    def __init__(self, fixtures_dir: Path, headless: bool = True):
        self.fixtures_dir = fixtures_dir
        self.headless = headless
        self.results: List[ValidationResult] = []
        
    async def run_all(self) -> OverallResults:
        """Run all fixture tests.
        
        Returns:
            OverallResults with comprehensive metrics
        """
        fixture_files = list(self.fixtures_dir.glob("*.json"))
        fixture_results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            overall_task = progress.add_task(
                f"Running {len(fixture_files)} fixtures...",
                total=len(fixture_files)
            )
            
            for fixture_file in fixture_files:
                # Skip HTML files
                if fixture_file.suffix != '.json':
                    continue
                    
                fixture_name = fixture_file.stem
                progress.update(overall_task, description=f"Testing {fixture_name}...")
                
                # Run fixture
                fixture_result = await self.run_fixture(fixture_file)
                fixture_results.append(fixture_result)
                
                progress.advance(overall_task)
                
        # Calculate overall metrics
        return self._calculate_overall_results(fixture_results)
        
    async def run_fixture(self, fixture_file: Path) -> FixtureResult:
        """Run a single fixture test.
        
        Args:
            fixture_file: Path to fixture JSON file
            
        Returns:
            FixtureResult with fixture-level metrics
        """
        # Load fixture
        with open(fixture_file) as f:
            fixture_data = json.load(f)
            
        fixture_name = fixture_data['fixture']
        intents = fixture_data['intents']
        
        # Check for corresponding HTML file
        html_file = fixture_file.with_suffix('.html')
        if not html_file.exists():
            console.print(f"[red]HTML file not found for {fixture_name}[/red]")
            return FixtureResult(
                name=fixture_name,
                total_intents=len(intents),
                passed=0,
                failed=len(intents),
                accuracy=0.0,
                avg_cold_latency_ms=0.0,
                avg_warm_latency_ms=0.0,
                cache_hit_rate=0.0,
                failures=[f"HTML file not found: {html_file}"]
            )
            
        # Initialize client
        client = HybridClient(headless=self.headless)
        await client.initialize()
        
        # Serve HTML file
        file_url = f"file://{html_file.absolute()}"
        await client.page.goto(file_url)
        
        intent_results = []
        failures = []
        
        try:
            for intent in intents:
                # Run cold (clear caches)
                if client.element_embedder:
                    client.element_embedder.clear_cache()
                if client.vector_cache:
                    await client.vector_cache.clear()
                    
                cold_result = await self._run_intent(client, intent, fixture_name, is_cold=True)
                
                # Run warm (with caches)
                warm_result = await self._run_intent(client, intent, fixture_name, is_cold=False)
                
                # Combine results
                cold_result.warm_latency_ms = warm_result.cold_latency_ms
                cold_result.cache_hit = warm_result.cache_hit
                
                intent_results.append(cold_result)
                self.results.append(cold_result)
                
                if not cold_result.success:
                    failures.append(f"{intent['id']}: {cold_result.error}")
                    
        finally:
            await client.close()
            
        # Calculate fixture metrics
        passed = sum(1 for r in intent_results if r.success)
        failed = len(intent_results) - passed
        accuracy = passed / len(intent_results) if intent_results else 0
        
        cold_latencies = [r.cold_latency_ms for r in intent_results if r.cold_latency_ms > 0]
        warm_latencies = [r.warm_latency_ms for r in intent_results if r.warm_latency_ms > 0]
        
        return FixtureResult(
            name=fixture_name,
            total_intents=len(intents),
            passed=passed,
            failed=failed,
            accuracy=accuracy,
            avg_cold_latency_ms=statistics.mean(cold_latencies) if cold_latencies else 0,
            avg_warm_latency_ms=statistics.mean(warm_latencies) if warm_latencies else 0,
            cache_hit_rate=sum(1 for r in intent_results if r.cache_hit) / len(intent_results) if intent_results else 0,
            failures=failures
        )
        
    async def _run_intent(
        self,
        client: HybridClient,
        intent: Dict[str, Any],
        fixture_name: str,
        is_cold: bool
    ) -> ValidationResult:
        """Run a single intent test.
        
        Args:
            client: HER client
            intent: Intent data
            fixture_name: Fixture name
            is_cold: Whether this is a cold run
            
        Returns:
            ValidationResult
        """
        start_time = time.time()
        
        try:
            # Query for element
            query_result = await client.query(intent['query'])
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Get ground truth
            ground_truth = intent['ground_truth']
            expected_selector = ground_truth['used_selector']
            expected_strategy = ground_truth['strategy']
            
            # Check if it's a negative test
            if ground_truth.get('should_fail', False):
                success = not query_result.success
                error = None if success else "Expected to fail but succeeded"
            else:
                # Validate results
                success = True
                error = None
                
                # Check selector match (exact or pattern)
                selector_match = self._check_selector_match(
                    query_result.selector,
                    expected_selector
                )
                if not selector_match:
                    success = False
                    error = f"Selector mismatch: got '{query_result.selector}', expected '{expected_selector}'"
                    
                # Check strategy
                strategy_match = query_result.strategy == expected_strategy
                if not strategy_match and success:
                    success = False
                    error = f"Strategy mismatch: got '{query_result.strategy}', expected '{expected_strategy}'"
                    
                # Check uniqueness
                if 'unique' in ground_truth:
                    expected_unique = ground_truth['unique']
                    actual_unique = query_result.verification.get('unique', False)
                    if expected_unique != actual_unique:
                        success = False
                        error = f"Uniqueness mismatch: got {actual_unique}, expected {expected_unique}"
                        
                # Check not matching (disambiguation)
                if 'not_matching' in ground_truth and success:
                    for should_not_match in ground_truth['not_matching']:
                        if should_not_match.lower() in query_result.selector.lower():
                            success = False
                            error = f"Incorrectly matched '{should_not_match}' in selector"
                            break
                            
            # Check cache hit (only on warm runs)
            cache_hit = False
            if not is_cold and client.vector_cache:
                stats = await client.vector_cache.get_stats()
                cache_hit = stats['hit_rate'] > 0.5
                
            return ValidationResult(
                fixture_name=fixture_name,
                intent_id=intent['id'],
                query=intent['query'],
                success=success,
                matched_selector=query_result.selector,
                expected_selector=expected_selector,
                strategy_match=query_result.strategy == expected_strategy,
                uniqueness_match=query_result.verification.get('unique', False) == ground_truth.get('unique', True),
                cold_latency_ms=latency_ms if is_cold else 0,
                warm_latency_ms=0,  # Will be set by caller
                cache_hit=cache_hit,
                error=error,
                details={
                    'confidence': query_result.confidence,
                    'semantic_score': query_result.metadata.get('semantic_score', 0),
                    'heuristic_score': query_result.metadata.get('heuristic_score', 0)
                }
            )
            
        except Exception as e:
            return ValidationResult(
                fixture_name=fixture_name,
                intent_id=intent['id'],
                query=intent['query'],
                success=False,
                matched_selector="",
                expected_selector=expected_selector,
                strategy_match=False,
                uniqueness_match=False,
                cold_latency_ms=(time.time() - start_time) * 1000 if is_cold else 0,
                warm_latency_ms=0,
                cache_hit=False,
                error=str(e)
            )
            
    def _check_selector_match(self, actual: str, expected: str) -> bool:
        """Check if selectors match (exact or pattern).
        
        Args:
            actual: Actual selector
            expected: Expected selector (can be regex)
            
        Returns:
            True if match
        """
        if not actual:
            return False
            
        # Exact match
        if actual == expected:
            return True
            
        # Normalize and compare
        actual_normalized = actual.replace('"', "'").replace(' ', '')
        expected_normalized = expected.replace('"', "'").replace(' ', '')
        
        if actual_normalized == expected_normalized:
            return True
            
        # Check if expected is contained in actual (for flexible matching)
        if expected in actual or expected_normalized in actual_normalized:
            return True
            
        return False
        
    def _calculate_overall_results(self, fixture_results: List[FixtureResult]) -> OverallResults:
        """Calculate overall results.
        
        Args:
            fixture_results: List of fixture results
            
        Returns:
            OverallResults with aggregated metrics
        """
        total_passed = sum(f.passed for f in fixture_results)
        total_failed = sum(f.failed for f in fixture_results)
        total_intents = total_passed + total_failed
        
        # IR@1 calculation (percentage of first-try successes)
        ir_at_1 = total_passed / total_intents if total_intents > 0 else 0
        
        # Latency calculations
        all_cold_latencies = [r.cold_latency_ms for r in self.results if r.cold_latency_ms > 0]
        all_warm_latencies = [r.warm_latency_ms for r in self.results if r.warm_latency_ms > 0]
        
        # Cache hit rate
        cache_hits = sum(1 for r in self.results if r.cache_hit)
        cache_attempts = sum(1 for r in self.results if r.warm_latency_ms > 0)
        
        return OverallResults(
            total_fixtures=len(fixture_results),
            total_intents=total_intents,
            total_passed=total_passed,
            total_failed=total_failed,
            overall_accuracy=total_passed / total_intents if total_intents > 0 else 0,
            ir_at_1=ir_at_1,
            median_cold_latency_ms=statistics.median(all_cold_latencies) if all_cold_latencies else 0,
            median_warm_latency_ms=statistics.median(all_warm_latencies) if all_warm_latencies else 0,
            overall_cache_hit_rate=cache_hits / cache_attempts if cache_attempts > 0 else 0,
            fixture_results=fixture_results,
            validation_results=self.results
        )
        

def generate_report(results: OverallResults, output_dir: Path) -> None:
    """Generate validation reports.
    
    Args:
        results: Overall results
        output_dir: Output directory for reports
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate JSON report
    json_report = {
        'timestamp': time.time(),
        'summary': {
            'total_fixtures': results.total_fixtures,
            'total_intents': results.total_intents,
            'passed': results.total_passed,
            'failed': results.total_failed,
            'accuracy': results.overall_accuracy,
            'ir_at_1': results.ir_at_1,
            'median_cold_latency_ms': results.median_cold_latency_ms,
            'median_warm_latency_ms': results.median_warm_latency_ms,
            'cache_hit_rate': results.overall_cache_hit_rate
        },
        'fixtures': [asdict(f) for f in results.fixture_results],
        'details': [asdict(v) for v in results.validation_results]
    }
    
    with open(output_dir / 'functional_results.json', 'w') as f:
        json.dump(json_report, f, indent=2)
        
    # Generate Markdown report
    md_lines = [
        "# HER Functional Validation Report\n",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        "## Summary\n",
        f"- **Total Fixtures**: {results.total_fixtures}",
        f"- **Total Intents**: {results.total_intents}",
        f"- **Passed**: {results.total_passed} ({results.overall_accuracy:.1%})",
        f"- **Failed**: {results.total_failed}",
        f"- **IR@1**: {results.ir_at_1:.1%}",
        f"- **Median Cold Latency**: {results.median_cold_latency_ms:.0f}ms",
        f"- **Median Warm Latency**: {results.median_warm_latency_ms:.0f}ms",
        f"- **Cache Hit Rate**: {results.overall_cache_hit_rate:.1%}\n",
        "## Fixture Results\n",
        "| Fixture | Intents | Passed | Failed | Accuracy | Avg Cold (ms) | Avg Warm (ms) | Cache Hit Rate |",
        "|---------|---------|--------|--------|----------|---------------|---------------|----------------|\n"
    ]
    
    for fixture in results.fixture_results:
        md_lines.append(
            f"| {fixture.name} | {fixture.total_intents} | {fixture.passed} | "
            f"{fixture.failed} | {fixture.accuracy:.1%} | {fixture.avg_cold_latency_ms:.0f} | "
            f"{fixture.avg_warm_latency_ms:.0f} | {fixture.cache_hit_rate:.1%} |"
        )
        
    # Add failures section
    md_lines.append("\n## Failures\n")
    
    for fixture in results.fixture_results:
        if fixture.failures:
            md_lines.append(f"\n### {fixture.name}\n")
            for failure in fixture.failures:
                md_lines.append(f"- {failure}")
                
    # Add detailed results
    md_lines.append("\n## Detailed Results\n")
    
    failed_results = [r for r in results.validation_results if not r.success]
    if failed_results:
        md_lines.append("\n### Failed Tests\n")
        for result in failed_results[:20]:  # Limit to 20
            md_lines.append(f"\n**{result.fixture_name}/{result.intent_id}**")
            md_lines.append(f"- Query: `{result.query}`")
            md_lines.append(f"- Expected: `{result.expected_selector}`")
            md_lines.append(f"- Got: `{result.matched_selector}`")
            md_lines.append(f"- Error: {result.error}")
            
    with open(output_dir / 'FUNCTIONAL_REPORT.md', 'w') as f:
        f.write('\n'.join(md_lines))
        
    console.print(f"[green]Reports generated in {output_dir}[/green]")
    

def print_summary(results: OverallResults) -> None:
    """Print results summary to console.
    
    Args:
        results: Overall results
    """
    # Summary table
    table = Table(title="Functional Validation Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Fixtures", str(results.total_fixtures))
    table.add_row("Total Intents", str(results.total_intents))
    table.add_row("Passed", f"{results.total_passed} ({results.overall_accuracy:.1%})")
    table.add_row("Failed", str(results.total_failed))
    table.add_row("IR@1", f"{results.ir_at_1:.1%}")
    table.add_row("Median Cold Latency", f"{results.median_cold_latency_ms:.0f}ms")
    table.add_row("Median Warm Latency", f"{results.median_warm_latency_ms:.0f}ms")
    table.add_row("Cache Hit Rate", f"{results.overall_cache_hit_rate:.1%}")
    
    console.print(table)
    
    # Fixture details table
    fixture_table = Table(title="Fixture Results")
    fixture_table.add_column("Fixture", style="cyan")
    fixture_table.add_column("Passed", style="green")
    fixture_table.add_column("Failed", style="red")
    fixture_table.add_column("Accuracy", style="yellow")
    
    for fixture in results.fixture_results:
        fixture_table.add_row(
            fixture.name,
            str(fixture.passed),
            str(fixture.failed),
            f"{fixture.accuracy:.1%}"
        )
        
    console.print(fixture_table)
    
    # Print failures
    if results.total_failed > 0:
        console.print("\n[red]Failed Tests:[/red]")
        for fixture in results.fixture_results:
            if fixture.failures:
                console.print(f"\n[yellow]{fixture.name}:[/yellow]")
                for failure in fixture.failures[:5]:  # Limit output
                    console.print(f"  • {failure}")
                    

async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run HER functional validation")
    parser.add_argument(
        '--fixtures-dir',
        type=Path,
        default=Path('functional_harness/fixtures'),
        help='Directory containing fixture files'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('.'),
        help='Output directory for reports'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        default=True,
        help='Run browser in headless mode'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Run validation
    console.print("[bold blue]HER Functional Validation[/bold blue]\n")
    console.print(f"Fixtures directory: {args.fixtures_dir}")
    
    validator = FunctionalValidator(args.fixtures_dir, headless=args.headless)
    results = await validator.run_all()
    
    # Generate reports
    generate_report(results, args.output_dir)
    
    # Print summary
    print_summary(results)
    
    # Exit with error code if failures
    if results.total_failed > 0:
        console.print(f"\n[red]❌ {results.total_failed} tests failed[/red]")
        sys.exit(1)
    else:
        console.print(f"\n[green]✅ All {results.total_passed} tests passed![/green]")
        sys.exit(0)
        

if __name__ == '__main__':
    asyncio.run(main())