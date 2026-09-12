"""
skill_taxonomy.py
------------------
Loads the canonical skill taxonomy (data/skill_taxonomy.json) and provides
utilities to:
  - normalize a raw skill mention to its canonical form (alias resolution)
  - find all taxonomy skills mentioned anywhere in a block of free text
  - fuzzy-fallback for near-miss spellings (e.g. "reactjs" vs "react js")

This is the shared vocabulary both the JD parser and the Resume parser map
into, so the Keyword Engine and Semantic Engine are always comparing
like-for-like skill labels rather than raw string variants.
"""

from __future__ import annotations
import json
import os
import re
from difflib import SequenceMatcher

_TAXONOMY_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "skill_taxonomy.json")


def _load_taxonomy(path: str = _TAXONOMY_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class SkillTaxonomy:
    def __init__(self, path: str = _TAXONOMY_PATH):
        self.canonical_to_aliases = _load_taxonomy(path)
        self.alias_to_canonical: dict[str, str] = {}
        for canonical, aliases in self.canonical_to_aliases.items():
            self.alias_to_canonical[canonical.lower()] = canonical
            for alias in aliases:
                self.alias_to_canonical[alias.lower()] = canonical

        # Sort aliases longest-first so multi-word aliases match before
        # shorter substrings do (e.g. "react native" before "react").
        self._all_aliases_sorted = sorted(
            self.alias_to_canonical.keys(), key=len, reverse=True
        )

    def normalize(self, raw_skill: str) -> str | None:
        """Resolve a raw skill string to its canonical taxonomy label, or None."""
        key = raw_skill.strip().lower()
        if key in self.alias_to_canonical:
            return self.alias_to_canonical[key]

        # Fuzzy fallback for minor typos / spacing differences
        best_match, best_ratio = None, 0.0
        for alias in self.alias_to_canonical:
            ratio = SequenceMatcher(None, key, alias).ratio()
            if ratio > best_ratio:
                best_match, best_ratio = alias, ratio
        if best_ratio >= 0.90:
            return self.alias_to_canonical[best_match]
        return None

    def find_skills_in_text(self, text: str) -> set[str]:
        """
        Scan free text and return the set of canonical skills mentioned,
        using word-boundary matching against every known alias.
        """
        text_lower = text.lower()
        found = set()
        for alias in self._all_aliases_sorted:
            pattern = r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])"
            if re.search(pattern, text_lower):
                found.add(self.alias_to_canonical[alias])
        return found

    def all_canonical_skills(self) -> list[str]:
        return list(self.canonical_to_aliases.keys())
