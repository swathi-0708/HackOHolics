#!/usr/bin/env python3
"""
run_pipeline.py
----------------
CLI entry point for the resume-matching pipeline.

Usage:
    python run_pipeline.py --jd data/jd/sample_jd.pdf --resumes data/resumes --out output

Outputs:
    output/results.json  — full structured results (all candidates, ranked)
    output/report.html   — interactive ranked report with evidence + explanations
"""

from __future__ import annotations
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.pipeline import run_pipeline, save_results
from src.semantic_engine import SentenceTransformerEngine, TfidfSemanticEngine
from src.ui_generator import generate_html_report
from src.pdf_parser import PDFParsingError


def main():
    parser = argparse.ArgumentParser(description="Rank resumes against a job description.")
    parser.add_argument("--jd", required=True, help="Path to the JD PDF (or .txt) file")
    parser.add_argument("--resumes", required=True, help="Path to a directory of resume PDFs (or .txt)")
    parser.add_argument("--out", default="output", help="Output directory (default: output/)")
    parser.add_argument("--top-n", type=int, default=3, help="How many top candidates get evidence-based explanations")
    parser.add_argument("--keyword-weight", type=float, default=0.65, help="Weight for keyword score in fusion")
    parser.add_argument("--semantic-weight", type=float, default=0.35, help="Weight for semantic score in fusion")
    parser.add_argument(
        "--semantic-engine",
        choices=["sentence-transformer", "tfidf"],
        default="sentence-transformer",
        help="Semantic engine to use (default: sentence-transformer)",
    )
    args = parser.parse_args()

    engine = (
        SentenceTransformerEngine()
        if args.semantic_engine == "sentence-transformer"
        else TfidfSemanticEngine()
    )

    try:
        results = run_pipeline(
            jd_path=args.jd,
            resumes_dir=args.resumes,
            top_n=args.top_n,
            keyword_weight=args.keyword_weight,
            semantic_weight=args.semantic_weight,
            semantic_engine=engine,
        )
    except PDFParsingError as e:
        print(f"Error: {e}")
        sys.exit(1)

    os.makedirs(args.out, exist_ok=True)
    json_path = os.path.join(args.out, "results.json")
    html_path = os.path.join(args.out, "report.html")

    save_results(results, json_path)
    generate_html_report(results, html_path)

    print(f"\nRanked {len(results['candidates'])} candidates for role: {results['jd_title']}\n")
    for c in results["candidates"][:args.top_n]:
        print(f"  #{c['rank']}  {c['candidate_name']:<28} {c['fused_score']['overall_score']:>5.1f}/100")

    print(f"\nWrote: {json_path}")
    print(f"Wrote: {html_path}")


if __name__ == "__main__":
    main()
