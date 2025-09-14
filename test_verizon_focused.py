#!/usr/bin/env python3
"""
Focused Verizon Test Suite

Tests the 7-step Verizon flow in both semantic and no-semantic modes
with detailed XPath and canonical element analysis.
"""

import os
import sys
import time
import json
from typing import Dict, Any, List
from unittest import mock

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Mock numpy if not available
try:
    import numpy as np
except ImportError:
    sys.modules['numpy'] = mock.MagicMock()
    print("Mocked numpy for testing.")

from src.her.cli.cli_api import HybridElementRetrieverClient
from src.her.core.config_service import reset_config_service

class VerizonTestRunner:
    """Focused Verizon test runner for both semantic and no-semantic modes."""
    
    def __init__(self):
        self.results = {
            'semantic': {'steps': [], 'performance': {}, 'summary': {}},
            'no_semantic': {'steps': [], 'performance': {}, 'summary': {}}
        }
        
    def run_test_step(self, client: HybridElementRetrieverClient, step_num: int, 
                     query: str, expected_url: str = None, mode: str = "semantic") -> Dict[str, Any]:
        """Run a single test step and capture detailed results."""
        print(f"\n  Step {step_num}: {query}")
        print(f"  Mode: {mode}")
        
        start_time = time.time()
        
        try:
            # Execute the query
            result = client.query(query, url="https://www.verizon.com/" if step_num == 1 else None)
            
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Extract detailed information
            step_result = {
                'step_number': step_num,
                'query': query,
                'mode': mode,
                'execution_time_ms': execution_time,
                'success': False,
                'xpath': None,
                'element_canonical': None,
                'confidence': 0.0,
                'strategy': None,
                'error': None,
                'element_details': None
            }
            
            if result and isinstance(result, dict):
                # Extract XPath
                if 'xpath' in result:
                    step_result['xpath'] = result['xpath']
                elif 'selector' in result:
                    step_result['xpath'] = result['selector']
                
                # Extract element details
                if 'element' in result:
                    element = result['element']
                    step_result['element_details'] = element
                    
                    # Build canonical descriptor
                    canonical_parts = []
                    if element.get('tag'):
                        canonical_parts.append(element['tag'])
                    
                    attrs = element.get('attributes', {})
                    for attr in ['id', 'class', 'type', 'role', 'name']:
                        if attrs.get(attr):
                            canonical_parts.append(f"{attr}={attrs[attr]}")
                    
                    if element.get('text'):
                        canonical_parts.append(f"text={element['text'][:50]}")
                    
                    step_result['element_canonical'] = " ".join(canonical_parts)
                
                # Extract confidence and strategy
                step_result['confidence'] = result.get('confidence', 0.0)
                step_result['strategy'] = result.get('strategy', 'unknown')
                
                # Determine success
                if step_result['xpath'] and step_result['confidence'] > 0.0:
                    step_result['success'] = True
                    
                    # Check URL if expected
                    if expected_url:
                        current_url = client.page.url if hasattr(client, 'page') and client.page else "unknown"
                        if expected_url in current_url:
                            step_result['url_match'] = True
                        else:
                            step_result['url_match'] = False
                            step_result['actual_url'] = current_url
                else:
                    step_result['error'] = "No valid XPath or low confidence"
            else:
                step_result['error'] = "No result returned"
            
            # Print detailed results
            print(f"    ✅ Success: {step_result['success']}")
            print(f"    🎯 XPath: {step_result['xpath']}")
            print(f"    📝 Canonical: {step_result['element_canonical']}")
            print(f"    📊 Confidence: {step_result['confidence']:.3f}")
            print(f"    ⚡ Time: {execution_time:.1f}ms")
            print(f"    🔧 Strategy: {step_result['strategy']}")
            
            if step_result['error']:
                print(f"    ❌ Error: {step_result['error']}")
            
            return step_result
            
        except Exception as e:
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000
            
            error_result = {
                'step_number': step_num,
                'query': query,
                'mode': mode,
                'execution_time_ms': execution_time,
                'success': False,
                'xpath': None,
                'element_canonical': None,
                'confidence': 0.0,
                'strategy': None,
                'error': str(e),
                'element_details': None
            }
            
            print(f"    ❌ Exception: {str(e)}")
            return error_result
    
    def run_verizon_flow(self, mode: str = "semantic") -> Dict[str, Any]:
        """Run the complete Verizon flow for the specified mode."""
        print(f"\n🚀 Running Verizon Flow - {mode.upper()} Mode")
        print("=" * 60)
        
        # Set environment variables
        os.environ['HER_USE_SEMANTIC_SEARCH'] = 'true' if mode == 'semantic' else 'false'
        os.environ['HER_USE_HIERARCHY'] = 'true'  # Default ON
        reset_config_service()
        
        # Initialize client
        try:
            client = HybridElementRetrieverClient(use_semantic_search=(mode == 'semantic'))
            print(f"✅ Client initialized in {mode} mode")
        except Exception as e:
            print(f"❌ Failed to initialize client: {e}")
            return {'error': str(e)}
        
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
        
        # Run each step
        step_results = []
        total_start_time = time.time()
        
        for i, step in enumerate(test_steps, 1):
            print(f"\n📋 Step {i}: {step['description']}")
            result = self.run_test_step(
                client, 
                i, 
                step['query'], 
                step['expected_url'], 
                mode
            )
            step_results.append(result)
        
        total_end_time = time.time()
        total_execution_time = (total_end_time - total_start_time) * 1000
        
        # Calculate summary statistics
        successful_steps = sum(1 for r in step_results if r['success'])
        total_steps = len(step_results)
        success_rate = (successful_steps / total_steps) * 100 if total_steps > 0 else 0
        
        avg_confidence = sum(r['confidence'] for r in step_results) / total_steps if total_steps > 0 else 0
        avg_execution_time = sum(r['execution_time_ms'] for r in step_results) / total_steps if total_steps > 0 else 0
        
        # Performance summary
        performance = {
            'total_execution_time_ms': total_execution_time,
            'avg_step_time_ms': avg_execution_time,
            'successful_steps': successful_steps,
            'total_steps': total_steps,
            'success_rate_percent': success_rate,
            'avg_confidence': avg_confidence
        }
        
        # Store results
        self.results[mode] = {
            'steps': step_results,
            'performance': performance,
            'summary': {
                'mode': mode,
                'total_time': f"{total_execution_time:.1f}ms",
                'success_rate': f"{success_rate:.1f}%",
                'avg_confidence': f"{avg_confidence:.3f}",
                'avg_step_time': f"{avg_execution_time:.1f}ms"
            }
        }
        
        print(f"\n📊 {mode.upper()} Mode Summary:")
        print(f"   Total Time: {total_execution_time:.1f}ms")
        print(f"   Success Rate: {success_rate:.1f}% ({successful_steps}/{total_steps})")
        print(f"   Avg Confidence: {avg_confidence:.3f}")
        print(f"   Avg Step Time: {avg_execution_time:.1f}ms")
        
        return self.results[mode]
    
    def run_comparison_test(self):
        """Run both semantic and no-semantic modes and compare results."""
        print("🎯 Verizon Flow Comparison Test")
        print("=" * 80)
        
        # Run semantic mode
        semantic_results = self.run_verizon_flow('semantic')
        
        # Run no-semantic mode
        no_semantic_results = self.run_verizon_flow('no_semantic')
        
        # Compare results
        self.print_comparison()
        
        return self.results
    
    def print_comparison(self):
        """Print detailed comparison between modes."""
        print("\n" + "=" * 80)
        print("📊 DETAILED COMPARISON")
        print("=" * 80)
        
        semantic = self.results['semantic']
        no_semantic = self.results['no_semantic']
        
        print(f"\n🔍 SEMANTIC MODE:")
        print(f"   Total Time: {semantic['summary']['total_time']}")
        print(f"   Success Rate: {semantic['summary']['success_rate']}")
        print(f"   Avg Confidence: {semantic['summary']['avg_confidence']}")
        print(f"   Avg Step Time: {semantic['summary']['avg_step_time']}")
        
        print(f"\n⚡ NO-SEMANTIC MODE:")
        print(f"   Total Time: {no_semantic['summary']['total_time']}")
        print(f"   Success Rate: {no_semantic['summary']['success_rate']}")
        print(f"   Avg Confidence: {no_semantic['summary']['avg_confidence']}")
        print(f"   Avg Step Time: {no_semantic['summary']['avg_step_time']}")
        
        print(f"\n📋 STEP-BY-STEP COMPARISON:")
        print("-" * 80)
        print(f"{'Step':<4} {'Query':<30} {'Semantic':<12} {'No-Semantic':<12} {'Winner':<10}")
        print("-" * 80)
        
        for i in range(len(semantic['steps'])):
            sem_step = semantic['steps'][i]
            no_sem_step = no_semantic['steps'][i]
            
            sem_status = "✅" if sem_step['success'] else "❌"
            no_sem_status = "✅" if no_sem_step['success'] else "❌"
            
            if sem_step['success'] and no_sem_step['success']:
                winner = "Tie"
            elif sem_step['success']:
                winner = "Semantic"
            elif no_sem_step['success']:
                winner = "No-Semantic"
            else:
                winner = "Both Failed"
            
            query_short = sem_step['query'][:28] + "..." if len(sem_step['query']) > 30 else sem_step['query']
            print(f"{i+1:<4} {query_short:<30} {sem_status:<12} {no_sem_status:<12} {winner:<10}")
        
        # Performance comparison
        print(f"\n⚡ PERFORMANCE COMPARISON:")
        sem_time = float(semantic['summary']['total_time'].replace('ms', ''))
        no_sem_time = float(no_semantic['summary']['total_time'].replace('ms', ''))
        
        if sem_time < no_sem_time:
            faster_mode = "Semantic"
            speed_improvement = ((no_sem_time - sem_time) / no_sem_time) * 100
        else:
            faster_mode = "No-Semantic"
            speed_improvement = ((sem_time - no_sem_time) / sem_time) * 100
        
        print(f"   Faster Mode: {faster_mode}")
        print(f"   Speed Improvement: {speed_improvement:.1f}%")
        
        # Accuracy comparison
        sem_success = float(semantic['summary']['success_rate'].replace('%', ''))
        no_sem_success = float(no_semantic['summary']['success_rate'].replace('%', ''))
        
        if sem_success > no_sem_success:
            more_accurate = "Semantic"
            accuracy_improvement = sem_success - no_sem_success
        else:
            more_accurate = "No-Semantic"
            accuracy_improvement = no_sem_success - sem_success
        
        print(f"   More Accurate: {more_accurate}")
        print(f"   Accuracy Improvement: {accuracy_improvement:.1f}%")
        
        # Save detailed results
        with open('verizon_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: verizon_test_results.json")

def main():
    """Run the focused Verizon test."""
    print("🎯 Verizon Focused Test Suite")
    print("Testing 7-step Verizon flow in both semantic and no-semantic modes")
    print("=" * 80)
    
    # Initialize test runner
    runner = VerizonTestRunner()
    
    # Run comparison test
    try:
        results = runner.run_comparison_test()
        print("\n🎉 Test completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()