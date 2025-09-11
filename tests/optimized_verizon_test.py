#!/usr/bin/env python3
"""
Optimized Verizon Test - XPath Generation Only for Top Embeddings
================================================================

This optimized version only generates XPath for the top embedding candidates,
not for all DOM elements. This is much more efficient.
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

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

class OptimizedHTMLElementExtractor:
    """Optimized HTML element extractor that only generates XPath for top candidates."""
    
    def __init__(self):
        self.soup = None
        self.dom_elements = []  # Store raw DOM elements without XPath
    
    def extract_elements_from_page(self, page: Page) -> List[Dict[str, Any]]:
        """Extract all interactive HTML elements from the page WITHOUT generating XPath."""
        try:
            # Get the full HTML content
            html_content = page.content()
            self.soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all potentially interactive elements
            interactive_tags = [
                'a', 'button', 'input', 'select', 'textarea', 'form',
                'div', 'span', 'li', 'ul', 'ol', 'nav', 'menu',
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'label'
            ]
            
            elements = []
            
            for tag_name in interactive_tags:
                tags = self.soup.find_all(tag_name)
                
                for i, tag in enumerate(tags):
                    # Skip if tag is not visible (hidden elements)
                    if self._is_hidden(tag):
                        continue
                    
                    # Extract element information WITHOUT XPath
                    element_info = self._extract_element_info_no_xpath(tag, i)
                    if element_info:
                        elements.append(element_info)
            
            logger.info(f"Extracted {len(elements)} HTML elements (no XPath generated yet)")
            return elements
            
        except Exception as e:
            logger.error(f"Error extracting HTML elements: {e}")
            return []
    
    def _is_hidden(self, tag) -> bool:
        """Check if element is hidden."""
        if not tag:
            return True
        
        # Check style attribute
        style = tag.get('style', '')
        if 'display:none' in style or 'visibility:hidden' in style:
            return True
        
        # Check if parent has hidden class
        parent = tag.parent
        while parent:
            if parent.get('class') and any('hidden' in cls for cls in parent.get('class')):
                return True
            parent = parent.parent
        
        return False
    
    def _extract_element_info_no_xpath(self, tag, index: int) -> Optional[Dict[str, Any]]:
        """Extract element information WITHOUT generating XPath."""
        try:
            # Get all attributes
            attrs = {}
            if tag.attrs:
                for key, value in tag.attrs.items():
                    if isinstance(value, list):
                        attrs[key] = ' '.join(str(v) for v in value)
                    else:
                        attrs[key] = str(value)
            
            # Get text content
            text_content = tag.get_text(strip=True)
            
            # Get tag name
            tag_name = tag.name.lower() if tag.name else 'unknown'
            
            # Determine if element is interactive
            is_interactive = self._is_interactive_element(tag, attrs)
            
            # Create element descriptor WITHOUT XPath
            element_info = {
                'tag': tag_name,
                'text': text_content,
                'attrs': attrs,
                'index': index,
                'is_interactive': is_interactive,
                'role': attrs.get('role', ''),
                'aria_label': attrs.get('aria-label', ''),
                'title': attrs.get('title', ''),
                'id': attrs.get('id', ''),
                'class': attrs.get('class', ''),
                'href': attrs.get('href', ''),
                'type': attrs.get('type', ''),
                'value': attrs.get('value', ''),
                'placeholder': attrs.get('placeholder', ''),
                'name': attrs.get('name', ''),
                'alt': attrs.get('alt', ''),
                'data_testid': attrs.get('data-testid', ''),
                'data_id': attrs.get('data-id', ''),
                'data_value': attrs.get('data-value', ''),
                # XPath will be generated later for top candidates only
                'xpath': None,
                'css_selector': None
            }
            
            return element_info
            
        except Exception as e:
            logger.error(f"Error extracting element info: {e}")
            return None
    
    def _is_interactive_element(self, tag, attrs: Dict[str, str]) -> bool:
        """Determine if element is interactive."""
        tag_name = tag.name.lower() if tag.name else ''
        
        # Interactive tags
        interactive_tags = {'a', 'button', 'input', 'select', 'textarea', 'form'}
        if tag_name in interactive_tags:
            return True
        
        # Elements with interactive roles
        role = attrs.get('role', '').lower()
        interactive_roles = {
            'button', 'link', 'menuitem', 'tab', 'option', 'checkbox', 'radio',
            'textbox', 'searchbox', 'combobox', 'listbox', 'menu', 'menubar'
        }
        if role in interactive_roles:
            return True
        
        # Elements with click handlers
        onclick = attrs.get('onclick', '')
        if onclick:
            return True
        
        # Elements with href
        if attrs.get('href'):
            return True
        
        return False
    
    def generate_xpath_for_candidates(self, page: Page, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate XPath only for top embedding candidates."""
        try:
            logger.info(f"Generating XPath for {len(candidates)} top candidates")
            
            # Use JavaScript to generate XPath for each candidate
            for candidate in candidates:
                try:
                    # Generate XPath using JavaScript
                    xpath_script = """
                    function generateXPath(element) {
                        if (!element) return '';
                        
                        const tag = element.tagName.toLowerCase();
                        const attrs = {};
                        for (const a of element.attributes) {
                            attrs[a.name] = a.value;
                        }
                        
                        const text = (element.innerText || '').trim();
                        
                        // Priority 1: data-testid
                        if (attrs['data-testid']) {
                            return `//*[@data-testid="${attrs['data-testid']}"]`;
                        }
                        
                        // Priority 2: id
                        if (attrs['id']) {
                            return `//*[@id="${attrs['id']}"]`;
                        }
                        
                        // Priority 3: aria-label
                        if (attrs['aria-label']) {
                            return `//*[@aria-label="${attrs['aria-label']}"]`;
                        }
                        
                        // Priority 4: text content
                        if (text) {
                            return `//${tag}[normalize-space()="${text}"]`;
                        }
                        
                        // Priority 5: href for links
                        if (tag === 'a' && attrs['href']) {
                            return `//a[@href="${attrs['href']}"]`;
                        }
                        
                        // Fallback: tag only
                        return `//${tag}`;
                    }
                    
                    // Find element by attributes and text
                    function findElementByCandidate(candidate) {
                        const tag = candidate.tag;
                        const text = candidate.text;
                        const attrs = candidate.attrs;
                        
                        // Try to find by data-testid first
                        if (attrs.data_testid) {
                            const el = document.querySelector(`[data-testid="${attrs.data_testid}"]`);
                            if (el) return el;
                        }
                        
                        // Try to find by id
                        if (attrs.id) {
                            const el = document.getElementById(attrs.id);
                            if (el) return el;
                        }
                        
                        // Try to find by text and tag
                        if (text) {
                            const elements = document.querySelectorAll(tag);
                            for (const el of elements) {
                                if (el.innerText.trim() === text) {
                                    return el;
                                }
                            }
                        }
                        
                        // Try to find by href for links
                        if (tag === 'a' && attrs.href) {
                            const el = document.querySelector(`a[href="${attrs.href}"]`);
                            if (el) return el;
                        }
                        
                        return null;
                    }
                    
                    return findElementByCandidate(arguments[0]);
                    """
                    
                    # Find the element in the DOM
                    element = page.evaluate(xpath_script, candidate)
                    
                    if element:
                        # Generate XPath for the found element
                        xpath_script2 = """
                        function generateXPath(element) {
                            if (!element) return '';
                            
                            const tag = element.tagName.toLowerCase();
                            const attrs = {};
                            for (const a of element.attributes) {
                                attrs[a.name] = a.value;
                            }
                            
                            const text = (element.innerText || '').trim();
                            
                            // Priority 1: data-testid
                            if (attrs['data-testid']) {
                                return `//*[@data-testid="${attrs['data-testid']}"]`;
                            }
                            
                            // Priority 2: id
                            if (attrs['id']) {
                                return `//*[@id="${attrs['id']}"]`;
                            }
                            
                            // Priority 3: aria-label
                            if (attrs['aria-label']) {
                                return `//*[@aria-label="${attrs['aria-label']}"]`;
                            }
                            
                            // Priority 4: text content
                            if (text) {
                                return `//${tag}[normalize-space()="${text}"]`;
                            }
                            
                            // Priority 5: href for links
                            if (tag === 'a' && attrs['href']) {
                                return `//a[@href="${attrs['href']}"]`;
                            }
                            
                            // Fallback: tag only
                            return `//${tag}`;
                        }
                        
                        return generateXPath(arguments[0]);
                        """
                        
                        xpath = page.evaluate(xpath_script2, element)
                        candidate['xpath'] = xpath
                        
                        # Generate CSS selector
                        css_selector = self._generate_css_selector(candidate)
                        candidate['css_selector'] = css_selector
                        
                        logger.info(f"Generated XPath for candidate: {xpath}")
                    else:
                        logger.warning(f"Could not find element in DOM for candidate: {candidate.get('text', '')[:50]}")
                        candidate['xpath'] = "not found"
                        candidate['css_selector'] = "not found"
                        
                except Exception as e:
                    logger.error(f"Error generating XPath for candidate: {e}")
                    candidate['xpath'] = f"error: {e}"
                    candidate['css_selector'] = f"error: {e}"
            
            return candidates
            
        except Exception as e:
            logger.error(f"Error generating XPath for candidates: {e}")
            return candidates
    
    def _generate_css_selector(self, element: Dict[str, Any]) -> str:
        """Generate CSS selector for element."""
        try:
            tag = element.get('tag', '')
            attrs = element.get('attrs', {})
            
            # Start with tag name
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
            return ""

class OptimizedVerizonAutomation:
    """Optimized Verizon automation using XPath generation only for top candidates."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None
        self.extractor = OptimizedHTMLElementExtractor()
        
    def start_browser(self):
        """Start browser."""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not available")
        
        if not BEAUTIFULSOUP_AVAILABLE:
            raise RuntimeError("BeautifulSoup not available. Install with: pip install beautifulsoup4")
        
        # Start browser
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
    
    def find_element_by_text_optimized(self, text: str, element_type: str = "any") -> Optional[Dict[str, Any]]:
        """Find element by text using optimized approach - XPath only for top candidates."""
        try:
            # Step 1: Extract all elements WITHOUT XPath (fast)
            elements = self.extractor.extract_elements_from_page(self.page)
            logger.info(f"Step 1: Extracted {len(elements)} elements (no XPath generated)")
            
            # Step 2: Filter by element type if specified
            if element_type != "any":
                elements = [e for e in elements if e['tag'] == element_type]
            
            # Step 3: Find matching elements (fast text matching)
            matching_elements = []
            search_text = text.lower()
            
            for element in elements:
                element_text = element.get('text', '').lower()
                
                # Exact match first
                if element_text == search_text:
                    matching_elements.insert(0, element)
                # Partial match
                elif search_text in element_text:
                    matching_elements.append(element)
                # Check attributes for text
                elif self._text_in_attributes(element, search_text):
                    matching_elements.append(element)
            
            if not matching_elements:
                logger.warning(f"No matching elements found for: {text}")
                return None
            
            # Step 4: Take only top 3 candidates (optimization)
            top_candidates = matching_elements[:3]
            logger.info(f"Step 2: Found {len(matching_elements)} matches, taking top {len(top_candidates)}")
            
            # Step 5: Generate XPath ONLY for top candidates (expensive operation)
            candidates_with_xpath = self.extractor.generate_xpath_for_candidates(self.page, top_candidates)
            logger.info(f"Step 3: Generated XPath for {len(candidates_with_xpath)} top candidates")
            
            # Step 6: Return the best candidate
            if candidates_with_xpath:
                best_candidate = candidates_with_xpath[0]
                logger.info(f"Selected best candidate: {best_candidate.get('text', '')[:50]}...")
                logger.info(f"XPath: {best_candidate.get('xpath', 'N/A')}")
                return best_candidate
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding element by text: {e}")
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
            if xpath and xpath != "not found" and not xpath.startswith("error"):
                try:
                    self.page.locator(f"xpath={xpath}").click()
                    print(f"   Clicked using XPath: {xpath}")
                    return True
                except Exception as e:
                    print(f"   Failed to click using XPath: {e}")
            
            # Try CSS selector
            css_selector = element.get('css_selector', '')
            if css_selector and css_selector != "not found" and not css_selector.startswith("error"):
                try:
                    self.page.locator(css_selector).click()
                    print(f"   Clicked using CSS selector: {css_selector}")
                    return True
                except Exception as e:
                    print(f"   Failed to click using CSS selector: {e}")
            
            # Try href-based selector
            href = element.get('href', '')
            if href:
                try:
                    self.page.locator(f"a[href='{href}']").click()
                    print(f"   Clicked using href: {href}")
                    return True
                except Exception as e:
                    print(f"   Failed to click using href: {e}")
            
            # Try text-based selector
            text = element.get('text', '')
            if text:
                try:
                    self.page.locator(f"text={text}").click()
                    print(f"   Clicked using text: {text}")
                    return True
                except Exception as e:
                    print(f"   Failed to click using text: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error clicking element: {e}")
            return False
    
    def run_optimized_verizon_test(self) -> Dict[str, Any]:
        """Run the optimized Verizon test case."""
        
        # Your exact test steps
        steps = [
            "Open verizon page https://www.verizon.com/",
            "Click on \"Phones\" button",
            "Click on \"Apple\" filter button", 
            "Click on \"Apple iPhone 16 Pro Max\"",
            "Validate that it landed on \"https://www.verizon.com/smartphones/apple-iphone-16-pro-max/\"",
            "Click on \"512 GB\""
        ]
        
        print("🚀 Optimized Verizon Test - XPath Only for Top Embeddings")
        print("=" * 70)
        print("Running your specific test steps:")
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step}")
        print("=" * 70)
        
        results = []
        
        try:
            # Start browser
            self.start_browser()
            
            # Step 1: Navigate to Verizon
            print(f"\n🔄 Step 1: {steps[0]}")
            self.page.goto("https://www.verizon.com/", wait_until="networkidle")
            time.sleep(3)
            
            # Dismiss popups
            try:
                self.page.click('button[aria-label="Close"]', timeout=2000)
            except:
                pass
            
            results.append({"step": 1, "success": True, "xpath": "navigation", "url": self.page.url})
            print(f"   ✅ Step 1 passed - Navigated to Verizon")
            
            # Step 2: Click on Phones button
            print(f"\n🔄 Step 2: {steps[1]}")
            phones_element = self.find_element_by_text_optimized("Phones", "a")
            if phones_element:
                print(f"   Found Phones element: {phones_element['tag']} - '{phones_element['text']}'")
                print(f"   XPath: {phones_element['xpath']}")
                print(f"   CSS Selector: {phones_element['css_selector']}")
                
                if self.click_element(phones_element):
                    time.sleep(3)
                    results.append({"step": 2, "success": True, "xpath": phones_element['xpath'], "url": self.page.url})
                    print(f"   ✅ Step 2 passed - Clicked Phones button")
                else:
                    results.append({"step": 2, "success": False, "xpath": phones_element['xpath'], "url": self.page.url})
                    print(f"   ❌ Step 2 failed - Could not click Phones button")
                    return {"success": False, "results": results}
            else:
                results.append({"step": 2, "success": False, "xpath": "not found", "url": self.page.url})
                print(f"   ❌ Step 2 failed - Could not find Phones button")
                return {"success": False, "results": results}
            
            # Step 3: Click on Apple filter
            print(f"\n🔄 Step 3: {steps[2]}")
            apple_element = self.find_element_by_text_optimized("Apple", "button")
            if apple_element:
                print(f"   Found Apple element: {apple_element['tag']} - '{apple_element['text']}'")
                print(f"   XPath: {apple_element['xpath']}")
                print(f"   CSS Selector: {apple_element['css_selector']}")
                
                if self.click_element(apple_element):
                    time.sleep(2)
                    results.append({"step": 3, "success": True, "xpath": apple_element['xpath'], "url": self.page.url})
                    print(f"   ✅ Step 3 passed - Clicked Apple filter")
                else:
                    results.append({"step": 3, "success": False, "xpath": apple_element['xpath'], "url": self.page.url})
                    print(f"   ❌ Step 3 failed - Could not click Apple filter")
                    return {"success": False, "results": results}
            else:
                results.append({"step": 3, "success": False, "xpath": "not found", "url": self.page.url})
                print(f"   ❌ Step 3 failed - Could not find Apple filter")
                return {"success": False, "results": results}
            
            # Step 4: Click on iPhone 16 Pro Max
            print(f"\n🔄 Step 4: {steps[3]}")
            iphone_element = self.find_element_by_text_optimized("Apple iPhone 16 Pro Max", "a")
            if iphone_element:
                print(f"   Found iPhone element: {iphone_element['tag']} - '{iphone_element['text']}'")
                print(f"   XPath: {iphone_element['xpath']}")
                print(f"   CSS Selector: {iphone_element['css_selector']}")
                
                if self.click_element(iphone_element):
                    time.sleep(3)
                    results.append({"step": 4, "success": True, "xpath": iphone_element['xpath'], "url": self.page.url})
                    print(f"   ✅ Step 4 passed - Clicked iPhone 16 Pro Max")
                else:
                    results.append({"step": 4, "success": False, "xpath": iphone_element['xpath'], "url": self.page.url})
                    print(f"   ❌ Step 4 failed - Could not click iPhone 16 Pro Max")
                    return {"success": False, "results": results}
            else:
                results.append({"step": 4, "success": False, "xpath": "not found", "url": self.page.url})
                print(f"   ❌ Step 4 failed - Could not find iPhone 16 Pro Max")
                return {"success": False, "results": results}
            
            # Step 5: Validate URL
            print(f"\n🔄 Step 5: {steps[4]}")
            expected_url = "https://www.verizon.com/smartphones/apple-iphone-16-pro-max/"
            current_url = self.page.url
            
            print(f"   Expected URL: {expected_url}")
            print(f"   Current URL: {current_url}")
            
            if expected_url in current_url or current_url in expected_url:
                results.append({"step": 5, "success": True, "xpath": "url validation", "url": current_url})
                print(f"   ✅ Step 5 passed - URL validation successful")
            else:
                results.append({"step": 5, "success": False, "xpath": "url mismatch", "url": current_url})
                print(f"   ❌ Step 5 failed - URL validation failed")
                return {"success": False, "results": results}
            
            # Step 6: Click on 512 GB
            print(f"\n🔄 Step 6: {steps[5]}")
            gb_element = self.find_element_by_text_optimized("512 GB", "button")
            if gb_element:
                print(f"   Found 512 GB element: {gb_element['tag']} - '{gb_element['text']}'")
                print(f"   XPath: {gb_element['xpath']}")
                print(f"   CSS Selector: {gb_element['css_selector']}")
                
                if self.click_element(gb_element):
                    time.sleep(2)
                    results.append({"step": 6, "success": True, "xpath": gb_element['xpath'], "url": self.page.url})
                    print(f"   ✅ Step 6 passed - Clicked 512 GB")
                else:
                    results.append({"step": 6, "success": False, "xpath": gb_element['xpath'], "url": self.page.url})
                    print(f"   ❌ Step 6 failed - Could not click 512 GB")
            else:
                results.append({"step": 6, "success": False, "xpath": "not found", "url": self.page.url})
                print(f"   ❌ Step 6 failed - Could not find 512 GB option")
            
            # Summary
            print("\n" + "=" * 70)
            print("📊 OPTIMIZED VERIZON TEST RESULTS")
            print("=" * 70)
            
            successful_steps = sum(1 for r in results if r["success"])
            total_steps = len(results)
            success_rate = (successful_steps / total_steps) * 100 if total_steps > 0 else 0
            
            print(f"Total Steps: {total_steps}")
            print(f"Successful Steps: {successful_steps}")
            print(f"Success Rate: {success_rate:.1f}%")
            print(f"Final URL: {self.page.url}")
            
            print(f"\n📋 Detailed Results with XPaths:")
            for result in results:
                status = "✅ PASS" if result["success"] else "❌ FAIL"
                print(f"  Step {result['step']}: {status}")
                print(f"    XPath Used: {result['xpath']}")
                print(f"    URL: {result['url']}")
                print()
            
            return {
                "success": success_rate >= 80,
                "success_rate": success_rate,
                "results": results,
                "final_url": self.page.url
            }
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "results": results, "error": str(e)}
        
        finally:
            self.stop_browser()

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Optimized Verizon Test")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    
    args = parser.parse_args()
    
    print("🚀 Starting Optimized Verizon Test")
    print("=" * 70)
    
    automation = OptimizedVerizonAutomation(headless=args.headless)
    result = automation.run_optimized_verizon_test()
    
    if result["success"]:
        print("🎉 Optimized Verizon test completed successfully!")
    else:
        print("💥 Optimized Verizon test failed!")
    
    exit(0 if result["success"] else 1)

if __name__ == "__main__":
    main()