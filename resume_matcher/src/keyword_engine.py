"""
keyword_engine.py
-----------------
Computes a keyword-match score between a parsed JD and a parsed resume.

Because both sides have already been normalized through the shared
SkillTaxonomy (see skill_taxonomy.py), this engine does *not* need fuzzy
string matching — it's a weighted set-overlap:

    score = sum(weight of matched requirement) / sum(weight of all requirements)

Weights come from the JD parser (required > preferred, "must have" boosted).
This produces a 0.0-1.0 score plus the matched/missing skill lists that the
Evidence Generator needs downstream.
"""

from __future__ import annotations
from dataclasses import dataclass

from .jd_parser import ParsedJD
from .resume_parser import ParsedResume


@dataclass
class KeywordMatchResult:
    score: float  # 0.0 - 1.0
    matched_required: list[str]
    matched_preferred: list[str]
    missing_required: list[str]
    missing_preferred: list[str]


def compute_keyword_match(jd: ParsedJD, resume: ParsedResume) -> KeywordMatchResult:
    if not jd.requirements:
        return KeywordMatchResult(0.0, [], [], [], [])

    total_weight = sum(r.weight for r in jd.requirements)
    matched_weight = 0.0

    matched_required, matched_preferred = [], []
    missing_required, missing_preferred = [], []

    for req in jd.requirements:
        if req.skill in resume.skills:
            matched_weight += req.weight
            (matched_required if req.tier == "required" else matched_preferred).append(req.skill)
        else:
            (missing_required if req.tier == "required" else missing_preferred).append(req.skill)

    score = matched_weight / total_weight if total_weight > 0 else 0.0
    return KeywordMatchResult(
        score=round(score, 4),
        matched_required=matched_required,
        matched_preferred=matched_preferred,
        missing_required=missing_required,
        missing_preferred=missing_preferred,
    )
