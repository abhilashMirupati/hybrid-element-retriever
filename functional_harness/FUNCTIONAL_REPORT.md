# Functional Validation Report

## Summary

- **Total Tests**: 20
- **Passed**: 0
- **Failed**: 20
- **Accuracy**: 0.0%
- **IR@1**: 0.0%

## Performance Metrics

- **Median Cold Latency**: 9.5ms
- **Median Warm Latency**: 3.9ms
- **Cache Hit Rate**: 70.0%

## Detailed Results

| Fixture | Intent | Query | Passed | Confidence | Cold (ms) | Warm (ms) |
|---------|--------|-------|--------|------------|-----------|-----------|
| auth | login-email | enter login email... | ❌ | 0.70 | 99.3 | 6.1 |
| auth | login-password | enter password... | ❌ | 0.70 | 12.1 | 6.1 |
| auth | click-signin | click sign in button... | ❌ | 0.50 | 14.2 | 6.1 |
| fixture | q3 | accept cookies... | ❌ | 0.50 | 25.1 | 3.5 |
| fixture | q4 | click proceed... | ❌ | 0.50 | 8.5 | 3.2 |
| products | phone-add-1 | add phone to cart... | ❌ | 0.70 | 15.3 | 3.9 |
| products | laptop-add-1 | add laptop to cart... | ❌ | 0.70 | 7.3 | 3.7 |
| products | tablet-add-1 | add tablet to cart... | ❌ | 0.70 | 7.8 | 3.5 |
| products | iphone-specific | add iPhone to cart... | ❌ | 0.70 | 7.8 | 3.5 |
| products | macbook-specific | buy MacBook Pro... | ❌ | 0.30 | 7.0 | 3.6 |
| fixture | q10 | add the laptop to cart... | ❌ | 0.70 | 15.8 | 3.2 |
| fixture | q11 | add phone to cart... | ❌ | 0.70 | 7.5 | 3.0 |
| fixture | q12 | type email... | ❌ | 0.70 | 30.4 | 3.1 |
| fixture | q13 | type username... | ❌ | 0.50 | 6.1 | 3.9 |
| fixture | q14 | type password... | ❌ | 0.70 | 6.2 | 2.8 |
| form | enter-email | enter email address... | ❌ | 0.70 | 47.5 | 4.7 |
| form | enter-username | enter username... | ❌ | 0.50 | 8.1 | 5.5 |
| form | enter-password | enter password... | ❌ | 0.70 | 8.5 | 4.8 |
| form | click-submit | click submit button... | ❌ | 0.50 | 9.5 | 4.5 |
| form | enter-referral | enter referral code... | ❌ | 0.50 | 9.5 | 4.5 |