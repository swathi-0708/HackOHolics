"""Render an employer-friendly, interactive resume-shortlisting report.

Two-page flow: an intake stage (job description + resumes) and a report
stage (ranked list / comparison / role details), styled as a navy-and-gold
Pantone-chip system. Brand mark is a single circle-and-tick logo (also used
as the page favicon), with "Shortlist" as the large wordmark and the task
description set smaller beneath it.

Candidate dicts may optionally include:
    prestige_signal_detected: bool
        True when resume_matcher's semantic_engine.strip_prestige_signals()
        found a well-known school/employer name-string in this candidate's
        resume text. Purely informational for the UI's "notable school /
        employer" tag — it must NOT be folded into fused_score. Ranking
        should already come from scoring with prestige_neutral=True so the
        rank order stays skills-based; this tag is a separate, non-scoring
        display signal only.
"""
from __future__ import annotations
import json

HTML_TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Shortlist — {{JD_TITLE}}</title>
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Ccircle cx='12' cy='12' r='11' fill='%23c9a869'/%3E%3Cpath d='M7 12.4l3.3 3.3L17.2 8.4' fill='none' stroke='%230f1b3c' stroke-width='2.3' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E">
<style>
:root{
  --navy:#0f1b3c;
  --gold:#c9a869;
  --gold-bright:#e4bd77;
  --cream:#f4efe4;
  --muted:#a6926b;
  --line:rgba(201,168,105,.38);
  --surface:rgba(244,239,228,.05);
  --surface-2:rgba(244,239,228,.09);
  --gold-surface:rgba(201,168,105,.13);
  --gold-surface-2:rgba(201,168,105,.22);
  --match:#9ad2a6;--match-bg:rgba(154,210,166,.14);
  --missing:#e3a68f;--missing-bg:rgba(227,166,143,.14);
}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;background:var(--navy);color:var(--cream);font:14px/1.5 "Segoe UI",Arial,sans-serif}
.stage{display:none}
.stage.active{display:block}

/* ---------- Stage 1: intake ---------- */
.landing.active{min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:26px;padding:64px 24px;text-align:center}
.hero-lockup{display:flex;align-items:center;gap:16px}
.hero-logo{width:46px;height:46px;flex:none}
.hero-logo-bg{fill:var(--gold)}
.hero-logo-tick{stroke:var(--navy)}
.hero-word{display:block;font:700 clamp(40px,7vw,68px)/1 Georgia,serif;color:var(--cream);letter-spacing:-.01em;text-align:left}
.hero-caption{display:block;margin-top:5px;color:var(--muted);font-size:13px;text-align:left}
.landing h1{margin:2px 0 0;max-width:480px;font:600 clamp(17px,2.1vw,21px)/1.4 "Segoe UI",Arial,sans-serif;color:var(--gold)}
.landing .lede{margin:0;max-width:460px;color:var(--muted)}
.intake-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px;width:100%;max-width:600px}
.intake-card{all:unset;cursor:pointer;display:flex;flex-direction:column;border:1px solid var(--line);border-radius:14px;overflow:hidden;transition:transform .15s ease,border-color .15s ease}
.intake-card:hover{transform:translateY(-2px);border-color:var(--gold)}
.intake-card.selected{border-color:var(--gold);box-shadow:0 0 0 1px var(--gold)}
.swatch-top{height:104px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;background:var(--navy)}
.intake-card.gold .swatch-top{background:var(--gold)}
.swatch-icon{width:26px;height:26px}
.swatch-icon path,.swatch-icon rect,.swatch-icon circle,.swatch-icon line{stroke:var(--gold)}
.intake-card.gold .swatch-icon path,.intake-card.gold .swatch-icon rect,.intake-card.gold .swatch-icon circle,.intake-card.gold .swatch-icon line{stroke:var(--navy)}
.swatch-code{font:600 11px/1 ui-monospace,Consolas,monospace;letter-spacing:.07em;color:var(--gold)}
.intake-card.gold .swatch-code{color:var(--navy)}
.swatch-label{background:var(--cream);color:var(--navy);padding:13px 15px;text-align:left}
.swatch-label strong{display:block;font:600 15px "Segoe UI",Arial,sans-serif}
.swatch-label span{display:block;margin-top:3px;font-size:12px;color:#5c5140}
.intake-detail{display:none;width:100%;max-width:600px;text-align:left;border:1px solid var(--line);border-radius:12px;padding:15px;background:var(--surface)}
.intake-detail.open{display:block}
.intake-detail textarea{width:100%;min-height:100px;background:var(--surface-2);border:1px solid var(--line);border-radius:8px;color:var(--cream);padding:10px;font:inherit;resize:vertical;outline:0}
.intake-detail textarea:focus{border-color:var(--gold)}
.filerow{display:flex;align-items:center;gap:10px;margin-top:10px;flex-wrap:wrap}
.filebtn{display:inline-flex;align-items:center;gap:8px;padding:9px 14px;border:1px dashed var(--line);border-radius:8px;color:var(--muted);cursor:pointer;font-size:13px}
.filebtn:hover{border-color:var(--gold);color:var(--cream)}
.filebtn input{display:none}
.filestatus{color:var(--muted);font-size:12px}
.start-button{margin-top:8px;padding:14px 34px;border:1px solid var(--gold);border-radius:10px;background:var(--gold);color:var(--navy);font-weight:800;cursor:pointer;font-size:15px}
.start-button:disabled{opacity:.35;cursor:not-allowed}
.start-hint{color:var(--muted);font-size:12px;margin-top:-14px}

/* ---------- Stage 2: report ---------- */
.app{display:grid;grid-template-columns:280px minmax(0,1fr);min-height:100vh;max-width:1500px;margin:auto;border-inline:1px solid var(--line)}
.sidebar{padding:34px 24px;background:var(--gold-surface);border-right:1px solid var(--line)}
.back-link{all:unset;cursor:pointer;display:inline-flex;align-items:center;gap:6px;margin-bottom:22px;color:var(--muted);font-size:12px;font-weight:700;letter-spacing:.04em}
.back-link:hover{color:var(--gold)}
.brand{display:flex;align-items:center;gap:10px;margin-bottom:30px}
.brand-logo{width:22px;height:22px;flex:none}
.brand-name{display:block;color:var(--gold);font:20px Georgia,serif}
.brand small{display:block;margin-top:3px;color:var(--muted);font:12px "Segoe UI",Arial,sans-serif}
.side-title,.filter-label{display:block;font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase}
.side-title{margin:24px 0 12px;color:var(--gold)}
.filter-group{margin-top:16px}
.filter-label{margin-bottom:7px;color:var(--muted);letter-spacing:.07em}
input[type=text],select,textarea{width:100%;padding:10px 11px;border:1px solid var(--line);border-radius:8px;outline:0;background:var(--surface-2);color:var(--cream);font:inherit;resize:vertical}
select option{color:var(--navy)}
input:focus,select:focus,textarea:focus{border-color:var(--gold)}
input[type=range]{width:100%;accent-color:var(--gold)}
.range-value{color:var(--gold);font-size:12px}
.selected-skills{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 6px}
.selected-skill{border:1px solid var(--line);border-radius:20px;padding:3px 8px;color:var(--gold);font-size:11px;cursor:pointer;background:var(--surface-2)}
.run-button{width:100%;margin-top:24px;padding:12px;border:1px solid var(--gold);border-radius:8px;background:var(--gold);color:var(--navy);cursor:pointer;font-weight:800}
.main{padding:46px clamp(24px,5vw,76px) 80px}
.report-head{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;padding-bottom:29px;border-bottom:1px solid var(--line)}
h1{margin:0;font:400 clamp(30px,4vw,48px)/1.1 Georgia,serif;color:var(--cream)}
.report-head p{margin:10px 0 0;color:var(--muted)}
.date{color:var(--gold);font-size:12px;white-space:nowrap}
.tabs{display:flex;gap:30px;margin:26px 0 30px;border-bottom:1px solid var(--line)}
.tab{padding:0 0 13px;border:0;border-bottom:2px solid transparent;background:none;color:var(--muted);cursor:pointer;font:600 14px inherit}
.tab.active{border-color:var(--gold);color:var(--gold)}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin-bottom:32px}
.stat{min-height:104px;padding:18px;border:1px solid var(--line);border-radius:14px;background:var(--surface)}
.stat span{display:block;color:var(--muted);font-size:12px}
.stat strong{display:block;margin-top:13px;color:var(--cream);font:28px Georgia,serif}
.panel{overflow:hidden;border:1px solid var(--line);border-radius:16px;background:var(--surface)}
.table-head,.candidate{display:grid;grid-template-columns:70px minmax(190px,1.4fr) minmax(160px,1.4fr) 90px 86px;align-items:center;gap:16px}
.table-head{padding:14px 22px;background:var(--gold-surface);color:var(--muted);font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}
.candidate{padding:20px 22px;border-top:1px solid var(--line)}
.candidate:hover{background:var(--surface-2)}
.rank{color:var(--muted)}
.rank.top{color:var(--gold);font-weight:800}
.prestige-tag{display:inline-flex;align-items:center;gap:4px;margin-left:8px;padding:2px 9px;border-radius:20px;background:var(--gold);color:var(--navy);font-size:10px;font-weight:700;letter-spacing:.03em;vertical-align:middle;white-space:nowrap}
.toggle-head{display:flex;align-items:center;justify-content:space-between;gap:10px}
.toggle-hint{display:block;margin-top:4px;color:var(--muted);font-size:11px;line-height:1.4}
.switch{position:relative;display:inline-block;width:36px;height:20px;flex:none}
.switch input{opacity:0;width:0;height:0}
.switch-slider{position:absolute;inset:0;background:var(--line);border-radius:20px;cursor:pointer;transition:.18s}
.switch-slider:before{content:"";position:absolute;height:14px;width:14px;left:3px;top:3px;background:var(--cream);border-radius:50%;transition:.18s}
.switch input:checked+.switch-slider{background:var(--gold)}
.switch input:checked+.switch-slider:before{transform:translateX(16px);background:var(--navy)}
.candidate-name{color:var(--cream);font:20px Georgia,serif}
.candidate-meta{margin-top:3px;color:var(--muted);font-size:12px}
.skill-summary,.badges{display:flex;flex-wrap:wrap;gap:5px}
.mini-skill{border-radius:12px;padding:2px 7px;background:var(--gold-surface);color:var(--gold);font-size:11px}
.score{color:var(--gold);font:25px Georgia,serif}
.expand{padding:7px 10px;border:1px solid var(--gold);border-radius:6px;background:transparent;color:var(--gold);cursor:pointer;font:600 12px inherit}
.details-row{display:none;border-top:1px solid var(--line);background:var(--surface-2)}
.details-row.open{display:block}
.detail-label{color:var(--muted);font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}
.badge{margin-top:6px;padding:4px 8px;border-radius:5px;font-size:11px}
.match{background:var(--match-bg);color:var(--match)}
.missing{background:var(--missing-bg);color:var(--missing)}
.penalty-note{margin-top:4px;color:var(--missing);font-size:11px;font-weight:700}
.evidence{padding:20px 22px 26px}
.evidence-meta{color:var(--muted);font-size:12px;margin-bottom:18px;padding-bottom:14px;border-bottom:1px solid var(--line)}
.evidence-section{padding:14px 0;border-top:1px solid var(--line)}
.evidence-section:first-of-type{border-top:0;padding-top:0}
.evidence-title{font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--gold);margin-bottom:12px}
.fit-summary{text-align:center;margin-bottom:14px}
.fit-big{font:36px Georgia,serif;color:var(--gold)}
.metric-row{display:flex;align-items:center;gap:12px;margin:9px 0}
.metric-label{width:130px;flex:none;color:var(--muted);font-size:12px}
.metric-bar{flex:1;height:8px;border-radius:5px;background:var(--gold-surface);overflow:hidden}
.metric-fill{height:100%;background:var(--gold);border-radius:5px}
.metric-pct{width:40px;text-align:right;color:var(--cream);font-size:12px;font-weight:700}
.evidence-skills{display:flex;flex-wrap:wrap;gap:8px 18px}
.evidence-skill{display:inline-flex;align-items:center;gap:6px;font-size:13px;color:var(--cream)}
.evidence-skill .mark{font-weight:800}
.evidence-skill.matched .mark{color:var(--match)}
.evidence-skill.missing{color:var(--muted)}
.evidence-skill.missing .mark{color:var(--muted)}
.why-text{margin:0;color:var(--cream);line-height:1.55}
.next-steps{list-style:none;margin:8px 0 0;padding:0;display:flex;flex-direction:column;gap:8px}
.next-steps li{position:relative;padding-left:18px;color:var(--cream);font-size:13px;line-height:1.4}
.next-steps li:before{content:"\2192";position:absolute;left:0;color:var(--gold);font-weight:800}
.score-cell{display:flex;flex-direction:column;align-items:flex-end;gap:2px}
.view{display:none}
.view.active{display:block}
.comparison{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:16px}
.compare-card,.details-copy{padding:22px;border:1px solid var(--line);border-radius:14px;background:var(--surface)}
.compare-card h3{margin:8px 0;font:23px Georgia,serif;color:var(--cream)}
.compare-card p{color:var(--muted)}
.details-copy{max-width:760px;border-left:2px solid var(--gold);color:var(--cream)}
.details-copy h2{color:var(--cream)}
.empty{padding:46px;color:var(--muted);text-align:center}
@media(max-width:900px){
  .app{display:block}
  .sidebar{border-right:0;border-bottom:1px solid var(--line)}
  .filter-row{display:grid;grid-template-columns:repeat(2,1fr);gap:0 16px}
  .stats{grid-template-columns:repeat(2,1fr)}
  .table-head{display:none}
  .candidate{grid-template-columns:45px 1fr auto}
  .candidate .skill-summary{display:none}
  .candidate .score{grid-column:2}
  .candidate .expand{grid-column:3;grid-row:1/span 2}
  .intake-grid{grid-template-columns:1fr}
}
@media(max-width:560px){
  .main{padding:34px 17px 60px}
  .filter-row,.stats,.report-head{align-items:flex-start;flex-direction:column}
  .candidate{padding:18px 14px}
  .details-row{padding:0 14px 22px}
  .landing{padding:44px 18px}
}
</style></head>
<body>

<!-- ===================== STAGE 1 — INTAKE ===================== -->
<section class="stage active landing" id="landingStage">
  <div class="hero-lockup">
    <svg class="hero-logo" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <circle class="hero-logo-bg" cx="12" cy="12" r="11"/>
      <path class="hero-logo-tick" d="M7 12.4l3.3 3.3L17.2 8.4" fill="none" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <div>
      <span class="hero-word">Shortlist</span>
      <span class="hero-caption">Employer candidate review</span>
    </div>
  </div>
  <h1>Match candidates to the role</h1>
  <p class="lede">Add the job listing and the resumes you're screening. Matching starts once both are in.</p>

  <div class="intake-grid">
    <button class="intake-card" id="jdCard" type="button">
      <div class="swatch-top">
        <svg class="swatch-icon" viewBox="0 0 24 24" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M7 3h7l4 4v14H7z"/><path d="M14 3v4h4"/><line x1="9.5" y1="12" x2="15.5" y2="12"/><line x1="9.5" y1="15.5" x2="15.5" y2="15.5"/></svg>
        <span class="swatch-code">JD · 01</span>
      </div>
      <div class="swatch-label"><strong>Job description</strong><span id="jdStatus">Paste text or upload a file</span></div>
    </button>
    <button class="intake-card gold" id="resumeCard" type="button">
      <div class="swatch-top">
        <svg class="swatch-icon" viewBox="0 0 24 24" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h9l5 5v13H6z"/><path d="M15 3v5h5"/><circle cx="11.5" cy="13" r="2"/><path d="M8.5 18.5c.6-1.8 2-2.7 3-2.7s2.4.9 3 2.7"/></svg>
        <span class="swatch-code">CV · 02</span>
      </div>
      <div class="swatch-label"><strong>Resumes</strong><span id="resumeStatus">Upload PDF or JPG files</span></div>
    </button>
  </div>

  <div class="intake-detail" id="jdDetail">
    <textarea id="jobDescription" rows="4" placeholder="Paste responsibilities, requirements and preferred skills…"></textarea>
    <div class="filerow">
      <label class="filebtn" for="jdFileInput">Or upload a file<input id="jdFileInput" type="file" accept=".pdf,.doc,.docx,.txt"></label>
      <span class="filestatus" id="jdFileStatus"></span>
    </div>
  </div>
  <div class="intake-detail" id="resumeDetail">
    <div class="filerow">
      <label class="filebtn" for="fileInput">Choose files<input id="fileInput" type="file" accept=".pdf,.jpg,.jpeg" multiple></label>
      <span class="filestatus" id="resumeFileStatus">No files selected</span>
    </div>
  </div>

  <button class="start-button" id="runButton" disabled>Start matching</button>
  <span class="start-hint" id="startHint">Add a job description and at least one resume to continue</span>
</section>

<!-- ===================== STAGE 2 — REPORT ===================== -->
<section class="stage" id="reportStage">
<div class="app">
<aside class="sidebar">
  <button class="back-link" id="backLink" type="button">&larr; New search</button>
  <div class="brand">
    <svg class="brand-logo" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <circle class="hero-logo-bg" cx="12" cy="12" r="11"/>
      <path class="hero-logo-tick" d="M7 12.4l3.3 3.3L17.2 8.4" fill="none" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <div><span class="brand-name">Shortlist.</span><small>Employer candidate review</small></div>
  </div>
  <span class="side-title">Filters</span>
  <div class="filter-row">
    <div class="filter-group"><label class="filter-label" for="skillSearch">Skills to match</label><input id="skillSearch" type="text" placeholder="Type a skill and press Enter"></div>
    <div class="selected-skills" id="selectedSkills"></div>
    <div class="filter-group"><label class="filter-label" for="locationFilter">Location</label><select id="locationFilter"><option value="">Any location</option></select></div>
    <div class="filter-group"><label class="filter-label" for="experienceFilter">Minimum experience <span class="range-value" id="experienceValue">0 yrs</span></label><input id="experienceFilter" type="range" min="0" max="15" value="0"></div>
    <div class="filter-group"><label class="filter-label" for="statusFilter">Employment status</label><select id="statusFilter"><option value="">Any status</option><option>Employed</option><option>Open to work</option><option>Not specified</option></select></div>
    <div class="filter-group prestige-toggle">
      <div class="toggle-head"><span class="filter-label" style="margin-bottom:0">Notable school / employer tag</span><label class="switch"><input type="checkbox" id="prestigeToggle"><span class="switch-slider"></span></label></div>
      <span class="toggle-hint">Off by default. Scores already exclude name-recognition (see resume_matcher's prestige-neutral scoring) — this only reveals the signal, it never changes rank.</span>
    </div>
  </div>
  <button class="run-button" id="rerunButton">Re-run ranking</button>
</aside>
<main class="main">
  <header class="report-head"><div><h1>{{JD_TITLE}}</h1><p>Candidate shortlisting and skill-fit review</p></div><div class="date" id="reportDate"></div></header>
  <nav class="tabs"><button class="tab active" data-view="list">List view</button><button class="tab" data-view="comparison">Comparison</button><button class="tab" data-view="details">Role details</button></nav>
  <section class="stats">
    <div class="stat"><span>Total candidates</span><strong id="totalStat">0</strong></div>
    <div class="stat"><span>Average score</span><strong id="scoreStat">—</strong></div>
    <div class="stat"><span>Average experience</span><strong id="experienceStat">—</strong></div>
    <div class="stat"><span>Skills matched</span><strong id="skillsStat">—</strong></div>
  </section>
  <section class="view active" id="listView"><div class="panel"><div class="table-head"><span>Rank</span><span>Candidate</span><span>Skills matched</span><span>Score</span><span>Review</span></div><div id="candidateList"></div></div></section>
  <section class="view" id="comparisonView"><div class="comparison" id="comparisonList"></div></section>
  <section class="view" id="detailsView"><div class="details-copy"><span class="detail-label">Selected role</span><h2>{{JD_TITLE}}</h2><p><strong>Required skills:</strong> {{JD_REQUIRED}}</p><p><strong>Preferred skills:</strong> {{JD_PREFERRED}}</p><p>{{JD_YEARS_TEXT}}</p></div></section>
</main>
</div>
</section>

<script>
const DATA={{DATA_JSON}};

const byId=id=>document.getElementById(id);
let selectedSkills=new Set(),prestigeEnabled=false;
const norm=v=>String(v||"").toLowerCase(),loc=c=>c.location||c.city||"Not specified",status=c=>c.employment_status||c.status||"Not specified",skills=c=>(c.matched_required||[]).concat(c.matched_preferred||[],c.missing_required||[],c.missing_preferred||[]);

/* ---------- Stage 1 behaviour ---------- */
let resumeFiles=[];
function toggleDetail(cardId,detailId,otherDetailId){byId(detailId).classList.toggle("open");byId(cardId).classList.toggle("selected",byId(detailId).classList.contains("open"))}
byId("jdCard").onclick=()=>toggleDetail("jdCard","jdDetail");
byId("resumeCard").onclick=()=>toggleDetail("resumeCard","resumeDetail");

function jdProvided(){return byId("jobDescription").value.trim().length>0||byId("jdFileInput").files.length>0}
function refreshStart(){
  const ready=jdProvided()&&resumeFiles.length>0;
  byId("runButton").disabled=!ready;
  byId("startHint").textContent=ready?"Ready to match "+resumeFiles.length+" resume(s) against the listing":"Add a job description and at least one resume to continue";
}
byId("jobDescription").oninput=()=>{byId("jdStatus").textContent=byId("jobDescription").value.trim()?byId("jobDescription").value.trim().split(/\s+/).length+" words pasted":"Paste text or upload a file";refreshStart()};
byId("jdFileInput").onchange=e=>{
  const file=e.target.files[0];
  if(!file)return;
  byId("jdFileStatus").textContent=file.name+" selected";
  byId("jdStatus").textContent=file.name;
  if(file.name.toLowerCase().endsWith(".txt")){
    const reader=new FileReader();
    reader.onload=r=>{byId("jobDescription").value=r.target.result;byId("jdStatus").textContent=byId("jobDescription").value.trim().split(/\s+/).length+" words loaded"};
    reader.readAsText(file);
  }
  refreshStart();
};
byId("fileInput").onchange=e=>{
  resumeFiles=[...e.target.files];
  byId("resumeFileStatus").textContent=resumeFiles.length?resumeFiles.length+" file(s) selected":"No files selected";
  byId("resumeStatus").textContent=resumeFiles.length?resumeFiles.length+" resume(s) added":"Upload PDF or JPG files";
  refreshStart();
};
byId("runButton").onclick=()=>{
  byId("landingStage").classList.remove("active");
  byId("reportStage").classList.add("active");
  renderAll();
};
byId("backLink").onclick=()=>{
  byId("reportStage").classList.remove("active");
  byId("landingStage").classList.add("active");
};
byId("rerunButton").onclick=renderAll;

/* ---------- Stage 2 (report) behaviour ---------- */
function prestigeTag(c){return (prestigeEnabled&&c.prestige_signal_detected)?'<span class="prestige-tag" title="Attended/worked at a widely recognized school or company. Informational only — excluded from the match score.">Notable background</span>':""}
byId("reportDate").textContent="Updated "+new Intl.DateTimeFormat(undefined,{month:"short",day:"numeric",year:"numeric"}).format(new Date());
function renderSelected(){byId("selectedSkills").innerHTML=[...selectedSkills].map(s=>'<button class="selected-skill" data-skill="'+s+'">'+s+' ×</button>').join("");document.querySelectorAll(".selected-skill").forEach(b=>b.onclick=()=>{selectedSkills.delete(b.dataset.skill);renderSelected();renderAll()})}
function candidates(){let l=byId("locationFilter").value,st=byId("statusFilter").value,min=+byId("experienceFilter").value,ranked=[...DATA.candidates].sort((a,b)=>b.fused_score.overall_score-a.fused_score.overall_score),top3=ranked.slice(0,3),filtered=ranked.filter(c=>(!l||loc(c)===l)&&(!st||status(c)===st)&&(c.years_of_experience||0)>=min&&[...selectedSkills].every(s=>skills(c).map(norm).includes(norm(s)))),merged=[...top3];filtered.forEach(c=>{if(!merged.includes(c))merged.push(c)});return merged.sort((a,b)=>b.fused_score.overall_score-a.fused_score.overall_score)}
function badge(items,type){return items&&items.length?items.map(s=>'<span class="badge '+type+'">'+s+'</span>').join(""):'<span class="detail-value">None</span>'}
function pct(n,d){return d?Math.round(n/d*100):100}
function metricRow(label,val){let v=Math.max(0,Math.min(100,val));return '<div class="metric-row"><span class="metric-label">'+label+'</span><div class="metric-bar"><div class="metric-fill" style="width:'+v+'%"></div></div><span class="metric-pct">'+v+'%</span></div>'}
function skillEvidence(matched,missing){let m=(matched||[]).map(s=>'<span class="evidence-skill matched"><span class="mark">\u2713</span>'+s+'</span>'),mi=(missing||[]).map(s=>'<span class="evidence-skill missing"><span class="mark">\u25cb</span>'+s+'</span>');return m.concat(mi).join("")||'<span class="evidence-skill missing">No skill data available</span>'}
function nextBestEvidence(c){let items=[];(c.missing_required||[]).forEach(s=>items.push("Verify "+s+" experience in interview"));(c.missing_preferred||[]).forEach(s=>items.push("Ask about "+s));if(!items.length)items.push("No missing skills detected — confirm depth in interview");return items.slice(0,4).map(t=>'<li>'+t+'</li>').join("")}
function evidenceCard(c){let score=c.fused_score.overall_score,matched=(c.matched_required||[]).concat(c.matched_preferred||[]),missing=(c.missing_required||[]).concat(c.missing_preferred||[]),reqMatched=(c.matched_required||[]).length,reqMissing=(c.missing_required||[]).length,prefMatched=(c.matched_preferred||[]).length,prefMissing=(c.missing_preferred||[]).length,reqPct=pct(reqMatched,reqMatched+reqMissing),prefPct=pct(prefMatched,prefMatched+prefMissing),minYears=DATA.jd_min_years_experience||0,expPct=minYears?Math.min(100,Math.round((c.years_of_experience||0)/minYears*100)):((c.years_of_experience||0)>0?100:0),semPct=Math.max(0,Math.min(100,Math.round(c.fused_score.semantic_score||0))),penalty=c.fused_score.missing_required_penalty||0,missingReqCount=c.fused_score.missing_required_count||0,ex=(DATA.explanations||{})[c.filename]||"Review the supplied evidence and interview notes before making a decision.",penaltyLine=penalty>0?'<div class="penalty-note">&minus;'+Math.round(penalty*100)+'% required-skill penalty ('+missingReqCount+' missing)</div>':"";return '<div class="evidence"><div class="evidence-meta">'+loc(c)+' · '+status(c)+' · '+(c.current_role||"Role not specified")+'</div><div class="evidence-section"><div class="evidence-title">Overall fit</div><div class="fit-summary"><span class="fit-big">'+score.toFixed(1)+'%</span></div>'+metricRow("Required skills",reqPct)+metricRow("Preferred skills",prefPct)+metricRow("Experience",expPct)+metricRow("Semantic match",semPct)+'</div><div class="evidence-section"><div class="evidence-title">Skill evidence</div><div class="evidence-skills">'+skillEvidence(matched,missing)+'</div></div><div class="evidence-section"><div class="evidence-title">Why this ranking</div><p class="why-text">'+ex+'</p>'+penaltyLine+'</div><div class="evidence-section"><div class="evidence-title">Next best evidence</div><ul class="next-steps">'+nextBestEvidence(c)+'</ul></div></div>'}
function row(c,i){let score=c.fused_score.overall_score,id="candidate-"+i,matched=(c.matched_required||[]).concat(c.matched_preferred||[]),penalty=c.fused_score.missing_required_penalty||0,penaltyNoteSmall=penalty>0?'<div class="penalty-note" title="'+(c.fused_score.missing_required_count||0)+' required skill(s) missing entirely">&minus;'+Math.round(penalty*100)+'%</div>':"";return '<div class="candidate"><span class="rank '+(i<3?"top":"")+'">#'+(i+1)+'</span><div><div class="candidate-name">'+c.candidate_name+prestigeTag(c)+'</div><div class="candidate-meta">'+(c.years_of_experience??"—")+' yrs experience · '+loc(c)+'</div></div><div class="skill-summary">'+matched.slice(0,3).map(s=>'<span class="mini-skill">'+s+'</span>').join("")+'</div><div class="score-cell"><div class="score">'+score.toFixed(1)+'</div>'+penaltyNoteSmall+'</div><button class="expand" data-target="'+id+'">Details</button></div><div class="details-row" id="'+id+'">'+evidenceCard(c)+'</div></div>'}
function renderAll(){let list=candidates(),avg=list.length?list.reduce((n,c)=>n+c.fused_score.overall_score,0)/list.length:0,yrs=list.length?list.reduce((n,c)=>n+(c.years_of_experience||0),0)/list.length:0,match=list.reduce((n,c)=>n+(c.matched_required||[]).length,0);byId("totalStat").textContent=list.length;byId("scoreStat").textContent=list.length?avg.toFixed(1):"—";byId("experienceStat").textContent=list.length?yrs.toFixed(1)+" yrs":"—";byId("skillsStat").textContent=match+"/"+((DATA.jd_required_skills||[]).length*list.length||0);byId("candidateList").innerHTML=list.length?list.map(row).join(""):'<div class="empty">No candidates match these filters.</div>';byId("comparisonList").innerHTML=list.length?list.slice(0,6).map((c,i)=>{let p=c.fused_score.missing_required_penalty||0,pNote=p>0?'<div class="penalty-note">&minus;'+Math.round(p*100)+'% required-skill penalty ('+(c.fused_score.missing_required_count||0)+' missing)</div>':"";return '<article class="compare-card"><span class="rank '+(i<3?"top":"")+'">#'+(i+1)+'</span><h3>'+c.candidate_name+prestigeTag(c)+'</h3><div class="score">'+c.fused_score.overall_score.toFixed(1)+'</div>'+pNote+'<p>'+(c.years_of_experience??"—")+' years · '+loc(c)+'</p><div class="badges">'+badge((c.matched_required||[]).slice(0,4),"match")+'</div></article>'}).join(""):'<div class="empty">No candidates to compare.</div>';document.querySelectorAll(".expand").forEach(b=>b.onclick=()=>{let d=byId(b.dataset.target),open=d.classList.toggle("open");b.textContent=open?"Collapse":"Details"})}

[...new Set(DATA.candidates.map(loc))].sort().forEach(l=>byId("locationFilter").insertAdjacentHTML("beforeend","<option>"+l+"</option>"));
byId("skillSearch").onkeydown=e=>{if(e.key==="Enter"){e.preventDefault();e.target.value.split(",").map(s=>s.trim()).filter(Boolean).forEach(s=>selectedSkills.add(s));e.target.value="";renderSelected();renderAll()}};
byId("experienceFilter").oninput=e=>{byId("experienceValue").textContent=e.target.value+" yrs";renderAll()};
byId("locationFilter").onchange=byId("statusFilter").onchange=renderAll;
byId("prestigeToggle").onchange=e=>{prestigeEnabled=e.target.checked;renderAll()};
document.querySelectorAll(".tab").forEach(t=>t.onclick=()=>{document.querySelectorAll(".tab,.view").forEach(e=>e.classList.remove("active"));t.classList.add("active");byId(t.dataset.view+"View").classList.add("active")});
renderSelected();
</script>
</body></html>
"""

def generate_html_report(results: dict, out_path: str) -> None:
    """Write results into a standalone HTML dashboard."""
    required = ", ".join(results["jd_required_skills"]) or "none detected"
    preferred = ", ".join(results["jd_preferred_skills"]) or "none detected"
    years = results.get("jd_min_years_experience")
    years_text = f"Minimum experience: {years} years." if years is not None else "No minimum-experience requirement supplied."
    html = (HTML_TEMPLATE
            .replace("{{JD_TITLE}}", results["jd_title"])
            .replace("{{JD_REQUIRED}}", required)
            .replace("{{JD_PREFERRED}}", preferred)
            .replace("{{JD_YEARS_TEXT}}", years_text)
            .replace("{{DATA_JSON}}", json.dumps(results)))
    with open(out_path, "w", encoding="utf-8") as output:
        output.write(html)