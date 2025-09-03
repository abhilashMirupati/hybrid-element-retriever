"""
Runtime orchestration module.

This package exposes the high-level `HerAgent` class, which coordinates
element snapshotting, incremental embedding, ranking, self-healing and
verification.  It is designed to bridge the gap between the low-level
building blocks in the existing HER framework (snapshotting, intent
parsing, hybrid ranking and promotion cache) and a single, easy to
call interface for executing natural-language test steps.  See
`her.runtime.agent.HerAgent` for details.
"""

from .agent import HerAgent  # noqa: F401

__all__ = ["HerAgent"]
