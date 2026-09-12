"""
semantic_engine.py
-------------------
Computes a semantic-similarity score between a JD and a resume, to catch
matches the Keyword Engine misses (paraphrased experience, related-but-not-
identical technologies, seniority language, domain context, etc).

Engines available:
1. SentenceTransformerEngine (preferred when PyTorch is available):
   Uses sentence-transformers ('all-MiniLM-L6-v2') and PyTorch cosine
   similarity between dense embeddings.

2. TfidfSemanticEngine (automatic fallback):
   Uses TF-IDF + cosine similarity over the JD/resume text.
   Runs fully offline and does not require PyTorch.

The default engine automatically selects SentenceTransformer when its
dependencies are available. Otherwise, it falls back to TF-IDF so that
the rest of the resume-matching pipeline can still run.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# ---------------------------------------------------------------------------
# Optional PyTorch / SentenceTransformer dependency
# ---------------------------------------------------------------------------
#
# PyTorch is not available in some environments, such as the current
# Intel/x86_64 Mac setup. Do NOT allow that optional dependency to prevent
# the entire pipeline from importing.
#
# If these imports fail, TORCH_AVAILABLE becomes False and the project
# automatically uses TfidfSemanticEngine instead.
# ---------------------------------------------------------------------------

try:
    import torch
    import torch.nn.functional as F
    from sentence_transformers import SentenceTransformer

    TORCH_AVAILABLE = True

except ImportError:
    torch = None
    F = None
    SentenceTransformer = None
    TORCH_AVAILABLE = False


# ---------------------------------------------------------------------------
# Scikit-learn semantic dependencies
# ---------------------------------------------------------------------------

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .jd_parser import ParsedJD
from .resume_parser import ParsedResume


# ---------------------------------------------------------------------------
# Prestige signal handling
# ---------------------------------------------------------------------------

# Well-known employer/university names.
#
# These are removed only when prestige_neutral=True.
# They are NOT part of the actual candidate score when prestige-neutral
# scoring is requested.

_PRESTIGE_TOKENS = [
    "harvard",
    "stanford",
    "mit",
    "massachusetts institute of technology",
    "princeton",
    "yale",
    "oxford",
    "cambridge",
    "caltech",
    "berkeley",
    "carnegie mellon",
    "columbia university",
    "cornell",
    "wharton",
    "google",
    "meta",
    "facebook",
    "amazon",
    "apple",
    "microsoft",
    "netflix",
    "uber",
    "salesforce",
    "oracle",
    "goldman sachs",
    "mckinsey",
    "bain & company",
    "boston consulting group",
]

_PRESTIGE_PATTERN = re.compile(
    r"(?<![a-z0-9])("
    + "|".join(re.escape(t) for t in _PRESTIGE_TOKENS)
    + r")(?![a-z0-9])",
    re.IGNORECASE,
)


def strip_prestige_signals(text: str) -> str:
    """
    Remove known prestige employer/university name-strings from text.

    This is used only for prestige-neutral semantic scoring.
    """
    if not text:
        return ""

    return _PRESTIGE_PATTERN.sub(" ", text)


# ---------------------------------------------------------------------------
# Result object
# ---------------------------------------------------------------------------

@dataclass
class SemanticMatchResult:
    """
    Result of semantic similarity calculation.

    score:
        Float between 0.0 and 1.0.
    """

    score: float


# ---------------------------------------------------------------------------
# Base semantic engine
# ---------------------------------------------------------------------------

class SemanticEngine:
    """
    Base interface for semantic engines.

    Concrete implementations must provide:
        compute_similarity()
        score_all()
        score_requirements()
    """

    def compute_similarity(self, text1: str, text2: str) -> float:
        raise NotImplementedError

    def score_all(
        self,
        jd: ParsedJD,
        resumes: list[ParsedResume],
        prestige_neutral: bool = False,
    ) -> dict[str, SemanticMatchResult]:
        raise NotImplementedError

    def score_requirements(
        self,
        jd_requirements: list[str],
        resume_sections: dict[str, str],
    ) -> dict[str, float]:
        raise NotImplementedError


# ===========================================================================
# SentenceTransformer Engine
# ===========================================================================

class SentenceTransformerEngine(SemanticEngine):
    """
    Semantic similarity engine using SentenceTransformer embeddings
    and PyTorch cosine similarity.

    This engine is used when PyTorch + sentence-transformers are available.

    The model is cached at class level so it is not loaded repeatedly.
    """

    _model: Optional["SentenceTransformer"] = None
    _model_name: str = "all-MiniLM-L6-v2"

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if not TORCH_AVAILABLE:
            raise RuntimeError(
                "SentenceTransformerEngine requires PyTorch and "
                "sentence-transformers. They are not available in this "
                "environment. Use TfidfSemanticEngine instead."
            )

        self.model_name = model_name
        self.model = self._get_model(self.model_name)

    @classmethod
    def _get_model(
        cls,
        model_name: str = "all-MiniLM-L6-v2",
    ) -> "SentenceTransformer":
        """
        Return the cached SentenceTransformer model.
        """

        if not TORCH_AVAILABLE:
            raise RuntimeError(
                "PyTorch/sentence-transformers are not available."
            )

        if cls._model is None or cls._model_name != model_name:
            cls._model = SentenceTransformer(model_name)
            cls._model_name = model_name

        return cls._model

    def compute_similarity(
        self,
        self_or_text1,
        text1_or_text2: str,
        text2: str | None = None,
    ) -> float:
        """
        Compute cosine similarity between two texts.

        Supports both:

            engine.compute_similarity(text1, text2)

        and the legacy class-style form:

            SentenceTransformerEngine.compute_similarity(text1, text2)
        """

        if not TORCH_AVAILABLE:
            raise RuntimeError(
                "PyTorch is unavailable. "
                "Use TfidfSemanticEngine instead."
            )

        # Legacy class-style call.
        if isinstance(self_or_text1, str) and text2 is None:
            t1 = self_or_text1
            t2 = text1_or_text2
            model = SentenceTransformerEngine._get_model()

        # Normal instance call.
        else:
            t1 = text1_or_text2
            t2 = text2 if text2 is not None else ""

            model_name = getattr(
                self_or_text1,
                "model_name",
                "all-MiniLM-L6-v2",
            )

            model = SentenceTransformerEngine._get_model(model_name)

        if not t1 or not t2:
            return 0.0

        if not t1.strip() or not t2.strip():
            return 0.0

        emb1 = model.encode(
            t1,
            convert_to_tensor=True,
        )

        emb2 = model.encode(
            t2,
            convert_to_tensor=True,
        )

        if emb1.ndim == 1:
            emb1 = emb1.unsqueeze(0)

        if emb2.ndim == 1:
            emb2 = emb2.unsqueeze(0)

        sim = F.cosine_similarity(
            emb1,
            emb2,
            dim=1,
        )

        sim_val = float(sim.item())

        return float(
            max(
                0.0,
                min(1.0, sim_val),
            )
        )

    def score_all(
        self,
        jd: ParsedJD,
        resumes: list[ParsedResume],
        prestige_neutral: bool = False,
    ) -> dict[str, SemanticMatchResult]:

        if not resumes:
            return {}

        jd_text = jd.raw_text

        resume_texts = [
            r.raw_text
            for r in resumes
        ]

        if prestige_neutral:
            jd_text = strip_prestige_signals(jd_text)

            resume_texts = [
                strip_prestige_signals(text)
                for text in resume_texts
            ]

        model = self._get_model(self.model_name)

        jd_emb = model.encode(
            jd_text,
            convert_to_tensor=True,
        )

        if jd_emb.ndim == 1:
            jd_emb = jd_emb.unsqueeze(0)

        resume_embs = model.encode(
            resume_texts,
            convert_to_tensor=True,
        )

        if resume_embs.ndim == 1:
            resume_embs = resume_embs.unsqueeze(0)

        similarities = F.cosine_similarity(
            jd_emb,
            resume_embs,
            dim=1,
        )

        results: dict[str, SemanticMatchResult] = {}

        for resume, sim in zip(resumes, similarities):
            sim_val = float(sim.item())

            score = round(
                float(
                    max(
                        0.0,
                        min(1.0, sim_val),
                    )
                ),
                4,
            )

            results[resume.filename] = SemanticMatchResult(
                score=score
            )

        return results

    def score_requirements(
        self_or_reqs,
        reqs_or_sections: list[str] | dict[str, str],
        sections: dict[str, str] | None = None,
    ) -> dict[str, float]:
        """
        Compute maximum semantic similarity between each JD requirement
        and all available resume sections.
        """

        if not TORCH_AVAILABLE:
            raise RuntimeError(
                "PyTorch is unavailable. "
                "Use TfidfSemanticEngine instead."
            )

        # Legacy class-style call.
        if isinstance(self_or_reqs, (list, tuple)) and sections is None:
            jd_reqs = self_or_reqs

            resume_secs = (
                reqs_or_sections
                if isinstance(reqs_or_sections, dict)
                else {}
            )

            model_name = "all-MiniLM-L6-v2"

        # Normal instance call.
        else:
            jd_reqs = (
                reqs_or_sections
                if isinstance(reqs_or_sections, (list, tuple))
                else []
            )

            resume_secs = (
                sections
                if sections is not None
                else {}
            )

            model_name = getattr(
                self_or_reqs,
                "model_name",
                "all-MiniLM-L6-v2",
            )

        if not jd_reqs:
            return {}

        valid_sections = {
            key: value.strip()
            for key, value in resume_secs.items()
            if isinstance(value, str) and value.strip()
        }

        if not valid_sections:
            return {
                req: 0.0
                for req in jd_reqs
            }

        model = SentenceTransformerEngine._get_model(
            model_name
        )

        non_empty_reqs = [
            req
            for req in jd_reqs
            if isinstance(req, str) and req.strip()
        ]

        if not non_empty_reqs:
            return {
                req: 0.0
                for req in jd_reqs
            }

        sec_texts = list(
            valid_sections.values()
        )

        req_embs = model.encode(
            non_empty_reqs,
            convert_to_tensor=True,
        )

        if req_embs.ndim == 1:
            req_embs = req_embs.unsqueeze(0)

        sec_embs = model.encode(
            sec_texts,
            convert_to_tensor=True,
        )

        if sec_embs.ndim == 1:
            sec_embs = sec_embs.unsqueeze(0)

        sim_matrix = F.cosine_similarity(
            req_embs.unsqueeze(1),
            sec_embs.unsqueeze(0),
            dim=2,
        )

        max_sims, _ = sim_matrix.max(
            dim=1
        )

        score_lookup: dict[str, float] = {}

        for req, max_sim in zip(
            non_empty_reqs,
            max_sims,
        ):
            val = float(max_sim.item())

            score_lookup[req] = round(
                float(
                    max(
                        0.0,
                        min(1.0, val),
                    )
                ),
                4,
            )

        results: dict[str, float] = {}

        for req in jd_reqs:
            results[req] = score_lookup.get(
                req,
                0.0,
            )

        return results


# Alias kept for compatibility with other project files.
EmbeddingSemanticEngine = SentenceTransformerEngine


# ===========================================================================
# TF-IDF Semantic Engine
# ===========================================================================

class TfidfSemanticEngine(SemanticEngine):
    """
    Fully offline semantic fallback.

    Uses TF-IDF vectors and cosine similarity.

    Does not require:
        torch
        sentence-transformers
        neural models
        model downloads
    """

    def __init__(
        self,
        max_features: int = 5000,
        ngram_range: tuple[int, int] = (1, 2),
    ):
        self.max_features = max_features
        self.ngram_range = ngram_range

    def compute_similarity(
        self,
        text1: str,
        text2: str,
    ) -> float:

        if not text1 or not text2:
            return 0.0

        if not text1.strip() or not text2.strip():
            return 0.0

        vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            ngram_range=self.ngram_range,
            stop_words="english",
        )

        try:
            matrix = vectorizer.fit_transform(
                [text1, text2]
            )

            sim = cosine_similarity(
                matrix[0:1],
                matrix[1:2],
            )[0][0]

            return float(
                max(
                    0.0,
                    min(1.0, float(sim)),
                )
            )

        except ValueError:
            return 0.0

    def score_all(
        self,
        jd: ParsedJD,
        resumes: list[ParsedResume],
        prestige_neutral: bool = False,
    ) -> dict[str, SemanticMatchResult]:

        if not resumes:
            return {}

        jd_text = jd.raw_text

        resume_texts = [
            r.raw_text
            for r in resumes
        ]

        if prestige_neutral:
            jd_text = strip_prestige_signals(
                jd_text
            )

            resume_texts = [
                strip_prestige_signals(text)
                for text in resume_texts
            ]

        documents = [
            jd_text,
            *resume_texts,
        ]

        vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            ngram_range=self.ngram_range,
            stop_words="english",
        )

        try:
            matrix = vectorizer.fit_transform(
                documents
            )

        except ValueError:
            # Happens when the vocabulary is empty.
            return {
                resume.filename: SemanticMatchResult(
                    score=0.0
                )
                for resume in resumes
            }

        jd_vector = matrix[0:1]

        resume_vectors = matrix[1:]

        similarities = cosine_similarity(
            jd_vector,
            resume_vectors,
        )[0]

        results: dict[str, SemanticMatchResult] = {}

        for resume, sim in zip(
            resumes,
            similarities,
        ):
            score = round(
                float(
                    max(
                        0.0,
                        min(1.0, float(sim)),
                    )
                ),
                4,
            )

            results[resume.filename] = SemanticMatchResult(
                score=score
            )

        return results

    def score_requirements(
        self,
        jd_requirements: list[str],
        resume_sections: dict[str, str],
    ) -> dict[str, float]:

        if not jd_requirements:
            return {}

        valid_sections = {
            key: value.strip()
            for key, value in resume_sections.items()
            if isinstance(value, str) and value.strip()
        }

        if not valid_sections:
            return {
                req: 0.0
                for req in jd_requirements
            }

        results: dict[str, float] = {}

        for req in jd_requirements:

            if not req or not req.strip():
                results[req] = 0.0
                continue

            max_score = 0.0

            for sec_text in valid_sections.values():

                sim = self.compute_similarity(
                    req,
                    sec_text,
                )

                if sim > max_score:
                    max_score = sim

            results[req] = round(
                float(max_score),
                4,
            )

        return results


# ===========================================================================
# Convenience functions
# ===========================================================================

def compute_similarity(
    text1: str,
    text2: str,
    model_name: str = "all-MiniLM-L6-v2",
) -> float:
    """
    Convenience function.

    Uses SentenceTransformer when PyTorch is available.
    Otherwise automatically uses TF-IDF.
    """

    if TORCH_AVAILABLE:
        engine = SentenceTransformerEngine(
            model_name=model_name
        )
    else:
        engine = TfidfSemanticEngine()

    return engine.compute_similarity(
        text1,
        text2,
    )


def score_requirements(
    jd_requirements: list[str],
    resume_sections: dict[str, str],
    engine: SemanticEngine | None = None,
) -> dict[str, float]:
    """
    Convenience function for requirement-level semantic scoring.

    If no engine is supplied, get_default_semantic_engine() chooses the
    best available engine automatically.
    """

    if engine is None:
        engine = get_default_semantic_engine()

    return engine.score_requirements(
        jd_requirements,
        resume_sections,
    )


def get_default_semantic_engine() -> SemanticEngine:
    """
    Return the best semantic engine available in the current environment.

    Priority:
        1. SentenceTransformer + PyTorch
        2. TF-IDF fallback

    This allows the project to run on environments where PyTorch cannot
    be installed, while preserving the neural semantic engine for machines
    that support it.
    """

    if TORCH_AVAILABLE:
        return SentenceTransformerEngine()

    return TfidfSemanticEngine()