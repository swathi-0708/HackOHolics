"""
semantic_engine.py
-------------------
Computes a semantic-similarity score between a JD and a resume, to catch
matches the Keyword Engine misses (paraphrased experience, related-but-not-
identical technologies, seniority language, domain context, etc).

Engines available:
1. SentenceTransformerEngine (default): Uses sentence-transformers
   ('all-MiniLM-L6-v2') and PyTorch cosine similarity between dense embeddings.
   Caches the model at the class level so it doesn't reload on every call.
2. TfidfSemanticEngine: TF-IDF + cosine similarity over the full JD text vs
   full resume text. Runs fully offline with no neural model download.
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional

import torch
import torch.nn.functional as F
from sentence_transformers import SentenceTransformer
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
    "uber", "salesforce", "oracle", "goldman sachs", "mckinsey", "bain & company", "boston consulting group",
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
    overriding `score_all` and `compute_similarity`."""

    def compute_similarity(self, text1: str, text2: str) -> float:
        raise NotImplementedError

    def score_all(
        self, jd: ParsedJD, resumes: list[ParsedResume], prestige_neutral: bool = False
    ) -> dict[str, SemanticMatchResult]:
        raise NotImplementedError

    def score_requirements(
        self, jd_requirements: list[str], resume_sections: dict[str, str]
    ) -> dict[str, float]:
        raise NotImplementedError


class SentenceTransformerEngine(SemanticEngine):
    """Semantic similarity engine using SentenceTransformer embeddings
    and PyTorch cosine similarity.

    The SentenceTransformer model is cached at the class level so it doesn't
    reload on every function call or instance creation.
    """

    _model: Optional[SentenceTransformer] = None
    _model_name: str = "all-MiniLM-L6-v2"

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = self._get_model(self.model_name)

    @classmethod
    def _get_model(cls, model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
        """Class-level cache for the SentenceTransformer model to prevent reloading."""
        if cls._model is None or cls._model_name != model_name:
            cls._model = SentenceTransformer(model_name)
            cls._model_name = model_name
        return cls._model

    def compute_similarity(self_or_text1, text1_or_text2: str, text2: str | None = None) -> float:
        """Compute cosine similarity between two texts using torch embeddings.
        Returns a standard Python float between 0.0 and 1.0.

        Supports both instance call: `engine.compute_similarity(text1, text2)`
        and class call: `SentenceTransformerEngine.compute_similarity(text1, text2)`.
        """
        if isinstance(self_or_text1, str) and text2 is None:
            t1 = self_or_text1
            t2 = text1_or_text2
            model = SentenceTransformerEngine._get_model()
        else:
            t1 = text1_or_text2
            t2 = text2 if text2 is not None else ""
            model_name = getattr(self_or_text1, "model_name", "all-MiniLM-L6-v2")
            model = SentenceTransformerEngine._get_model(model_name)

        if not t1 or not t2 or not t1.strip() or not t2.strip():
            return 0.0

        emb1 = model.encode(t1, convert_to_tensor=True)
        emb2 = model.encode(t2, convert_to_tensor=True)

        if emb1.ndim == 1:
            emb1 = emb1.unsqueeze(0)
        if emb2.ndim == 1:
            emb2 = emb2.unsqueeze(0)

        sim = F.cosine_similarity(emb1, emb2, dim=1)
        sim_val = float(sim.item())
        # Return a standard Python float clamped strictly between 0.0 and 1.0
        return float(max(0.0, min(1.0, sim_val)))

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

        model = self._get_model(self.model_name)

        jd_emb = model.encode(jd_text, convert_to_tensor=True)
        if jd_emb.ndim == 1:
            jd_emb = jd_emb.unsqueeze(0)

        resume_embs = model.encode(resume_texts, convert_to_tensor=True)
        if resume_embs.ndim == 1:
            resume_embs = resume_embs.unsqueeze(0)

        similarities = F.cosine_similarity(jd_emb, resume_embs, dim=1)

        results = {}
        for resume, sim in zip(resumes, similarities):
            sim_val = float(sim.item())
            score = round(float(max(0.0, min(1.0, sim_val))), 4)
            results[resume.filename] = SemanticMatchResult(score=score)
        return results

    def score_requirements(
        self_or_reqs,
        reqs_or_sections: list[str] | dict[str, str],
        sections: dict[str, str] | None = None,
    ) -> dict[str, float]:
        """Compute the maximum semantic similarity score across all resume sections
        for each JD requirement.

        Args:
            jd_requirements: List of requirement strings (e.g., ['backend development experience'])
            resume_sections: Dict mapping section names to text (e.g., {'skills': '...', 'experience': '...'})

        Returns:
            Dict mapping {requirement_text: max_semantic_score}
        """
        if isinstance(self_or_reqs, (list, tuple)) and sections is None:
            jd_reqs = self_or_reqs
            resume_secs = reqs_or_sections if isinstance(reqs_or_sections, dict) else {}
            model_name = "all-MiniLM-L6-v2"
        else:
            jd_reqs = reqs_or_sections if isinstance(reqs_or_sections, (list, tuple)) else []
            resume_secs = sections if sections is not None else {}
            model_name = getattr(self_or_reqs, "model_name", "all-MiniLM-L6-v2")

        if not jd_reqs:
            return {}

        valid_sections = {
            k: v.strip() for k, v in resume_secs.items() if isinstance(v, str) and v.strip()
        }
        if not valid_sections:
            return {req: 0.0 for req in jd_reqs}

        model = SentenceTransformerEngine._get_model(model_name)

        non_empty_reqs = [r for r in jd_reqs if isinstance(r, str) and r.strip()]
        if not non_empty_reqs:
            return {req: 0.0 for req in jd_reqs}

        sec_texts = list(valid_sections.values())

        req_embs = model.encode(non_empty_reqs, convert_to_tensor=True)
        if req_embs.ndim == 1:
            req_embs = req_embs.unsqueeze(0)

        sec_embs = model.encode(sec_texts, convert_to_tensor=True)
        if sec_embs.ndim == 1:
            sec_embs = sec_embs.unsqueeze(0)

        sim_matrix = F.cosine_similarity(req_embs.unsqueeze(1), sec_embs.unsqueeze(0), dim=2)
        max_sims, _ = sim_matrix.max(dim=1)

        score_lookup = {}
        for req, max_sim in zip(non_empty_reqs, max_sims):
            val = float(max_sim.item())
            score_lookup[req] = round(float(max(0.0, min(1.0, val))), 4)

        results = {}
        for req in jd_reqs:
            results[req] = score_lookup.get(req, 0.0)

        return results


# Alias for compatibility with architecture docstring / external references
EmbeddingSemanticEngine = SentenceTransformerEngine


class TfidfSemanticEngine(SemanticEngine):
    def __init__(self, max_features: int = 5000, ngram_range: tuple[int, int] = (1, 2)):
        self.max_features = max_features
        self.ngram_range = ngram_range

    def compute_similarity(self, text1: str, text2: str) -> float:
        if not text1 or not text2 or not text1.strip() or not text2.strip():
            return 0.0
        vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            ngram_range=self.ngram_range,
            stop_words="english",
        )
        try:
            matrix = vectorizer.fit_transform([text1, text2])
            sim = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
            return float(max(0.0, min(1.0, float(sim))))
        except ValueError:
            return 0.0

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

    def score_requirements(
        self, jd_requirements: list[str], resume_sections: dict[str, str]
    ) -> dict[str, float]:
        if not jd_requirements:
            return {}

        valid_sections = {
            k: v.strip() for k, v in resume_sections.items() if isinstance(v, str) and v.strip()
        }
        if not valid_sections:
            return {req: 0.0 for req in jd_requirements}

        results: dict[str, float] = {}
        for req in jd_requirements:
            if not req or not req.strip():
                results[req] = 0.0
                continue
            max_score = 0.0
            for sec_text in valid_sections.values():
                sim = self.compute_similarity(req, sec_text)
                if sim > max_score:
                    max_score = sim
            results[req] = round(float(max_score), 4)
        return results


def compute_similarity(text1: str, text2: str, model_name: str = "all-MiniLM-L6-v2") -> float:
    """Convenience function to compute cosine similarity between two texts
    using SentenceTransformer embeddings.
    """
    engine = SentenceTransformerEngine(model_name=model_name)
    return engine.compute_similarity(text1, text2)


def score_requirements(
    jd_requirements: list[str],
    resume_sections: dict[str, str],
    engine: SemanticEngine | None = None,
) -> dict[str, float]:
    """Convenience function to score JD requirements against resume sections
    using SentenceTransformer embeddings or a specified SemanticEngine.
    """
    if engine is None:
        engine = get_default_semantic_engine()
    return engine.score_requirements(jd_requirements, resume_sections)


def get_default_semantic_engine() -> SemanticEngine:
    return SentenceTransformerEngine()
