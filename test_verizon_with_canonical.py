#!/usr/bin/env python3
"""
Verizon Focused Test with Canonical Element Trees and XPaths for Manual UI Testing.
"""

import sys
import os
import time
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.her.core.pipeline import HybridPipeline
from src.her.config.settings import HERConfig

class VerizonCanonicalTest:
    """Test Verizon flow with canonical element trees and XPaths for manual testing."""
    
    def __init__(self):
        self.semantic_pipeline = None
        self.no_semantic_pipeline = None
        self.results = {}
        
    def initialize_pipelines(self):
        """Initialize both semantic and no-semantic pipelines."""
        print("🔧 Initializing Pipelines...")
        
        try:
            # Semantic mode
            os.environ['HER_USE_SEMANTIC_SEARCH'] = 'true'
            self.semantic_pipeline = HybridPipeline(models_root="src/her/models")
            print("✅ Semantic pipeline initialized")
            
            # No-semantic mode  
            os.environ['HER_USE_SEMANTIC_SEARCH'] = 'false'
            self.no_semantic_pipeline = HybridPipeline(models_root="src/her/models")
            print("✅ No-semantic pipeline initialized")
            
            return True
        except Exception as e:
            print(f"❌ Pipeline initialization failed: {e}")
            return False
    
    def get_verizon_elements(self):
        """Get mock Verizon page elements with canonical descriptors."""
        return [
            # Navigation elements
            {
                'tag': 'nav',
                'text': 'Shop',
                'attributes': {'class': 'gnav-shop', 'data-testid': 'gnav-shop'},
                'visible': True,
                'interactive': True,
                'meta': {'frame_hash': 'main'}
            },
            {
                'tag': 'a',
                'text': 'Phones',
                'attributes': {'href': '/smartphones/', 'class': 'gnav-link', 'data-testid': 'gnav-phones'},
                'visible': True,
                'interactive': True,
                'meta': {'frame_hash': 'main'}
            },
            {
                'tag': 'button',
                'text': 'Apple',
                'attributes': {'class': 'filter-button', 'data-brand': 'apple', 'data-testid': 'filter-apple'},
                'visible': True,
                'interactive': True,
                'meta': {'frame_hash': 'main'}
            },
            {
                'tag': 'div',
                'text': 'Apple iPhone 17',
                'attributes': {'class': 'product-card', 'data-product': 'iphone-17', 'data-testid': 'product-iphone-17'},
                'visible': True,
                'interactive': True,
                'meta': {'frame_hash': 'main'}
            },
            {
                'tag': 'h1',
                'text': 'Apple iPhone 17',
                'attributes': {'class': 'product-title', 'data-testid': 'product-title'},
                'visible': True,
                'interactive': False,
                'meta': {'frame_hash': 'main'}
            },
            {
                'tag': 'button',
                'text': 'White',
                'attributes': {'class': 'color-option', 'data-color': 'white', 'data-testid': 'color-white'},
                'visible': True,
                'interactive': True,
                'meta': {'frame_hash': 'main'}
            },
            # Additional elements for context
            {
                'tag': 'div',
                'text': 'Verizon Wireless',
                'attributes': {'class': 'logo', 'data-testid': 'logo'},
                'visible': True,
                'interactive': False,
                'meta': {'frame_hash': 'main'}
            },
            {
                'tag': 'input',
                'text': '',
                'attributes': {'type': 'search', 'placeholder': 'Search phones', 'data-testid': 'search-input'},
                'visible': True,
                'interactive': True,
                'meta': {'frame_hash': 'main'}
            }
        ]
    
    def build_canonical_descriptor(self, element):
        """Build canonical descriptor for an element."""
        parts = []
        
        # Tag
        parts.append(f"tag={element['tag']}")
        
        # Key attributes
        attrs = element.get('attributes', {})
        for attr in ['id', 'class', 'data-testid', 'href', 'type', 'placeholder']:
            if attrs.get(attr):
                parts.append(f"{attr}={attrs[attr]}")
        
        # Text content
        if element.get('text'):
            text = element['text'][:50] + "..." if len(element['text']) > 50 else element['text']
            parts.append(f"text={text}")
        
        # Visibility and interactivity
        if element.get('visible'):
            parts.append("visible=true")
        if element.get('interactive'):
            parts.append("interactive=true")
        
        return " | ".join(parts)
    
    def test_step(self, step_num, query, mode, pipeline):
        """Test a single step and return detailed results."""
        print(f"\n📋 Step {step_num}: {query}")
        print(f"  Mode: {mode}")
        
        start_time = time.time()
        
        try:
            # Get elements
            elements = self.get_verizon_elements()
            
            # Query pipeline
            result = pipeline.query(query, elements, top_k=5)
            
            execution_time = (time.time() - start_time) * 1000
            
            # Extract results
            if result and 'results' in result and result['results']:
                top_result = result['results'][0]
                
                # Get canonical descriptor
                element_meta = top_result.get('meta', {})
                canonical = self.build_canonical_descriptor({
                    'tag': element_meta.get('tag', ''),
                    'text': element_meta.get('text', ''),
                    'attributes': element_meta.get('attributes', {}),
                    'visible': element_meta.get('visible', False),
                    'interactive': element_meta.get('interactive', False)
                })
                
                # Get XPath
                xpath = top_result.get('selector', 'N/A')
                
                # Get confidence
                confidence = top_result.get('score', 0.0)
                
                print(f"  ✅ Success: True")
                print(f"  🎯 XPath: {xpath}")
                print(f"  📝 Canonical: {canonical}")
                print(f"  📊 Confidence: {confidence:.3f}")
                print(f"  ⚡ Time: {execution_time:.1f}ms")
                print(f"  🔧 Strategy: {result.get('strategy', 'unknown')}")
                
                return {
                    'success': True,
                    'xpath': xpath,
                    'canonical': canonical,
                    'confidence': confidence,
                    'execution_time': execution_time,
                    'strategy': result.get('strategy', 'unknown'),
                    'error': None
                }
            else:
                print(f"  ❌ Success: False")
                print(f"  🎯 XPath: None")
                print(f"  📝 Canonical: None")
                print(f"  📊 Confidence: 0.000")
                print(f"  ⚡ Time: {execution_time:.1f}ms")
                print(f"  🔧 Strategy: unknown")
                print(f"  ❌ Error: No results returned")
                
                return {
                    'success': False,
                    'xpath': None,
                    'canonical': None,
                    'confidence': 0.0,
                    'execution_time': execution_time,
                    'strategy': 'unknown',
                    'error': 'No results returned'
                }
                
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            print(f"  ❌ Success: False")
            print(f"  🎯 XPath: None")
            print(f"  📝 Canonical: None")
            print(f"  📊 Confidence: 0.000")
            print(f"  ⚡ Time: {execution_time:.1f}ms")
            print(f"  🔧 Strategy: unknown")
            print(f"  ❌ Error: {str(e)}")
            
            return {
                'success': False,
                'xpath': None,
                'canonical': None,
                'confidence': 0.0,
                'execution_time': execution_time,
                'strategy': 'unknown',
                'error': str(e)
            }
    
    def run_verizon_flow(self, mode):
        """Run the complete Verizon flow for a specific mode."""
        print(f"\n🚀 Running Verizon Flow - {mode.upper()} Mode")
        print("=" * 60)
        
        pipeline = self.semantic_pipeline if mode == 'semantic' else self.no_semantic_pipeline
        
        # Test steps
        test_steps = [
            "Navigate to https://www.verizon.com/",
            "Click on Phones button",
            "Click on Apple filter", 
            "Click on Apple iPhone 17 device",
            "Validate it landed on https://www.verizon.com/smartphones/apple-iphone-17/",
            "Validate Apple iPhone 17 text on pdp page",
            "Click on White color"
        ]
        
        step_results = []
        total_time = 0
        successful_steps = 0
        
        for i, query in enumerate(test_steps, 1):
            result = self.test_step(i, query, mode, pipeline)
            step_results.append(result)
            total_time += result['execution_time']
            
            if result['success']:
                successful_steps += 1
        
        # Calculate metrics
        success_rate = (successful_steps / len(test_steps)) * 100
        avg_time = total_time / len(test_steps)
        
        print(f"\n📊 {mode.upper()} Mode Summary:")
        print(f"   Total Time: {total_time:.1f}ms")
        print(f"   Success Rate: {success_rate:.1f}% ({successful_steps}/{len(test_steps)})")
        print(f"   Avg Step Time: {avg_time:.1f}ms")
        
        return {
            'steps': step_results,
            'summary': {
                'mode': mode,
                'total_time': f"{total_time:.1f}ms",
                'success_rate': f"{success_rate:.1f}%",
                'avg_time': f"{avg_time:.1f}ms"
            }
        }
    
    def print_manual_testing_guide(self):
        """Print manual testing guide with XPaths and canonical descriptors."""
        print("\n" + "="*80)
        print("🎯 MANUAL TESTING GUIDE")
        print("="*80)
        print("Use these XPaths and canonical descriptors to manually test in the UI:")
        print()
        
        # Test steps with expected elements
        test_cases = [
            {
                'step': 1,
                'query': 'Navigate to https://www.verizon.com/',
                'expected_xpath': '//nav[@data-testid="gnav-shop"]',
                'canonical': 'tag=nav | class=gnav-shop | data-testid=gnav-shop | text=Shop | visible=true | interactive=true'
            },
            {
                'step': 2, 
                'query': 'Click on Phones button',
                'expected_xpath': '//a[@data-testid="gnav-phones"]',
                'canonical': 'tag=a | href=/smartphones/ | class=gnav-link | data-testid=gnav-phones | text=Phones | visible=true | interactive=true'
            },
            {
                'step': 3,
                'query': 'Click on Apple filter',
                'expected_xpath': '//button[@data-testid="filter-apple"]',
                'canonical': 'tag=button | class=filter-button | data-brand=apple | data-testid=filter-apple | text=Apple | visible=true | interactive=true'
            },
            {
                'step': 4,
                'query': 'Click on Apple iPhone 17 device',
                'expected_xpath': '//div[@data-testid="product-iphone-17"]',
                'canonical': 'tag=div | class=product-card | data-product=iphone-17 | data-testid=product-iphone-17 | text=Apple iPhone 17 | visible=true | interactive=true'
            },
            {
                'step': 5,
                'query': 'Validate it landed on https://www.verizon.com/smartphones/apple-iphone-17/',
                'expected_xpath': '//h1[@data-testid="product-title"]',
                'canonical': 'tag=h1 | class=product-title | data-testid=product-title | text=Apple iPhone 17 | visible=true | interactive=false'
            },
            {
                'step': 6,
                'query': 'Validate Apple iPhone 17 text on pdp page',
                'expected_xpath': '//h1[@data-testid="product-title"]',
                'canonical': 'tag=h1 | class=product-title | data-testid=product-title | text=Apple iPhone 17 | visible=true | interactive=false'
            },
            {
                'step': 7,
                'query': 'Click on White color',
                'expected_xpath': '//button[@data-testid="color-white"]',
                'canonical': 'tag=button | class=color-option | data-color=white | data-testid=color-white | text=White | visible=true | interactive=true'
            }
        ]
        
        for case in test_cases:
            print(f"Step {case['step']}: {case['query']}")
            print(f"  🎯 XPath: {case['expected_xpath']}")
            print(f"  📝 Canonical: {case['canonical']}")
            print(f"  🔧 Manual Test: Use browser dev tools to find element with this XPath")
            print(f"  ✅ Expected: Element should be visible and interactive")
            print()
    
    def run_comparison_test(self):
        """Run comparison test between semantic and no-semantic modes."""
        print("🎯 Verizon Canonical Test Suite")
        print("Testing 7-step Verizon flow with canonical element trees and XPaths")
        print("=" * 80)
        
        # Initialize pipelines
        if not self.initialize_pipelines():
            return False
        
        # Run both modes
        print("\n🚀 Running Semantic Mode...")
        semantic_results = self.run_verizon_flow('semantic')
        
        print("\n🚀 Running No-Semantic Mode...")
        no_semantic_results = self.run_verizon_flow('no_semantic')
        
        # Store results
        self.results = {
            'semantic': semantic_results,
            'no_semantic': no_semantic_results
        }
        
        # Print manual testing guide
        self.print_manual_testing_guide()
        
        # Print comparison
        self.print_comparison()
        
        # Save results
        self.save_results()
        
        return True
    
    def print_comparison(self):
        """Print detailed comparison between modes."""
        print("\n" + "="*80)
        print("📊 DETAILED COMPARISON")
        print("="*80)
        
        semantic = self.results['semantic']
        no_semantic = self.results['no_semantic']
        
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
    
    def save_results(self):
        """Save results to JSON file."""
        results_file = "verizon_canonical_test_results.json"
        
        # Convert to serializable format
        serializable_results = {}
        for mode, data in self.results.items():
            serializable_results[mode] = {
                'steps': data['steps'],
                'summary': data['summary']
            }
        
        with open(results_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {results_file}")

def main():
    """Main test runner."""
    runner = VerizonCanonicalTest()
    success = runner.run_comparison_test()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("📋 Use the manual testing guide above to test XPaths in the actual UI")
        return 0
    else:
        print("\n❌ Test failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())