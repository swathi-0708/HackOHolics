"""
text_normalize.py
------------------
Shared text normalization used by skill_taxonomy.py before skill matching.

Resumes and JDs write the same technology many different ways: "Node.js",
"NodeJS", "node js", "nodejs" all mean the same thing, and symbol-bearing
names ("C++", "C#") get mangled by naive punctuation stripping. This module
folds those variants into one alphanumeric surface form BEFORE alias/regex
matching runs, so the taxonomy's alias lists don't need to enumerate every
punctuation variant by hand.

Ported from the project's earlier standalone prototype (root-level
normalize.py) and adapted to fold into the resume_matcher package.
"""

from __future__ import annotations
import re
import unicodedata

# Symbol-bearing technology names must survive punctuation stripping, so they
# are rewritten to alphanumeric tokens *before* generic cleanup runs.
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
    (r"api['\u2019]?s\b", " api "),
]

_WS = re.compile(r"\s+")
_NON_WORD = re.compile(r"[^a-z0-9+#]+")


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize_text(text: str) -> str:
    """Lowercase, fold symbol-bearing tech names, drop punctuation."""
    text = strip_accents(text or "").lower()
    text = text.replace("\u2019", "'").replace("\u2013", "-").replace("\u2014", "-")
    for pattern, repl in _SYMBOL_TOKENS:
        text = re.sub(pattern, repl, text)
    text = _NON_WORD.sub(" ", text)
    return _WS.sub(" ", text).strip()