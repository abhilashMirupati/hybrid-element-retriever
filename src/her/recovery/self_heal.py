# PLACE THIS FILE AT: src/her/recovery/self_heal.py

class SelfHealer:
    def heal(self, locator, dom):
        # Try a relaxed fallback strategy
        return locator.replace("[@id", "[contains(@id")
