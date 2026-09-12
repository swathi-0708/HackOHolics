"""
Resume Matcher - Core Modules
"""

from .pipeline import run_pipeline, save_results
from .semantic_engine import (
    SemanticEngine,
    SentenceTransformerEngine,
    TfidfSemanticEngine,
    EmbeddingSemanticEngine,
    SemanticMatchResult,
    compute_similarity,
    score_requirements,
    get_default_semantic_engine,
    strip_prestige_signals,
)
from .keyword_engine import compute_keyword_match, KeywordMatchResult
from .score_fusion import fuse_scores, FusedScore
from .evidence_generator import build_evidence, rank_candidates, CandidateEvidence
from .explanation_generator import generate_explanation
from .jd_parser import parse_jd, ParsedJD
from .resume_parser import parse_resume, ParsedResume
from .skill_taxonomy import SkillTaxonomy
from .pdf_parser import parse_pdf_or_text, parse_directory, PDFParsingError

__all__ = [
    "run_pipeline",
    "save_results",
    "SemanticEngine",
    "SentenceTransformerEngine",
    "TfidfSemanticEngine",
    "EmbeddingSemanticEngine",
    "SemanticMatchResult",
    "compute_similarity",
    "score_requirements",
    "get_default_semantic_engine",
    "strip_prestige_signals",
    "compute_keyword_match",
    "KeywordMatchResult",
    "fuse_scores",
    "FusedScore",
    "build_evidence",
    "rank_candidates",
    "CandidateEvidence",
    "generate_explanation",
    "parse_jd",
    "ParsedJD",
    "parse_resume",
    "ParsedResume",
    "SkillTaxonomy",
    "parse_pdf_or_text",
    "parse_directory",
    "PDFParsingError",
]
