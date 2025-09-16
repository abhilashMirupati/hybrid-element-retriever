#!/usr/bin/env python3
"""
Verizon Automation Test - Real Environment Setup

This test implements the exact Verizon automation flow as specified:
1) Navigate to Verizon page "https://www.verizon.com/"
2) Click on "Phones" button
3) Click on "Apple" filter
4) Click on "Apple IPhone 17" device
5) Validate it landed on "https://www.verizon.com/smartphones/apple-iphone-17/"
6) Validate "Apple iPhone 17" text on pdp page
7) Click on "White" color

Features:
- Real environment setup (no mocking)
- HTML-aware markup processing
- Contextual element selection based on user intent
- Detailed logging of each step with canonical descriptions
- XPath generation and element analysis
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from her.core.runner import Runner
from her.core.pipeline import HybridPipeline
from her.executor.main import Executor
from her.bridge.cdp_bridge import capture_complete_snapshot
from her.descriptors.merge import merge_dom_ax, enhance_element_descriptor
from her.utils.xpath_generator import generate_xpath_for_element


class VerizonAutomationTest:
    """Comprehensive Verizon automation test with real environment setup."""
    
    def __init__(self, headless: bool = False):
        """Initialize the test with real environment setup.
        
        Args:
            headless: Whether to run browser in headless mode (default: False for visibility)
        """
        self.headless = headless
        self.runner = None
        self.results = []
        self.detailed_logs = []
        
        # Ensure models are available
        self._verify_environment()
        
    def _verify_environment(self):
        """Verify that the environment is properly set up with real models."""
        print("🔍 Verifying environment setup...")
        
        # Check if models directory exists
        models_dir = Path("src/her/models")
        if not models_dir.exists():
            print("❌ Models directory not found. Please run: bash scripts/install_models.sh")
            sys.exit(1)
            
        # Check for required models
        required_models = [
            "e5-small-onnx",
            "markuplm-base"
        ]
        
        for model in required_models:
            model_path = models_dir / model
            if not model_path.exists():
                print(f"❌ Model {model} not found at {model_path}")
                print("Please run: bash scripts/install_models.sh")
                sys.exit(1)
                
        print("✅ Environment verification complete - all models available")
        
    def _log_step_details(self, step_num: int, step: str, result: Dict[str, Any]):
        """Log detailed information for each step."""
        log_entry = {
            "step_number": step_num,
            "step_description": step,
            "timestamp": time.time(),
            "result": result,
            "canonical_description": self._generate_canonical_description(step, result),
            "input_analysis": self._analyze_input(step),
            "output_analysis": self._analyze_output(result),
            "markup_analysis": self._analyze_markup(result),
            "xpath_analysis": self._analyze_xpath(result)
        }
        
        self.detailed_logs.append(log_entry)
        
        # Print to console
        print(f"\n{'='*80}")
        print(f"STEP {step_num}: {step}")
        print(f"{'='*80}")
        print(f"✅ Success: {result.get('success', False)}")
        print(f"🎯 Canonical Description: {log_entry['canonical_description']}")
        print(f"📥 Input Analysis: {log_entry['input_analysis']}")
        print(f"📤 Output Analysis: {log_entry['output_analysis']}")
        print(f"🔍 Markup Analysis: {log_entry['markup_analysis']}")
        print(f"📍 XPath Analysis: {log_entry['xpath_analysis']}")
        
    def _generate_canonical_description(self, step: str, result: Dict[str, Any]) -> str:
        """Generate a canonical description of what the step accomplished."""
        step_lower = step.lower()
        
        if "navigate" in step_lower or "open" in step_lower:
            return f"Successfully navigated to {step.split()[-1]} and loaded the page"
        elif "click" in step_lower:
            target = step.split("on")[-1].strip().strip('"').strip("'")
            return f"Successfully clicked on the '{target}' element"
        elif "validate" in step_lower and "landed" in step_lower:
            expected_url = step.split("on")[-1].strip().strip('"').strip("'")
            return f"Successfully validated navigation to {expected_url}"
        elif "validate" in step_lower and "text" in step_lower:
            target_text = step.split("text")[-1].strip().strip('"').strip("'")
            return f"Successfully validated presence of '{target_text}' text on page"
        else:
            return f"Successfully executed: {step}"
            
    def _analyze_input(self, step: str) -> Dict[str, Any]:
        """Analyze the input step to understand user intent and target."""
        step_lower = step.lower()
        
        analysis = {
            "user_intent": "unknown",
            "target_element": "unknown",
            "action_type": "unknown",
            "context": "unknown"
        }
        
        # Extract action type
        if "navigate" in step_lower or "open" in step_lower:
            analysis["action_type"] = "navigation"
            analysis["user_intent"] = "Navigate to a specific URL"
            analysis["target_element"] = step.split()[-1]
        elif "click" in step_lower:
            analysis["action_type"] = "click"
            analysis["user_intent"] = "Click on a specific element"
            analysis["target_element"] = step.split("on")[-1].strip().strip('"').strip("'")
        elif "validate" in step_lower:
            analysis["action_type"] = "validation"
            if "landed" in step_lower:
                analysis["user_intent"] = "Validate URL navigation"
                analysis["target_element"] = step.split("on")[-1].strip().strip('"').strip("'")
            elif "text" in step_lower:
                analysis["user_intent"] = "Validate text presence"
                analysis["target_element"] = step.split("text")[-1].strip().strip('"').strip("'")
        
        # Extract context
        if "phones" in step_lower:
            analysis["context"] = "Main navigation menu"
        elif "apple" in step_lower and "filter" in step_lower:
            analysis["context"] = "Product filter section"
        elif "iphone" in step_lower:
            analysis["context"] = "Product listing page"
        elif "white" in step_lower and "color" in step_lower:
            analysis["context"] = "Product detail page color selection"
            
        return analysis
        
    def _analyze_output(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the output/result of the step."""
        analysis = {
            "success": result.get("success", False),
            "confidence": result.get("confidence", 0.0),
            "selector_used": result.get("selector", ""),
            "strategy_used": result.get("strategy", "unknown"),
            "candidates_found": len(result.get("candidates", [])),
            "execution_time": result.get("execution_time", 0.0)
        }
        
        if "error" in result:
            analysis["error"] = result["error"]
            
        return analysis
        
    def _analyze_markup(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the markup/HTML context for the step."""
        analysis = {
            "html_aware": True,
            "element_tag": "unknown",
            "element_attributes": {},
            "element_text": "",
            "element_role": "",
            "accessibility_info": {}
        }
        
        # Extract element information from candidates
        candidates = result.get("candidates", [])
        if candidates:
            best_candidate = candidates[0]
            meta = best_candidate.get("meta", {})
            
            analysis["element_tag"] = meta.get("tag", "unknown")
            analysis["element_attributes"] = meta.get("attributes", {})
            analysis["element_text"] = meta.get("text", "")
            analysis["element_role"] = meta.get("role", "")
            
            # Check for accessibility information
            attrs = meta.get("attributes", {})
            analysis["accessibility_info"] = {
                "aria_label": attrs.get("aria-label", ""),
                "aria_role": attrs.get("role", ""),
                "aria_expanded": attrs.get("aria-expanded", ""),
                "tabindex": attrs.get("tabindex", ""),
                "title": attrs.get("title", "")
            }
            
        return analysis
        
    def _analyze_xpath(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the XPath selector used for the step."""
        analysis = {
            "xpath_selector": result.get("selector", ""),
            "xpath_type": "unknown",
            "xpath_precision": "unknown",
            "xpath_stability": "unknown"
        }
        
        selector = result.get("selector", "")
        if selector:
            if selector.startswith("//"):
                analysis["xpath_type"] = "absolute_xpath"
            elif selector.startswith("./"):
                analysis["xpath_type"] = "relative_xpath"
            else:
                analysis["xpath_type"] = "css_selector"
                
            # Analyze precision
            if "[" in selector and "]" in selector:
                analysis["xpath_precision"] = "high_precision"
            elif selector.count("/") > 3:
                analysis["xpath_precision"] = "medium_precision"
            else:
                analysis["xpath_precision"] = "low_precision"
                
            # Analyze stability
            if "text()" in selector or "contains" in selector:
                analysis["xpath_stability"] = "text_dependent"
            elif "position()" in selector or "last()" in selector:
                analysis["xpath_stability"] = "position_dependent"
            else:
                analysis["xpath_stability"] = "attribute_based"
                
        return analysis
        
    def run_verizon_test(self):
        """Execute the complete Verizon automation test."""
        print("🚀 Starting Verizon Automation Test")
        print("=" * 80)
        
        # Initialize runner with real environment
        self.runner = Runner(headless=self.headless)
        
        # Define test steps
        test_steps = [
            'Navigate to Verizon page "https://www.verizon.com/"',
            'Click on "Phones" button',
            'Click on "Apple" filter',
            'Click on "Apple IPhone 17" device',
            'Validate it landed on "https://www.verizon.com/smartphones/apple-iphone-17/"',
            'Validate "Apple iPhone 17" text on pdp page',
            'Click on "White" color'
        ]
        
        # Execute each step
        for i, step in enumerate(test_steps, 1):
            start_time = time.time()
            
            try:
                print(f"\n🔄 Executing Step {i}: {step}")
                
                # Execute the step
                result = self._execute_step(step)
                execution_time = time.time() - start_time
                result["execution_time"] = execution_time
                
                # Log detailed results
                self._log_step_details(i, step, result)
                
                # Store result
                self.results.append({
                    "step_number": i,
                    "step": step,
                    "result": result,
                    "execution_time": execution_time
                })
                
                # Check if step failed
                if not result.get("success", False):
                    print(f"❌ Step {i} failed: {result.get('error', 'Unknown error')}")
                    break
                    
                # Wait between steps for page stability
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Step {i} failed with exception: {str(e)}")
                result = {
                    "success": False,
                    "error": str(e),
                    "execution_time": time.time() - start_time
                }
                self._log_step_details(i, step, result)
                self.results.append({
                    "step_number": i,
                    "step": step,
                    "result": result,
                    "execution_time": result["execution_time"]
                })
                break
                
        # Generate final report
        self._generate_final_report()
        
        # Cleanup
        if self.runner:
            self.runner._close()
            
        return self.results
        
    def _execute_step(self, step: str) -> Dict[str, Any]:
        """Execute a single step and return detailed results."""
        step_lower = step.lower()
        
        if "navigate" in step_lower or "open" in step_lower:
            return self._execute_navigation(step)
        elif "click" in step_lower:
            return self._execute_click(step)
        elif "validate" in step_lower:
            return self._execute_validation(step)
        else:
            return {"success": False, "error": f"Unknown step type: {step}"}
            
    def _execute_navigation(self, step: str) -> Dict[str, Any]:
        """Execute navigation step."""
        # Extract URL from step
        url = step.split('"')[1] if '"' in step else step.split()[-1]
        
        try:
            # Take snapshot (which navigates to URL)
            snapshot = self.runner.snapshot(url)
            
            return {
                "success": True,
                "url": url,
                "elements_found": len(snapshot.get("elements", [])),
                "dom_hash": snapshot.get("dom_hash", ""),
                "strategy": "navigation"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def _execute_click(self, step: str) -> Dict[str, Any]:
        """Execute click step with detailed element analysis."""
        # Extract target from step
        target = step.split("on")[-1].strip().strip('"').strip("'")
        
        try:
            # Take snapshot first
            snapshot = self.runner.snapshot()
            elements = snapshot.get("elements", [])
            
            # Resolve selector for the target
            resolved = self.runner.resolve_selector(target, snapshot)
            selector = resolved.get("selector", "")
            confidence = resolved.get("confidence", 0.0)
            candidates = resolved.get("candidates", [])
            strategy = resolved.get("strategy", "unknown")
            
            if not selector:
                return {
                    "success": False,
                    "error": "No selector found for target",
                    "target": target,
                    "candidates": candidates
                }
                
            # Execute the click
            parsed = self.runner.intent.parse(step)
            self.runner.do_action(parsed.action, selector, promo=resolved.get("promo", {}))
            
            return {
                "success": True,
                "target": target,
                "selector": selector,
                "confidence": confidence,
                "strategy": strategy,
                "candidates": candidates,
                "elements_analyzed": len(elements)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e), "target": target}
            
    def _execute_validation(self, step: str) -> Dict[str, Any]:
        """Execute validation step."""
        try:
            # Use runner's validation method
            is_valid = self.runner._validate(step)
            
            return {
                "success": is_valid,
                "validation_type": "url" if "landed" in step.lower() else "text",
                "expected": step.split()[-1].strip('"').strip("'") if '"' in step else "unknown"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def _generate_final_report(self):
        """Generate comprehensive final report."""
        print("\n" + "="*80)
        print("📊 FINAL TEST REPORT")
        print("="*80)
        
        total_steps = len(self.results)
        successful_steps = sum(1 for r in self.results if r["result"].get("success", False))
        
        print(f"Total Steps: {total_steps}")
        print(f"Successful Steps: {successful_steps}")
        print(f"Failed Steps: {total_steps - successful_steps}")
        print(f"Success Rate: {(successful_steps/total_steps)*100:.1f}%")
        
        # Save detailed results to file
        report_data = {
            "test_summary": {
                "total_steps": total_steps,
                "successful_steps": successful_steps,
                "failed_steps": total_steps - successful_steps,
                "success_rate": (successful_steps/total_steps)*100
            },
            "detailed_logs": self.detailed_logs,
            "step_results": self.results
        }
        
        with open("verizon_automation_results.json", "w") as f:
            json.dump(report_data, f, indent=2, default=str)
            
        print(f"\n📄 Detailed results saved to: verizon_automation_results.json")
        
        # Print step-by-step summary
        print(f"\n📋 STEP-BY-STEP SUMMARY:")
        for result in self.results:
            step_num = result["step_number"]
            step = result["step"]
            success = result["result"].get("success", False)
            status = "✅" if success else "❌"
            print(f"  {status} Step {step_num}: {step}")


def main():
    """Main function to run the Verizon automation test."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Verizon Automation Test")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set environment variables for real setup
    os.environ["HER_USE_SEMANTIC_SEARCH"] = "true"
    os.environ["HER_CACHE_DIR"] = str(Path(".her_cache").resolve())
    
    # Create and run test
    test = VerizonAutomationTest(headless=args.headless)
    results = test.run_verizon_test()
    
    # Exit with appropriate code
    failed_steps = sum(1 for r in results if not r["result"].get("success", False))
    sys.exit(1 if failed_steps > 0 else 0)


if __name__ == "__main__":
    main()