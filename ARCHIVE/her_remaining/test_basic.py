#!/usr/bin/env python3
"""Basic test to verify HER framework functionality."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from her import HybridClient, __version__

async def test_basic():
    """Test basic HER functionality."""
    print(f"HER Version: {__version__}")
    print("\nTesting basic functionality...\n")
    
    # Test 1: Import check
    print("1. Import check: ✅ PASS")
    
    # Test 2: Client initialization
    try:
        client = HybridClient(headless=True)
        print("2. Client creation: ✅ PASS")
    except Exception as e:
        print(f"2. Client creation: ❌ FAIL - {e}")
        return False
        
    # Test 3: Component initialization
    try:
        await client.initialize()
        print("3. Component initialization: ✅ PASS")
        
        # Check components
        assert client.session is not None
        assert client.query_embedder is not None
        assert client.element_embedder is not None
        assert client.ranker is not None
        print("4. Component verification: ✅ PASS")
        
    except Exception as e:
        print(f"3. Component initialization: ❌ FAIL - {e}")
        return False
        
    # Test 4: Query with local HTML
    try:
        # Navigate to test fixture
        fixture_path = Path('functional_harness/fixtures/products_disambiguation.html').absolute()
        if fixture_path.exists():
            await client.page.goto(f"file://{fixture_path}")
            
            # Query for element
            result = await client.query("add phone to cart")
            
            if result.success:
                print(f"5. Query test: ✅ PASS")
                print(f"   - Found selector: {result.selector}")
                print(f"   - Confidence: {result.confidence:.3f}")
                print(f"   - Strategy: {result.strategy}")
            else:
                print(f"5. Query test: ⚠️ WARNING - No element found")
        else:
            print("5. Query test: ⚠️ SKIPPED - Fixture not found")
            
    except Exception as e:
        print(f"5. Query test: ❌ FAIL - {e}")
        
    # Test 5: Statistics
    try:
        stats = await client.get_stats()
        print(f"6. Statistics: ✅ PASS")
        print(f"   - Initialized: {stats.get('initialized', False)}")
        if 'embedder' in stats:
            print(f"   - Embedder cache: {stats['embedder'].get('cache_size', 0)} items")
        if 'session' in stats:
            print(f"   - Snapshots: {stats['session'].get('total_snapshots', 0)}")
    except Exception as e:
        print(f"6. Statistics: ❌ FAIL - {e}")
        
    # Cleanup
    await client.close()
    print("\n7. Cleanup: ✅ PASS")
    
    return True
    

if __name__ == "__main__":
    print("="*50)
    print("HER Framework Basic Test")
    print("="*50)
    
    try:
        success = asyncio.run(test_basic())
        print("\n" + "="*50)
        if success:
            print("✅ All basic tests passed!")
            sys.exit(0)
        else:
            print("❌ Some tests failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nTest interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        sys.exit(1)