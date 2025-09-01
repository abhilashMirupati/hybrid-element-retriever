# Functional Validation Report

## Summary

- **Total Tests**: 20
- **Passed**: 0
- **Failed**: 20
- **Accuracy**: 0.0%
- **IR@1**: 0.0%

## Performance Metrics

- **Median Cold Latency**: 4.0ms
- **Median Warm Latency**: 3.6ms
- **Cache Hit Rate**: 5.0%

## Detailed Results

| Fixture | Intent | Query | Passed | Confidence | Cold (ms) | Warm (ms) |
|---------|--------|-------|--------|------------|-----------|-----------|
| auth | login-email | enter login email... | ❌ | 1.00 | 9.9 | 5.5 |
| auth | login-password | enter password... | ❌ | 1.00 | 4.5 | 5.0 |
| auth | click-signin | click sign in button... | ❌ | 1.00 | 5.1 | 7.1 |
| fixture | q3 | accept cookies... | ❌ | 0.99 | 4.0 | 2.1 |
| fixture | q4 | click proceed... | ❌ | 1.00 | 3.5 | 2.1 |
| products | phone-add-1 | add phone to cart... | ❌ | 0.98 | 5.2 | 3.6 |
| products | laptop-add-1 | add laptop to cart... | ❌ | 0.99 | 3.2 | 3.8 |
| products | tablet-add-1 | add tablet to cart... | ❌ | 0.98 | 4.0 | 3.2 |
| products | iphone-specific | add iPhone to cart... | ❌ | 0.98 | 4.1 | 3.6 |
| products | macbook-specific | buy MacBook Pro... | ❌ | 0.99 | 3.6 | 2.9 |
| fixture | q10 | add the laptop to cart... | ❌ | 0.99 | 11.9 | 4.7 |
| fixture | q11 | add phone to cart... | ❌ | 0.98 | 3.6 | 2.6 |
| fixture | q12 | type email... | ❌ | 1.00 | 4.7 | 2.8 |
| fixture | q13 | type username... | ❌ | 1.00 | 2.7 | 2.8 |
| fixture | q14 | type password... | ❌ | 0.89 | 2.9 | 3.8 |
| form | enter-email | enter email address... | ❌ | 1.00 | 4.8 | 3.6 |
| form | enter-username | enter username... | ❌ | 1.00 | 3.3 | 3.5 |
| form | enter-password | enter password... | ❌ | 1.00 | 4.0 | 3.5 |
| form | click-submit | click submit button... | ❌ | 1.00 | 3.9 | 3.9 |
| form | enter-referral | enter referral code... | ❌ | 1.00 | 3.4 | 3.4 |