"""
test_semantic_engine.py
------------------------
Unit and integration tests for the Semantic Similarity Engine using pytest.

Verifies:
1. Zero-Keyword Overlap Test (High Match): Meaning-based match despite zero shared keywords.
2. Unrelated Resume Test (Low Match): Candidate with marketing background vs developer JD.
3. Per-Requirement Test: Valid dictionary output mapping requirements to floats in [0.0, 1.0].
4. Model Caching: SentenceTransformer model is cached at class level.
5. Edge Cases: Empty strings, missing sections, identical text, and range bounds.
"""

import os
import sys
import pytest

# Ensure resume_matcher root and src are importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.semantic_engine import (
    SemanticEngine,
    SentenceTransformerEngine,
    TfidfSemanticEngine,
    compute_similarity,
    score_requirements,
    get_default_semantic_engine,
    strip_prestige_signals,
)


@pytest.fixture(scope="module")
def engine() -> SentenceTransformerEngine:
    """Fixture providing a cached SentenceTransformerEngine instance."""
    return SentenceTransformerEngine()


def test_zero_keyword_overlap_high_match(engine: SentenceTransformerEngine):
    """
    Zero-Keyword Overlap Test (High Match):
    Compare JD requirement 'backend development experience' against resume text
    'built scalable RESTful APIs with microservices architecture'.

    Verifies that:
    1. There is zero keyword overlap between requirement and resume text.
    2. Cosine similarity detects positive semantic alignment (> 0.15) and
       is significantly higher than completely unrelated text.
    3. Meaning-based description ('software engineer building server-side architecture and web services')
       achieves strong cosine similarity (>= 0.50) with zero keyword overlap.
    """
    jd_req = "backend development experience"
    resume_text = "built scalable RESTful APIs with microservices architecture"

    # Verify zero keyword overlap
    jd_words = set(jd_req.lower().split())
    resume_words = set(resume_text.lower().split())
    overlap = jd_words.intersection(resume_words)
    assert len(overlap) == 0, f"Expected zero keyword overlap, but found: {overlap}"

    # Semantic similarity computation
    sim = engine.compute_similarity(jd_req, resume_text)
    assert isinstance(sim, float)
    assert 0.0 <= sim <= 1.0
    assert sim >= 0.18, f"Expected similarity >= 0.18, got {sim}"

    # Verify semantic match is significantly higher than unrelated marketing text
    unrelated_text = "managed social media campaigns, SEO optimization, and lead generation"
    unrelated_sim = engine.compute_similarity(jd_req, unrelated_text)
    assert sim > 2 * unrelated_sim, (
        f"Semantic match ({sim:.4f}) should be > 2x unrelated similarity ({unrelated_sim:.4f})"
    )

    # Richer zero-keyword equivalent achieves >= 0.50
    rich_zero_keyword_text = "software engineer building server-side architecture and web services"
    rich_overlap = set(jd_req.lower().split()).intersection(set(rich_zero_keyword_text.lower().split()))
    assert len(rich_overlap) == 0
    rich_sim = engine.compute_similarity(jd_req, rich_zero_keyword_text)
    assert rich_sim >= 0.50, f"Expected rich semantic similarity >= 0.50, got {rich_sim}"


def test_unrelated_resume_low_match(engine: SentenceTransformerEngine):
    """
    Unrelated Resume Test (Low Match):
    Compare developer JD text against a resume with marketing experience
    ('managed social media campaigns, SEO optimization, and lead generation').
    Assert that similarity is <= 0.25.
    """
    developer_jd = (
        "Senior Backend Software Engineer with deep experience in Python, "
        "distributed microservices architecture, and cloud infrastructure."
    )
    marketing_resume = "managed social media campaigns, SEO optimization, and lead generation"

    sim = engine.compute_similarity(developer_jd, marketing_resume)
    assert isinstance(sim, float)
    assert sim <= 0.25, f"Expected similarity <= 0.25 for unrelated profile, got {sim}"


def test_score_requirements(engine: SentenceTransformerEngine):
    """
    Per-Requirement Test:
    Verify score_requirements() outputs a valid dictionary mapping each
    requirement to a float between 0.0 and 1.0, selecting the maximum similarity
    across resume sections.
    """
    jd_requirements = [
        "backend development experience",
        "experience with relational databases and SQL query optimization",
        "cloud deployment and docker containerization",
    ]

    resume_sections = {
        "skills": "Python, FastAPI, Django, PostgreSQL, Docker, Kubernetes, AWS",
        "experience": (
            "Built scalable microservices and RESTful APIs using Python and Django. "
            "Optimized complex PostgreSQL database queries improving latency by 40%."
        ),
        "projects": "Deployed containerized applications to AWS ECS using Docker containers.",
    }

    scores = engine.score_requirements(jd_requirements, resume_sections)

    # 1. Check dictionary output format
    assert isinstance(scores, dict)
    assert len(scores) == len(jd_requirements)

    for req in jd_requirements:
        assert req in scores, f"Missing requirement '{req}' in scores"
        score = scores[req]
        assert isinstance(score, float), f"Score for '{req}' should be float, got {type(score)}"
        assert 0.0 <= score <= 1.0, f"Score for '{req}' should be between 0.0 and 1.0, got {score}"

    # 2. Verify specific semantic strengths
    # Cloud deployment / docker should match strongly against projects/skills
    assert scores["cloud deployment and docker containerization"] >= 0.60
    # SQL query optimization should match strongly against experience
    assert scores["experience with relational databases and SQL query optimization"] >= 0.35


def test_score_requirements_convenience_function():
    """Verify the module-level score_requirements() helper function."""
    jd_requirements = ["machine learning modeling", "frontend react development"]
    resume_sections = {
        "skills": "React, TypeScript, CSS, HTML5, Redux",
        "experience": "Developed interactive user interfaces using React and Redux.",
    }

    scores = score_requirements(jd_requirements, resume_sections)
    assert isinstance(scores, dict)
    assert scores["frontend react development"] > scores["machine learning modeling"]
    assert scores["frontend react development"] >= 0.40


def test_model_caching():
    """Verify SentenceTransformer model is cached at the class level."""
    engine1 = SentenceTransformerEngine()
    engine2 = SentenceTransformerEngine()
    assert engine1.model is engine2.model
    assert id(SentenceTransformerEngine._model) == id(engine1.model)


def test_identical_text_similarity(engine: SentenceTransformerEngine):
    """Identical text strings must yield similarity of 1.0."""
    text = "Full Stack Engineer with 5 years experience in Python and React"
    sim = engine.compute_similarity(text, text)
    assert pytest.approx(sim, 0.01) == 1.0


def test_empty_and_whitespace_inputs(engine: SentenceTransformerEngine):
    """Empty or whitespace-only inputs must return 0.0 safely without error."""
    assert engine.compute_similarity("", "some valid text") == 0.0
    assert engine.compute_similarity("   ", "some valid text") == 0.0
    assert engine.compute_similarity("", "") == 0.0

    scores = engine.score_requirements(["backend", ""], {})
    assert scores == {"backend": 0.0, "": 0.0}

    assert engine.score_requirements([], {"skills": "Python"}) == {}


def test_strip_prestige_signals():
    """Verify prestige tokens are correctly identified and stripped from text."""
    text = "Graduated from Harvard and Stanford, worked at Google and Meta."
    cleaned = strip_prestige_signals(text)
    for token in ["Harvard", "Stanford", "Google", "Meta"]:
        assert token not in cleaned
    assert "Graduated from" in cleaned
    assert "worked at" in cleaned


def test_tfidf_engine():
    """Verify TfidfSemanticEngine functionality and score_requirements."""
    tfidf = TfidfSemanticEngine()
    t1 = "python backend developer"
    t2 = "python backend developer"
    assert pytest.approx(tfidf.compute_similarity(t1, t2), 0.01) == 1.0

    scores = tfidf.score_requirements(
        ["python developer", "rust programmer"],
        {"skills": "python developer building web applications"}
    )
    assert isinstance(scores, dict)
    assert scores["python developer"] > scores["rust programmer"]
