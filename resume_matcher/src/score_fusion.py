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
"""

from __future__ import annotations
from dataclasses import dataclass

from .keyword_engine import KeywordMatchResult
from .semantic_engine import SemanticMatchResult

DEFAULT_KEYWORD_WEIGHT = 0.65
DEFAULT_SEMANTIC_WEIGHT = 0.35


@dataclass
class FusedScore:
    overall_score: float  # 0-100
    keyword_score: float  # 0-100
    semantic_score: float  # 0-100
    keyword_weight: float
    semantic_weight: float


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
    overall = keyword_weight * keyword_pct + semantic_weight * semantic_pct

    return FusedScore(
        overall_score=round(overall, 1),
        keyword_score=round(keyword_pct, 1),
        semantic_score=round(semantic_pct, 1),
        keyword_weight=round(keyword_weight, 2),
        semantic_weight=round(semantic_weight, 2),
    )
