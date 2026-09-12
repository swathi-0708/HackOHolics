# Resume Matcher

Ranks resumes against a job description using keyword + semantic matching,
produces auditable evidence per candidate, and generates a natural-language
explanation for the top N — plus an interactive HTML report.

```
JD PDF ─┐                    ┌─ Resume PDFs (×N)
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
 Keyword Engine   Semantic Engine (Dense Embeddings)
       |               |
       └───────┬───────┘
               v
         Score Fusion
               v
      Rank All Candidates
               v
     Evidence Generator
               v
             Top N
               v
     Explanation Engine
               v
              UI
```

## Setup

```bash
pip install -r requirements.txt
```

Core dependencies (`pdfplumber`, `pypdf`, `scikit-learn`, `numpy`, `sentence-transformers`, `torch`) run fully offline — no API keys or network calls required to run the pipeline.

`reportlab` is only needed to generate the bundled sample data.

## Quickstart (with bundled sample data)

```bash
python generate_sample_data.py
python run_pipeline.py --jd data/jd/sample_jd.pdf --resumes data/resumes --out output
```

This writes:
- `output/results.json` — full structured results, every candidate ranked
- `output/report.html` — open this in a browser for the interactive report

## Using your own files

```bash
python run_pipeline.py --jd path/to/job_description.pdf --resumes path/to/resume_folder --out output
```

- `--jd` accepts a single `.pdf` (or `.txt`, useful for testing without a real PDF)
- `--resumes` accepts a directory of `.pdf`/`.txt` files (15–18+ resumes is fine)
- `--top-n` controls how many candidates get evidence-based explanations (default 3)
- `--keyword-weight` / `--semantic-weight` control the Score Fusion blend (default 0.65 / 0.35)
- `--semantic-engine` engine choice: `sentence-transformer` (default) or `tfidf`

## Candidate Explanations

Explanations are generated deterministically and factually from candidate evidence records without requiring external API keys.

The explanation synthesizer processes the pre-computed evidence (matched/missing skills, scores, experience comparison) to summarize candidate strengths and gaps clearly and auditably.

## Architecture notes / design decisions

**Skill Taxonomy (`data/skill_taxonomy.json`)** is the shared vocabulary both
the JD parser and Resume parser normalize into (e.g. "k8s", "kubernetes" →
`kubernetes`). This is what lets the Keyword Engine do exact-set overlap
instead of fragile substring/fuzzy matching. Add new skills/aliases here as
needed — it's just JSON.

**Keyword Engine** computes a weighted overlap: JD requirements are tiered
(required vs preferred, with a "must have" language boost), and the score is
`sum(matched weight) / sum(total weight)`.

**Semantic Engine** uses dense sentence embeddings via `all-MiniLM-L6-v2` (`sentence-transformers`) and PyTorch cosine similarity. It captures deep semantic meaning, domain context, and paraphrased experience that exact keyword matching misses. It also supports per-requirement similarity mapping (`score_requirements`). A fallback TF-IDF engine is also provided.

**Score Fusion** blends keyword (65%) and semantic (35%) by default — keyword
match is weighted higher since it's grounded in explicit, auditable JD
requirements; semantic similarity is a softer signal for catching paraphrased
experience and breaking ties. Adjust the blend per role type via
`--keyword-weight`/`--semantic-weight` (e.g. a soft-skills-heavy role might
want more semantic weight).

**Evidence Generator** builds one deterministic, auditable record per
candidate (matched/missing skills, score breakdown, experience-vs-minimum
comparison, representative resume bullets) — this is what both the UI and
the Explanation engine consume, ensuring a complete and transparent evidence trail.

**Prestige-neutral scoring toggle** (in the HTML report): a fixed list of
well-known employer/university names is stripped from the text before
computing semantic similarity, producing a second score that doesn't reward
resumes purely for containing a famous name. Both scores are pre-computed;
the toggle just switches which one the report sorts/displays by.

## Known limitations

- **Scanned/image-only PDFs** aren't supported — `pdf_parser.py` raises a
  clear error rather than silently returning empty text; you'd need to add
  an OCR step (e.g. `pytesseract`) for those.
- **Years-of-experience estimation** is best-effort (looks for an explicit
  "X years of experience" statement, then falls back to the span between the
  earliest and latest year mentioned in the resume) — it's a heuristic, not
  a guarantee, and should be spot-checked for edge cases (e.g. resumes that
  mention unrelated years, like a graduation year decades ago).
- **No feedback loop yet** — recruiter overrides ("candidate X should rank
  higher") aren't fed back into weight tuning. Score Fusion weights are a
  configurable starting point, not something this pipeline learns over time.
