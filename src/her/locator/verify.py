# PLACE THIS FILE AT: src/her/locator/verify.py

class LocatorVerifier:
    def verify(self, locator, dom):
        return bool(dom.xpath(locator))
