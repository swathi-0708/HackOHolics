"""Resume/JD ingestion: raw bytes -> a structured :class:`Document`.

Real resume batches are messy, so parsing is deliberately forgiving:

* PDF, TXT and MD inputs, plus a DOCX reader that needs no third-party library.
* Section headers are matched fuzzily, so "EXPERINCE", "Work experience" and
  "PROFESSIONAL EXPERIENCE" all land in the same bucket.
* Nothing here is required to succeed: a resume with no recognizable sections
  still yields usable full text, and section weighting simply falls back to 1.0.
"""
from __future__ import annotations

import difflib
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from .normalize import clean_line, normalize, split_sentences

SUPPORTED_SUFFIXES = {".pdf", ".txt", ".md", ".docx"}

# Canonical section -> header spellings we expect to see.
_SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "summary": ("summary", "professional summary", "career objective", "objective",
                "about me", "profile", "career summary", "personal statement"),
    "skills": ("skills", "technical skills", "technical skill", "key skills", "core competencies",
               "skills and technologies", "technologies", "tech stack", "areas of expertise",
               "technical proficiency", "tools and technologies", "computer skills"),
    "experience": ("experience", "work experience", "professional experience", "employment",
                   "employment history", "internship", "internships", "internship experience",
                   "work history", "relevant experience", "industrial training"),
    "projects": ("projects", "academic projects", "personal projects", "key projects",
                 "project work", "selected projects", "project experience", "major projects",
                 "mini projects"),
    "education": ("education", "academic background", "academics", "qualifications",
                  "educational qualifications", "academic qualification", "education details"),
    "certifications": ("certifications", "certification", "courses", "certifications and courses",
                       "online courses", "training", "licenses"),
    "achievements": ("achievements", "awards", "accomplishments", "honors", "awards and achievements",
                     "extracurricular", "activities", "positions of responsibility", "co curricular"),
    "publications": ("publications", "papers", "research", "research papers"),
    "links": ("links", "profiles", "portfolio", "social", "online presence"),
}

# Requirement-bearing sections carry more signal than boilerplate, and this
# weighting is applied when a match's provenance is scored.
SECTION_WEIGHTS: dict[str, float] = {
    "skills": 1.0,
    "experience": 1.25,
    "projects": 1.15,
    "summary": 0.9,
    "certifications": 0.8,
    "education": 0.7,
    "achievements": 0.7,
    "publications": 0.7,
    "links": 0.3,
    "other": 0.85,
}

_HEADER_TO_SECTION = {alias: section for section, aliases in _SECTION_ALIASES.items() for alias in aliases}
_ALL_HEADERS = tuple(_HEADER_TO_SECTION)

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]{2,}")
_PHONE = re.compile(r"(?:\+\d{1,3}[\s-]?)?(?:\(?\d{3,5}\)?[\s.-]?)\d{3}[\s.-]?\d{4}\b")
_URL = re.compile(r"(?:https?://|www\.)\S+|(?:github|linkedin|gitlab)\.com/\S+", re.I)
_PAGE_NOISE = re.compile(r"^(page\s*\d+(\s*(of|/)\s*\d+)?|\d+\s*/\s*\d+|-\s*\d+\s*-)$", re.I)

# Date-range forms seen in the wild: "Jan 2023 - Mar 2023", "2022-2024",
# "06/2021 to present", "Summer '23".
_MONTHS = ("jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec")
_DATE_RANGE = re.compile(
    rf"((?:{_MONTHS})[a-z]*\.?\s*'?\d{{2,4}}|\d{{1,2}}[/-]\d{{4}}|\d{{4}})"
    rf"\s*(?:-|–|—|to|until|through)\s*"
    rf"((?:{_MONTHS})[a-z]*\.?\s*'?\d{{2,4}}|\d{{1,2}}[/-]\d{{4}}|\d{{4}}|present|current|now|ongoing|date)",
    re.I,
)
_YEARS_PHRASE = re.compile(
    r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:professional\s*|relevant\s*|hands[\s-]?on\s*)?"
    r"(?:work\s*)?(?:experience|exp\b)",
    re.I,
)
_MONTHS_PHRASE = re.compile(r"(\d{1,2})\s*\+?\s*months?\s*(?:of\s*)?(?:internship|experience|exp\b)", re.I)

_DEGREE_LEVELS: tuple[tuple[str, int], ...] = (
    ("phd", 4), ("ph d", 4), ("doctorate", 4),
    ("m tech", 3), ("mtech", 3), ("m e ", 3), ("m sc", 3), ("msc", 3), ("mca", 3),
    ("master", 3), ("mba", 3), ("ms in", 3),
    ("b tech", 2), ("btech", 2), ("b e ", 2), ("be in", 2), ("bachelor", 2),
    ("b sc", 2), ("bsc", 2), ("bca", 2), ("b s ", 2), ("bs in", 2), ("b com", 2),
    ("diploma", 1), ("polytechnic", 1),
)
_CS_FIELDS = ("computer science", "computer engineering", "information technology", "software engineering",
              "computer application", "information science", "data science", "electronics and communication",
              "artificial intelligence", "cse", "it engineering")


@dataclass
class Document:
    """A parsed resume or job description."""

    doc_id: str
    path: str
    raw_text: str
    sections: dict[str, str] = field(default_factory=dict)
    candidate_name: str = ""
    email: str = ""
    phone: str = ""
    links: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        return self.candidate_name or self.doc_id

    @property
    def normalized_text(self) -> str:
        return normalize(self.raw_text)

    def section_text(self, name: str) -> str:
        return self.sections.get(name, "")

    def chunks(self, min_len: int = 12) -> list[tuple[str, str]]:
        """``(section, sentence)`` units used as the retrieval granularity.

        Matching per chunk instead of per document is what stops a long,
        unfocused resume from out-scoring a short, precisely relevant one.
        """
        out: list[tuple[str, str]] = []
        seen: set[str] = set()
        for section, text in (self.sections or {"other": self.raw_text}).items():
            if section == "links":
                continue
            for sentence in split_sentences(text):
                if len(sentence) < min_len:
                    continue
                key = normalize(sentence)
                if key and key not in seen:
                    seen.add(key)
                    out.append((section, sentence))
        return out

    def years_experience(self) -> float:
        return estimate_years_experience(self)

    def degree_level(self) -> int:
        """0 none/unknown, 1 diploma, 2 bachelor, 3 master, 4 doctorate."""
        text = normalize(self.section_text("education") or self.raw_text)
        return max((level for token, level in _DEGREE_LEVELS if token.strip() in text), default=0)

    def is_cs_field(self) -> bool:
        text = normalize(self.section_text("education") or self.raw_text)
        return any(field_name in text for field_name in _CS_FIELDS)


# ---------------------------------------------------------------------------
# text extraction
# ---------------------------------------------------------------------------
def _extract_pdf(path: Path) -> tuple[str, list[str]]:
    warnings: list[str] = []
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "PDF support needs PyMuPDF. Install it with `pip install PyMuPDF`, "
            "or convert the file to .txt."
        ) from exc

    pages: list[str] = []
    with fitz.open(path) as pdf:
        for page in pdf:
            # "blocks" keeps multi-column layouts from interleaving mid-sentence.
            blocks = page.get_text("blocks") or []
            if blocks:
                blocks.sort(key=lambda b: (round(b[1], 1), round(b[0], 1)))
                pages.append("\n".join(str(b[4]).strip() for b in blocks if str(b[4]).strip()))
            else:
                pages.append(page.get_text("text") or "")
    text = "\n".join(pages)
    if len(text.strip()) < 80:
        warnings.append("Very little text extracted - the PDF may be a scan needing OCR.")
    return text, warnings


def _extract_docx(path: Path) -> tuple[str, list[str]]:
    """Read DOCX paragraph text straight from the OOXML, no python-docx needed."""
    try:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml").decode("utf-8", "ignore")
    except (KeyError, zipfile.BadZipFile) as exc:
        return "", [f"Could not read DOCX ({exc})."]
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<w:tab[^>]*/>", "\t", xml)
    text = re.sub(r"<[^>]+>", "", xml)
    return re.sub(r"&amp;", "&", text), []


def extract_text(path: Path) -> tuple[str, list[str]]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf(path)
    if suffix == ".docx":
        return _extract_docx(path)
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="replace"), []
    raise ValueError(f"Unsupported file type: {path.name}")


# ---------------------------------------------------------------------------
# structure recovery
# ---------------------------------------------------------------------------
def _match_header(line: str) -> str | None:
    """Return the canonical section for a header-looking line, else ``None``.

    Uses fuzzy matching so misspelled headers ("EXPERINCE", "Skils") still bind.
    """
    stripped = clean_line(line).strip(" :|-—_·")
    if not stripped or len(stripped) > 45:
        return None
    words = stripped.split()
    if len(words) > 5:
        return None
    # Real headers are not sentences and rarely end in punctuation.
    if stripped.endswith((".", ",", ";")):
        return None
    key = normalize(stripped)
    if not key:
        return None
    if key in _HEADER_TO_SECTION:
        return _HEADER_TO_SECTION[key]

    looks_like_header = stripped.isupper() or stripped.istitle() or line.rstrip().endswith(":")
    if not looks_like_header:
        return None
    close = difflib.get_close_matches(key, _ALL_HEADERS, n=1, cutoff=0.86)
    return _HEADER_TO_SECTION[close[0]] if close else None


def segment_sections(text: str) -> dict[str, str]:
    """Split resume text into canonical sections.

    Content before the first recognized header (name, contact details, a summary
    with no heading) is kept under ``"other"`` so nothing is silently dropped.
    """
    buckets: dict[str, list[str]] = {}
    current = "other"
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or _PAGE_NOISE.match(line.strip()):
            continue
        section = _match_header(line)
        if section:
            current = section
            # A header like "Skills: Python, SQL" carries content on the same line.
            inline = line.split(":", 1)[1].strip() if ":" in line else ""
            if inline:
                buckets.setdefault(current, []).append(inline)
            continue
        buckets.setdefault(current, []).append(clean_line(line))
    return {name: "\n".join(lines).strip() for name, lines in buckets.items() if any(lines)}


def _guess_name(text: str, fallback: str) -> str:
    """Take the first plausible person-name line from the header block."""
    for raw_line in text.splitlines()[:12]:
        line = clean_line(raw_line)
        if not line or len(line) > 48:
            continue
        if _EMAIL.search(line) or _URL.search(line) or _PHONE.search(line):
            continue
        if _match_header(line):
            continue
        words = [w for w in re.split(r"\s+", line) if w]
        if not 1 < len(words) <= 4:
            continue
        letters = re.sub(r"[^A-Za-z]", "", line)
        if len(letters) < 4:
            continue
        # Reject job titles and objective lines that also sit near the top.
        if re.search(r"\b(resume|curriculum|vitae|cv|engineer|developer|intern|student|seeking)\b",
                     line, re.I):
            continue
        if all(w[:1].isupper() or w.isupper() for w in words):
            return " ".join(w if w.isupper() and len(w) <= 3 else w.title() for w in words)
    return _humanize(fallback)


def _humanize(stem: str) -> str:
    cleaned = re.sub(r"[_\-]+", " ", re.sub(r"(?i)\b(resume|cv|final|updated|v\d+)\b", " ", stem))
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned.title() or stem


def _month_index(token: str) -> int | None:
    token = token.strip().lower()
    for i, m in enumerate(_MONTHS.split("|")):
        if token.startswith(m):
            return min(i, 11) if m != "sept" else 8
    return None


def _to_months(token: str) -> int | None:
    """Convert one endpoint of a date range to an absolute month count."""
    token = token.strip().lower().replace(".", "")
    if re.match(r"present|current|now|ongoing|date", token):
        return 2026 * 12 + 8  # anchored to the current date (Sep 2026)
    slash = re.match(r"(\d{1,2})[/-](\d{4})", token)
    if slash:
        month, year = int(slash.group(1)), int(slash.group(2))
        return year * 12 + max(0, min(11, month - 1))
    with_month = re.match(rf"({_MONTHS})[a-z]*\s*'?(\d{{2,4}})", token)
    if with_month:
        month_idx = _month_index(with_month.group(1)) or 0
        year = int(with_month.group(2))
        year += 2000 if year < 100 else 0
        return year * 12 + month_idx
    plain_year = re.match(r"(\d{4})$", token)
    if plain_year:
        return int(plain_year.group(1)) * 12
    return None


def estimate_years_experience(doc: Document) -> float:
    """Best-effort professional/internship experience in years.

    Prefers an explicit claim ("2 years of experience"), otherwise sums the
    non-overlapping date ranges found in experience-like sections. Education-only
    date ranges are excluded so a 4-year degree is not read as 4 years of work.
    """
    text = doc.raw_text
    explicit = [float(m.group(1)) for m in _YEARS_PHRASE.finditer(text)]
    if explicit:
        return min(max(explicit), 45.0)

    scope = "\n".join(doc.section_text(s) for s in ("experience", "projects", "summary", "other")) or text
    intervals: list[tuple[int, int]] = []
    for match in _DATE_RANGE.finditer(scope):
        start, end = _to_months(match.group(1)), _to_months(match.group(2))
        if start is None or end is None or end < start:
            continue
        span = end - start
        if span > 12 * 12:  # implausible for a resume; likely a parse artifact
            continue
        intervals.append((start, end))

    months_phrase = [int(m.group(1)) for m in _MONTHS_PHRASE.finditer(text)]

    if not intervals:
        return round(max(months_phrase, default=0) / 12.0, 2)

    intervals.sort()
    merged: list[list[int]] = [list(intervals[0])]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    total_months = max(sum(e - s for s, e in merged), max(months_phrase, default=0))
    return round(min(total_months / 12.0, 45.0), 2)


def parse_document(path: str | Path, doc_id: str | None = None) -> Document:
    path = Path(path)
    text, warnings = extract_text(path)
    if not text.strip():
        warnings.append("No text could be extracted from this file.")

    sections = segment_sections(text)
    doc = Document(
        doc_id=doc_id or path.stem,
        path=str(path),
        raw_text=text,
        sections=sections,
        warnings=warnings,
    )
    doc.candidate_name = _guess_name(text, path.stem)
    emails = _EMAIL.findall(text)
    doc.email = emails[0] if emails else ""
    phones = _PHONE.findall(text)
    doc.phone = phones[0].strip() if phones else ""
    doc.links = sorted({u.rstrip(").,") for u in _URL.findall(text)})

    if not sections or set(sections) == {"other"}:
        doc.warnings.append("No section headers recognized - scored on full text only.")
    if "skills" not in sections:
        doc.warnings.append("No explicit skills section found.")
    return doc


def load_batch(folder: str | Path) -> list[Document]:
    """Parse every supported file in ``folder``, sorted by filename.

    One unreadable resume must not abort a batch, so failures are recorded as a
    warning on an otherwise empty document.
    """
    folder = Path(folder)
    if not folder.is_dir():
        raise NotADirectoryError(f"Not a directory: {folder}")
    docs: list[Document] = []
    for path in sorted(folder.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
            try:
                docs.append(parse_document(path))
            except Exception as exc:  # noqa: BLE001 - keep the batch alive
                docs.append(Document(doc_id=path.stem, path=str(path), raw_text="",
                                     warnings=[f"Failed to parse: {exc}"]))
    return docs
