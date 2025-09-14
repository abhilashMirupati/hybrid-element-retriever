#!/usr/bin/env python3
"""
Verizon Manual Testing Guide with Canonical Element Trees and XPaths.
This provides the XPaths and canonical descriptors for manual UI testing.
"""

def print_verizon_manual_testing_guide():
    """Print comprehensive manual testing guide for Verizon flow."""
    
    print("🎯 VERIZON MANUAL TESTING GUIDE")
    print("=" * 80)
    print("Use these XPaths and canonical descriptors to manually test in the UI:")
    print()
    
    # Test steps with expected elements
    test_cases = [
        {
            'step': 1,
            'query': 'Navigate to https://www.verizon.com/',
            'description': 'Navigate to Verizon homepage',
            'expected_xpath': '//nav[@data-testid="gnav-shop"]',
            'canonical': 'tag=nav | class=gnav-shop | data-testid=gnav-shop | text=Shop | visible=true | interactive=true',
            'manual_instructions': [
                '1. Open browser and navigate to https://www.verizon.com/',
                '2. Look for the main navigation menu',
                '3. Verify the "Shop" navigation element is visible',
                '4. Test XPath: //nav[@data-testid="gnav-shop"]'
            ]
        },
        {
            'step': 2, 
            'query': 'Click on Phones button',
            'description': 'Click on Phones navigation',
            'expected_xpath': '//a[@data-testid="gnav-phones"]',
            'canonical': 'tag=a | href=/smartphones/ | class=gnav-link | data-testid=gnav-phones | text=Phones | visible=true | interactive=true',
            'manual_instructions': [
                '1. Look for "Phones" link in the navigation menu',
                '2. Verify it has href="/smartphones/"',
                '3. Test XPath: //a[@data-testid="gnav-phones"]',
                '4. Click on the element to navigate to phones section'
            ]
        },
        {
            'step': 3,
            'query': 'Click on Apple filter',
            'description': 'Click on Apple brand filter',
            'expected_xpath': '//button[@data-testid="filter-apple"]',
            'canonical': 'tag=button | class=filter-button | data-brand=apple | data-testid=filter-apple | text=Apple | visible=true | interactive=true',
            'manual_instructions': [
                '1. Look for brand filter section on phones page',
                '2. Find "Apple" filter button',
                '3. Test XPath: //button[@data-testid="filter-apple"]',
                '4. Click to filter phones by Apple brand'
            ]
        },
        {
            'step': 4,
            'query': 'Click on Apple iPhone 17 device',
            'description': 'Click on iPhone 17 product',
            'expected_xpath': '//div[@data-testid="product-iphone-17"]',
            'canonical': 'tag=div | class=product-card | data-product=iphone-17 | data-testid=product-iphone-17 | text=Apple iPhone 17 | visible=true | interactive=true',
            'manual_instructions': [
                '1. Look for product cards in the filtered results',
                '2. Find "Apple iPhone 17" product card',
                '3. Test XPath: //div[@data-testid="product-iphone-17"]',
                '4. Click on the product card to view details'
            ]
        },
        {
            'step': 5,
            'query': 'Validate it landed on https://www.verizon.com/smartphones/apple-iphone-17/',
            'description': 'Validate URL navigation',
            'expected_xpath': '//h1[@data-testid="product-title"]',
            'canonical': 'tag=h1 | class=product-title | data-testid=product-title | text=Apple iPhone 17 | visible=true | interactive=false',
            'manual_instructions': [
                '1. Verify URL changed to /smartphones/apple-iphone-17/',
                '2. Look for product title heading',
                '3. Test XPath: //h1[@data-testid="product-title"]',
                '4. Verify page title shows "Apple iPhone 17"'
            ]
        },
        {
            'step': 6,
            'query': 'Validate Apple iPhone 17 text on pdp page',
            'description': 'Validate product title text',
            'expected_xpath': '//h1[@data-testid="product-title"]',
            'canonical': 'tag=h1 | class=product-title | data-testid=product-title | text=Apple iPhone 17 | visible=true | interactive=false',
            'manual_instructions': [
                '1. Look for the main product title on the page',
                '2. Verify text content is "Apple iPhone 17"',
                '3. Test XPath: //h1[@data-testid="product-title"]',
                '4. Confirm the title is visible and properly formatted'
            ]
        },
        {
            'step': 7,
            'query': 'Click on White color',
            'description': 'Click on White color option',
            'expected_xpath': '//button[@data-testid="color-white"]',
            'canonical': 'tag=button | class=color-option | data-color=white | data-testid=color-white | text=White | visible=true | interactive=true',
            'manual_instructions': [
                '1. Look for color selection options on the product page',
                '2. Find "White" color option button',
                '3. Test XPath: //button[@data-testid="color-white"]',
                '4. Click to select white color variant'
            ]
        }
    ]
    
    for case in test_cases:
        print(f"Step {case['step']}: {case['query']}")
        print(f"  📝 Description: {case['description']}")
        print(f"  🎯 XPath: {case['expected_xpath']}")
        print(f"  📋 Canonical: {case['canonical']}")
        print(f"  🔧 Manual Test Instructions:")
        for instruction in case['manual_instructions']:
            print(f"     {instruction}")
        print()

def print_alternative_xpaths():
    """Print alternative XPath strategies for each step."""
    
    print("\n" + "="*80)
    print("🔄 ALTERNATIVE XPATH STRATEGIES")
    print("="*80)
    print("If the primary XPath doesn't work, try these alternatives:")
    print()
    
    alternatives = [
        {
            'step': 1,
            'primary': '//nav[@data-testid="gnav-shop"]',
            'alternatives': [
                '//nav[contains(@class, "gnav")]',
                '//nav[contains(text(), "Shop")]',
                '//*[@data-testid="gnav-shop"]',
                '//nav//a[contains(text(), "Shop")]'
            ]
        },
        {
            'step': 2,
            'primary': '//a[@data-testid="gnav-phones"]',
            'alternatives': [
                '//a[contains(@href, "smartphones")]',
                '//a[contains(text(), "Phones")]',
                '//*[@data-testid="gnav-phones"]',
                '//nav//a[contains(text(), "Phones")]'
            ]
        },
        {
            'step': 3,
            'primary': '//button[@data-testid="filter-apple"]',
            'alternatives': [
                '//button[contains(@class, "filter")]',
                '//button[contains(text(), "Apple")]',
                '//*[@data-brand="apple"]',
                '//button[contains(@data-testid, "apple")]'
            ]
        },
        {
            'step': 4,
            'primary': '//div[@data-testid="product-iphone-17"]',
            'alternatives': [
                '//div[contains(@class, "product-card")]',
                '//div[contains(text(), "iPhone 17")]',
                '//*[contains(@data-product, "iphone")]',
                '//div[contains(@data-testid, "product")]'
            ]
        },
        {
            'step': 5,
            'primary': '//h1[@data-testid="product-title"]',
            'alternatives': [
                '//h1[contains(@class, "product-title")]',
                '//h1[contains(text(), "iPhone 17")]',
                '//*[@data-testid="product-title"]',
                '//h1[contains(text(), "Apple")]'
            ]
        },
        {
            'step': 6,
            'primary': '//h1[@data-testid="product-title"]',
            'alternatives': [
                '//h1[contains(@class, "product-title")]',
                '//h1[contains(text(), "iPhone 17")]',
                '//*[@data-testid="product-title"]',
                '//h1[contains(text(), "Apple")]'
            ]
        },
        {
            'step': 7,
            'primary': '//button[@data-testid="color-white"]',
            'alternatives': [
                '//button[contains(@class, "color-option")]',
                '//button[contains(text(), "White")]',
                '//*[@data-color="white"]',
                '//button[contains(@data-testid, "color")]'
            ]
        }
    ]
    
    for alt in alternatives:
        print(f"Step {alt['step']}:")
        print(f"  Primary: {alt['primary']}")
        print(f"  Alternatives:")
        for i, alternative in enumerate(alt['alternatives'], 1):
            print(f"    {i}. {alternative}")
        print()

def print_browser_testing_commands():
    """Print browser console commands for testing XPaths."""
    
    print("\n" + "="*80)
    print("🌐 BROWSER CONSOLE TESTING COMMANDS")
    print("="*80)
    print("Use these commands in browser developer console to test XPaths:")
    print()
    
    commands = [
        {
            'step': 1,
            'description': 'Test navigation element',
            'commands': [
                '// Test if element exists',
                'document.evaluate("//nav[@data-testid=\\"gnav-shop\\"]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue',
                '',
                '// Test if element is visible',
                'document.evaluate("//nav[@data-testid=\\"gnav-shop\\"]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue?.offsetParent !== null',
                '',
                '// Test if element is interactive',
                'document.evaluate("//nav[@data-testid=\\"gnav-shop\\"]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue?.click'
            ]
        },
        {
            'step': 2,
            'description': 'Test phones link',
            'commands': [
                '// Test if element exists and has correct href',
                'const link = document.evaluate("//a[@data-testid=\\"gnav-phones\\"]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue',
                'link?.href.includes("/smartphones/")',
                '',
                '// Test click functionality',
                'link?.click()'
            ]
        },
        {
            'step': 3,
            'description': 'Test Apple filter button',
            'commands': [
                '// Test if filter button exists',
                'document.evaluate("//button[@data-testid=\\"filter-apple\\"]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue',
                '',
                '// Test button click',
                'document.evaluate("//button[@data-testid=\\"filter-apple\\"]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue?.click()'
            ]
        },
        {
            'step': 4,
            'description': 'Test iPhone 17 product card',
            'commands': [
                '// Test if product card exists',
                'document.evaluate("//div[@data-testid=\\"product-iphone-17\\"]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue',
                '',
                '// Test product card click',
                'document.evaluate("//div[@data-testid=\\"product-iphone-17\\"]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue?.click()'
            ]
        },
        {
            'step': 5,
            'description': 'Test product title',
            'commands': [
                '// Test if title exists and has correct text',
                'const title = document.evaluate("//h1[@data-testid=\\"product-title\\"]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue',
                'title?.textContent.includes("iPhone 17")',
                '',
                '// Test URL validation',
                'window.location.href.includes("apple-iphone-17")'
            ]
        },
        {
            'step': 6,
            'description': 'Test product title text validation',
            'commands': [
                '// Test title text content',
                'const title = document.evaluate("//h1[@data-testid=\\"product-title\\"]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue',
                'title?.textContent.trim() === "Apple iPhone 17"',
                '',
                '// Test title visibility',
                'title?.offsetParent !== null'
            ]
        },
        {
            'step': 7,
            'description': 'Test White color option',
            'commands': [
                '// Test if color option exists',
                'document.evaluate("//button[@data-testid=\\"color-white\\"]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue',
                '',
                '// Test color option click',
                'document.evaluate("//button[@data-testid=\\"color-white\\"]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue?.click()'
            ]
        }
    ]
    
    for cmd in commands:
        print(f"Step {cmd['step']}: {cmd['description']}")
        for command in cmd['commands']:
            print(f"  {command}")
        print()

def print_playwright_test_code():
    """Print Playwright test code for automated testing."""
    
    print("\n" + "="*80)
    print("🤖 PLAYWRIGHT AUTOMATED TEST CODE")
    print("="*80)
    print("Use this Playwright code for automated testing:")
    print()
    
    playwright_code = '''
import { test, expect } from '@playwright/test';

test('Verizon Flow - Manual XPath Testing', async ({ page }) => {
  // Step 1: Navigate to Verizon homepage
  await page.goto('https://www.verizon.com/');
  
  // Test navigation element
  const navElement = page.locator('//nav[@data-testid="gnav-shop"]');
  await expect(navElement).toBeVisible();
  
  // Step 2: Click on Phones button
  const phonesLink = page.locator('//a[@data-testid="gnav-phones"]');
  await expect(phonesLink).toBeVisible();
  await phonesLink.click();
  
  // Step 3: Click on Apple filter
  const appleFilter = page.locator('//button[@data-testid="filter-apple"]');
  await expect(appleFilter).toBeVisible();
  await appleFilter.click();
  
  // Step 4: Click on Apple iPhone 17 device
  const iphone17Card = page.locator('//div[@data-testid="product-iphone-17"]');
  await expect(iphone17Card).toBeVisible();
  await iphone17Card.click();
  
  // Step 5: Validate URL navigation
  await expect(page).toHaveURL(/.*apple-iphone-17/);
  const productTitle = page.locator('//h1[@data-testid="product-title"]');
  await expect(productTitle).toBeVisible();
  
  // Step 6: Validate product title text
  await expect(productTitle).toHaveText(/Apple iPhone 17/);
  
  // Step 7: Click on White color
  const whiteColor = page.locator('//button[@data-testid="color-white"]');
  await expect(whiteColor).toBeVisible();
  await whiteColor.click();
});
'''
    
    print(playwright_code)

def main():
    """Main function to print all testing guides."""
    print_verizon_manual_testing_guide()
    print_alternative_xpaths()
    print_browser_testing_commands()
    print_playwright_test_code()
    
    print("\n" + "="*80)
    print("📋 SUMMARY")
    print("="*80)
    print("✅ Canonical element trees provided for all 7 steps")
    print("✅ XPaths provided for manual UI testing")
    print("✅ Alternative XPath strategies included")
    print("✅ Browser console testing commands provided")
    print("✅ Playwright automated test code included")
    print()
    print("🎯 Next Steps:")
    print("1. Use the XPaths to manually test each step in the browser")
    print("2. Try alternative XPaths if the primary ones don't work")
    print("3. Use browser console commands to verify element properties")
    print("4. Use Playwright code for automated testing")
    print("5. Report any XPath issues or element changes")

if __name__ == "__main__":
    main()