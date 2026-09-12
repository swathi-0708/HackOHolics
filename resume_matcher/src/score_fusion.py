"""
score_fusion.py
----------------
Combines the Keyword Engine score and Semantic Engine score into one
overall 0-100 fit score per candidate.

Default blend: 65% keyword, 35% semantic. Keyword match is weighted higher
because it's grounded in explicit JD requirements (auditable, defensible in
a hiring context); semantic similarity is a softer signal used to catch
paraphrased or adjacent experience the keyword layer misses, and to break
ties among candidates with similar keyword coverage.

These weights are a configurable starting point, not a tuned constant —
see README.md for guidance on adjusting them per role type.

Missing-required penalty
-------------------------
The weighted blend above is not, by itself, enough to make a fully-missing
"must have" requirement clearly hurt: required-skill weight (1.0-1.5) already
outweighs preferred-skill weight (0.5) inside the Keyword Engine's own
score, but that gap gets diluted the more total requirements a JD has, and
the semantic half of the blend doesn't know about tiers at all. Measured
against the bundled sample JD (9 required / 5 preferred requirements),
missing one ordinary required skill with everything else perfect only cost
~5 points out of 100 on the old pure blend - not enough to reliably outrank
a candidate who has every required skill but a slightly weaker semantic
match. A requirement with genuinely zero evidence (present in
`missing_required`, as opposed to one satisfied at IMPLIED_CREDIT/
RELATED_CREDIT) now takes an extra, explicit multiplicative penalty on top
of the blend, capped so a JD with many required skills doesn't zero out a
candidate for one gap.
"""

from __future__ import annotations
from dataclasses import dataclass

from .keyword_engine import KeywordMatchResult
from .semantic_engine import SemanticMatchResult

DEFAULT_KEYWORD_WEIGHT = 0.65
DEFAULT_SEMANTIC_WEIGHT = 0.35

# Multiplicative penalty applied on top of the blended score for each
# required requirement with NO evidence at all (not even implied/related).
# 8% per missing required skill, capped at 40% total - enough that missing
# a hard requirement clearly separates a candidate from one who has it,
# without letting a JD with a long required list zero a candidate out.
REQUIRED_SKILL_MISS_PENALTY = 0.08
MAX_REQUIRED_MISS_PENALTY = 0.40


@dataclass
class FusedScore:
    overall_score: float  # 0-100
    keyword_score: float  # 0-100
    semantic_score: float  # 0-100
    keyword_weight: float
    semantic_weight: float
    missing_required_count: int = 0
    missing_required_penalty: float = 0.0  # fraction knocked off, 0.0-MAX_REQUIRED_MISS_PENALTY


def fuse_scores(
    keyword_result: KeywordMatchResult,
    semantic_result: SemanticMatchResult,
    keyword_weight: float = DEFAULT_KEYWORD_WEIGHT,
    semantic_weight: float = DEFAULT_SEMANTIC_WEIGHT,
) -> FusedScore:
    total_weight = keyword_weight + semantic_weight
    if total_weight == 0:
        raise ValueError("keyword_weight + semantic_weight must be > 0")
    keyword_weight, semantic_weight = keyword_weight / total_weight, semantic_weight / total_weight

    keyword_pct = keyword_result.score * 100
    semantic_pct = semantic_result.score * 100
    blended = keyword_weight * keyword_pct + semantic_weight * semantic_pct

    missing_required_count = len(keyword_result.missing_required)
    penalty = min(MAX_REQUIRED_MISS_PENALTY, REQUIRED_SKILL_MISS_PENALTY * missing_required_count)
    overall = blended * (1 - penalty)

    return FusedScore(
        overall_score=round(overall, 1),
        keyword_score=round(keyword_pct, 1),
        semantic_score=round(semantic_pct, 1),
        keyword_weight=round(keyword_weight, 2),
        semantic_weight=round(semantic_weight, 2),
        missing_required_count=missing_required_count,
        missing_required_penalty=round(penalty, 4),
    )