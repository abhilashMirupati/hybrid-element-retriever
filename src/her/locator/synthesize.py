# PLACE THIS FILE AT: src/her/locator/synthesize.py

class LocatorSynthesizer:
    def synthesize(self, element, context):
        # Build candidate selectors
        return [f"//*[@id='{element.get('id', '')}']"]
