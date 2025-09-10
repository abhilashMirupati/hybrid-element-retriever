#!/usr/bin/env python3
"""
Verizon Flow Test with MiniLM and MarkupLM Scores Before Heuristics
Shows detailed scoring breakdown for each step
"""

import os
import sys
import time
import subprocess
from datetime import datetime

def run_verizon_scoring_test():
    """Run Verizon flow test with MiniLM and MarkupLM scoring details"""
    print("🚀 VERIZON FLOW TEST WITH MINILM & MARKUPLM SCORES")
    print("=" * 80)
    
    test_script = """
import os
import sys
import time
sys.path.insert(0, 'src')

# Set environment variables
os.environ['HER_CANONICAL_MODE'] = 'both'
os.environ['HER_USE_HIERARCHY'] = 'false'
os.environ['HER_USE_TWO_STAGE'] = 'false'

from her.runner import Runner

def print_minilm_scores(step_name, query, mini_hits):
    print("\\n" + "="*60)
    print(f"🔍 MINILM TOP-K RESULTS: {step_name}")
    print("="*60)
    print(f"Query: '{query}'")
    print(f"Total MiniLM candidates: {len(mini_hits)}")
    print("-" * 60)
    
    for i, (score, meta) in enumerate(mini_hits[:10]):  # Top 10
        text = meta.get('text', '')[:50]
        tag = meta.get('tag', '')
        interactive = meta.get('interactive', False)
        xpath = meta.get('xpath', '')[:60]
        
        print(f"{i+1:2d}. MiniLM: {score:6.3f} | {tag:8s} | Int: {interactive} | '{text}...'")
        print(f"     XPath: {xpath}...")
        print()

def print_markuplm_scores(step_name, query, markup_scores):
    print("\\n" + "="*60)
    print(f"🎯 MARKUPLM RERANKING RESULTS: {step_name}")
    print("="*60)
    print(f"Query: '{query}'")
    print(f"Total MarkupLM candidates: {len(markup_scores)}")
    print("-" * 60)
    
    for i, (score, meta) in enumerate(markup_scores[:10]):  # Top 10
        text = meta.get('text', '')[:50]
        tag = meta.get('tag', '')
        interactive = meta.get('interactive', False)
        xpath = meta.get('xpath', '')[:60]
        
        print(f"{i+1:2d}. MarkupLM: {score:6.3f} | {tag:8s} | Int: {interactive} | '{text}...'")
        print(f"     XPath: {xpath}...")
        print()

def run_scoring_verizon_flow():
    try:
        print("🔧 Initializing Runner...")
        runner = Runner()
        print("✅ Runner initialized")
        
        # Step 1: Open Verizon page
        print("\\n📱 STEP 1: Opening Verizon page...")
        snapshot = runner._snapshot('https://www.verizon.com/')
        print(f"✅ Page loaded with {len(snapshot.get('elements', []))} elements")
        
        # Step 2: Click on Phones
        print("\\n📱 STEP 2: Clicking on Phones...")
        phones_query = 'Click on the "Phones" button'
        
        # Get detailed pipeline results
        from her.pipeline import HybridPipeline
        pipeline = HybridPipeline()
        elements = snapshot.get('elements', [])
        
        # Prepare elements
        E, all_meta = pipeline._prepare_elements(elements)
        
        # Get MiniLM results
        q_mini = pipeline.embed_query(phones_query)
        mini_hits = []
        for fh, mini_store in pipeline._mini_stores.items():
            k = 20
            raw = mini_store.search(q_mini.tolist(), k=k)
            for idx, _dist, md in raw:
                vec = pipeline._mini_stores[fh].vectors[idx]
                score = pipeline._cos(q_mini, vec)
                mini_hits.append((score, md))
        
        # Filter for interactive elements
        interactive_hits = []
        non_interactive_hits = []
        for score, md in mini_hits:
            is_interactive = md.get('interactive', False)
            tag = (md.get('tag') or '').lower()
            if is_interactive or tag in ('button', 'a', 'input', 'select', 'option'):
                interactive_hits.append((score, md))
            else:
                non_interactive_hits.append((score, md))
        
        mini_hits = interactive_hits + non_interactive_hits[:5]
        
        print_minilm_scores("STEP 2: Phones Navigation", phones_query, mini_hits)
        
        # Get MarkupLM results
        q_markup = pipeline._embed_query_markup(phones_query)
        shortlist = mini_hits[:5]
        shortlist_elements = []
        for (_, meta) in shortlist:
            enhanced_meta = meta.copy()
            shortlist_elements.append(enhanced_meta)
        
        shortlist_embeddings = pipeline.element_embedder.batch_encode(shortlist_elements)
        markup_scores = []
        for i, (mini_score, meta) in enumerate(shortlist):
            markup_score = pipeline._cos(q_markup, shortlist_embeddings[i])
            intent_score = pipeline._compute_intent_score('click', 'the "Phones" button', phones_query, meta)
            final_score = (mini_score * 0.3) + (markup_score * 0.4) + (intent_score * 0.3)
            markup_scores.append((final_score, meta))
        
        markup_scores.sort(key=lambda x: x[0], reverse=True)
        print_markuplm_scores("STEP 2: Phones Navigation", phones_query, markup_scores)
        
        # Get final result
        phones_result = runner._resolve_selector(phones_query, snapshot)
        print(f"\\n🎯 FINAL RESULT:")
        print(f"Selected: {phones_result.get('selector', 'N/A')}")
        print(f"Confidence: {phones_result.get('confidence', 0.0):.3f}")
        
        if not phones_result.get('selector'):
            print("❌ Failed to find Phones button")
            return False
        
        print("\\n🎉 SCORING ANALYSIS COMPLETED!")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            runner.cleanup_models()
            runner._browser.close()
            runner._playwright.stop()
            print("\\n🧹 Cleanup completed")
        except:
            pass

if __name__ == "__main__":
    success = run_scoring_verizon_flow()
    exit(0 if success else 1)
"""
    
    # Run the test
    print(f"🚀 Starting scoring test at: {datetime.now().isoformat()}")
    process = subprocess.run(['python', '-c', test_script], 
                           capture_output=True, text=True, 
                           env=os.environ.copy())
    
    print("STDOUT:")
    print(process.stdout)
    
    if process.stderr:
        print("STDERR:")
        print(process.stderr)
    
    print(f"\\n🏁 Test completed at: {datetime.now().isoformat()}")
    print(f"Exit code: {process.returncode}")
    
    return process.returncode == 0

def main():
    """Main test function"""
    print("🚀 VERIZON MINILM & MARKUPLM SCORING TEST")
    print("=" * 80)
    
    success = run_verizon_scoring_test()
    
    print("\\n🏁 SCORING TEST COMPLETED")
    return success

if __name__ == "__main__":
    main()