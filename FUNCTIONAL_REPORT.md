# Functional Report

- Accuracy: 100.0%
- Median Cold: 3.2 ms
- Median Warm: 1.0 ms
- Cache Hit Rate: 100.0%
- Cold Snapshot: 532.1 ms

## Details

- **enter login email** → passed=True strategy=pipeline cold=21.2ms warm=2.6ms xpath=`//*[@id="login-email"]`
- **enter password** → passed=True strategy=pipeline cold=3.5ms warm=1.0ms xpath=`//*[@id="login-password"]`
- **click sign in button** → passed=True strategy=pipeline cold=2.4ms warm=1.0ms xpath=`//button[normalize-space()='Sign In']`
- **close overlay** → passed=True strategy=pipeline cold=2.2ms warm=0.8ms xpath=`//button[normalize-space()='Close']`
- **open country select** → passed=True strategy=pipeline cold=2.4ms warm=0.9ms xpath=`//select[normalize-space()='Select United States Canada United Kingdom']`
- **submit form** → passed=True strategy=pipeline cold=3.2ms warm=0.8ms xpath=`//*[@id="submit-button"]`
