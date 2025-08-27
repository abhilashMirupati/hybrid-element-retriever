# PLACE THIS FILE AT: src/her/recovery/promotion.py

class Promotion:
    def promote(self, candidates):
        return max(candidates, key=lambda x: x[1])
