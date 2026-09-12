"""
ui_generator.py
-----------------
Renders the pipeline's results dict into a single self-contained HTML file:
ranked candidate list, expandable evidence per candidate, LLM explanations
for the top N, and a client-side "prestige-neutral scoring" toggle (the
Score Fusion module already computed both versions, so the toggle just
re-sorts/re-displays using data already embedded in the page — no server
or re-computation needed).
"""

from __future__ import annotations
import json

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Resume Match Report — {{JD_TITLE}}</title>
<style>
  :root {
    --bg: #0f1115; --panel: #171a21; --panel2: #1e222b; --border: #2a2f3a;
    --text: #e8eaed; --muted: #9aa2b1; --accent: #6ea8ff; --good: #4ade80;
    --mid: #fbbf24; --bad: #f87171;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: var(--bg); color: var(--text); line-height: 1.5;
  }
  .wrap { max-width: 920px; margin: 0 auto; padding: 32px 20px 80px; }
  header { margin-bottom: 24px; }
  h1 { font-size: 22px; margin: 0 0 4px; }
  .sub { color: var(--muted); font-size: 14px; }
  .toolbar {
    display: flex; align-items: center; gap: 12px; margin: 20px 0 24px;
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
    padding: 12px 16px; font-size: 14px;
  }
  .toggle {
    display: inline-flex; align-items: center; gap: 8px; cursor: pointer; user-select: none;
  }
  .switch {
    width: 38px; height: 22px; border-radius: 11px; background: #333a47;
    position: relative; transition: background .15s;
  }
  .switch::after {
    content: ""; position: absolute; width: 18px; height: 18px; border-radius: 50%;
    background: #fff; top: 2px; left: 2px; transition: left .15s;
  }
  input[type=checkbox] { display: none; }
  input[type=checkbox]:checked + .switch { background: var(--accent); }
  input[type=checkbox]:checked + .switch::after { left: 18px; }
  .note { color: var(--muted); font-size: 12px; }
  .card {
    background: var(--panel); border: 1px solid var(--border); border-radius: 12px;
    padding: 18px 20px; margin-bottom: 14px;
  }
  .card.top3 { border-color: var(--accent); }
  .row { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
  .name { font-size: 17px; font-weight: 600; }
  .rank-badge {
    display: inline-block; font-size: 12px; font-weight: 700; color: var(--bg);
    background: var(--accent); border-radius: 20px; padding: 2px 10px; margin-right: 8px;
  }
  .score { font-size: 24px; font-weight: 700; }
  .score.good { color: var(--good); } .score.mid { color: var(--mid); } .score.bad { color: var(--bad); }
  .score-sub { font-size: 12px; color: var(--muted); text-align: right; }
  .penalty-note { color: var(--bad); font-size: 11px; margin-top: 3px; text-align: right; }
  .skills { margin-top: 10px; font-size: 13px; }
  .pill {
    display: inline-block; padding: 2px 9px; border-radius: 14px; margin: 3px 4px 0 0;
    font-size: 12px; border: 1px solid var(--border);
  }
  .pill.matched { background: rgba(74,222,128,.12); color: var(--good); border-color: rgba(74,222,128,.3); }
  .pill.missing { background: rgba(248,113,113,.1); color: var(--bad); border-color: rgba(248,113,113,.3); }
  .label { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .04em; margin-top: 12px; }
  .explanation { margin-top: 10px; font-size: 14px; color: #dfe3ea; background: var(--panel2);
    border-radius: 8px; padding: 10px 12px; border: 1px solid var(--border); }
  details { margin-top: 10px; }
  summary { cursor: pointer; color: var(--accent); font-size: 13px; }
  .bullets { margin: 8px 0 0 18px; font-size: 13px; color: #cfd4dd; }
  .exp-line { font-size: 13px; color: var(--muted); margin-top: 6px; }
  .jd-box { font-size: 13px; color: var(--muted); }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Resume Match Report</h1>
    <div class="sub">Role: <strong style="color:var(--text)">{{JD_TITLE}}</strong></div>
    <div class="jd-box">Required: {{JD_REQUIRED}} &nbsp;·&nbsp; Preferred: {{JD_PREFERRED}}{{JD_YEARS}}</div>
  </header>

  <div class="toolbar">
    <label class="toggle">
      <input type="checkbox" id="prestigeToggle" onchange="renderAll()">
      <span class="switch"></span>
      Prestige-neutral scoring
    </label>
    <span class="note">Recomputes fit using scores with well-known employer/university names removed from the semantic match, to reduce pedigree-driven bias. Skill matching is unaffected either way.</span>
  </div>

  <div id="list"></div>
</div>

<script>
const DATA = {{DATA_JSON}};

function scoreClass(v) { return v >= 75 ? "good" : v >= 50 ? "mid" : "bad"; }

function pillList(items, cls) {
  if (!items.length) return '<span class="note">none</span>';
  return items.map(s => `<span class="pill ${cls}">${s}</span>`).join("");
}

function renderAll() {
  const neutral = document.getElementById('prestigeToggle').checked;
  const candidates = [...DATA.candidates];
  candidates.sort((a, b) => {
    const av = neutral ? a.prestige_neutral_overall_score : a.fused_score.overall_score;
    const bv = neutral ? b.prestige_neutral_overall_score : b.fused_score.overall_score;
    return bv - av;
  });

  const listEl = document.getElementById('list');
  listEl.innerHTML = candidates.map((c, idx) => {
    const displayScore = neutral ? c.prestige_neutral_overall_score : c.fused_score.overall_score;
    const isTop = idx < DATA.top_n;
    const explanation = DATA.explanations[c.filename];
    let expLine = "";
    if (c.years_of_experience !== null && c.years_of_experience !== undefined) {
      let bar = "";
      if (c.meets_experience_bar === true) bar = " — meets JD minimum";
      else if (c.meets_experience_bar === false) bar = " — below JD minimum";
      expLine = `<div class="exp-line">Est. experience: ~${c.years_of_experience} yrs${bar}</div>`;
    }
    const bullets = (c.sample_bullets || []).map(b => `<li>${b}</li>`).join("");
    const penalty = c.fused_score.missing_required_penalty || 0;
    const penaltyNote = penalty > 0
      ? `<div class="penalty-note">&minus;${Math.round(penalty * 100)}% required-skill penalty (${c.fused_score.missing_required_count} missing)</div>`
      : "";
    return `
      <div class="card ${isTop ? 'top3' : ''}">
        <div class="row">
          <div>
            <span class="rank-badge">#${idx + 1}</span>
            <span class="name">${c.candidate_name}</span>
            ${c.email ? `<div class="note">${c.email}</div>` : ""}
          </div>
          <div>
            <div class="score ${scoreClass(displayScore)}">${displayScore.toFixed(1)}</div>
            <div class="score-sub">keyword ${c.fused_score.keyword_score} · semantic ${c.fused_score.semantic_score}</div>
            ${penaltyNote}
          </div>
        </div>
        ${expLine}
        <div class="skills">
          <div class="label">Matched required</div>
          ${pillList(c.matched_required, 'matched')}
          <div class="label">Matched preferred</div>
          ${pillList(c.matched_preferred, 'matched')}
          <div class="label">Missing required</div>
          ${pillList(c.missing_required, 'missing')}
          <div class="label">Missing preferred</div>
          ${pillList(c.missing_preferred, 'missing')}
        </div>
        ${explanation ? `<div class="explanation">${explanation}</div>` : ""}
        ${bullets ? `<details><summary>Sample resume evidence</summary><ul class="bullets">${bullets}</ul></details>` : ""}
      </div>`;
  }).join("");
}

renderAll();
</script>
</body>
</html>
"""


def generate_html_report(results: dict, out_path: str) -> None:
    jd_required = ", ".join(results["jd_required_skills"]) or "none detected"
    jd_preferred = ", ".join(results["jd_preferred_skills"]) or "none detected"
    jd_years = (
        f" &nbsp;·&nbsp; Min. years: {results['jd_min_years_experience']}"
        if results.get("jd_min_years_experience") is not None
        else ""
    )

    html = (
        HTML_TEMPLATE
        .replace("{{JD_TITLE}}", results["jd_title"])
        .replace("{{JD_REQUIRED}}", jd_required)
        .replace("{{JD_PREFERRED}}", jd_preferred)
        .replace("{{JD_YEARS}}", jd_years)
        .replace("{{DATA_JSON}}", json.dumps(results))
    )

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)