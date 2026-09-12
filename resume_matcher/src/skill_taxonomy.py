"""
skill_taxonomy.py
------------------
Loads the canonical skill taxonomy (data/skill_taxonomy.json) and provides
utilities to:
  - normalize a raw skill mention to its canonical form (alias resolution)
  - find all taxonomy skills mentioned anywhere in a block of free text
  - fuzzy-fallback for near-miss spellings (e.g. "reactjs" vs "react js")
  - walk implication/relation edges between skills (e.g. Express implies
    Node.js; Vue is related to React) so the Keyword Engine can give partial
    credit for adjacent-but-not-identical experience instead of a binary
    match/no-match.

This is the shared vocabulary both the JD parser and the Resume parser map
into, so the Keyword Engine and Semantic Engine are always comparing
like-for-like skill labels rather than raw string variants.

Data format (data/skill_taxonomy.json): a dict keyed by canonical skill name,
each entry holding "aliases", "implies", "related", and "category".
  "expressjs": {
    "aliases": ["express", "express framework", "expres"],
    "implies": ["nodejs", "javascript", "rest api", "backend development"],
    "related": ["nestjs", "fastify", "koa"],
    "category": "backend"
  }

Credit weights:
  EXACT_CREDIT   1.0  - the requirement itself, or a listed alias, was found.
  IMPLIED_CREDIT 0.75 - a skill that implies the requirement was found
                        (Express found, "Node.js" required).
  RELATED_CREDIT 0.45 - a skill in the same neighbourhood was found
                        (Vue found, "React" required) - weaker evidence,
                        named tools should still dominate a ranking.
"""

from __future__ import annotations
import json
import os
import re
from difflib import SequenceMatcher
from dataclasses import dataclass

from .text_normalize import normalize_text

_TAXONOMY_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "skill_taxonomy.json")

EXACT_CREDIT = 1.0
IMPLIED_CREDIT = 0.75
RELATED_CREDIT = 0.45

# Fuzzy-token matching for near-miss spellings ("Kuberentes", "Dockerr").
# Applied only to short, list-style tokens (split on commas/bullets/lines) -
# never to the whole free-text blob - since fuzzy-matching an entire
# sentence against a short alias produces nonsense matches. A single typo'd
# edit on a 4+ letter word almost always lands >= FUZZY_TOKEN_MIN_RATIO;
# distinct-but-similar-length skill names in the taxonomy (java/javascript,
# sql/"sql server", go/gcp, ...) all fall well below it.
FUZZY_TOKEN_MIN_RATIO = 0.87
_FUZZY_TOKEN_MIN_LEN = 4
_FUZZY_TOKEN_MAX_LEN = 30
_FUZZY_TOKEN_MAX_LEN_DIFF = 3
_SKILL_LIST_SPLIT = re.compile(r"[,;\n|•·]+")


def _load_taxonomy(path: str = _TAXONOMY_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@dataclass(frozen=True)
class SkillMatch:
    """One resume skill counted as evidence for one JD requirement."""
    requirement: str
    matched_skill: str  # the skill actually found in the resume
    credit: float        # 1.0 exact, 0.75 implied, 0.45 related
    relation: str         # "exact", "implied", or "related"


class SkillTaxonomy:
    def __init__(self, path: str = _TAXONOMY_PATH):
        raw = _load_taxonomy(path)

        self.alias_to_canonical: dict[str, str] = {}
        self._implies: dict[str, set[str]] = {name: set() for name in raw}
        self._related: dict[str, set[str]] = {name: set() for name in raw}
        self._category: dict[str, str] = {}

        for canonical, spec in raw.items():
            self.alias_to_canonical[canonical.lower()] = canonical
            for alias in spec.get("aliases", []):
                # First writer wins, so a canonical name is never shadowed by
                # another skill's alias.
                self.alias_to_canonical.setdefault(alias.lower(), canonical)
            self._category[canonical] = spec.get("category", "other")

        # Wire implication/relation edges only between skills that exist in
        # the loaded taxonomy; symmetrize "related" (Vue<->React).
        for canonical, spec in raw.items():
            for target in spec.get("implies", []):
                if target in raw:
                    self._implies[canonical].add(target)
            for target in spec.get("related", []):
                if target in raw:
                    self._related[canonical].add(target)
                    self._related[target].add(canonical)

        # Sort aliases longest-first so multi-word aliases match before
        # shorter substrings do (e.g. "react native" before "react").
        self._all_aliases_sorted = sorted(
            self.alias_to_canonical.keys(), key=len, reverse=True
        )

    # -- basic lookups --------------------------------------------------

    def normalize(self, raw_skill: str) -> str | None:
        """Resolve a raw skill string to its canonical taxonomy label, or None."""
        key = normalize_text(raw_skill)
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

    def _fuzzy_canonical_for_token(self, token_normalized: str) -> str | None:
        """Near-miss spelling lookup for a single short list-style token."""
        if not token_normalized:
            return None
        if token_normalized in self.alias_to_canonical:
            return self.alias_to_canonical[token_normalized]
        if not (_FUZZY_TOKEN_MIN_LEN <= len(token_normalized) <= _FUZZY_TOKEN_MAX_LEN):
            return None

        best_match, best_ratio = None, 0.0
        for alias in self.alias_to_canonical:
            if abs(len(alias) - len(token_normalized)) > _FUZZY_TOKEN_MAX_LEN_DIFF:
                continue
            ratio = SequenceMatcher(None, token_normalized, alias).ratio()
            if ratio > best_ratio:
                best_match, best_ratio = alias, ratio
        if best_ratio >= FUZZY_TOKEN_MIN_RATIO:
            return self.alias_to_canonical[best_match]
        return None

    def find_skills_in_text(self, text: str) -> set[str]:
        """
        Scan free text and return the set of canonical skills mentioned,
        using word-boundary matching against every known alias. Text is
        normalized first so punctuation variants (Node.js / nodejs / node js)
        all resolve the same way.

        Also runs a fuzzy near-miss pass over comma/bullet/line-separated
        tokens (the shape a resume's "Skills:" line actually takes), so a
        typo'd spelling ("Kuberentes", "Dockerr") is still counted as
        evidence instead of silently vanishing.
        """
        normalized = normalize_text(text)
        found = set()
        for alias in self._all_aliases_sorted:
            alias_normalized = normalize_text(alias)
            if not alias_normalized:
                continue
            pattern = r"(?<![a-z0-9])" + alias_normalized.replace(" ", r"\s+") + r"(?![a-z0-9])"
            if re.search(pattern, normalized):
                found.add(self.alias_to_canonical[alias])

        for raw_token in _SKILL_LIST_SPLIT.split(text):
            token_normalized = normalize_text(raw_token)
            canonical = self._fuzzy_canonical_for_token(token_normalized)
            if canonical:
                found.add(canonical)

        return found

    def all_canonical_skills(self) -> list[str]:
        return list(self._implies.keys())

    def category_of(self, skill: str) -> str:
        return self._category.get(skill, "other")

    # -- implication / relation graph ------------------------------------

    def implies(self, skill: str, depth: int = 2) -> set[str]:
        """Transitive closure of implication edges (Next.js -> React -> JS)."""
        seen: set[str] = set()
        frontier = {skill}
        for _ in range(depth):
            frontier = {t for f in frontier for t in self._implies.get(f, ())} - seen - {skill}
            if not frontier:
                break
            seen |= frontier
        return seen

    def related(self, skill: str) -> set[str]:
        return set(self._related.get(skill, ()))

    def best_match_for_requirement(
        self, requirement: str, resume_skills: set[str]
    ) -> SkillMatch | None:
        """
        Find the strongest evidence in `resume_skills` for `requirement`.
        Checks exact match first, then anything that implies the requirement,
        then anything merely related to it. Returns None if nothing found.
        """
        if requirement in resume_skills:
            return SkillMatch(requirement, requirement, EXACT_CREDIT, "exact")

        for skill in resume_skills:
            if requirement in self.implies(skill):
                return SkillMatch(requirement, skill, IMPLIED_CREDIT, "implied")

        for skill in resume_skills:
            if skill in self.related(requirement):
                return SkillMatch(requirement, skill, RELATED_CREDIT, "related")

        return None