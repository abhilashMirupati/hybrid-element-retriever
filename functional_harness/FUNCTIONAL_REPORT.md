# Functional Validation Report

## Summary

- **Total Tests**: 20
- **Passed**: 0
- **Failed**: 20
- **Accuracy**: 0.0%
- **IR@1**: 0.0%

## Performance Metrics

- **Median Cold Latency**: 8.2ms
- **Median Warm Latency**: 3.8ms
- **Cache Hit Rate**: 55.0%

## Detailed Results

| Fixture | Intent | Query | Passed | Confidence | Cold (ms) | Warm (ms) |
|---------|--------|-------|--------|------------|-----------|-----------|
| auth | login-email | enter login email... | ❌ | 0.70 | 46.0 | 6.9 |
| auth | login-password | enter password... | ❌ | 0.70 | 15.6 | 6.9 |
| auth | click-signin | click sign in button... | ❌ | 0.50 | 14.8 | 6.4 |
| fixture | q3 | accept cookies... | ❌ | 0.50 | 15.4 | 3.4 |
| fixture | q4 | click proceed... | ❌ | 0.50 | 7.0 | 2.9 |
| products | phone-add-1 | add phone to cart... | ❌ | 0.70 | 13.0 | 3.8 |
| products | laptop-add-1 | add laptop to cart... | ❌ | 0.70 | 7.6 | 3.8 |
| products | tablet-add-1 | add tablet to cart... | ❌ | 0.70 | 7.3 | 3.5 |
| products | iphone-specific | add iPhone to cart... | ❌ | 0.70 | 7.0 | 3.7 |
| products | macbook-specific | buy MacBook Pro... | ❌ | 0.30 | 7.0 | 3.5 |
| fixture | q10 | add the laptop to cart... | ❌ | 0.70 | 16.1 | 3.6 |
| fixture | q11 | add phone to cart... | ❌ | 0.70 | 5.9 | 3.1 |
| fixture | q12 | type email... | ❌ | 0.70 | 16.2 | 3.0 |
| fixture | q13 | type username... | ❌ | 0.50 | 5.9 | 3.1 |
| fixture | q14 | type password... | ❌ | 0.70 | 6.7 | 2.9 |
| form | enter-email | enter email address... | ❌ | 0.70 | 28.0 | 5.2 |
| form | enter-username | enter username... | ❌ | 0.50 | 8.1 | 4.5 |
| form | enter-password | enter password... | ❌ | 0.70 | 8.7 | 4.5 |
| form | click-submit | click submit button... | ❌ | 0.50 | 8.2 | 4.7 |
| form | enter-referral | enter referral code... | ❌ | 0.50 | 7.9 | 5.0 |