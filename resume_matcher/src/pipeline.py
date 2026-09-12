"""
pipeline.py
-----------
Orchestrates the full resume-screening pipeline:

  JD PDF ─┐                    ┌─ Resume PDFs (x N)
          v                    v
     PDF Parser            PDF Parser
          |                    |
          v                    v
      JD Parser             Resume Parser
          |                    |
          └──────┬─────────────┘
                 v
        Skill Taxonomy / Alias Layer
                 |
         ┌───────┴───────┐
         v               v
   Keyword Engine   Semantic Engine
         |               |
         └───────┬───────┘
                 v
           Score Fusion
                 v
         Rank All Candidates
                 v
        Evidence Generator
                 v
               Top 3
                 v
        Explanation Engine
                 v
                UI

Run via run_pipeline.py at the project root, not this file directly.
"""

from __future__ import annotations
import json
import os
from dataclasses import asdict

from .pdf_parser import parse_pdf_or_text, parse_directory, PDFParsingError
from .skill_taxonomy import SkillTaxonomy
from .jd_parser import parse_jd, ParsedJD
from .resume_parser import parse_resume
from .keyword_engine import compute_keyword_match
from .semantic_engine import (
    get_default_semantic_engine,
    SemanticEngine,
    SentenceTransformerEngine,
    TfidfSemanticEngine,
    EmbeddingSemanticEngine,
)
from .score_fusion import fuse_scores, DEFAULT_KEYWORD_WEIGHT, DEFAULT_SEMANTIC_WEIGHT
from .evidence_generator import build_evidence, rank_candidates, CandidateEvidence
from .explanation_generator import generate_explanation


def run_pipeline(
    jd_path: str,
    resumes_dir: str,
    top_n: int = 3,
    keyword_weight: float = DEFAULT_KEYWORD_WEIGHT,
    semantic_weight: float = DEFAULT_SEMANTIC_WEIGHT,
    semantic_engine: SemanticEngine | None = None,
) -> dict:
    taxonomy = SkillTaxonomy()

    # 1-2. Parse JD and resumes from PDF (or .txt for testing)
    parsed_jd_doc = parse_pdf_or_text(jd_path)
    jd: ParsedJD = parse_jd(parsed_jd_doc.text, taxonomy)

    resume_docs = parse_directory(resumes_dir)
    if not resume_docs:
        raise PDFParsingError(f"No parseable .pdf/.txt resumes found in {resumes_dir}")

    resumes = [parse_resume(doc.filename, doc.text, taxonomy) for doc in resume_docs]

    # 3. Semantic engine computes similarity between JD and candidate resumes
    if semantic_engine is None:
        semantic_engine = get_default_semantic_engine()
    semantic_results = semantic_engine.score_all(jd, resumes, prestige_neutral=False)
    semantic_results_neutral = semantic_engine.score_all(jd, resumes, prestige_neutral=True)

    # 4-6. Keyword match + fusion + evidence, per candidate
    evidences: list[CandidateEvidence] = []
    for resume in resumes:
        keyword_result = compute_keyword_match(jd, resume, taxonomy)
        semantic_result = semantic_results[resume.filename]
        semantic_result_neutral = semantic_results_neutral[resume.filename]

        fused = fuse_scores(keyword_result, semantic_result, keyword_weight, semantic_weight)
        fused_neutral = fuse_scores(keyword_result, semantic_result_neutral, keyword_weight, semantic_weight)

        evidence = build_evidence(
            jd, resume, keyword_result, fused,
            prestige_neutral_overall_score=fused_neutral.overall_score,
        )
        evidences.append(evidence)

    # 7. Rank all candidates (not just the top N) so the full list is auditable
    ranked = rank_candidates(evidences)

    # 8-9. Generate NL explanations for the top N only (cost control)
    explanations: dict[str, str] = {}
    for evidence in ranked[:top_n]:
        explanations[evidence.filename] = generate_explanation(evidence)

    return {
        "jd_title": jd.title,
        "jd_required_skills": jd.required_skills(),
        "jd_preferred_skills": jd.preferred_skills(),
        "jd_min_years_experience": jd.min_years_experience,
        "keyword_weight": keyword_weight,
        "semantic_weight": semantic_weight,
        "candidates": [asdict(e) for e in ranked],
        "explanations": explanations,
        "top_n": top_n,
    }


def save_results(results: dict, out_path: str) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)