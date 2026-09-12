"""
jd_parser.py
------------
Parses a job description's raw text into a structured representation:
  - title
  - required skills (weight 1.0, or higher if flagged "must have")
  - preferred / nice-to-have skills (weight 0.5)
  - min_years_experience (if stated)
  - raw_text (kept for the semantic engine)

Approach: JDs are split into sections using common headers
("Requirements", "Qualifications", "Preferred", "Nice to have", etc.).
Skills are then extracted from each section using the shared
SkillTaxonomy, so the same alias resolution used on resumes applies here.
Lines containing strong emphasis language ("must have", "required",
"mandatory") get an extra weight boost.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field

from .skill_taxonomy import SkillTaxonomy

REQUIRED_HEADERS = [
    "requirements", "required qualifications", "required skills",
    "must have", "must-have", "minimum qualifications", "basic qualifications",
    "qualifications",
]
PREFERRED_HEADERS = [
    "preferred", "preferred qualifications", "nice to have", "nice-to-have",
    "bonus", "good to have", "desired skills", "pluses",
]
MUST_HAVE_BOOST_PATTERN = re.compile(
    r"\b(must have|must-have|mandatory|required|non-negotiable)\b", re.IGNORECASE
)
YEARS_PATTERN = re.compile(
    r"(\d+)\+?\s*(?:to\s*\d+\s*)?years?\s+(?:of\s+)?(?:[a-z]+\s+){0,3}experience", re.IGNORECASE
)


@dataclass
class RequirementSkill:
    skill: str
    weight: float
    tier: str  # "required" or "preferred"


@dataclass
class ParsedJD:
    title: str
    raw_text: str
    requirements: list[RequirementSkill] = field(default_factory=list)
    min_years_experience: int | None = None

    def required_skills(self) -> list[str]:
        return [r.skill for r in self.requirements if r.tier == "required"]

    def preferred_skills(self) -> list[str]:
        return [r.skill for r in self.requirements if r.tier == "preferred"]

    def weight_of(self, skill: str) -> float:
        for r in self.requirements:
            if r.skill == skill:
                return r.weight
        return 0.0


def _split_into_sections(text: str) -> dict[str, str]:
    """
    Split JD text into named sections keyed by lower-cased header text.
    Any text before the first recognized header is stored under "_preamble".
    """
    lines = text.split("\n")
    sections: dict[str, list[str]] = {"_preamble": []}
    current = "_preamble"

    all_headers = REQUIRED_HEADERS + PREFERRED_HEADERS + ["responsibilities", "about", "summary"]

    for line in lines:
        stripped = line.strip().strip(":").lower()
        # A "header" line is short and matches (or closely matches) a known header
        if stripped and len(stripped) < 60:
            matched_header = None
            for header in all_headers:
                if stripped == header or stripped.startswith(header):
                    matched_header = header
                    break
            if matched_header:
                current = matched_header
                sections.setdefault(current, [])
                continue
        sections.setdefault(current, [])
        sections[current].append(line)

    return {k: "\n".join(v) for k, v in sections.items()}


def _extract_title(text: str) -> str:
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped:
            return stripped[:120]
    return "Untitled Role"


def parse_jd(text: str, taxonomy: SkillTaxonomy) -> ParsedJD:
    title = _extract_title(text)
    sections = _split_into_sections(text)

    required_skills: set[str] = set()
    preferred_skills: set[str] = set()
    boosted_lines: set[str] = set()

    # Anything under a "required"-type header -> required tier
    for header in REQUIRED_HEADERS:
        if header in sections:
            required_skills |= taxonomy.find_skills_in_text(sections[header])
            for line in sections[header].split("\n"):
                if MUST_HAVE_BOOST_PATTERN.search(line):
                    boosted_lines |= taxonomy.find_skills_in_text(line)

    # Anything under a "preferred"-type header -> preferred tier
    for header in PREFERRED_HEADERS:
        if header in sections:
            preferred_skills |= taxonomy.find_skills_in_text(sections[header])

    # Fallback: if no sections were detected at all (JD has no clear headers),
    # scan the whole doc and treat everything as "required" at a lower default
    # confidence, since we cannot distinguish tiers from structure alone.
    if not required_skills and not preferred_skills:
        required_skills = taxonomy.find_skills_in_text(text)
        for line in text.split("\n"):
            if MUST_HAVE_BOOST_PATTERN.search(line):
                boosted_lines |= taxonomy.find_skills_in_text(line)

    # A skill should not be double-counted in both tiers; required wins.
    preferred_skills -= required_skills

    requirements: list[RequirementSkill] = []
    for skill in sorted(required_skills):
        weight = 1.5 if skill in boosted_lines else 1.0
        requirements.append(RequirementSkill(skill=skill, weight=weight, tier="required"))
    for skill in sorted(preferred_skills):
        requirements.append(RequirementSkill(skill=skill, weight=0.5, tier="preferred"))

    years_match = YEARS_PATTERN.search(text)
    min_years = int(years_match.group(1)) if years_match else None

    return ParsedJD(
        title=title,
        raw_text=text,
        requirements=requirements,
        min_years_experience=min_years,
    )
