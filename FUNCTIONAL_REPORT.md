# Functional Report

- Accuracy: 100.0%
- Median Cold: 4.9 ms
- Median Warm: 2.5 ms
- Cache Hit Rate: 100.0%
- Cold Snapshot: 540.0 ms

## Details

- **enter login email** → passed=True strategy=pipeline cold=14.2ms warm=2.3ms xpath=`//*[@id="login-email"]`
- **enter password** → passed=True strategy=pipeline cold=8.0ms warm=2.2ms xpath=`//*[@id="login-password"]`
- **click sign in button** → passed=True strategy=pipeline cold=4.9ms warm=2.5ms xpath=`//button[normalize-space()='Sign In']`
- **close overlay** → passed=True strategy=pipeline cold=3.5ms warm=2.7ms xpath=`//button[normalize-space()='Close']`
- **open country select** → passed=True strategy=pipeline cold=3.4ms warm=2.5ms xpath=`//select[normalize-space()='Select United States Canada United Kingdom']`
- **submit form** → passed=True strategy=pipeline cold=3.8ms warm=2.6ms xpath=`//*[@id="submit-button"]`
