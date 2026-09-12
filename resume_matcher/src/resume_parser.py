"""
resume_parser.py
----------------
Parses a resume's raw text into a structured representation:
  - candidate_name (best-effort, from filename or first line)
  - skills (canonical, via SkillTaxonomy)
  - years_of_experience (best-effort, from date ranges or explicit statements)
  - projects / experience bullets (kept as raw text for the semantic engine
    and for evidence snippets)
"""

from __future__ import annotations
import os
import re
from dataclasses import dataclass, field
from datetime import datetime

from .skill_taxonomy import SkillTaxonomy

YEARS_STATEMENT_PATTERN = re.compile(
    r"(\d+)\+?\s*years?\s+(?:of\s+)?(?:[a-z]+\s+){0,3}experience", re.IGNORECASE
)
DATE_RANGE_PATTERN = re.compile(
    r"(19|20)\d{2}\s*[-–—to]{1,3}\s*((19|20)\d{2}|present|current)", re.IGNORECASE
)
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


@dataclass
class ParsedResume:
    filename: str
    candidate_name: str
    raw_text: str
    skills: set[str] = field(default_factory=set)
    years_of_experience: float | None = None
    email: str | None = None
    experience_bullets: list[str] = field(default_factory=list)


def _guess_name(text: str, filename: str) -> str:
    # Prefer the first non-empty line if it looks like a name (short, no digits, no @)
    for line in text.split("\n")[:5]:
        stripped = line.strip()
        if (
            stripped
            and len(stripped.split()) <= 5
            and not any(ch.isdigit() for ch in stripped)
            and "@" not in stripped
            and len(stripped) < 60
        ):
            return stripped
    # Fallback to filename without extension/underscores
    base = os.path.splitext(filename)[0]
    return base.replace("_", " ").replace("-", " ").title()


def _estimate_years_of_experience(text: str) -> float | None:
    explicit = YEARS_STATEMENT_PATTERN.search(text)
    if explicit:
        return float(explicit.group(1))

    # Fall back to spanning the earliest-to-latest year mentioned anywhere
    # (e.g. in date ranges like "2018 - 2022" or "2019 - Present").
    all_years = [int(y) for y in re.findall(r"\b(19[9]\d|20[0-4]\d)\b", text)]
    if all_years:
        span = max(all_years) - min(all_years)
        if span > 0:
            return float(span)
    return None


def _extract_experience_bullets(text: str) -> list[str]:
    bullets = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith(("-", "•", "*", "◦")) or re.match(r"^\d+[.)]", stripped):
            cleaned = re.sub(r"^[-•*◦]\s*|^\d+[.)]\s*", "", stripped)
            if len(cleaned) > 15:
                bullets.append(cleaned)
    return bullets


def parse_resume(filename: str, text: str, taxonomy: SkillTaxonomy) -> ParsedResume:
    candidate_name = _guess_name(text, filename)
    skills = taxonomy.find_skills_in_text(text)
    years = _estimate_years_of_experience(text)
    email_match = EMAIL_PATTERN.search(text)
    email = email_match.group(0) if email_match else None
    bullets = _extract_experience_bullets(text)

    return ParsedResume(
        filename=filename,
        candidate_name=candidate_name,
        raw_text=text,
        skills=skills,
        years_of_experience=years,
        email=email,
        experience_bullets=bullets,
    )
