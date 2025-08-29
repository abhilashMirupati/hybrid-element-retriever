# Functional Validation Report

## Summary

- **Total Tests**: 13
- **Passed**: 7
- **Failed**: 6
- **Accuracy**: 53.8%
- **IR@1**: 53.8%

## Performance Metrics

- **Median Cold Latency**: 103.4ms
- **Median Warm Latency**: 3.5ms
- **Cache Hit Rate**: 100.0%

## Detailed Results

| Fixture | Intent | Query | Passed | Confidence | Cold (ms) | Warm (ms) |
|---------|--------|-------|--------|------------|-----------|-----------|
| auth | login-email | enter login email... | ✅ | 0.96 | 118.4 | 4.3 |
| auth | login-password | enter password... | ❌ | 0.94 | 103.4 | 4.0 |
| auth | click-signin | click sign in button... | ❌ | 0.50 | 102.9 | 3.9 |
| products | phone-add-1 | add phone to cart... | ✅ | 0.88 | 104.4 | 3.5 |
| products | laptop-add-1 | add laptop to cart... | ✅ | 0.89 | 103.9 | 4.0 |
| products | tablet-add-1 | add tablet to cart... | ✅ | 0.87 | 103.2 | 3.5 |
| products | iphone-specific | add iPhone to cart... | ✅ | 0.92 | 103.5 | 5.0 |
| products | macbook-specific | buy MacBook Pro... | ❌ | 0.50 | 103.4 | 4.1 |
| form | enter-email | enter email address... | ✅ | 0.96 | 102.7 | 3.4 |
| form | enter-username | enter username... | ❌ | 0.95 | 103.1 | 3.0 |
| form | enter-password | enter password... | ❌ | 0.94 | 103.4 | 3.2 |
| form | click-submit | click submit button... | ✅ | 0.91 | 103.1 | 2.8 |
| form | enter-referral | enter referral code... | ❌ | 0.50 | 103.2 | 3.4 |