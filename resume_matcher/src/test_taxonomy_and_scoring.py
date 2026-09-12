"""
test_taxonomy_and_scoring.py
------------------------------
Covers the three scenarios called out for the taxonomy/keyword-engine
tuning pass, plus a direct re-verification of the Score Fusion penalty:

  1. A resume with a typo'd skill spelling should still get credit.
  2. A resume using an abbreviation (vs the JD's full form, or vice versa)
     should still get exact credit.
  3. A resume genuinely missing a required skill should show up as missing
     - and should be penalized more than a genuinely missing preferred
       skill, by more than just the raw weight ratio would suggest.

Run with: python3 -m pytest tests/ -v   (from resume_matcher/)
"""

from __future__ import annotations
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.skill_taxonomy import SkillTaxonomy
from src.jd_parser import parse_jd
from src.resume_parser import parse_resume
from src.keyword_engine import compute_keyword_match
from src.score_fusion import fuse_scores
from src.semantic_engine import SemanticMatchResult


SAMPLE_JD_TEXT = """Senior Backend Engineer

Requirements:
- Python
- Docker
- Kubernetes
- PostgreSQL

Preferred:
- Terraform
- Machine Learning
"""


def _make_jd():
    tax = SkillTaxonomy()
    jd = parse_jd(SAMPLE_JD_TEXT, tax)
    return tax, jd


# ---------------------------------------------------------------------------
# 1. Typo'd skill spelling
# ---------------------------------------------------------------------------

def test_typo_skill_still_credited():
    tax, jd = _make_jd()
    resume_text = "Skills:\nPython, Dockerr, Kuberentes, PostgreSQL\n"
    resume = parse_resume("typo_resume.txt", resume_text, tax)

    # The typo'd spellings should still resolve to their canonical skills.
    assert "docker" in resume.skills
    assert "kubernetes" in resume.skills

    result = compute_keyword_match(jd, resume, tax)
    assert result.missing_required == []
    assert set(result.matched_required) == {"python", "docker", "kubernetes", "postgresql"}
    # All 4 required requirements (weight 4.0 of the 5.0 total, since the
    # JD's 2 preferred items aren't on this resume at all) are genuinely
    # matched despite the typos, so score = 4.0 / 5.0.
    assert result.score == 0.8


def test_severe_typo_is_not_blindly_matched():
    # A guardrail on the fuzzy pass itself: garbage shouldn't get credit.
    tax, jd = _make_jd()
    resume_text = "Skills:\nPython, Zzzzzzz, Something Else Entirely\n"
    resume = parse_resume("garbage_resume.txt", resume_text, tax)
    assert "docker" not in resume.skills
    assert "kubernetes" not in resume.skills


# ---------------------------------------------------------------------------
# 2. Abbreviation vs full form (both directions)
# ---------------------------------------------------------------------------

def test_abbreviation_on_resume_matches_full_form_in_jd():
    tax, jd = _make_jd()
    # JD says "Machine Learning" (preferred) and "Kubernetes" (required);
    # resume uses the short forms.
    resume_text = "Skills:\nPython, Docker, K8s, PostgreSQL, ML\n"
    resume = parse_resume("abbrev_resume.txt", resume_text, tax)

    result = compute_keyword_match(jd, resume, tax)
    assert "kubernetes" in result.matched_required
    assert "machine learning" in result.matched_preferred
    assert result.missing_required == []


def test_full_form_on_resume_matches_abbreviation_style_jd():
    tax = SkillTaxonomy()
    jd_text = "Requirements:\n- JS\n- K8s\n"
    jd = parse_jd(jd_text, tax)
    resume_text = "Skills:\nJavaScript, Kubernetes\n"
    resume = parse_resume("full_form_resume.txt", resume_text, tax)

    result = compute_keyword_match(jd, resume, tax)
    assert set(result.matched_required) == {"javascript", "kubernetes"}
    assert result.score == 1.0


# ---------------------------------------------------------------------------
# 3. A required skill missing entirely
# ---------------------------------------------------------------------------

def test_missing_required_skill_flagged_and_not_partial_credited():
    tax, jd = _make_jd()
    # Everything except Kubernetes - and nothing implies/relates to it.
    resume_text = "Skills:\nPython, Docker, PostgreSQL, Terraform, ML\n"
    resume = parse_resume("missing_required.txt", resume_text, tax)

    result = compute_keyword_match(jd, resume, tax)
    assert result.missing_required == ["kubernetes"]
    assert "kubernetes" not in result.matched_required
    assert not any(m.requirement == "kubernetes" for m in result.partial_credit_matches)
    assert 0.0 < result.score < 1.0


# ---------------------------------------------------------------------------
# Score Fusion re-verification: does missing a required skill actually
# tank the score more than missing a preferred one?
# ---------------------------------------------------------------------------

def _fixed_semantic(score: float) -> SemanticMatchResult:
    return SemanticMatchResult(score=score)


def test_missing_required_penalized_more_than_missing_preferred():
    tax, jd = _make_jd()
    semantic = _fixed_semantic(0.70)  # hold semantic constant to isolate the keyword effect

    perfect_resume = parse_resume(
        "perfect.txt", "Skills:\nPython, Docker, Kubernetes, PostgreSQL, Terraform, ML\n", tax
    )
    missing_required_resume = parse_resume(
        "missing_required.txt", "Skills:\nPython, Docker, PostgreSQL, Terraform, ML\n", tax
    )
    missing_preferred_resume = parse_resume(
        "missing_preferred.txt", "Skills:\nPython, Docker, Kubernetes, PostgreSQL, ML\n", tax
    )

    baseline = fuse_scores(compute_keyword_match(jd, perfect_resume, tax), semantic)
    missing_required = fuse_scores(compute_keyword_match(jd, missing_required_resume, tax), semantic)
    missing_preferred = fuse_scores(compute_keyword_match(jd, missing_preferred_resume, tax), semantic)

    required_drop = baseline.overall_score - missing_required.overall_score
    preferred_drop = baseline.overall_score - missing_preferred.overall_score

    assert missing_required.missing_required_count == 1
    assert missing_preferred.missing_required_count == 0
    assert missing_required.missing_required_penalty > 0.0
    assert missing_preferred.missing_required_penalty == 0.0

    # The required miss must cost noticeably more than the preferred miss -
    # not just the ~2x you'd get from weight alone (1.0 vs 0.5), since the
    # dedicated penalty stacks on top of the weighted blend.
    assert required_drop > preferred_drop * 2.5

    # And it should be a real, visible amount on a 0-100 scale, not a
    # rounding-error dent.
    assert required_drop >= 8.0


def test_required_miss_penalty_caps_out():
    tax = SkillTaxonomy()
    # 6 required skills with no implication/relation chains between them or
    # to the resume's (unrelated) skills, so all 6 are cleanly "missing" -
    # enough to exceed the penalty cap (0.08 * 6 = 0.48 > 0.40).
    jd_text = "Requirements:\n- Python\n- Docker\n- Kubernetes\n- PostgreSQL\n- AWS\n- React\n"
    jd = parse_jd(jd_text, tax)
    semantic = _fixed_semantic(0.70)
    unrelated_resume = parse_resume("empty.txt", "Skills:\nFigma, Excel\n", tax)

    result = fuse_scores(compute_keyword_match(jd, unrelated_resume, tax), semantic)
    assert result.missing_required_count == 6

    from src.score_fusion import MAX_REQUIRED_MISS_PENALTY
    assert result.missing_required_penalty == MAX_REQUIRED_MISS_PENALTY


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))