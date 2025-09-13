"""
Natural Language Test Runner
Allows users to write tests in plain English business language.
The framework automatically handles all technical details.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from ..core.runner import Runner
from ..core.config_service import get_config_service

logger = logging.getLogger("her.natural_test")


@dataclass
class TestStep:
    """Represents a single test step in natural language."""
    step_number: int
    description: str
    expected_outcome: Optional[str] = None
    timeout: int = 30  # seconds


class NaturalTestRunner:
    """Runs tests written in natural language."""
    
    def __init__(self, headless: bool = True):
        """Initialize the natural test runner.
        
        Args:
            headless: Whether to run browser in headless mode.
        """
        self.runner = Runner(headless=headless)
        self.config_service = get_config_service()
        self.current_url = ""
        self.step_results = []
        
    def run_test(self, test_name: str, steps: List[str], start_url: str) -> Dict[str, Any]:
        """Run a test defined by natural language steps.
        
        Args:
            test_name: Name of the test.
            steps: List of natural language step descriptions.
            start_url: URL to start the test from.
            
        Returns:
            Dictionary with test results.
        """
        logger.info(f"Starting test: {test_name}")
        logger.info(f"Steps to execute: {len(steps)}")
        
        try:
            # Navigate to starting URL
            self._navigate_to_start(start_url)
            
            # Execute each step
            for i, step_description in enumerate(steps, 1):
                logger.info(f"Executing step {i}: {step_description}")
                result = self._execute_step(i, step_description)
                self.step_results.append(result)
                
                # Check if step failed
                if not result['success']:
                    logger.error(f"Step {i} failed: {result['error']}")
                    return self._create_test_result(test_name, False, f"Failed at step {i}")
                
                # Auto-detect page transitions and take new snapshot
                self._handle_page_transition()
                
            logger.info(f"Test '{test_name}' completed successfully!")
            return self._create_test_result(test_name, True, "All steps completed successfully")
            
        except Exception as e:
            logger.error(f"Test '{test_name}' failed with exception: {e}")
            return self._create_test_result(test_name, False, str(e))
        finally:
            self.runner._close()
    
    def _navigate_to_start(self, start_url: str) -> None:
        """Navigate to the starting URL."""
        logger.info(f"Navigating to: {start_url}")
        snapshot = self.runner.snapshot(start_url)
        self.current_url = self.runner.get_current_url()
        logger.info(f"Successfully navigated to: {self.current_url}")
    
    def _execute_step(self, step_number: int, description: str) -> Dict[str, Any]:
        """Execute a single natural language step.
        
        Args:
            step_number: Step number.
            description: Natural language description of what to do.
            
        Returns:
            Dictionary with step execution results.
        """
        try:
            # Parse the step description to understand the action
            action_info = self._parse_step_description(description)
            
            # Handle special cases
            if action_info['action'] == 'navigate':
                # For navigation, just navigate to the URL
                self._navigate_to_start(action_info['target'])
                return {
                    'step_number': step_number,
                    'success': True,
                    'action': 'navigate',
                    'target': action_info['target'],
                    'confidence': 1.0,
                    'selector': 'N/A'
                }
            elif action_info['action'] == 'wait':
                # For wait actions, just wait
                return {
                    'step_number': step_number,
                    'success': True,
                    'action': 'wait',
                    'target': 'page',
                    'confidence': 1.0,
                    'selector': 'N/A'
                }
            
            # Take a snapshot of current page
            snapshot = self.runner.snapshot()
            
            # Find the target element
            result = self.runner.resolve_selector(action_info['target'], snapshot)
            
            if result['confidence'] < 0.5:
                return {
                    'step_number': step_number,
                    'success': False,
                    'error': f"Could not find element for '{action_info['target']}' (confidence: {result['confidence']:.3f})",
                    'confidence': result['confidence']
                }
            
            # Execute the action
            self.runner.do_action(
                action=action_info['action'],
                selector=result['selector'],
                value=action_info.get('value'),
                promo=result.get('promo', {}),
                user_intent=description
            )
            
            # Wait for action to complete
            self.runner.wait_for_timeout(2000)
            
            # Take a fresh snapshot after action to capture any page changes
            fresh_snapshot = self.runner.snapshot()
            
            return {
                'step_number': step_number,
                'success': True,
                'action': action_info['action'],
                'target': action_info['target'],
                'confidence': result['confidence'],
                'selector': result['selector']
            }
            
        except Exception as e:
            return {
                'step_number': step_number,
                'success': False,
                'error': str(e),
                'confidence': 0.0
            }
    
    def _parse_step_description(self, description: str) -> Dict[str, Any]:
        """Parse natural language step description into actionable information.
        
        Args:
            description: Natural language description.
            
        Returns:
            Dictionary with parsed action information.
        """
        description_lower = description.lower().strip()
        
        # Define action patterns
        action_patterns = {
            'click': ['click', 'tap', 'press', 'select', 'choose', 'hit'],
            'type': ['type', 'enter', 'input', 'fill', 'write'],
            'hover': ['hover', 'mouse over', 'point to'],
            'wait': ['wait', 'pause', 'sleep'],
            'navigate': ['go to', 'navigate to', 'visit', 'open'],
            'verify': ['verify', 'check', 'confirm', 'ensure'],
            'scroll': ['scroll', 'scroll down', 'scroll up']
        }
        
        # Find the action
        action = 'click'  # default
        for action_type, patterns in action_patterns.items():
            if any(pattern in description_lower for pattern in patterns):
                action = action_type
                break
        
        # Extract target and value
        target = description
        value = None
        
        if action == 'type':
            # Extract text to type - look for common patterns
            if 'type' in description_lower:
                parts = description.split('type', 1)
                if len(parts) > 1:
                    target = parts[0].strip()
                    value = parts[1].strip().strip('"\'')
            elif 'enter' in description_lower:
                parts = description.split('enter', 1)
                if len(parts) > 1:
                    target = parts[0].strip()
                    value = parts[1].strip().strip('"\'')
            elif 'fill' in description_lower:
                parts = description.split('fill', 1)
                if len(parts) > 1:
                    target = parts[0].strip()
                    value = parts[1].strip().strip('"\'')
            else:
                # If no clear pattern, assume the whole description is the value
                # and look for common input field names
                value = description
                target = "search box" if any(word in description_lower for word in ['search', 'query']) else "input field"
        elif action == 'navigate':
            # Extract URL
            if 'to' in description_lower:
                parts = description.split('to', 1)
                if len(parts) > 1:
                    target = parts[1].strip()
        elif action == 'wait':
            # Extract wait time
            import re
            time_match = re.search(r'(\d+)\s*(second|sec|s|minute|min|m)', description_lower)
            if time_match:
                time_value = int(time_match.group(1))
                time_unit = time_match.group(2)
                if time_unit in ['minute', 'min', 'm']:
                    time_value *= 60
                self.runner.wait_for_timeout(time_value * 1000)  # convert to milliseconds
                return {'action': 'wait', 'target': 'page', 'value': time_value}
        
        return {
            'action': action,
            'target': target,
            'value': value
        }
    
    def _handle_page_transition(self) -> None:
        """Automatically detect page transitions and take new snapshot."""
        new_url = self.runner.get_current_url()
        
        if new_url != self.current_url:
            logger.info(f"Page transition detected: {self.current_url} -> {new_url}")
            self.current_url = new_url
             
            # Wait for page to fully load
            self.runner.wait_for_timeout(3000)
            
            # Take a new snapshot to ensure we have current page state
            snapshot = self.runner.snapshot()
            logger.info(f"New page loaded with {len(snapshot.get('elements', []))} elements")
    
    def _create_test_result(self, test_name: str, success: bool, message: str) -> Dict[str, Any]:
        """Create test result summary.
        
        Args:
            test_name: Name of the test.
            success: Whether test passed.
            message: Result message.
            
        Returns:
            Dictionary with test results.
        """
        return {
            'test_name': test_name,
            'success': success,
            'message': message,
            'total_steps': len(self.step_results),
            'successful_steps': sum(1 for r in self.step_results if r['success']),
            'failed_steps': sum(1 for r in self.step_results if not r['success']),
            'step_results': self.step_results,
            'final_url': self.current_url
        }


def run_natural_test(test_name: str, steps: List[str], start_url: str, headless: bool = True) -> Dict[str, Any]:
    """Convenience function to run a natural language test.
    
    Args:
        test_name: Name of the test.
        steps: List of natural language step descriptions.
        start_url: URL to start the test from.
        headless: Whether to run browser in headless mode.
        
    Returns:
        Dictionary with test results.
    """
    runner = NaturalTestRunner(headless=headless)
    return runner.run_test(test_name, steps, start_url)