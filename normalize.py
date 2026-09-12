"""Text normalization shared by the keyword and semantic lanes.

Resumes are messy: "Node.js", "NodeJS", "node js" and "nodejs" all mean the same
thing, and typos ("Javscript") are common. Everything downstream therefore works
on a single canonical surface form produced here.
"""
from __future__ import annotations

import re
import unicodedata

# Symbol-bearing technology names must survive punctuation stripping, so they are
# rewritten to alphanumeric tokens *before* the generic cleanup runs.
_SYMBOL_TOKENS = [
    (r"c\+\+", " cpp "),
    (r"c#", " csharp "),
    (r"f#", " fsharp "),
    (r"objective-c", " objectivec "),
    (r"\.net", " dotnet "),
    (r"node\.js", " nodejs "),
    (r"next\.js", " nextjs "),
    (r"nuxt\.js", " nuxtjs "),
    (r"nest\.js", " nestjs "),
    (r"express\.js", " expressjs "),
    (r"vue\.js", " vuejs "),
    (r"react\.js", " reactjs "),
    (r"d3\.js", " d3js "),
    (r"three\.js", " threejs "),
    (r"socket\.io", " socketio "),
    (r"ci/cd", " cicd "),
    (r"\bci\s*&\s*cd\b", " cicd "),
    (r"front[\s\-]?end", " frontend "),
    (r"back[\s\-]?end", " backend "),
    (r"full[\s\-]?stack", " fullstack "),
    (r"rest[\s\-]?ful", " rest "),
    (r"api['’]?s\b", " api "),
    (r"\bre-?act\b", " react "),
]

_WS = re.compile(r"\s+")
_NON_WORD = re.compile(r"[^a-z0-9+#]+")
_BULLET = re.compile(r"^[\s•●▪‣⁃\-\*·o]+")

# Light, dependency-free stemming. Full lemmatization would need NLTK/spaCy; for
# skill and requirement text these five rules cover the realistic variation
# ("developing" -> "develop", "APIs" -> "api", "deployed" -> "deploy").
_SUFFIXES = ("ing", "edly", "ed", "es", "s", "ly")


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize(text: str) -> str:
    """Lowercase, fold symbol-bearing tech names, drop punctuation."""
    text = strip_accents(text or "").lower()
    text = text.replace("’", "'").replace("–", "-").replace("—", "-")
    for pattern, repl in _SYMBOL_TOKENS:
        text = re.sub(pattern, repl, text)
    text = _NON_WORD.sub(" ", text)
    return _WS.sub(" ", text).strip()


def stem(token: str) -> str:
    """Crude suffix stripping; never shortens a token below 4 characters."""
    for suffix in _SUFFIXES:
        if len(token) - len(suffix) >= 4 and token.endswith(suffix):
            return token[: -len(suffix)]
    return token


def tokenize(text: str, do_stem: bool = False) -> list[str]:
    tokens = normalize(text).split()
    return [stem(t) for t in tokens] if do_stem else tokens


def ngrams(tokens: list[str], max_n: int = 4):
    """Yield ``(start_index, n, " ".join(window))`` for n = max_n .. 1.

    Longest-first so that "amazon web services" is consumed before "amazon".
    """
    for n in range(max_n, 0, -1):
        for i in range(len(tokens) - n + 1):
            yield i, n, " ".join(tokens[i : i + n])


def clean_line(line: str) -> str:
    """Strip bullet glyphs and collapse whitespace, preserving original casing."""
    return _WS.sub(" ", _BULLET.sub("", line)).strip()


def split_sentences(text: str) -> list[str]:
    """Segment into sentence-ish units.

    Resume bullets frequently lack terminal punctuation, so newlines are treated
    as hard boundaries and only then is each line split on sentence enders.
    """
    units: list[str] = []
    for raw_line in (text or "").splitlines():
        line = clean_line(raw_line)
        if not line:
            continue
        for piece in re.split(r"(?<=[.!?;])\s+(?=[A-Z(])", line):
            piece = piece.strip(" .;•-")
            if len(piece) >= 3:
                units.append(piece)
    return units
