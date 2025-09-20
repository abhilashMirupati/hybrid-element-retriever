import json

from gemma_embedding import retrieve_best_element


def main():
    cfg = {
        "use_visual_fallback": False,
        "debug_dump_candidates": True,
        "debug_dump_top_k": 0,
        "return_top_k": 0,
    }
    out = retrieve_best_element(
        "https://www.verizon.com/smartphones/",
        "Click on Apple button in footer",
        target_text="Apple",
        config=cfg,
    )
    summary = {
        "best_tag": out.get("best_canonical", {}).get("node", {}).get("tag"),
        "best_text": out.get("best_canonical", {}).get("node", {}).get("text"),
        "best_score": out.get("best_score"),
        "num_candidates": out.get("diagnostics", {}).get("num_candidates"),
        "fallback_used": out.get("fallback_used"),
    }
    print("\n[SUMMARY]")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

