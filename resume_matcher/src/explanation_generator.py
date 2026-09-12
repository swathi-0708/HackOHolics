"""
explanation_generator.py
-------------------------
Turns a CandidateEvidence record into a short natural-language explanation
of why the candidate ranked where they did.

The explanation generator is deterministic and auditable — it synthesizes
the already-computed evidence (matched/missing skills, scores, experience
comparison, partial credit) into fluent, factual summaries without requiring
any external API keys or network dependencies.
"""

from __future__ import annotations

from .evidence_generator import CandidateEvidence


def generate_explanation(evidence: CandidateEvidence) -> str:
    """Generate a deterministic, factual explanation for a candidate's ranking."""
    parts = []
    score = evidence.fused_score.overall_score
    tier = "a strong" if score >= 75 else "a moderate" if score >= 50 else "a weak"
    parts.append(
        f"{evidence.candidate_name} is {tier} match at {score}/100 "
        f"(#{evidence.rank} of the ranked candidates)."
    )

    if evidence.matched_required:
        parts.append(
            f"They cover {len(evidence.matched_required)} of the role's required skills, "
            f"including {', '.join(evidence.matched_required[:4])}."
        )
    else:
        parts.append("They do not show any of the role's explicitly required skills in their resume.")

    if evidence.partial_credit_notes:
        parts.append(
            f"Some requirements are covered indirectly: {'; '.join(evidence.partial_credit_notes[:3])}."
        )

    if evidence.missing_required:
        parts.append(f"Notably missing: {', '.join(evidence.missing_required[:4])}.")

    if evidence.meets_experience_bar is True:
        parts.append(
            f"Their estimated {evidence.years_of_experience:.0f} years of experience "
            f"meets the role's {evidence.min_years_required}-year minimum."
        )
    elif evidence.meets_experience_bar is False:
        parts.append(
            f"Their estimated {evidence.years_of_experience:.0f} years of experience "
            f"falls short of the role's {evidence.min_years_required}-year minimum."
        )

    return " ".join(parts)
