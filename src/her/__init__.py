"""Top‑level package for Hybrid Element Retriever.

This package exposes a simplified public API through :class:`HybridClient` in
:mod:`her.cli_api`.  Most implementation details live under the subpackages
such as ``parser``, ``session``, ``bridge`` and ``rank``.

When importing this package your code should avoid calling any indexing
functions directly.  All indexing is handled automatically by the
:class:`HybridClient`.

"""

from .cli_api import HybridClient  # noqa: F401

__all__ = ["HybridClient"]
