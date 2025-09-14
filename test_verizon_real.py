#!/usr/bin/env python3
"""
Verizon Real Test - Uses actual HER system with real browser automation.
Fails hard if setup is incomplete.
"""

import sys
import os
import time
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def check_real_setup():
    """Check if real setup is complete. Fail hard if not."""
    print("🔍 Checking Real Setup Requirements...")
    
    # Check 1: Required Python packages
    required_packages = [
        ('onnxruntime', 'onnxruntime'),
        ('transformers', 'transformers'), 
        ('torch', 'torch'),
        ('faiss', 'faiss'),
        ('playwright', 'playwright'),
        ('numpy', 'numpy'),
        ('scipy', 'scipy'),
        ('scikit-learn', 'sklearn'),
        ('psutil', 'psutil'),
        ('python-dotenv', 'dotenv')
    ]
    
    missing_packages = []
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"  ✅ {package_name}")
        except ImportError:
            missing_packages.append(package_name)
            print(f"  ❌ {package_name} - MISSING")
    
    if missing_packages:
        print(f"\n❌ HARD FAIL: Missing required packages: {', '.join(missing_packages)}")
        print("📋 Install missing packages with:")
        print(f"   pip install --break-system-packages {' '.join(missing_packages)}")
        return False
    
    # Check 2: Models directory and files
    models_dir = Path("src/her/models")
    required_models = [
        "e5-small-onnx/model.onnx",
        "e5-small-onnx/tokenizer.json", 
        "markuplm-base/config.json",
        "markuplm-base/pytorch_model.bin",
        "markuplm-base/tokenizer.json"
    ]
    
    missing_models = []
    for model_file in required_models:
        model_path = models_dir / model_file
        if model_path.exists():
            print(f"  ✅ {model_file}")
        else:
            missing_models.append(model_file)
            print(f"  ❌ {model_file} - MISSING")
    
    if missing_models:
        print(f"\n❌ HARD FAIL: Missing required models: {', '.join(missing_models)}")
        print("📋 Install models with:")
        print("   bash scripts/setup/install_models.sh")
        return False
    
    # Check 3: Playwright browsers
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                browser.close()
                print("  ✅ Playwright Chromium browser")
            except Exception as e:
                print(f"  ❌ Playwright Chromium browser - MISSING: {e}")
                print("📋 Install Playwright browsers with:")
                print("   python -m playwright install chromium")
                return False
    except Exception as e:
        print(f"  ❌ Playwright not working: {e}")
        return False
    
    print("\n✅ Real setup is complete!")
    return True

def run_real_verizon_test():
    """Run real Verizon test with actual browser automation."""
    print("\n🎯 VERIZON REAL TEST - Using Actual HER System")
    print("=" * 60)
    
    # Import HER components
    try:
        from src.her.cli.cli_api import HybridElementRetrieverClient
        from src.her.config.settings import HERConfig
        print("✅ HER components imported successfully")
    except Exception as e:
        print(f"❌ HARD FAIL: Cannot import HER components: {e}")
        print("📋 Check that HER source code is properly installed")
        return False
    
    # Test steps
    test_steps = [
        {
            'query': 'Navigate to "https://www.verizon.com/"',
            'expected_url': 'https://www.verizon.com/',
            'description': 'Navigate to Verizon homepage'
        },
        {
            'query': 'Click on "Phones" button',
            'expected_url': None,
            'description': 'Click on Phones navigation'
        },
        {
            'query': 'Click on "Apple" filter',
            'expected_url': None,
            'description': 'Click on Apple brand filter'
        },
        {
            'query': 'Click on "Apple iPhone 17" device',
            'expected_url': None,
            'description': 'Click on iPhone 17 product'
        },
        {
            'query': 'Validate it landed on "https://www.verizon.com/smartphones/apple-iphone-17/"',
            'expected_url': 'https://www.verizon.com/smartphones/apple-iphone-17/',
            'description': 'Validate URL navigation'
        },
        {
            'query': 'Validate "Apple iPhone 17" text on pdp page',
            'expected_url': None,
            'description': 'Validate product title text'
        },
        {
            'query': 'Click on "White" color',
            'expected_url': None,
            'description': 'Click on White color option'
        }
    ]
    
    # Test both modes
    modes = ['semantic', 'no_semantic']
    results = {}
    
    for mode in modes:
        print(f"\n🚀 Testing {mode.upper()} Mode")
        print("-" * 40)
        
        try:
            # Initialize client
            client = HybridElementRetrieverClient(use_semantic_search=(mode == 'semantic'))
            print(f"✅ {mode} client initialized")
            
            step_results = []
            total_time = 0
            successful_steps = 0
            
            for i, step in enumerate(test_steps, 1):
                print(f"\n📋 Step {i}: {step['description']}")
                print(f"  Query: {step['query']}")
                
                start_time = time.time()
                
                try:
                    # Navigate if URL provided
                    if step['expected_url']:
                        result = client.query(step['query'], url=step['expected_url'])
                    else:
                        result = client.query(step['query'])
                    
                    execution_time = (time.time() - start_time) * 1000
                    total_time += execution_time
                    
                    # Extract results
                    if result and isinstance(result, dict):
                        # Get XPath
                        xpath = result.get('selector') or result.get('xpath', 'N/A')
                        
                        # Get canonical descriptor
                        element = result.get('element', {})
                        canonical_parts = []
                        
                        if element.get('tag'):
                            canonical_parts.append(f"tag={element['tag']}")
                        
                        attrs = element.get('attributes', {})
                        for attr in ['id', 'class', 'type', 'role', 'name', 'data-testid']:
                            if attrs.get(attr):
                                canonical_parts.append(f"{attr}={attrs[attr]}")
                        
                        if element.get('text'):
                            text = element['text'][:50] + "..." if len(element['text']) > 50 else element['text']
                            canonical_parts.append(f"text={text}")
                        
                        canonical = " | ".join(canonical_parts) if canonical_parts else "N/A"
                        
                        # Get confidence
                        confidence = result.get('confidence', 0.0)
                        
                        # Determine success
                        success = confidence > 0.5 and xpath != 'N/A'
                        
                        if success:
                            successful_steps += 1
                            print(f"  ✅ Success: True")
                        else:
                            print(f"  ❌ Success: False")
                        
                        print(f"  🎯 XPath: {xpath}")
                        print(f"  📝 Canonical: {canonical}")
                        print(f"  📊 Confidence: {confidence:.3f}")
                        print(f"  ⚡ Time: {execution_time:.1f}ms")
                        print(f"  🔧 Strategy: {result.get('strategy', 'unknown')}")
                        
                        step_results.append({
                            'step_number': i,
                            'query': step['query'],
                            'mode': mode,
                            'execution_time_ms': execution_time,
                            'success': success,
                            'xpath': xpath,
                            'element_canonical': canonical,
                            'confidence': confidence,
                            'strategy': result.get('strategy', 'unknown'),
                            'error': None,
                            'element_details': element
                        })
                    else:
                        execution_time = (time.time() - start_time) * 1000
                        total_time += execution_time
                        
                        print(f"  ❌ Success: False")
                        print(f"  🎯 XPath: None")
                        print(f"  📝 Canonical: None")
                        print(f"  📊 Confidence: 0.000")
                        print(f"  ⚡ Time: {execution_time:.1f}ms")
                        print(f"  🔧 Strategy: unknown")
                        print(f"  ❌ Error: No valid result returned")
                        
                        step_results.append({
                            'step_number': i,
                            'query': step['query'],
                            'mode': mode,
                            'execution_time_ms': execution_time,
                            'success': False,
                            'xpath': None,
                            'element_canonical': None,
                            'confidence': 0.0,
                            'strategy': 'unknown',
                            'error': 'No valid result returned',
                            'element_details': None
                        })
                
                except Exception as e:
                    execution_time = (time.time() - start_time) * 1000
                    total_time += execution_time
                    
                    print(f"  ❌ Success: False")
                    print(f"  🎯 XPath: None")
                    print(f"  📝 Canonical: None")
                    print(f"  📊 Confidence: 0.000")
                    print(f"  ⚡ Time: {execution_time:.1f}ms")
                    print(f"  🔧 Strategy: unknown")
                    print(f"  ❌ Error: {str(e)}")
                    
                    step_results.append({
                        'step_number': i,
                        'query': step['query'],
                        'mode': mode,
                        'execution_time_ms': execution_time,
                        'success': False,
                        'xpath': None,
                        'element_canonical': None,
                        'confidence': 0.0,
                        'strategy': 'unknown',
                        'error': str(e),
                        'element_details': None
                    })
            
            # Calculate metrics
            success_rate = (successful_steps / len(test_steps)) * 100
            avg_time = total_time / len(test_steps)
            
            print(f"\n📊 {mode.upper()} Mode Summary:")
            print(f"   Total Time: {total_time:.1f}ms")
            print(f"   Success Rate: {success_rate:.1f}% ({successful_steps}/{len(test_steps)})")
            print(f"   Avg Step Time: {avg_time:.1f}ms")
            
            results[mode] = {
                'steps': step_results,
                'summary': {
                    'mode': mode,
                    'total_time': f"{total_time:.1f}ms",
                    'success_rate': f"{success_rate:.1f}%",
                    'avg_time': f"{avg_time:.1f}ms"
                }
            }
            
            # Close client
            client.close()
            
        except Exception as e:
            print(f"❌ HARD FAIL: {mode} mode failed: {e}")
            print("📋 Check HER system configuration and dependencies")
            return False
    
    # Print comparison
    print_comparison(results)
    
    # Save results
    save_results(results)
    
    return True

def print_comparison(results):
    """Print detailed comparison between modes."""
    print("\n" + "="*80)
    print("📊 DETAILED COMPARISON")
    print("="*80)
    
    semantic = results['semantic']
    no_semantic = results['no_semantic']
    
    print(f"\n🔍 SEMANTIC MODE:")
    print(f"   Total Time: {semantic['summary']['total_time']}")
    print(f"   Success Rate: {semantic['summary']['success_rate']}")
    print(f"   Avg Time: {semantic['summary']['avg_time']}")
    
    print(f"\n⚡ NO-SEMANTIC MODE:")
    print(f"   Total Time: {no_semantic['summary']['total_time']}")
    print(f"   Success Rate: {no_semantic['summary']['success_rate']}")
    print(f"   Avg Time: {no_semantic['summary']['avg_time']}")
    
    print(f"\n📋 STEP-BY-STEP COMPARISON:")
    print("-" * 80)
    print(f"{'Step':<4} {'Query':<30} {'Semantic':<12} {'No-Semantic':<12} {'Winner':<12}")
    print("-" * 80)
    
    for i, (sem_step, no_sem_step) in enumerate(zip(semantic['steps'], no_semantic['steps']), 1):
        sem_status = "✅" if sem_step['success'] else "❌"
        no_sem_status = "✅" if no_sem_step['success'] else "❌"
        
        if sem_step['success'] and no_sem_step['success']:
            winner = "Both"
        elif sem_step['success']:
            winner = "Semantic"
        elif no_sem_step['success']:
            winner = "No-Semantic"
        else:
            winner = "Both Failed"
        
        query = f"Step {i}"[:30]
        print(f"{i:<4} {query:<30} {sem_status:<12} {no_sem_status:<12} {winner:<12}")
    
    print(f"\n🎯 CANONICAL ELEMENT TREES AND XPATHS:")
    print("-" * 80)
    for i, (sem_step, no_sem_step) in enumerate(zip(semantic['steps'], no_semantic['steps']), 1):
        print(f"\nStep {i}: {sem_step['query']}")
        print(f"  Semantic XPath: {sem_step['xpath'] or 'None'}")
        print(f"  Semantic Canonical: {sem_step['element_canonical'] or 'None'}")
        print(f"  No-Semantic XPath: {no_sem_step['xpath'] or 'None'}")
        print(f"  No-Semantic Canonical: {no_sem_step['element_canonical'] or 'None'}")

def save_results(results):
    """Save results to JSON file."""
    results_file = "verizon_real_test_results.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {results_file}")

def main():
    """Main test runner."""
    print("🎯 VERIZON REAL TEST - No Mocks, Real Setup Required")
    print("=" * 60)
    
    # Check setup first
    if not check_real_setup():
        print("\n❌ HARD FAIL: Real setup is incomplete!")
        print("📋 Please install all required dependencies and models before running this test.")
        return 1
    
    # Run real test
    if not run_real_verizon_test():
        print("\n❌ HARD FAIL: Real test failed!")
        return 1
    
    print("\n🎉 Real test completed successfully!")
    print("📋 Check the canonical element trees and XPaths above for manual testing")
    return 0

if __name__ == "__main__":
    sys.exit(main())