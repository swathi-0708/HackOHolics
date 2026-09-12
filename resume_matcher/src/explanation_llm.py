"""
explanation_llm.py
--------------------
Turns a CandidateEvidence record into a short natural-language explanation
of why the candidate ranked where they did.

The LLM's job here is strictly *phrasing*, not *judgment* — it is only
given the already-computed evidence (matched/missing skills, scores,
experience comparison) and asked to write it up fluently. This keeps the
ranking itself deterministic and auditable, and keeps the LLM from
inventing evidence that isn't actually in the resume.

If the `anthropic` package and an ANTHROPIC_API_KEY are both available,
this calls the Claude API. Otherwise it falls back to a deterministic
template — so the pipeline runs end-to-end with zero external
dependencies, and upgrades automatically once a key is configured.
"""

from __future__ import annotations
import os

from .evidence_generator import CandidateEvidence

SYSTEM_PROMPT = """You are writing a short, factual explanation for a recruiter about why a \
candidate ranked where they did for a role. You will be given structured evidence \
(matched skills, missing skills, scores, years of experience). Write 2-4 sentences, \
plain and specific, referencing only the evidence given. Do not invent skills, \
experience, or qualifications that are not in the evidence. Do not restate every \
number — synthesize. Neutral, professional tone; no flattery, no hedging filler."""


def _evidence_to_prompt(evidence: CandidateEvidence) -> str:
    lines = [
        f"Candidate: {evidence.candidate_name}",
        f"Overall fit score: {evidence.fused_score.overall_score}/100 "
        f"(keyword: {evidence.fused_score.keyword_score}/100, "
        f"semantic: {evidence.fused_score.semantic_score}/100)",
        f"Matched required skills: {', '.join(evidence.matched_required) or 'none'}",
        f"Matched preferred skills: {', '.join(evidence.matched_preferred) or 'none'}",
        f"Missing required skills: {', '.join(evidence.missing_required) or 'none'}",
        f"Missing preferred skills: {', '.join(evidence.missing_preferred) or 'none'}",
    ]
    if evidence.years_of_experience is not None:
        lines.append(f"Estimated years of experience: {evidence.years_of_experience}")
    if evidence.min_years_required is not None:
        lines.append(f"JD minimum years required: {evidence.min_years_required}")
    if evidence.sample_bullets:
        lines.append("Sample resume bullets:")
        for b in evidence.sample_bullets:
            lines.append(f"  - {b}")
    return "\n".join(lines)


def _template_explanation(evidence: CandidateEvidence) -> str:
    """Deterministic fallback used when no LLM is configured."""
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


def _llm_explanation(evidence: CandidateEvidence) -> str | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic
    except ImportError:
        return None

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _evidence_to_prompt(evidence)}],
        )
        text_blocks = [block.text for block in message.content if getattr(block, "type", "") == "text"]
        return "\n".join(text_blocks).strip() or None
    except Exception as e:
        print(f"[explanation_llm] LLM call failed, falling back to template: {e}")
        return None


def generate_explanation(evidence: CandidateEvidence) -> str:
    llm_result = _llm_explanation(evidence)
    if llm_result:
        return llm_result
    return _template_explanation(evidence)
