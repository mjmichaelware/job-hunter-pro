"""Tiny stdlib base for all data models.

Replaces pydantic. Each model is a plain ``@dataclass`` that inherits this
mixin to keep the ``.model_dump()`` / ``.dict()`` interface the rest of the
codebase already calls. No third-party dependency.
"""

from __future__ import annotations

from dataclasses import asdict


class Model:
    """Mixin providing dict serialization for dataclass models."""

    def model_dump(self) -> dict:
        return asdict(self)

    # Back-compat alias for any caller still using pydantic v1 style.
    def dict(self) -> dict:
        return asdict(self)
