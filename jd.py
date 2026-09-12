"""Job-description analysis.

Turns free-form JD text into two structures the matcher consumes:

``requirements``  requirement-bearing bullets, each with an importance weight, used
                 as the queries for the semantic lane.
``skill_demands`` canonical skills the JD explicitly names, each tagged
                  must-have / preferred with a weight, used by the keyword lane.

Importance comes from two independent signals -- which JD section a line sits in,
and imperative language inside the line ("must have", "a plus") -- so a JD that
never uses section headings still gets sensible weights.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .keyword import SkillMatcher
from .normalize import clean_line, normalize, split_sentences
from .skills import SKILL_GRAPH, SkillGraph

# JD sections, keyed by the intent of the heading rather than its exact wording.
_JD_SECTION_PATTERNS: tuple[tuple[str, str], ...] = (
    ("must_have", r"(must[\s-]?have|required skills|requirements|qualifications|what we (are looking for|expect)|"
                  r"who you are|eligibility|essential skills|minimum qualifications|skills required|"
                  r"technical requirements)"),
    ("preferred", r"(nice[\s-]?to[\s-]?have|preferred|good to have|bonus|plus points|desirable|"
                  r"added advantage|optional skills|preferred qualifications)"),
    ("responsibilities", r"(responsibilit|what you.?ll do|role overview|the role|day to day|duties|"
                         r"key tasks|you will)"),
    ("about", r"(about (us|the company|technova)|who we are|our team|company overview)"),
    ("benefits", r"(benefits|perks|what we offer|compensation|stipend|why join)"),
)

# Section base weights: an unmet must-have should hurt far more than an unmet perk.
_SECTION_WEIGHT: dict[str, float] = {
    "must_have": 1.0,
    "responsibilities": 0.8,
    "preferred": 0.45,
    "about": 0.15,
    "benefits": 0.0,
    "other": 0.6,
}

_MUST_CUES = re.compile(
    r"\b(must|required|require[sd]?|essential|mandatory|strong (?:command|grasp|knowledge|understanding)|"
    r"solid (?:understanding|grasp)|proficien|expertise in|hands[\s-]?on (?:experience )?(?:with|in)|"
    r"should (?:have|know|be)|need to (?:have|know)|working knowledge)\b", re.I)
_NICE_CUES = re.compile(
    r"\b(nice to have|preferred|preferably|a plus|plus point|bonus|good to have|desirable|"
    r"advantage|familiarity|exposure to|awareness of|willingness|optional|ideally)\b", re.I)
_NOISE_LINE = re.compile(
    r"\b(stipend|salary|ctc|per month|apply (now|at|by)|deadline|location|job type|"
    r"employment type|equal opportunity|send your resume|company overview|founded in|"
    r"we are an|about technova)\b", re.I)


@dataclass
class Requirement:
    """One requirement-bearing line from the JD."""

    text: str
    section: str
    importance: float
    skills: tuple[str, ...] = ()
    kind: str = "must_have"  # must_have | preferred | contextual

    @property
    def is_must(self) -> bool:
        return self.kind == "must_have"


@dataclass
class SkillDemand:
    """A skill the JD explicitly asks for."""

    skill: str
    weight: float
    kind: str            # must_have | preferred
    category: str
    mentions: int = 1
    evidence: str = ""   # the JD line it was found in

    @property
    def is_must(self) -> bool:
        return self.kind == "must_have"


@dataclass
class JobProfile:
    title: str
    raw_text: str
    sections: dict[str, str] = field(default_factory=dict)
    requirements: list[Requirement] = field(default_factory=list)
    skill_demands: dict[str, SkillDemand] = field(default_factory=dict)

    @property
    def must_have_skills(self) -> list[str]:
        return [s for s, d in self.skill_demands.items() if d.is_must]

    @property
    def preferred_skills(self) -> list[str]:
        return [s for s, d in self.skill_demands.items() if not d.is_must]

    def demand_weight(self, skill: str) -> float:
        demand = self.skill_demands.get(skill)
        return demand.weight if demand else 0.0

    def query_texts(self) -> list[tuple[str, float]]:
        """``(text, weight)`` queries for the semantic lane."""
        return [(r.text, r.importance) for r in self.requirements if r.importance > 0]


def _classify_heading(line: str) -> str | None:
    stripped = clean_line(line).strip(" :|-—_")
    if not stripped or len(stripped.split()) > 8:
        return None
    # Headings are short and unpunctuated; bullets and sentences are not headings.
    if re.match(r"^[•\-\*]", clean_line(line)) or stripped.endswith((".", ",")):
        return None
    for section, pattern in _JD_SECTION_PATTERNS:
        if re.search(pattern, stripped, re.I):
            return section
    return None


def segment_jd(text: str) -> dict[str, list[str]]:
    """Group JD lines under the intent of the heading above them."""
    buckets: dict[str, list[str]] = {}
    current = "other"
    for raw_line in text.splitlines():
        if not raw_line.strip():
            continue
        heading = _classify_heading(raw_line)
        if heading:
            current = heading
            tail = raw_line.split(":", 1)[1].strip() if ":" in raw_line else ""
            if tail:
                buckets.setdefault(current, []).append(tail)
            continue
        buckets.setdefault(current, []).append(clean_line(raw_line))
    return buckets


def _extract_title(text: str) -> str:
    for raw_line in text.splitlines()[:8]:
        line = clean_line(raw_line)
        if not line:
            continue
        if re.search(r"\b(intern|developer|engineer|analyst|designer|manager|scientist|architect)\b",
                     line, re.I):
            return re.sub(r"^(job title|role|position)\s*[:\-]\s*", "", line, flags=re.I).strip()
    first = next((clean_line(l) for l in text.splitlines() if clean_line(l)), "")
    return first or "Untitled role"


def analyze_jd(text: str, graph: SkillGraph | None = None,
               matcher: SkillMatcher | None = None) -> JobProfile:
    """Parse JD text into a :class:`JobProfile`."""
    graph = graph or SKILL_GRAPH
    matcher = matcher or SkillMatcher(graph)

    buckets = segment_jd(text)
    profile = JobProfile(
        title=_extract_title(text),
        raw_text=text,
        sections={name: "\n".join(lines) for name, lines in buckets.items()},
    )

    for section, lines in buckets.items():
        base = _SECTION_WEIGHT.get(section, 0.6)
        if base <= 0:
            continue
        for line in lines:
            for sentence in split_sentences(line):
                if len(sentence) < 12 or _NOISE_LINE.search(sentence):
                    continue

                # In-line cues override the section default in both directions:
                # a "must" bullet under Preferred is still a real requirement.
                if _NICE_CUES.search(sentence):
                    kind, weight = "preferred", min(base, 0.5)
                elif _MUST_CUES.search(sentence) or section == "must_have":
                    kind, weight = "must_have", max(base, 0.9)
                elif section == "responsibilities":
                    kind, weight = "must_have", base
                elif section == "preferred":
                    kind, weight = "preferred", base
                else:
                    kind, weight = "contextual", base

                matches = matcher.match(sentence)
                # A requirement naming concrete technologies is more actionable
                # than a generic one ("be a self-starter"), so nudge it up.
                if matches:
                    weight = min(1.0, weight + 0.08)

                profile.requirements.append(Requirement(
                    text=sentence, section=section, importance=round(weight, 3),
                    skills=tuple(sorted(matches)), kind=kind,
                ))

                for skill, match in matches.items():
                    # Only direct mentions define what the JD *asks for*; implied
                    # skills are evidence a candidate can offer, not a demand.
                    if match.method not in {"exact", "alias", "fuzzy"}:
                        continue
                    existing = profile.skill_demands.get(skill)
                    if existing is None:
                        profile.skill_demands[skill] = SkillDemand(
                            skill=skill, weight=weight, kind=kind if kind != "contextual" else "preferred",
                            category=graph.category(skill), evidence=sentence,
                        )
                    else:
                        existing.mentions += 1
                        if weight > existing.weight:
                            existing.weight, existing.evidence = weight, sentence
                        if kind == "must_have":
                            existing.kind = "must_have"

    # Repetition across a JD signals emphasis; cap so it cannot dominate.
    for demand in profile.skill_demands.values():
        demand.weight = round(min(1.0, demand.weight * (1 + 0.06 * (demand.mentions - 1))), 3)

    return profile


def analyze_jd_file(path, graph: SkillGraph | None = None) -> JobProfile:
    from .parsing import extract_text
    from pathlib import Path

    text, _ = extract_text(Path(path))
    return analyze_jd(text, graph=graph)
