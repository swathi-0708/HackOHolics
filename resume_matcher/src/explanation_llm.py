"""
explanation_llm.py
-------------------
Compatibility shim: re-exports from explanation_generator.
"""

from .explanation_generator import generate_explanation

__all__ = ["generate_explanation"]
