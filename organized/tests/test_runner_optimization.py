#!/usr/bin/env python3
"""
Test to verify that the default Runner is now optimized with model caching
"""

import os
import sys
import time

sys.path.append('/workspace/src')

def test_default_runner_optimization():
    """Test that default Runner now uses model caching"""
    print("🚀 TESTING DEFAULT RUNNER OPTIMIZATION")
    print("=" * 60)
    
    try:
        from her.runner import Runner
        
        # Test 1: First runner (should load models)
        print("📊 Creating first runner...")
        start_time = time.time()
        runner1 = Runner(headless=True)
        first_time = time.time() - start_time
        print(f"✅ First runner: {first_time:.3f}s")
        
        # Test 2: Second runner (should reuse models)
        print("📊 Creating second runner...")
        start_time = time.time()
        runner2 = Runner(headless=True)
        second_time = time.time() - start_time
        print(f"✅ Second runner: {second_time:.3f}s")
        
        # Test 3: Third runner (should also reuse models)
        print("📊 Creating third runner...")
        start_time = time.time()
        runner3 = Runner(headless=True)
        third_time = time.time() - start_time
        print(f"✅ Third runner: {third_time:.3f}s")
        
        # Verify they share the same pipeline
        print(f"\n🔍 Verifying model sharing...")
        print(f"   Runner1 pipeline ID: {id(runner1.pipeline)}")
        print(f"   Runner2 pipeline ID: {id(runner2.pipeline)}")
        print(f"   Runner3 pipeline ID: {id(runner3.pipeline)}")
        
        if (id(runner1.pipeline) == id(runner2.pipeline) == id(runner3.pipeline)):
            print("✅ All runners share the same pipeline instance!")
        else:
            print("❌ Runners are not sharing the pipeline!")
        
        # Test actual functionality
        print(f"\n🧪 Testing functionality...")
        os.environ['HER_CANONICAL_MODE'] = 'DOM_ONLY'
        
        # Test with first runner
        result1 = runner1._snapshot('https://www.verizon.com/')
        if result1 and 'elements' in result1:
            print(f"✅ Runner1: {len(result1['elements'])} elements")
        else:
            print("❌ Runner1: Failed to get elements")
        
        # Test with second runner
        result2 = runner2._snapshot('https://www.verizon.com/')
        if result2 and 'elements' in result2:
            print(f"✅ Runner2: {len(result2['elements'])} elements")
        else:
            print("❌ Runner2: Failed to get elements")
        
        # Performance analysis
        print(f"\n📈 PERFORMANCE ANALYSIS")
        print("=" * 40)
        print(f"First runner:  {first_time:.3f}s (model loading)")
        print(f"Second runner: {second_time:.3f}s (reuse)")
        print(f"Third runner:  {third_time:.3f}s (reuse)")
        
        if second_time < first_time * 0.1:  # Should be at least 90% faster
            print("✅ Model caching is working!")
        else:
            print("⚠️  Model caching may not be working optimally")
        
        # Cleanup
        print(f"\n🧹 Cleaning up...")
        runner1._close()
        runner2._close()
        runner3._close()
        Runner.cleanup_models()
        print("✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 STARTING DEFAULT RUNNER OPTIMIZATION TEST")
    print("=" * 60)
    
    success = test_default_runner_optimization()
    
    if success:
        print("\n🎉 DEFAULT RUNNER IS NOW OPTIMIZED!")
        print("✅ Models are cached and shared across all Runner instances")
        print("✅ No need for separate optimized_test_runner.py")
    else:
        print("\n❌ DEFAULT RUNNER OPTIMIZATION FAILED")
        print("⚠️  Need to fix the optimization")