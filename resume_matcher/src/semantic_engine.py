"""
semantic_engine.py
-------------------
Computes a semantic-similarity score between a JD and a resume, to catch
matches the Keyword Engine misses (paraphrased experience, related-but-not-
identical technologies, seniority language, domain context, etc).

Default implementation: TF-IDF + cosine similarity over the full JD text vs
full resume text. This runs fully offline with no model download, which
matters for environments without network access. Because TF-IDF is fit per
JD (over the JD + all its candidate resumes), it acts as a corpus-relative
"semantic-ish" signal: two documents that share a lot of relatively rare,
JD-relevant vocabulary score higher than documents that only share common
words like "the" or "team" (those get down-weighted automatically by IDF).

Pluggable upgrade path: if you have network access and want true embedding-
based semantics (e.g. sentence-transformers, or an Anthropic/OpenAI
embeddings endpoint), implement `EmbeddingSemanticEngine` following the same
`SemanticEngine` interface and swap it in `pipeline.py` — nothing else in
the pipeline needs to change, since both engines return the same
SemanticMatchResult shape.
"""

from __future__ import annotations
import re
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .jd_parser import ParsedJD
from .resume_parser import ParsedResume


# Well-known "prestige" employer/university names. Left in raw text, these
# tokens can inflate TF-IDF/cosine similarity purely because a candidate
# happened to work at or study at a famous name that also appears in the
# JD's "about us" boilerplate or a hiring manager's alma mater bias — not
# because their actual skills/experience match. Stripping them before
# vectorizing produces a "prestige-neutral" semantic score that the UI can
# toggle to, so reviewers can see how much of a candidate's similarity is
# name-recognition vs substance. This is NOT an inference about the
# candidate's identity or protected characteristics — it only removes a
# fixed list of institution/employer name strings from the text.
_PRESTIGE_TOKENS = [
    "harvard", "stanford", "mit", "massachusetts institute of technology",
    "princeton", "yale", "oxford", "cambridge", "caltech", "berkeley",
    "carnegie mellon", "columbia university", "cornell", "wharton",
    "google", "meta", "facebook", "amazon", "apple", "microsoft", "netflix",
    "goldman sachs", "mckinsey", "bain & company", "boston consulting group",
    "openai", "anthropic",
]
_PRESTIGE_PATTERN = re.compile(
    r"(?<![a-z0-9])(" + "|".join(re.escape(t) for t in _PRESTIGE_TOKENS) + r")(?![a-z0-9])",
    re.IGNORECASE,
)


def strip_prestige_signals(text: str) -> str:
    """Remove known prestige employer/university name-strings from text."""
    return _PRESTIGE_PATTERN.sub(" ", text)


@dataclass
class SemanticMatchResult:
    score: float  # 0.0 - 1.0, cosine similarity


class SemanticEngine:
    """Base interface. Swap in a different engine by subclassing and
    overriding `score_all`."""

    def score_all(self, jd: ParsedJD, resumes: list[ParsedResume]) -> dict[str, SemanticMatchResult]:
        raise NotImplementedError


class TfidfSemanticEngine(SemanticEngine):
    def __init__(self, max_features: int = 5000, ngram_range: tuple[int, int] = (1, 2)):
        self.max_features = max_features
        self.ngram_range = ngram_range

    def score_all(
        self, jd: ParsedJD, resumes: list[ParsedResume], prestige_neutral: bool = False
    ) -> dict[str, SemanticMatchResult]:
        if not resumes:
            return {}

        jd_text = jd.raw_text
        resume_texts = [r.raw_text for r in resumes]
        if prestige_neutral:
            jd_text = strip_prestige_signals(jd_text)
            resume_texts = [strip_prestige_signals(t) for t in resume_texts]

        documents = [jd_text] + resume_texts
        vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            ngram_range=self.ngram_range,
            stop_words="english",
        )
        try:
            matrix = vectorizer.fit_transform(documents)
        except ValueError:
            # Happens if the vocabulary is empty (e.g. all-stopword docs).
            return {r.filename: SemanticMatchResult(score=0.0) for r in resumes}

        jd_vector = matrix[0:1]
        resume_vectors = matrix[1:]
        similarities = cosine_similarity(jd_vector, resume_vectors)[0]

        results = {}
        for resume, sim in zip(resumes, similarities):
            results[resume.filename] = SemanticMatchResult(score=round(float(sim), 4))
        return results


def get_default_semantic_engine() -> SemanticEngine:
    return TfidfSemanticEngine()
