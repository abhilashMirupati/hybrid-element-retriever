#!/usr/bin/env python3
"""
Quick mock probe for the HER framework.

Feeds representative DOM snapshots (including frames/shadow/nested cases)
through the legacy-compatible HERPipeline and prints strict JSON outputs.
"""

from __future__ import annotations

import json
from typing import Dict, Any

from her.pipeline import HERPipeline, PipelineConfig


def run_case(title: str, query: str, dom: Dict[str, Any]) -> None:
    pipe = HERPipeline(config=PipelineConfig())
    out = pipe.process(query, dom)
    print(f"\n=== {title} ===")
    print(json.dumps(out, indent=2))


def main() -> None:
    # 1) Simple page with multiple similar elements
    dom_simple = {
        "elements": [
            {"tag": "button", "text": "Login", "xpath": "//button[1]"},
            {"tag": "a", "text": "Login", "xpath": "//a[1]"},
            {"tag": "input", "attributes": {"type": "email"}, "text": "", "xpath": "//input[@type='email']"},
        ]
    }
    run_case("Simple/Login disambiguation", "click login button", dom_simple)
    run_case("Email field", "enter email", dom_simple)

    # 2) Product disambiguation
    dom_products = {
        "elements": [
            {"tag": "div", "text": "iPhone 14 Pro", "xpath": "//div[@class='product'][1]"},
            {"tag": "div", "text": "MacBook Pro 16-inch", "xpath": "//div[@class='product'][2]"},
            {"tag": "div", "text": "Samsung Galaxy S23", "xpath": "//div[@class='product'][3]"},
        ]
    }
    run_case("Phone selection", "select phone", dom_products)
    run_case("Laptop selection", "select laptop", dom_products)

    # 3) Frames (main + iframe)
    dom_frames = {
        "main_frame": {
            "elements": [
                {"tag": "div", "text": "Main content", "xpath": "//div[1]"}
            ],
            "frames": [
                {
                    "frame_id": "nav_frame",
                    "elements": [
                        {"tag": "a", "text": "Home", "xpath": "//a[1]"},
                        {"tag": "a", "text": "About", "xpath": "//a[2]"},
                    ],
                }
            ],
        }
    }
    run_case("Frame navigation", "click about link", dom_frames)

    # 4) Shadow DOM-like structure
    dom_shadow = {
        "elements": [
            {
                "tag": "custom-element",
                "shadow_root": True,
                "shadow_elements": [
                    {"tag": "button", "text": "Shadow button", "xpath": "//button[1]"}
                ],
                "xpath": "//custom-element",
            }
        ]
    }
    run_case("Shadow button", "click shadow button", dom_shadow)

    # 5) Complex nested elements with multiple candidates
    dom_complex = {
        "elements": [
            {"tag": "button", "text": "Add to Cart", "xpath": "//div[@id='p1']//button[1]"},
            {"tag": "button", "text": "Remove", "xpath": "//div[@id='p1']//button[2]"},
            {"tag": "button", "text": "Add to Cart", "xpath": "//div[@id='p2']//button[1]"},
        ]
    }
    run_case("Nested add-to-cart", "add to cart", dom_complex)


if __name__ == "__main__":
    main()

