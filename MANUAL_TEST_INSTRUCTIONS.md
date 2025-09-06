# Manual Test Instructions for Verizon Flow

## The Complete Flow That Should Work:

### Step 1: Open Verizon Homepage
```javascript
window.location.href = 'https://www.verizon.com/';
```

### Step 2: Click on Phones Button (THE ISSUE IS HERE!)
**WRONG (what framework is clicking):**
```javascript
// This clicks "Details" - a dropdown toggle, NOT navigation
$x('/HTML[1]/BODY[1]/DIV[1]/DIV[1]/DIV[1]/DIV[1]/DIV[1]/DIV[1]/DIV[1]/DIV[1]/DIV[1]/DIV[4]/DIV[1]/DIV[1]/DIV[1]/DIV[1]/DIV[1]/DIV[1]/DIV[1]/SPAN[1]/SPAN[2]/A[1]')[0].click()
```

**CORRECT (what should be clicked):**
```javascript
// Click the actual "Phones" navigation link
document.querySelector('a[href="/smartphones/"]').click();
// OR
Array.from(document.querySelectorAll('a')).find(a => a.textContent.trim() === 'Phones').click();
```

### Step 3: Select Apple Filter (on /smartphones/ page)
```javascript
// After navigating to smartphones page
document.querySelector('button:has-text("Apple")').click();
// OR
document.querySelector('label:has-text("Apple")').click();
```

### Step 4: Select Apple iPhone 16 Pro
```javascript
// Click on the product (should be visible after filtering)
Array.from(document.querySelectorAll('a')).find(a => 
  a.textContent.includes('iPhone 16 Pro') && 
  a.href.includes('apple-iphone-16-pro')
).click();
```

### Step 5: Validate Landing Page
```javascript
// Check if we're on the product page
console.log('Current URL:', window.location.href);
console.log('Success:', window.location.href.includes('apple-iphone-16-pro'));
```

## Summary of Issues:

1. **Step 2 is broken**: Framework selects "Details" (dropdown toggle) instead of "Phones" (navigation link)
2. **This breaks the entire flow**: Without navigating to /smartphones/, steps 3-4 can't work
3. **The correct elements exist**: The page has the right "Phones" link, just wrong selection

## Working Alternative (Skip the broken navigation):

```javascript
// Start directly on smartphones page
window.location.href = 'https://www.verizon.com/smartphones/';

// Then click on iPhone 16 Pro (visible on page)
setTimeout(() => {
  Array.from(document.querySelectorAll('a')).find(a => 
    a.textContent.includes('iPhone 16 Pro') && 
    a.href.includes('apple-iphone-16-pro')
  ).click();
}, 2000);
```

This is why our simplified test (starting directly on /smartphones/) partially works!