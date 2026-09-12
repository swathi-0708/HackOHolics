"""
keyword_engine.py
-----------------
Computes a keyword-match score between a parsed JD and a parsed resume.

This is a credit-weighted set-overlap, not a binary in/out check:

    score = sum(requirement weight * best credit found) / sum(requirement weight)

For each JD requirement, `SkillTaxonomy.best_match_for_requirement` looks for
the strongest evidence present in the resume's skill set:
  - exact match (the requirement itself, or a listed alias)   -> credit 1.0
  - an implying skill (Express found, "Node.js" required)     -> credit 0.75
  - a related skill (Vue found, "React" required)              -> credit 0.45
  - nothing found                                              -> credit 0.0

This is what lets a candidate who "built REST APIs with Express and MongoDB"
score meaningfully against a Node.js requirement even though the JD's exact
word never appears on their resume — while a requirement with NO evidence at
all still shows up as genuinely missing, not quietly waved through.

Weights come from the JD parser (required > preferred, "must have" boosted).
"""

from __future__ import annotations
from dataclasses import dataclass, field

from .jd_parser import ParsedJD
from .resume_parser import ParsedResume
from .skill_taxonomy import SkillTaxonomy, SkillMatch


@dataclass
class KeywordMatchResult:
    score: float  # 0.0 - 1.0

    # Exact-match only (kept for backward-compatible display / summaries).
    matched_required: list[str]
    matched_preferred: list[str]

    # No evidence at all was found for these - genuinely missing.
    missing_required: list[str]
    missing_preferred: list[str]

    # Requirements satisfied via an implied/related skill rather than an
    # exact match - e.g. "Node.js" satisfied by "Express" on the resume.
    # This is the detail the Evidence Generator / Explanation LLM need to
    # say *why* a candidate without the literal word still scored well.
    partial_credit_matches: list[SkillMatch] = field(default_factory=list)


def compute_keyword_match(
    jd: ParsedJD, resume: ParsedResume, taxonomy: SkillTaxonomy
) -> KeywordMatchResult:
    if not jd.requirements:
        return KeywordMatchResult(0.0, [], [], [], [], [])

    total_weight = sum(r.weight for r in jd.requirements)
    matched_weight = 0.0

    matched_required, matched_preferred = [], []
    missing_required, missing_preferred = [], []
    partial_credit_matches: list[SkillMatch] = []

    for req in jd.requirements:
        match = taxonomy.best_match_for_requirement(req.skill, resume.skills)

        if match is None:
            matched_weight += 0.0
            (missing_required if req.tier == "required" else missing_preferred).append(req.skill)
            continue

        matched_weight += req.weight * match.credit

        if match.relation == "exact":
            (matched_required if req.tier == "required" else matched_preferred).append(req.skill)
        else:
            # Partial credit: not a literal match, but real evidence (implied
            # or related skill). Don't count it as fully "matched" or fully
            # "missing" - surface it separately so explanations stay honest
            # about what was actually found.
            partial_credit_matches.append(match)

    score = matched_weight / total_weight if total_weight > 0 else 0.0
    return KeywordMatchResult(
        score=round(score, 4),
        matched_required=matched_required,
        matched_preferred=matched_preferred,
        missing_required=missing_required,
        missing_preferred=missing_preferred,
        partial_credit_matches=partial_credit_matches,
    )