#!/usr/bin/env python3
"""
Deep Timing Analysis with Detailed Logging
Traces each step, data input/output, and timing for all 3 CDP modes
"""

import os
import time
import logging
from datetime import datetime
from her.runner import run_steps
from her.config import CanonicalMode

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspace/debug_timing_analysis.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def log_step_timing(func_name, start_time, end_time, input_data=None, output_data=None):
    """Log detailed timing and data for each step"""
    duration = end_time - start_time
    logger.info(f"⏱️  {func_name}: {duration:.3f}s")
    if input_data:
        logger.info(f"   📥 Input: {type(input_data).__name__} - {len(input_data) if hasattr(input_data, '__len__') else 'N/A'} items")
    if output_data:
        logger.info(f"   📤 Output: {type(output_data).__name__} - {len(output_data) if hasattr(output_data, '__len__') else 'N/A'} items")
    return duration

def test_mode_with_detailed_logging(mode, mode_name):
    """Test a specific mode with detailed logging"""
    logger.info(f"\n{'='*80}")
    logger.info(f"🔬 TESTING {mode_name.upper()} MODE")
    logger.info(f"{'='*80}")
    
    # Set environment variable
    os.environ['HER_CANONICAL_MODE'] = mode.value
    logger.info(f"🔧 Environment set: HER_CANONICAL_MODE = {mode.value}")
    
    total_start = time.time()
    
    try:
        # Step 1: Run steps
        logger.info(f"\n📋 STEP 1: Running steps")
        steps_start = time.time()
        steps = ['Open https://www.google.com/', 'Wait for page load']
        logger.info(f"   Steps: {steps}")
        
        result = run_steps(steps, headless=True)
        steps_duration = log_step_timing("run_steps", steps_start, time.time(), steps, result)
        
        # Step 2: Analyze result
        logger.info(f"\n📊 STEP 2: Analyzing result")
        analysis_start = time.time()
        
        if hasattr(result, 'elements') and result.elements:
            elements = result.elements
            node_count = len(elements)
            
            # Analyze element types
            tag_counts = {}
            attr_counts = {}
            interactive_count = 0
            
            for element in elements:
                tag = element.get('tag', 'unknown')
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
                
                attrs = element.get('attrs', {})
                attr_count = len(attrs)
                attr_counts[attr_count] = attr_counts.get(attr_count, 0) + 1
                
                # Check if interactive
                if tag.lower() in ['button', 'input', 'select', 'textarea', 'a']:
                    interactive_count += 1
                elif attrs.get('role') in ['button', 'link', 'textbox', 'combobox']:
                    interactive_count += 1
            
            logger.info(f"   📊 Node Analysis:")
            logger.info(f"      Total Elements: {node_count}")
            logger.info(f"      Interactive Elements: {interactive_count}")
            logger.info(f"      Non-Interactive Elements: {node_count - interactive_count}")
            
            # Top 10 element types
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            logger.info(f"      Top 10 Element Types:")
            for i, (tag, count) in enumerate(sorted_tags[:10]):
                logger.info(f"         {i+1}. {tag}: {count}")
            
            # Attribute distribution
            sorted_attrs = sorted(attr_counts.items(), key=lambda x: x[0])
            logger.info(f"      Attribute Distribution:")
            for i, (attr_count, element_count) in enumerate(sorted_attrs[:10]):
                logger.info(f"         {i+1}. {attr_count} attributes: {element_count} elements")
            
        else:
            node_count = 0
            logger.warning("   ⚠️  No elements found in result")
        
        analysis_duration = log_step_timing("result_analysis", analysis_start, time.time(), result, elements if 'elements' in locals() else None)
        
        total_duration = time.time() - total_start
        
        logger.info(f"\n✅ {mode_name.upper()} MODE COMPLETE")
        logger.info(f"   Total Duration: {total_duration:.3f}s")
        logger.info(f"   Node Count: {node_count}")
        
        return {
            'success': True,
            'total_duration': total_duration,
            'steps_duration': steps_duration,
            'analysis_duration': analysis_duration,
            'node_count': node_count,
            'error': None
        }
        
    except Exception as e:
        total_duration = time.time() - total_start
        logger.error(f"❌ {mode_name.upper()} MODE FAILED: {str(e)}")
        return {
            'success': False,
            'total_duration': total_duration,
            'steps_duration': 0,
            'analysis_duration': 0,
            'node_count': 0,
            'error': str(e)
        }

def test_direct_cdp_extraction():
    """Test direct CDP extraction to get raw node counts"""
    logger.info(f"\n{'='*80}")
    logger.info(f"🔍 DIRECT CDP EXTRACTION TEST")
    logger.info(f"{'='*80}")
    
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser_start = time.time()
        browser = p.chromium.launch(headless=True)
        browser_duration = log_step_timing("browser_launch", browser_start, time.time())
        
        page_start = time.time()
        page = browser.new_page()
        page_duration = log_step_timing("page_creation", page_start, time.time())
        
        try:
            # Navigate to page
            nav_start = time.time()
            page.goto('https://www.google.com/')
            page.wait_for_load_state('networkidle')
            nav_duration = log_step_timing("page_navigation", nav_start, time.time())
            
            # Get DOM node count
            dom_start = time.time()
            dom_count = page.evaluate("""
                () => {
                    const allElements = document.querySelectorAll('*');
                    return allElements.length;
                }
            """)
            dom_duration = log_step_timing("dom_count_extraction", dom_start, time.time())
            
            # Get accessibility tree count
            ax_start = time.time()
            try:
                ax_tree = page.accessibility.snapshot()
                ax_count = count_accessibility_nodes(ax_tree)
                ax_duration = log_step_timing("accessibility_extraction", ax_start, time.time())
            except Exception as e:
                ax_count = 0
                ax_duration = log_step_timing("accessibility_extraction", ax_start, time.time())
                logger.warning(f"   ⚠️  Accessibility tree extraction failed: {e}")
            
            # Close browser
            close_start = time.time()
            browser.close()
            close_duration = log_step_timing("browser_close", close_start, time.time())
            
            total_duration = time.time() - browser_start
            
            logger.info(f"\n📊 RAW NODE COUNTS:")
            logger.info(f"   DOM Elements: {dom_count}")
            logger.info(f"   Accessibility Nodes: {ax_count}")
            logger.info(f"   Total Potential: {dom_count + ax_count}")
            logger.info(f"   Total Duration: {total_duration:.3f}s")
            
            return {
                'dom_count': dom_count,
                'ax_count': ax_count,
                'total_potential': dom_count + ax_count,
                'total_duration': total_duration,
                'browser_duration': browser_duration,
                'page_duration': page_duration,
                'nav_duration': nav_duration,
                'dom_duration': dom_duration,
                'ax_duration': ax_duration,
                'close_duration': close_duration
            }
            
        except Exception as e:
            browser.close()
            logger.error(f"❌ Direct CDP test failed: {e}")
            return None

def count_accessibility_nodes(node, count=0):
    """Recursively count accessibility tree nodes"""
    if not node:
        return count
    
    count += 1
    
    if 'children' in node and node['children']:
        for child in node['children']:
            count = count_accessibility_nodes(child, count)
    
    return count

def main():
    """Main analysis function with detailed logging"""
    logger.info("🚀 Starting Deep Timing Analysis with Detailed Logging")
    logger.info(f"📅 Timestamp: {datetime.now().isoformat()}")
    
    # Test direct CDP extraction first
    raw_data = test_direct_cdp_extraction()
    
    # Test all three modes
    modes = [
        (CanonicalMode.DOM_ONLY, "DOM Only"),
        (CanonicalMode.ACCESSIBILITY_ONLY, "Accessibility Only"), 
        (CanonicalMode.BOTH, "Both DOM + Accessibility")
    ]
    
    results = {}
    
    for mode, mode_name in modes:
        results[mode_name] = test_mode_with_detailed_logging(mode, mode_name)
    
    # Summary analysis
    logger.info(f"\n{'='*80}")
    logger.info(f"📊 COMPREHENSIVE SUMMARY")
    logger.info(f"{'='*80}")
    
    logger.info(f"\n🔍 RAW CDP EXTRACTION:")
    if raw_data:
        logger.info(f"   DOM Elements: {raw_data['dom_count']}")
        logger.info(f"   Accessibility Nodes: {raw_data['ax_count']}")
        logger.info(f"   Total Potential: {raw_data['total_potential']}")
        logger.info(f"   Total Duration: {raw_data['total_duration']:.3f}s")
    
    logger.info(f"\n📋 FRAMEWORK MODES PERFORMANCE:")
    for mode_name, result in results.items():
        if result['success']:
            logger.info(f"   ✅ {mode_name}:")
            logger.info(f"      Total Duration: {result['total_duration']:.3f}s")
            logger.info(f"      Steps Duration: {result['steps_duration']:.3f}s")
            logger.info(f"      Analysis Duration: {result['analysis_duration']:.3f}s")
            logger.info(f"      Node Count: {result['node_count']}")
        else:
            logger.info(f"   ❌ {mode_name}: FAILED - {result['error']}")
    
    # Performance analysis
    logger.info(f"\n⚡ PERFORMANCE ANALYSIS:")
    successful_results = {k: v for k, v in results.items() if v['success']}
    if successful_results:
        fastest_mode = min(successful_results.items(), key=lambda x: x[1]['total_duration'])
        slowest_mode = max(successful_results.items(), key=lambda x: x[1]['total_duration'])
        
        logger.info(f"   🏆 Fastest: {fastest_mode[0]} ({fastest_mode[1]['total_duration']:.3f}s)")
        logger.info(f"   🐌 Slowest: {slowest_mode[0]} ({slowest_mode[1]['total_duration']:.3f}s)")
        
        # Calculate efficiency
        if raw_data:
            for mode_name, result in successful_results.items():
                efficiency = result['node_count'] / result['total_duration']
                logger.info(f"   📈 {mode_name} Efficiency: {efficiency:.1f} nodes/second")
    
    logger.info(f"\n✅ Deep Timing Analysis Complete!")
    logger.info(f"📄 Detailed log saved to: /workspace/debug_timing_analysis.log")

if __name__ == "__main__":
    main()