# PLACE THIS FILE AT: src/her/rank/fusion.py

class RankFusion:
    def fuse(self, candidates):
        # Weighted average fusion
        scores = {}
        for name, cand_list in candidates.items():
            for c, score in cand_list:
                scores[c] = scores.get(c, 0) + score
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)
