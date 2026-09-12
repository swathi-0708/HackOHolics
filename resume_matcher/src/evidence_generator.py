"""
evidence_generator.py
----------------------
Builds a structured "evidence" record per candidate: matched/missing skills,
score breakdown, years-of-experience comparison against the JD's stated
minimum, and a couple of representative resume bullet snippets. This is the
deterministic, auditable artifact that both the UI and the Explanation LLM
consume — the LLM is only asked to phrase this evidence in natural language,
never to (re-)judge the candidate itself.
"""

from __future__ import annotations
from dataclasses import dataclass, field

from .jd_parser import ParsedJD
from .resume_parser import ParsedResume
from .keyword_engine import KeywordMatchResult
from .score_fusion import FusedScore


@dataclass
class CandidateEvidence:
    filename: str
    candidate_name: str
    email: str | None
    fused_score: FusedScore
    matched_required: list[str]
    matched_preferred: list[str]
    missing_required: list[str]
    missing_preferred: list[str]
    years_of_experience: float | None
    min_years_required: int | None
    meets_experience_bar: bool | None
    sample_bullets: list[str] = field(default_factory=list)
    # Requirements satisfied via an implied/related skill rather than an
    # exact keyword hit, e.g. "Node.js" satisfied by "Express" on the resume.
    # Each entry: "requirement (via matched_skill, relation)".
    partial_credit_notes: list[str] = field(default_factory=list)
    prestige_neutral_overall_score: float | None = None
    rank: int = 0


def build_evidence(
    jd: ParsedJD,
    resume: ParsedResume,
    keyword_result: KeywordMatchResult,
    fused_score: FusedScore,
    max_sample_bullets: int = 3,
    prestige_neutral_overall_score: float | None = None,
) -> CandidateEvidence:
    meets_experience_bar = None
    if jd.min_years_experience is not None and resume.years_of_experience is not None:
        meets_experience_bar = resume.years_of_experience >= jd.min_years_experience

    # Prefer bullets that mention a matched required skill, so the sample
    # evidence is directly relevant rather than arbitrary.
    matched_all = set(keyword_result.matched_required) | set(keyword_result.matched_preferred)
    relevant_bullets = [
        b for b in resume.experience_bullets
        if any(skill.split()[0].lower() in b.lower() for skill in matched_all)
    ]
    sample_bullets = (relevant_bullets or resume.experience_bullets)[:max_sample_bullets]

    partial_credit_notes = [
        f"{m.requirement} (via {m.matched_skill}, {m.relation})"
        for m in keyword_result.partial_credit_matches
    ]

    return CandidateEvidence(
        filename=resume.filename,
        candidate_name=resume.candidate_name,
        email=resume.email,
        fused_score=fused_score,
        matched_required=keyword_result.matched_required,
        matched_preferred=keyword_result.matched_preferred,
        missing_required=keyword_result.missing_required,
        missing_preferred=keyword_result.missing_preferred,
        partial_credit_notes=partial_credit_notes,
        years_of_experience=resume.years_of_experience,
        min_years_required=jd.min_years_experience,
        meets_experience_bar=meets_experience_bar,
        sample_bullets=sample_bullets,
        prestige_neutral_overall_score=prestige_neutral_overall_score,
    )


def rank_candidates(evidences: list[CandidateEvidence]) -> list[CandidateEvidence]:
    ranked = sorted(evidences, key=lambda e: e.fused_score.overall_score, reverse=True)
    for i, e in enumerate(ranked, start=1):
        e.rank = i
    return ranked