"""Render pipeline results into a warm, heart-accented HTML report."""

from __future__ import annotations

import json


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Resume Match Report — {{JD_TITLE}}</title>
<style>
  :root {
    --bordeaux: #6C151E;
    --green: #0F3D3A;
    --cream: #F5DABF;
    --paper: #fff4e6;
    --ink: #32161a;
    --muted: #765c54;
    --rose: #b74f5b;
    --line: rgba(108, 21, 30, .18);
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; min-height: 100vh; overflow-x: hidden;
    font-family: "Trebuchet MS", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: var(--paper); color: var(--ink); line-height: 1.5;
  }
  body::before, body::after {
    content: "♥"; position: fixed; z-index: -1; pointer-events: none;
    font-family: Georgia, serif; color: rgba(108, 21, 30, .09); line-height: 1;
  }
  body::before { font-size: clamp(190px, 28vw, 410px); top: -80px; right: -50px; transform: rotate(14deg); }
  body::after { font-size: clamp(160px, 24vw, 330px); bottom: -95px; left: -60px; color: rgba(15, 61, 58, .1); transform: rotate(-18deg); }
  .wrap { max-width: 920px; margin: 0 auto; padding: 52px 20px 80px; }
  header { position: relative; margin-bottom: 24px; padding: 28px 30px; border-radius: 22px; color: var(--cream); background: var(--bordeaux); box-shadow: 0 14px 34px rgba(70, 19, 24, .22); overflow: hidden; }
  header::after { content: "♥"; position: absolute; right: 26px; top: -35px; color: rgba(245, 218, 191, .18); font: 150px Georgia, serif; }
  h1 { position: relative; z-index: 1; margin: 0 0 4px; font-size: clamp(25px, 4vw, 36px); letter-spacing: -.04em; }
  .sub { position: relative; z-index: 1; color: rgba(245, 218, 191, .82); font-size: 14px; }
  .sub strong { color: var(--cream); }
  .jd-box { position: relative; z-index: 1; margin-top: 12px; color: rgba(245, 218, 191, .78); font-size: 13px; }
  .toolbar { display: flex; align-items: center; gap: 12px; margin: 20px 0 24px; padding: 15px 18px; border: 1px solid var(--line); border-radius: 16px; background: var(--cream); box-shadow: 0 8px 22px rgba(75, 39, 32, .08); font-size: 14px; }
  .toggle { display: inline-flex; flex: 0 0 auto; align-items: center; gap: 8px; cursor: pointer; color: var(--green); font-weight: 700; user-select: none; }
  .switch { width: 42px; height: 24px; position: relative; border-radius: 14px; background: #c9a997; transition: background .15s; }
  .switch::after { content: ""; position: absolute; top: 3px; left: 3px; width: 18px; height: 18px; border-radius: 50%; background: var(--paper); box-shadow: 0 1px 3px rgba(0,0,0,.18); transition: left .15s; }
  input[type=checkbox] { display: none; }
  input[type=checkbox]:checked + .switch { background: var(--green); }
  input[type=checkbox]:checked + .switch::after { left: 21px; }
  .note { color: var(--muted); font-size: 12px; }
  .card { position: relative; margin-bottom: 14px; padding: 19px 21px; border: 1px solid var(--line); border-radius: 18px; background: rgba(255, 244, 230, .94); box-shadow: 0 8px 22px rgba(75, 39, 32, .07); }
  .card.top3 { border-color: var(--green); border-width: 2px; }
  .card.top3::after { content: "♥"; position: absolute; right: 17px; bottom: 10px; color: rgba(108, 21, 30, .12); font: 45px Georgia, serif; }
  .row { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
  .name { font-size: 17px; font-weight: 700; color: var(--bordeaux); }
  .rank-badge { display: inline-block; margin-right: 8px; padding: 3px 10px; border-radius: 20px; background: var(--green); color: var(--cream); font-size: 12px; font-weight: 700; }
  .score { font-size: 25px; font-weight: 800; color: var(--bordeaux); }
  .score.good { color: var(--green); } .score.mid { color: #ae6515; } .score.bad { color: var(--bordeaux); }
  .score-sub { color: var(--muted); font-size: 12px; text-align: right; }
  .skills { margin-top: 10px; font-size: 13px; }
  .pill { display: inline-block; margin: 3px 4px 0 0; padding: 3px 9px; border: 1px solid var(--line); border-radius: 14px; font-size: 12px; }
  .pill.matched { border-color: rgba(15, 61, 58, .28); background: rgba(15, 61, 58, .1); color: var(--green); }
  .pill.missing { border-color: rgba(108, 21, 30, .25); background: rgba(108, 21, 30, .08); color: var(--bordeaux); }
  .label { margin-top: 12px; color: var(--muted); font-size: 11px; letter-spacing: .08em; text-transform: uppercase; }
  .explanation { margin-top: 10px; padding: 11px 13px; border: 1px solid rgba(15, 61, 58, .16); border-radius: 11px; background: rgba(15, 61, 58, .08); color: var(--green); font-size: 14px; }
  details { margin-top: 10px; } summary { cursor: pointer; color: var(--bordeaux); font-size: 13px; font-weight: 700; } .bullets { margin: 8px 0 0 18px; color: var(--muted); font-size: 13px; } .exp-line { margin-top: 6px; color: var(--muted); font-size: 13px; }
  @media (max-width: 600px) { .wrap { padding: 28px 14px 60px; } header { padding: 24px 21px; } .toolbar { align-items: flex-start; flex-direction: column; } }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Resume Match Report</h1>
    <div class="sub">Role: <strong>{{JD_TITLE}}</strong></div>
    <div class="jd-box">Required: {{JD_REQUIRED}} &nbsp;·&nbsp; Preferred: {{JD_PREFERRED}}{{JD_YEARS}}</div>
  </header>
  <div class="toolbar">
    <label class="toggle"><input type="checkbox" id="prestigeToggle" onchange="renderAll()"><span class="switch"></span>Prestige-neutral scoring</label>
    <span class="note">Recomputes fit using scores with well-known employer/university names removed from the semantic match, to reduce pedigree-driven bias. Skill matching is unaffected either way.</span>
  </div>
  <div id="list"></div>
</div>
<script>
const DATA = {{DATA_JSON}};
function scoreClass(v) { return v >= 75 ? "good" : v >= 50 ? "mid" : "bad"; }
function pillList(items, cls) { if (!items.length) return '<span class="note">none</span>'; return items.map(s => `<span class="pill ${cls}">${s}</span>`).join(""); }
function renderAll() {
  const neutral = document.getElementById('prestigeToggle').checked;
  const candidates = [...DATA.candidates];
  candidates.sort((a, b) => (neutral ? b.prestige_neutral_overall_score : b.fused_score.overall_score) - (neutral ? a.prestige_neutral_overall_score : a.fused_score.overall_score));
  document.getElementById('list').innerHTML = candidates.map((c, idx) => {
    const score = neutral ? c.prestige_neutral_overall_score : c.fused_score.overall_score, explanation = DATA.explanations[c.filename];
    const exp = c.years_of_experience == null ? "" : `<div class="exp-line">Est. experience: ~${c.years_of_experience} yrs${c.meets_experience_bar === true ? " — meets JD minimum" : c.meets_experience_bar === false ? " — below JD minimum" : ""}</div>`;
    const bullets = (c.sample_bullets || []).map(b => `<li>${b}</li>`).join("");
    return `<div class="card ${idx < DATA.top_n ? 'top3' : ''}"><div class="row"><div><span class="rank-badge">#${idx + 1}</span><span class="name">${c.candidate_name}</span>${c.email ? `<div class="note">${c.email}</div>` : ""}</div><div><div class="score ${scoreClass(score)}">${score.toFixed(1)}</div><div class="score-sub">keyword ${c.fused_score.keyword_score} · semantic ${c.fused_score.semantic_score}</div></div></div>${exp}<div class="skills"><div class="label">Matched required</div>${pillList(c.matched_required, 'matched')}<div class="label">Matched preferred</div>${pillList(c.matched_preferred, 'matched')}<div class="label">Missing required</div>${pillList(c.missing_required, 'missing')}<div class="label">Missing preferred</div>${pillList(c.missing_preferred, 'missing')}</div>${explanation ? `<div class="explanation">${explanation}</div>` : ""}${bullets ? `<details><summary>Sample resume evidence</summary><ul class="bullets">${bullets}</ul></details>` : ""}</div>`;
  }).join("");
}
renderAll();
</script>
</body>
</html>"""


def generate_html_report(results: dict, out_path: str) -> None:
    jd_required = ", ".join(results["jd_required_skills"]) or "none detected"
    jd_preferred = ", ".join(results["jd_preferred_skills"]) or "none detected"
    jd_years = f" &nbsp;·&nbsp; Min. years: {results['jd_min_years_experience']}" if results.get("jd_min_years_experience") is not None else ""
    html = (HTML_TEMPLATE.replace("{{JD_TITLE}}", results["jd_title"]).replace("{{JD_REQUIRED}}", jd_required).replace("{{JD_PREFERRED}}", jd_preferred).replace("{{JD_YEARS}}", jd_years).replace("{{DATA_JSON}}", json.dumps(results)))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
