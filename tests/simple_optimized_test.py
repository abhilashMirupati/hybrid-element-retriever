#!/usr/bin/env python3
"""
Simple Optimized Test - XPath Only for Top Candidates
====================================================

This demonstrates the optimization concept: generate XPath only for top embedding candidates.
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add src to path for HER framework
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from playwright.sync_api import sync_playwright, Page, Browser, Playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleOptimizedExtractor:
    """Simple optimized extractor that only generates XPath for top candidates."""
    
    def __init__(self):
        self.soup = None
    
    def extract_elements_fast(self, page: Page) -> List[Dict[str, Any]]:
        """Extract elements quickly without XPath generation."""
        try:
            html_content = page.content()
            self.soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find interactive elements
            interactive_tags = ['a', 'button', 'input', 'select', 'textarea']
            elements = []
            
            for tag_name in interactive_tags:
                tags = self.soup.find_all(tag_name)
                
                for i, tag in enumerate(tags):
                    if self._is_hidden(tag):
                        continue
                    
                    element_info = self._extract_basic_info(tag, i)
                    if element_info:
                        elements.append(element_info)
            
            logger.info(f"Extracted {len(elements)} elements (no XPath generated)")
            return elements
            
        except Exception as e:
            logger.error(f"Error extracting elements: {e}")
            return []
    
    def _is_hidden(self, tag) -> bool:
        """Check if element is hidden."""
        if not tag:
            return True
        
        style = tag.get('style', '')
        if 'display:none' in style or 'visibility:hidden' in style:
            return True
        
        return False
    
    def _extract_basic_info(self, tag, index: int) -> Optional[Dict[str, Any]]:
        """Extract basic element info without XPath."""
        try:
            attrs = {}
            if tag.attrs:
                for key, value in tag.attrs.items():
                    if isinstance(value, list):
                        attrs[key] = ' '.join(str(v) for v in value)
                    else:
                        attrs[key] = str(value)
            
            text_content = tag.get_text(strip=True)
            tag_name = tag.name.lower() if tag.name else 'unknown'
            
            return {
                'tag': tag_name,
                'text': text_content,
                'attrs': attrs,
                'index': index,
                'xpath': None,  # Will be generated later for top candidates only
                'css_selector': None
            }
            
        except Exception as e:
            logger.error(f"Error extracting basic info: {e}")
            return None
    
    def generate_xpath_for_top_candidates(self, page: Page, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate XPath only for top candidates using simple selectors."""
        try:
            logger.info(f"Generating XPath for {len(candidates)} top candidates")
            
            for candidate in candidates:
                try:
                    # Generate simple XPath based on attributes
                    xpath = self._generate_simple_xpath(candidate)
                    candidate['xpath'] = xpath
                    
                    # Generate CSS selector
                    css_selector = self._generate_simple_css(candidate)
                    candidate['css_selector'] = css_selector
                    
                    logger.info(f"Generated XPath: {xpath}")
                    
                except Exception as e:
                    logger.error(f"Error generating XPath for candidate: {e}")
                    candidate['xpath'] = f"error: {e}"
                    candidate['css_selector'] = f"error: {e}"
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error generating XPath for candidates: {e}")
            return candidates
    
    def _generate_simple_xpath(self, element: Dict[str, Any]) -> str:
        """Generate simple XPath based on element attributes."""
        try:
            tag = element.get('tag', '')
            attrs = element.get('attrs', {})
            text = element.get('text', '')
            
            # Priority 1: data-testid
            if attrs.get('data-testid'):
                return f"//*[@data-testid='{attrs['data-testid']}']"
            
            # Priority 2: id
            if attrs.get('id'):
                return f"//*[@id='{attrs['id']}']"
            
            # Priority 3: aria-label
            if attrs.get('aria-label'):
                return f"//*[@aria-label='{attrs['aria-label']}']"
            
            # Priority 4: href for links
            if tag == 'a' and attrs.get('href'):
                return f"//a[@href='{attrs['href']}']"
            
            # Priority 5: text content
            if text:
                return f"//{tag}[normalize-space()='{text}']"
            
            # Fallback: tag only
            return f"//{tag}"
            
        except Exception:
            return "//unknown"
    
    def _generate_simple_css(self, element: Dict[str, Any]) -> str:
        """Generate simple CSS selector."""
        try:
            tag = element.get('tag', '')
            attrs = element.get('attrs', {})
            
            selector = tag
            
            # Add ID if present
            if attrs.get('id'):
                selector += f"#{attrs['id']}"
            
            # Add classes if present
            classes = attrs.get('class', [])
            if classes:
                class_str = '.'.join(classes)
                selector += f".{class_str}"
            
            return selector
            
        except Exception:
            return "unknown"

class SimpleOptimizedAutomation:
    """Simple optimized automation demonstrating the concept."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None
        self.extractor = SimpleOptimizedExtractor()
        
    def start_browser(self):
        """Start browser."""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not available")
        
        if not BEAUTIFULSOUP_AVAILABLE:
            raise RuntimeError("BeautifulSoup not available")
        
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-web-security']
        )
        self.page = self.browser.new_page()
        self.page.set_default_timeout(30000)
        
        logger.info("Browser started")
    
    def stop_browser(self):
        """Stop browser and clean up."""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            logger.warning(f"Error stopping browser: {e}")
    
    def find_element_optimized(self, text: str, element_type: str = "any") -> Optional[Dict[str, Any]]:
        """Find element using optimized approach - XPath only for top candidates."""
        try:
            print(f"🔍 OPTIMIZATION DEMO: Finding '{text}' element")
            
            # Step 1: Extract all elements WITHOUT XPath (fast)
            start_time = time.time()
            elements = self.extractor.extract_elements_fast(self.page)
            extract_time = time.time() - start_time
            print(f"   Step 1: Extracted {len(elements)} elements in {extract_time:.3f}s (no XPath generated)")
            
            # Step 2: Filter by element type
            if element_type != "any":
                elements = [e for e in elements if e['tag'] == element_type]
            
            # Step 3: Find matching elements (fast text matching)
            start_time = time.time()
            matching_elements = []
            search_text = text.lower()
            
            for element in elements:
                element_text = element.get('text', '').lower()
                
                if element_text == search_text:
                    matching_elements.insert(0, element)
                elif search_text in element_text:
                    matching_elements.append(element)
                elif self._text_in_attributes(element, search_text):
                    matching_elements.append(element)
            
            match_time = time.time() - start_time
            print(f"   Step 2: Found {len(matching_elements)} matches in {match_time:.3f}s")
            
            if not matching_elements:
                print(f"   ❌ No matching elements found")
                return None
            
            # Step 4: Take only top 3 candidates (optimization)
            top_candidates = matching_elements[:3]
            print(f"   Step 3: Taking top {len(top_candidates)} candidates (optimization)")
            
            # Step 5: Generate XPath ONLY for top candidates (expensive operation)
            start_time = time.time()
            candidates_with_xpath = self.extractor.generate_xpath_for_top_candidates(self.page, top_candidates)
            xpath_time = time.time() - start_time
            print(f"   Step 4: Generated XPath for {len(candidates_with_xpath)} candidates in {xpath_time:.3f}s")
            
            # Step 6: Return the best candidate
            if candidates_with_xpath:
                best_candidate = candidates_with_xpath[0]
                print(f"   ✅ Selected best candidate: '{best_candidate.get('text', '')[:50]}...'")
                print(f"   XPath: {best_candidate.get('xpath', 'N/A')}")
                print(f"   CSS: {best_candidate.get('css_selector', 'N/A')}")
                return best_candidate
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding element: {e}")
            return None
    
    def _text_in_attributes(self, element: Dict[str, Any], search_text: str) -> bool:
        """Check if text appears in element attributes."""
        attrs = element.get('attrs', {})
        text_attrs = ['aria-label', 'title', 'alt', 'placeholder', 'value', 'data-testid']
        
        for attr in text_attrs:
            if attr in attrs and search_text in attrs[attr].lower():
                return True
        return False
    
    def click_element(self, element: Dict[str, Any]) -> bool:
        """Click an element using its XPath or CSS selector."""
        try:
            if not element:
                return False
            
            # Try XPath first
            xpath = element.get('xpath', '')
            if xpath and not xpath.startswith("error"):
                try:
                    self.page.locator(f"xpath={xpath}").click()
                    print(f"   ✅ Clicked using XPath: {xpath}")
                    return True
                except Exception as e:
                    print(f"   ❌ Failed to click using XPath: {e}")
            
            # Try CSS selector
            css_selector = element.get('css_selector', '')
            if css_selector and not css_selector.startswith("error"):
                try:
                    self.page.locator(css_selector).click()
                    print(f"   ✅ Clicked using CSS selector: {css_selector}")
                    return True
                except Exception as e:
                    print(f"   ❌ Failed to click using CSS selector: {e}")
            
            # Try href-based selector
            href = element.get('attrs', {}).get('href', '')
            if href:
                try:
                    self.page.locator(f"a[href='{href}']").click()
                    print(f"   ✅ Clicked using href: {href}")
                    return True
                except Exception as e:
                    print(f"   ❌ Failed to click using href: {e}")
            
            # Try text-based selector
            text = element.get('text', '')
            if text:
                try:
                    self.page.locator(f"text={text}").click()
                    print(f"   ✅ Clicked using text: {text}")
                    return True
                except Exception as e:
                    print(f"   ❌ Failed to click using text: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error clicking element: {e}")
            return False
    
    def run_optimization_demo(self) -> Dict[str, Any]:
        """Run optimization demonstration."""
        
        print("🚀 OPTIMIZATION DEMO: XPath Only for Top Embeddings")
        print("=" * 70)
        print("This demonstrates the optimization concept:")
        print("1. Extract ALL elements quickly (no XPath generation)")
        print("2. Find matching elements using fast text matching")
        print("3. Take only top 3 candidates")
        print("4. Generate XPath ONLY for top candidates (expensive operation)")
        print("=" * 70)
        
        results = []
        
        try:
            # Start browser
            self.start_browser()
            
            # Navigate to Verizon
            print(f"\n🌐 Navigating to Verizon...")
            self.page.goto("https://www.verizon.com/", wait_until="networkidle")
            time.sleep(3)
            
            # Dismiss popups
            try:
                self.page.click('button[aria-label="Close"]', timeout=2000)
            except:
                pass
            
            print(f"✅ Navigated to Verizon")
            
            # Demo: Find Phones button
            print(f"\n🔍 DEMO: Finding 'Phones' button")
            phones_element = self.find_element_optimized("Phones", "a")
            if phones_element:
                print(f"\n📋 Phones Element Details:")
                print(f"   Tag: {phones_element['tag']}")
                print(f"   Text: '{phones_element['text']}'")
                print(f"   XPath: {phones_element['xpath']}")
                print(f"   CSS Selector: {phones_element['css_selector']}")
                print(f"   Attributes: {phones_element['attrs']}")
                
                if self.click_element(phones_element):
                    time.sleep(3)
                    results.append({"element": "Phones", "success": True, "xpath": phones_element['xpath']})
                    print(f"   ✅ Successfully clicked Phones button")
                else:
                    results.append({"element": "Phones", "success": False, "xpath": phones_element['xpath']})
                    print(f"   ❌ Failed to click Phones button")
            else:
                results.append({"element": "Phones", "success": False, "xpath": "not found"})
                print(f"   ❌ Could not find Phones button")
            
            # Demo: Find Apple filter
            print(f"\n🔍 DEMO: Finding 'Apple' filter")
            apple_element = self.find_element_optimized("Apple", "button")
            if apple_element:
                print(f"\n📋 Apple Element Details:")
                print(f"   Tag: {apple_element['tag']}")
                print(f"   Text: '{apple_element['text']}'")
                print(f"   XPath: {apple_element['xpath']}")
                print(f"   CSS Selector: {apple_element['css_selector']}")
                print(f"   Attributes: {apple_element['attrs']}")
                
                if self.click_element(apple_element):
                    time.sleep(2)
                    results.append({"element": "Apple", "success": True, "xpath": apple_element['xpath']})
                    print(f"   ✅ Successfully clicked Apple filter")
                else:
                    results.append({"element": "Apple", "success": False, "xpath": apple_element['xpath']})
                    print(f"   ❌ Failed to click Apple filter")
            else:
                results.append({"element": "Apple", "success": False, "xpath": "not found"})
                print(f"   ❌ Could not find Apple filter")
            
            # Summary
            print("\n" + "=" * 70)
            print("📊 OPTIMIZATION DEMO RESULTS")
            print("=" * 70)
            
            successful_elements = sum(1 for r in results if r["success"])
            total_elements = len(results)
            success_rate = (successful_elements / total_elements) * 100 if total_elements > 0 else 0
            
            print(f"Total Elements: {total_elements}")
            print(f"Successful Elements: {successful_elements}")
            print(f"Success Rate: {success_rate:.1f}%")
            
            print(f"\n📋 Element Results:")
            for result in results:
                status = "✅ PASS" if result["success"] else "❌ FAIL"
                print(f"  {result['element']}: {status}")
                print(f"    XPath: {result['xpath']}")
                print()
            
            print("🎯 OPTIMIZATION BENEFITS:")
            print("✅ XPath generated only for top 3 candidates (not all elements)")
            print("✅ Much faster element extraction")
            print("✅ Reduced computational overhead")
            print("✅ Better performance for large DOMs")
            
            return {
                "success": success_rate >= 50,
                "success_rate": success_rate,
                "results": results
            }
            
        except Exception as e:
            print(f"❌ Demo failed with error: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "results": results, "error": str(e)}
        
        finally:
            self.stop_browser()

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Optimization Demo")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    
    args = parser.parse_args()
    
    print("🚀 Starting Optimization Demo")
    print("=" * 70)
    
    automation = SimpleOptimizedAutomation(headless=args.headless)
    result = automation.run_optimization_demo()
    
    if result["success"]:
        print("🎉 Optimization demo completed successfully!")
    else:
        print("💥 Optimization demo failed!")
    
    exit(0 if result["success"] else 1)

if __name__ == "__main__":
    main()