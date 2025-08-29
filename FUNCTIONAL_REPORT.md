# Functional Validation Report

## Summary

- **Total Tests**: 10
- **Passed**: 6
- **Failed**: 4
- **Accuracy**: 60.0%
- **IR@1**: 60.0%

## Performance Metrics

- **Median Cold Latency**: 103.3ms
- **Median Warm Latency**: 3.4ms
- **Cache Hit Rate**: 100.0%

## Detailed Results

| Fixture | Intent | Query | Passed | Confidence | Cold (ms) | Warm (ms) |
|---------|--------|-------|--------|------------|-----------|-----------|
| products | phone-add-1 | add phone to cart... | ✅ | 0.88 | 118.5 | 3.2 |
| products | laptop-add-1 | add laptop to cart... | ✅ | 0.89 | 103.3 | 3.5 |
| products | tablet-add-1 | add tablet to cart... | ✅ | 0.87 | 103.2 | 3.4 |
| products | iphone-specific | add iPhone to cart... | ✅ | 0.92 | 103.0 | 4.1 |
| products | macbook-specific | buy MacBook Pro... | ❌ | 0.50 | 103.3 | 3.4 |
| form | enter-email | enter email address... | ✅ | 0.96 | 102.6 | 3.5 |
| form | enter-username | enter username... | ❌ | 0.95 | 103.0 | 3.1 |
| form | enter-password | enter password... | ❌ | 0.94 | 103.0 | 2.8 |
| form | click-submit | click submit button... | ✅ | 0.91 | 103.3 | 3.2 |
| form | enter-referral | enter referral code... | ❌ | 0.50 | 103.3 | 3.1 |