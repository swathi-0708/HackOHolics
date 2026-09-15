"""Render an employer-friendly, interactive resume-shortlisting report.

Two-page flow: an intake stage (job description + resumes) and a report
stage (ranked list / comparison / role details), styled with a refined
Swan Wing cream, Royal Blue navy, sapphire, and Quicksand gold design system.
"""
from __future__ import annotations
import json

HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Shortlistr — {{JD_TITLE}}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700;800&family=Archivo+Black&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Ccircle cx='12' cy='12' r='11' fill='%23DCDDE1'/%3E%3Cpath d='M7 12.4l3.3 3.3L17.2 8.4' fill='none' stroke='%23E0C58F' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E">
<style>
:root {
  --bg-cream: #0E1617;
  --paper: #DCDDE1;
  --stone: #7C7C77;
  --stone-muted: rgba(124, 124, 119, 0.85);
  --gold: #E0C58F;
  --gold-hover: #d4b67b;
  --gold-gradient: linear-gradient(135deg, #f3e3ba 0%, #e0c58f 45%, #c9a227 100%);
  --gold-gradient-hover: linear-gradient(135deg, #f8ecd0 0%, #e6cf9e 45%, #d4af37 100%);
  --mist: #ACAEB1;
  --stone-border: #7C7C77;
  --match-green: #2e7d32;
  --match-bg: rgba(46, 125, 50, 0.12);
  --missing-red: #c62828;
  --missing-bg: rgba(198, 40, 40, 0.12);
}

* { box-sizing: border-box; }
body {
  margin: 0;
  min-height: 100vh;
  background: var(--bg-cream);
  color: var(--paper);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
}

.stage { display: none; }
.stage.active { display: block; }

h1, h2, h3, .serif-font {
  font-family: 'Space Grotesk', sans-serif;
}

/* ------------ NAV BAR (top, pill-style) ------------ */
.landing-header {
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 24px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.nav-pill-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  background: rgba(69, 70, 65, 0.55);
  border-bottom: 1px solid #454641;
  padding: 16px 8px;
}
.nav-links {
  display: flex;
  align-items: center;
  gap: 32px;
  list-style: none;
  margin: 0;
  padding: 0;
}
.nav-links a {
  color: #ACAEB1;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  font-family: 'Inter', sans-serif;
  transition: color 0.2s ease;
}
.nav-links a:hover { color: #DCDDE1; }
@media (max-width: 720px) {
  .nav-links { display: none; }
}
.nav-logo-mark {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
}
.logo-icon-badge {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--paper);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.logo-wordmark {
  font-family: 'Space Grotesk', sans-serif !important;
  font-size: 20px;
  font-weight: 800;
  color: var(--paper);
  letter-spacing: -0.03em;
}
.nav-cta-btn {
  background: transparent;
  color: var(--gold);
  border: 1.5px solid var(--gold);
  border-radius: 25px;
  padding: 9px 22px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: 'Inter', sans-serif;
}
.nav-cta-btn:hover {
  background: var(--gold-gradient);
  color: var(--bg-cream);
  transform: translateY(-1px);
}

/* ------------ HERO SECTION — 2-COLUMN GRID ------------ */
.landing-content {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 24px 64px;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 28px;
}

/* Two-column hero grid */
.hero-grid {
  display: grid;
  grid-template-columns: 45fr 55fr;
  gap: 48px;
  align-items: start;
  padding: 48px 0 24px;
}

/* LEFT COLUMN */
.hero-left {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 24px;
}
.hero-title {
  font-family: 'Space Grotesk', sans-serif !important;
  font-size: clamp(40px, 5.5vw, 68px);
  font-weight: 800;
  line-height: 1.1;
  color: var(--paper);
  letter-spacing: -0.04em;
  margin: 0;
  text-align: left;
}
.hero-title-line {
  display: block;
}
.hero-subhead {
  margin: 0;
  font-size: 15px;
  line-height: 1.65;
  color: var(--mist);
  max-width: 440px;
  text-align: left;
}
.hero-cta-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}
.hero-btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--gold-gradient);
  color: #0E1617;
  border: none;
  border-radius: 30px;
  padding: 12px 26px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 16px rgba(224, 197, 143, 0.35);
  font-family: 'Inter', sans-serif;
}
.hero-btn-primary:hover {
  background: var(--gold-gradient-hover);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(224, 197, 143, 0.45);
}
.hero-btn-outline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  color: var(--paper);
  border: 1px solid var(--paper);
  border-radius: 30px;
  padding: 12px 26px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: 'Inter', sans-serif;
}
.hero-btn-outline:hover {
  background: rgba(220, 221, 225, 0.08);
  border-color: var(--gold);
  color: var(--gold);
  transform: translateY(-2px);
}

/* ------------ FEATURE BADGE ROW (below CTA, left-aligned) ------------ */
.feature-badge-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
  flex-wrap: wrap;
}
.feature-badge-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #454641;
  border: 1px solid var(--gold);
  border-radius: 20px;
  padding: 7px 14px;
  font-size: 12px;
  font-weight: 600;
  color: var(--paper);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}
.badge-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--gold);
}

/* ------------ RIGHT COLUMN — FANNED CARD STACK ------------ */
.hero-right-pin-wrap {
  position: relative;
}
.hero-right {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  min-height: 420px;
  /* leave top padding for tabs poking above cards */
  padding-top: 40px;
  perspective: 1400px;
}
.fan-glow {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 50% 60%, rgba(224,197,143,0.10) 0%, rgba(14,22,23,0.35) 55%, transparent 78%);
  pointer-events: none;
  border-radius: 50%;
}

/*
  Fan stack: 4 cards, DOM order = card4 (back) first, card1 (front) last.
  Each card is translated so all four are clearly visible.
  z-index goes up so front card is always on top.
*/
.fan-stack {
  position: relative;
  width: 300px;   /* wide enough to show all rotated cards without overflow */
  height: 320px;
}

/* All cards share base styles */
.fan-card {
  position: absolute;
  width: 220px;
  height: 280px;
  background: #DCDDE1;
  border-radius: 12px;
  padding: 24px 20px 18px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  /* overflow visible so tabs poke above card top */
  overflow: visible;
}

/* Card 4 — furthest back (DOM child 1) */
.fan-card:nth-child(1) {
  transform: rotate(-8deg) translate(-30px, 30px);
  z-index: 1;
  opacity: 0.40;
  box-shadow: 0 4px 12px rgba(0,0,0,0.22);
}
/* Card 3 (DOM child 2) */
.fan-card:nth-child(2) {
  transform: rotate(-3deg) translate(-12px, 16px);
  z-index: 2;
  opacity: 0.60;
  box-shadow: 0 6px 18px rgba(0,0,0,0.26);
}
/* Card 2 — second from front (DOM child 3) */
.fan-card:nth-child(3) {
  transform: rotate(2deg) translate(8px, 6px);
  z-index: 3;
  opacity: 0.85;
  box-shadow: 0 8px 22px rgba(0,0,0,0.30);
}
/* Card 1 — front card (DOM child 4) */
.fan-card:nth-child(4) {
  transform: rotate(6deg) translate(24px, 0px);
  z-index: 4;
  opacity: 1;
  box-shadow: 0 14px 40px rgba(0,0,0,0.40), 0 2px 8px rgba(224,197,143,0.12);
}

/* Hover lift on front card only */
.fan-card:nth-child(4):hover {
  transform: rotate(6deg) translate(24px, -8px);
  box-shadow: 0 20px 50px rgba(0,0,0,0.45), 0 4px 16px rgba(224,197,143,0.18);
}

/* ---------- Card tab (library index-card style) ---------- */
.fan-tab {
  position: absolute;
  /* sits above top edge of card */
  top: -28px;
  left: 16px;
  height: 28px;
  min-width: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gold);
  color: #0E1617;
  font-size: 13px;
  font-weight: 800;
  padding: 0 12px;
  border-radius: 6px 6px 0 0;
  letter-spacing: 0.05em;
  box-shadow: 0 -3px 10px rgba(224,197,143,0.35);
  font-family: 'Inter', sans-serif;
  /* ensure tab renders above sibling cards */
  z-index: 5;
}
.fan-tab.muted {
  background: #5A5B54;
  color: #ACAEB1;
  font-size: 11px;
  font-weight: 700;
  box-shadow: 0 -2px 6px rgba(0,0,0,0.18);
  min-width: 44px;
  height: 24px;
  top: -24px;
  left: 14px;
}

/* ---------- Card content placeholders ---------- */
/* Bold name line */
.fan-name-line {
  height: 12px;
  background: #2A2B27;
  border-radius: 4px;
  margin-bottom: 14px;
  width: 65%;
  opacity: 0.80;
}
/* Thin text lines */
.fan-text-line {
  height: 7px;
  background: #8A8B86;
  border-radius: 3px;
  margin-bottom: 9px;
  opacity: 0.55;
}
.fan-text-line.w-90 { width: 90%; }
.fan-text-line.w-70 { width: 70%; }
.fan-text-line.w-55 { width: 55%; }
/* Extra lines to fill the taller card */
.fan-text-line.w-80 { width: 80%; }
.fan-text-line.w-40 { width: 40%; }

@media(max-width: 860px) {
  .hero-grid {
    grid-template-columns: 1fr;
    gap: 40px;
    padding: 32px 0 16px;
  }
  .hero-right {
    min-height: 320px;
    padding-top: 40px;
  }
  .fan-stack { width: 260px; height: 280px; }
  .fan-card { width: 190px; height: 240px; }
  .feature-badge-row { justify-content: flex-start; }
}

/* ------------ CARD CATALOG DRAWER (replaces live score card) ------------ */
.card-catalog {
  position: relative;
  width: 360px;
  padding-top: 16px;
  transform: rotateX(var(--tiltY, 0deg)) rotateY(var(--tiltX, 0deg));
  transition: transform 0.2s ease-out;
  transform-style: preserve-3d;
}
.catalog-guide-tab {
  position: absolute;
  top: 18px;
  left: 50%;
  transform: translateX(108px) rotate(4deg);
  z-index: 1;
  width: 54px;
  background: var(--gold);
  color: #0E1617;
  font-family: ui-monospace, Consolas, monospace;
  font-size: 11px;
  font-weight: 700;
  text-align: center;
  padding: 5px 0;
  border-radius: 3px 3px 0 0;
  box-shadow: 0 -2px 8px rgba(0,0,0,0.25);
  z-index: 1;
}
.catalog-fan {
  position: relative;
  width: 100%;
  height: 175px;
  z-index: 2;
  perspective: 1000px;
}
.catalog-card {
  position: absolute;
  left: 50%;
  bottom: 0;
  width: 290px;
  background: var(--paper);
  border-radius: 4px;
  box-shadow: 0 10px 26px rgba(0,0,0,0.35);
  transform-origin: bottom center;
  --tx: 0px;
  --rot: 0deg;
  --ry: 0deg;
  --scale: 1;
  transform: translateX(calc(-50% + var(--tx))) rotate(var(--rot)) rotateY(var(--ry)) scale(var(--scale));
}
.catalog-card.layer-1 {
  height: 120px;
  --tx: -14px;
  --rot: -9deg;
  opacity: 0.45;
}
.catalog-card.layer-2 {
  height: 140px;
  --tx: -6px;
  --rot: -4deg;
  opacity: 0.65;
  background: #CBD6D3;
}
.catalog-card.layer-3 {
  height: 158px;
  --tx: 0px;
  --rot: 2deg;
  opacity: 0.85;
}
.catalog-card.front {
  height: auto;
  --tx: 4px;
  --rot: -1.5deg;
  padding: 18px 20px 16px;
  z-index: 3;
}
.catalog-card-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 2px;
}
.catalog-card-name {
  font-family: ui-monospace, Consolas, monospace;
  font-size: 13px;
  font-weight: 700;
  color: #0E1617;
}
.catalog-card-badge {
  background: var(--gold);
  color: #0E1617;
  font-family: ui-monospace, Consolas, monospace;
  font-weight: 800;
  font-size: 13px;
  border-radius: 4px;
  padding: 2px 8px;
}
.catalog-card-role {
  font-family: ui-monospace, Consolas, monospace;
  font-size: 11px;
  color: #6E6F69;
  margin-bottom: 10px;
}
.catalog-card-divider {
  border-top: 1px dashed rgba(14,22,23,0.25);
  margin-bottom: 10px;
}
.catalog-card-line {
  display: flex;
  justify-content: space-between;
  font-family: ui-monospace, Consolas, monospace;
  font-size: 11px;
  color: #454641;
  margin-bottom: 4px;
}
.catalog-card-line span:last-child { font-weight: 700; color: #0E1617; }
.catalog-bar-track {
  width: 100%;
  height: 4px;
  background: rgba(14,22,23,0.12);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 8px;
}
.catalog-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.15s linear;
}
.catalog-bar-fill.keyword { background: var(--stone); }
.catalog-bar-fill.semantic { background: var(--gold); }
.catalog-card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}
.catalog-tag {
  font-family: ui-monospace, Consolas, monospace;
  font-size: 9.5px;
  font-weight: 600;
  color: #0E1617;
  background: rgba(224,197,143,0.35);
  border: 1px solid var(--gold);
  border-radius: 3px;
  padding: 3px 7px;
}
.catalog-drawer-box {
  position: relative;
  width: 100%;
  height: 92px;
  margin-top: -22px;
  background: linear-gradient(180deg, #55564f, #3a3b36);
  border-top: 3px solid var(--gold);
  border-radius: 3px 3px 10px 10px;
  clip-path: polygon(6% 0%, 94% 0%, 100% 100%, 0% 100%);
  box-shadow: 0 22px 48px rgba(0,0,0,0.4);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding-bottom: 12px;
}
.catalog-drawer-label {
  font-family: ui-monospace, Consolas, monospace;
  font-size: 10px;
  letter-spacing: 0.1em;
  color: var(--gold);
  text-transform: uppercase;
  background: rgba(224,197,143,0.12);
  border: 1px solid rgba(224,197,143,0.4);
  padding: 3px 10px;
  border-radius: 3px;
}

/* ------------ TRUST BAR (feature tags moved below the fold) ------------ */
.trust-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 40px;
  flex-wrap: wrap;
  padding: 20px 0 8px;
  border-top: 1px solid #454641;
}
.trust-item {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; font-weight: 500; color: #7C7C77;
}
.trust-item svg { flex-shrink: 0; opacity: 0.7; }

/* ------------ HERO IMAGE CARD (RESUME PEDESTAL SCENE) ------------ */
.hero-image-card {
  width: 100%;
  max-width: 960px;
  margin: 0 auto;
  background: linear-gradient(180deg, #454641 0%, #0E1617 100%);
  border: 1px solid var(--stone-border);
  border-radius: 24px;
  padding: 36px 32px;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  gap: 32px;
  position: relative;
  overflow: hidden;
}

/* ------------ UPLOAD CARDS (JD + Resumes) ------------ */
.upload-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  width: 100%;
}
.upload-card {
  background: linear-gradient(180deg, #171d1e 0%, #0E1617 100%);
  border: 1px solid #2b2f2c;
  border-radius: 18px;
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  text-align: left;
}
.upload-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
}
.upload-card-header svg { flex-shrink: 0; }
.upload-card-header svg path, .upload-card-header svg line, .upload-card-header svg circle {
  stroke: var(--gold);
}
.upload-card-header span {
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 700;
  font-size: 15px;
  color: var(--paper);
}
.upload-dropzone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: 1.5px dashed rgba(224, 197, 143, 0.45);
  border-radius: 12px;
  padding: 22px 16px;
  cursor: pointer;
  text-align: center;
  background: rgba(224, 197, 143, 0.03);
  transition: border-color 0.18s ease, background 0.18s ease;
}
.upload-dropzone:hover {
  border-color: var(--gold);
  background: rgba(224, 197, 143, 0.07);
}
.upload-dropzone strong {
  font-size: 13px;
  color: var(--paper);
  font-weight: 700;
}
.upload-dropzone span {
  font-size: 11.5px;
  color: var(--stone);
}
.upload-file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.upload-file-row {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid #2b2f2c;
  border-radius: 10px;
  padding: 9px 12px;
}
.upload-file-icon {
  width: 26px;
  height: 26px;
  border-radius: 5px;
  background: rgba(224, 197, 143, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.upload-file-icon svg { width: 14px; height: 14px; stroke: var(--gold); }
.upload-file-meta { flex: 1; min-width: 0; }
.upload-file-name {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--paper);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.upload-file-sub {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 10.5px;
  color: var(--stone);
  margin-top: 1px;
}
.upload-file-sub .done { color: var(--match-green); font-weight: 600; }
.upload-file-remove {
  width: 22px;
  height: 22px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--stone);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 5px;
  transition: color 0.15s ease, background 0.15s ease;
}
.upload-file-remove:hover { color: var(--missing-red); background: var(--missing-bg); }
.upload-textarea {
  width: 100%;
  min-height: 64px;
  resize: vertical;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid #2b2f2c;
  border-radius: 10px;
  padding: 10px 12px;
  color: var(--paper);
  font-family: 'Inter', sans-serif;
  font-size: 12.5px;
  outline: 0;
}
.upload-textarea::placeholder { color: var(--stone); }
.upload-textarea:focus { border-color: var(--gold); }
.upload-status-line { font-size: 11.5px; color: var(--stone); }
.upload-action-btn {
  align-self: flex-start;
  padding: 8px 19px;
  border: 1.5px solid var(--gold);
  border-radius: 24px;
  background: transparent;
  color: var(--gold);
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  font-size: 12.5px;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease, transform 0.15s ease;
}
.upload-action-btn:hover { background: var(--gold-gradient); color: var(--bg-cream); transform: translateY(-1px); }

.start-button {
  width: 100%;
  padding: 16px 36px;
  border: none;
  border-radius: 30px;
  background: var(--gold-gradient);
  color: var(--bg-cream);
  font-family: 'Inter', sans-serif;
  font-weight: 800;
  font-size: 16px;
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(224, 197, 143, 0.4);
  transition: all 0.2s ease;
}
.start-button:hover:not(:disabled) {
  background: var(--gold-gradient-hover);
  transform: translateY(-1px);
}
.start-button:disabled {
  background: rgba(255, 255, 255, 0.06);
  color: var(--stone);
  cursor: not-allowed;
  box-shadow: none;
}
.start-hint {
  color: var(--stone);
  font-size: 13px;
  margin-top: -18px;
}

/* ------------ DARK BAND SECTION ------------ */
.dark-band-section {
  width: 100%;
  background: linear-gradient(180deg, #12181a 0%, var(--bg-cream) 100%);
  padding: 72px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.dark-band-content {
  max-width: 960px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 32px;
}
.dark-band-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 32px;
  font-weight: 700;
  color: var(--paper);
  margin: 0;
}
.dark-band-accent-badge {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--mist);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(224, 197, 143, 0.25);
}
.dark-band-labels {
  display: flex;
  align-items: center;
  gap: 24px;
  color: var(--gold);
  font-weight: 600;
  font-size: 15px;
}
.dark-band-labels span {
  display: block;
}
.dark-band-label-arrow {
  color: var(--stone-muted);
  display: inline-flex;
  align-items: center;
}
@media(max-width: 700px) {
  .dark-band-labels {
    flex-direction: column;
    gap: 12px;
  }
  .dark-band-label-arrow {
    transform: rotate(90deg);
  }
}

/* ------------ SCROLL REVEAL SYSTEM ------------ */
[data-reveal] {
  opacity: 0;
}
[data-reveal="up"] {
  transform: translateY(34px);
  transition: opacity 0.7s cubic-bezier(.16,1,.3,1), transform 0.7s cubic-bezier(.16,1,.3,1);
}
[data-reveal="pop"] {
  transform: scale(.4) rotate(-14deg);
  transition: opacity 0.5s ease, transform 0.8s cubic-bezier(.34,1.56,.64,1);
}
[data-reveal="arrow"] {
  transition: opacity 0.3s ease;
}
[data-reveal="arrow"] .arrow-line {
  stroke-dasharray: 22;
  stroke-dashoffset: 22;
  transition: stroke-dashoffset 0.5s cubic-bezier(.16,1,.3,1);
}
[data-reveal="arrow"] .arrow-head {
  opacity: 0;
  transition: opacity 0.25s ease;
  transition-delay: 0.35s;
}
[data-reveal-group].in-view [data-reveal="up"],
[data-reveal-group].in-view [data-reveal="pop"] {
  opacity: 1;
  transform: none;
}
[data-reveal-group].in-view [data-reveal="arrow"] {
  opacity: 1;
}
[data-reveal-group].in-view [data-reveal="arrow"] .arrow-line {
  stroke-dashoffset: 0;
}
[data-reveal-group].in-view [data-reveal="arrow"] .arrow-head {
  opacity: 1;
}
@media (prefers-reduced-motion: reduce) {
  [data-reveal], [data-reveal] .arrow-line, [data-reveal] .arrow-head {
    transition: none !important;
    opacity: 1 !important;
    transform: none !important;
    stroke-dashoffset: 0 !important;
  }
}

/* ------------ FOOTER CARD ------------ */
.footer-card {
  width: 100%;
  max-width: 960px;
  background: #454641;
  border: 1px solid var(--stone-border);
  border-radius: 20px;
  padding: 28px 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
  text-align: left;
}
.footer-info h3 {
  margin: 0;
  font-family: 'Archivo Black', sans-serif;
  font-size: 22px;
  font-weight: 700;
  color: var(--paper);
}
.footer-info p {
  margin: 6px 0 0;
  color: var(--stone);
  font-size: 14px;
  line-height: 1.5;
  max-width: 620px;
}
.footer-cta-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--gold-gradient);
  color: var(--bg-cream);
  border: none;
  border-radius: 25px;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(224, 197, 143, 0.3);
}
.footer-cta-btn:hover {
  background: var(--gold-gradient-hover);
  transform: translateY(-1px);
}

/* ------------ STAGE 2: REPORT DASHBOARD STYLES ------------ */
.app {
  display: grid;
  grid-template-columns: 290px minmax(0, 1fr);
  min-height: 100vh;
  max-width: 1500px;
  margin: auto;
  border-inline: 1px solid var(--stone-border);
  background: var(--bg-cream);
}
.sidebar {
  padding: 34px 24px;
  background: #454641;
  border-right: 1px solid var(--stone-border);
}
.back-link {
  all: unset;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 22px;
  color: var(--stone);
  font-size: 13px;
  font-weight: 700;
}
.back-link:hover { color: var(--paper); }
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 30px;
}
.brand-name {
  font-family: 'Archivo Black', sans-serif;
  font-size: 22px;
  font-weight: 700;
  color: var(--paper);
}
.brand small {
  display: block;
  margin-top: 2px;
  color: var(--stone);
  font-size: 12px;
}
.side-title, .filter-label {
  display: block;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.side-title { margin: 24px 0 12px; color: var(--paper); }
.filter-group { margin-top: 16px; }
.filter-label { margin-bottom: 7px; color: var(--stone); }
input[type=text], select, textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--stone-border);
  border-radius: 8px;
  outline: 0;
  background: #454641;
  color: var(--paper);
  font-family: 'Inter', sans-serif;
  font-size: 13px;
}
select option { color: var(--paper); }
input:focus, select:focus, textarea:focus { border-color: var(--paper); }
input[type=range] { width: 100%; accent-color: var(--paper); }
.range-value { color: var(--paper); font-size: 12px; font-weight: 700; }
.selected-skills { display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0 6px; }
.selected-skill {
  border: 1px solid var(--stone-border);
  border-radius: 20px;
  padding: 4px 10px;
  color: var(--paper);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  background: #454641;
}
.run-button {
  width: 100%;
  margin-top: 24px;
  padding: 12px;
  border: none;
  border-radius: 8px;
  background: var(--paper);
  color: var(--bg-cream);
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.2s;
}
.run-button:hover { background: #FFFFFF; }

.main { padding: 46px clamp(24px, 5vw, 76px) 80px; }
.report-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--stone-border);
}
.report-head h1 {
  margin: 0;
  font-family: 'Archivo Black', sans-serif;
  font-size: clamp(28px, 4vw, 42px);
  font-weight: 700;
  color: var(--paper);
}
.report-head p { margin: 8px 0 0; color: var(--stone); }
.date { color: var(--stone); font-size: 12px; white-space: nowrap; font-weight: 500; }
.tabs { display: flex; gap: 28px; margin: 24px 0 28px; border-bottom: 1px solid var(--stone-border); }
.tab {
  padding: 0 0 12px;
  border: 0;
  border-bottom: 2px solid transparent;
  background: none;
  color: var(--stone);
  cursor: pointer;
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  font-size: 14px;
}
.tab.active { border-color: var(--paper); color: var(--paper); }
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 32px; }
.stat {
  min-height: 96px;
  padding: 18px;
  border: 1px solid var(--stone-border);
  border-radius: 14px;
  background: #454641;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
}
.stat span { display: block; color: var(--stone); font-size: 12px; font-weight: 500; }
.stat strong {
  display: block;
  margin-top: 10px;
  color: var(--paper);
  font-family: 'Archivo Black', sans-serif;
  font-size: 28px;
  font-weight: 700;
}
.panel { overflow: hidden; border: 1px solid var(--stone-border); border-radius: 16px; background: #454641; }
.table-head, .candidate {
  display: grid;
  grid-template-columns: 70px minmax(190px, 1.4fr) minmax(160px, 1.4fr) 90px 86px;
  align-items: center;
  gap: 16px;
}
.table-head {
  padding: 14px 22px;
  background: #454641;
  color: var(--paper);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.candidate { padding: 20px 22px; border-top: 1px solid var(--stone-border); }
.candidate:hover { background: var(--bg-cream); }
.rank { color: var(--stone); font-weight: 600; }
.rank.top { color: var(--paper); font-weight: 800; }
.prestige-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-left: 8px;
  padding: 2px 9px;
  border-radius: 20px;
  background: var(--gold);
  color: var(--bg-cream);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.03em;
  vertical-align: middle;
}
.candidate-name { color: var(--paper); font-family: 'Archivo Black', sans-serif; font-size: 20px; font-weight: 700; }
.candidate-meta { margin-top: 3px; color: var(--stone); font-size: 12px; }
.skill-summary, .badges { display: flex; flex-wrap: wrap; gap: 6px; }
.mini-skill { border-radius: 12px; padding: 3px 8px; background: #454641; color: var(--paper); font-size: 11px; font-weight: 600; }
.score { color: var(--paper); font-family: 'Archivo Black', sans-serif; font-size: 26px; font-weight: 700; }
.expand {
  padding: 8px 12px;
  border: 1px solid var(--paper);
  border-radius: 6px;
  background: transparent;
  color: var(--paper);
  cursor: pointer;
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  font-size: 12px;
  transition: all 0.15s ease;
}
.expand:hover { background: var(--paper); color: var(--bg-cream); }
.details-row { display: none; border-top: 1px solid var(--stone-border); background: var(--bg-cream); }
.details-row.open { display: block; }
.evidence { padding: 22px 24px 28px; }
.evidence-meta { color: var(--stone); font-size: 13px; margin-bottom: 18px; padding-bottom: 14px; border-bottom: 1px solid var(--stone-border); }
.evidence-section { padding: 16px 0; border-top: 1px solid var(--stone-border); }
.evidence-section:first-of-type { border-top: 0; padding-top: 0; }
.evidence-title { font-size: 11px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--paper); margin-bottom: 12px; }
.fit-summary { text-align: center; margin-bottom: 14px; }
.fit-big { font-family: 'Archivo Black', sans-serif; font-size: 38px; font-weight: 700; color: var(--paper); }
.metric-row { display: flex; align-items: center; gap: 12px; margin: 9px 0; }
.metric-label { width: 130px; flex: none; color: var(--stone); font-size: 12px; }
.metric-bar { flex: 1; height: 8px; border-radius: 5px; background: #454641; overflow: hidden; }
.metric-fill { height: 100%; background: var(--paper); border-radius: 5px; }
.metric-pct { width: 40px; text-align: right; color: var(--paper); font-size: 12px; font-weight: 700; }
.evidence-skills { display: flex; flex-wrap: wrap; gap: 8px 18px; }
.evidence-skill { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; color: var(--paper); }
.evidence-skill .mark { font-weight: 800; }
.evidence-skill.matched .mark { color: var(--match-green); }
.evidence-skill.missing { color: var(--stone); }
.why-text { margin: 0; color: var(--paper); line-height: 1.6; }
.next-steps { list-style: none; margin: 8px 0 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
.next-steps li { position: relative; padding-left: 18px; color: var(--paper); font-size: 13px; line-height: 1.4; }
.next-steps li:before { content: "→"; position: absolute; left: 0; color: var(--gold); font-weight: 800; }
.score-cell { display: flex; flex-direction: column; align-items: flex-end; gap: 2px; }
.badge { margin-top: 6px; padding: 4px 8px; border-radius: 5px; font-size: 11px; font-weight: 600; }
.match { background: var(--match-bg); color: var(--match-green); }
.missing { background: var(--missing-bg); color: var(--missing-red); }
.penalty-note { margin-top: 4px; color: var(--missing-red); font-size: 11px; font-weight: 700; }
.view { display: none; }
.view.active { display: block; }
.comparison { display: grid; grid-template-columns: repeat(auto-fit, minmax(215px, 1fr)); gap: 16px; }
.compare-card, .details-copy { padding: 22px; border: 1px solid var(--stone-border); border-radius: 14px; background: #454641; }
.compare-card h3 { margin: 8px 0; font-family: 'Archivo Black', sans-serif; font-size: 22px; font-weight: 700; color: var(--paper); }
.compare-card p { color: var(--stone); }
.details-copy { max-width: 760px; border-left: 3px solid var(--paper); color: var(--paper); }
.details-copy h2 { color: var(--paper); font-family: 'Archivo Black', sans-serif; }
.empty { padding: 46px; color: var(--stone); text-align: center; }

.toggle-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.toggle-hint { display: block; margin-top: 4px; color: var(--stone); font-size: 11px; line-height: 1.4; }
.switch { position: relative; display: inline-block; width: 36px; height: 20px; flex: none; }
.switch input { opacity: 0; width: 0; height: 0; }
.switch-slider { position: absolute; inset: 0; background: var(--stone-border); border-radius: 20px; cursor: pointer; transition: .18s; }
.switch-slider:before { content: ""; position: absolute; height: 14px; width: 14px; left: 3px; top: 3px; background: #454641; border-radius: 50%; transition: .18s; }
.switch input:checked+.switch-slider { background: var(--paper); }
.switch input:checked+.switch-slider:before { transform: translateX(16px); background: var(--gold); }

@media(max-width: 900px) {
  .app { display: block; }
  .sidebar { border-right: 0; border-bottom: 1px solid var(--stone-border); }
  .filter-row { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0 16px; }
  .stats { grid-template-columns: repeat(2, 1fr); }
  .table-head { display: none; }
  .candidate { grid-template-columns: 45px 1fr auto; }
  .candidate .skill-summary { display: none; }
  .upload-grid { grid-template-columns: 1fr; }
  .footer-card { flex-direction: column; text-align: center; }
}
@media(max-width: 560px) {
  .main { padding: 34px 17px 60px; }
  .landing-content { padding: 24px 16px 44px; }
  .hero-title { font-size: 34px; }
}
</style></head>
<body>

<!-- ===================== STAGE 1 — INTAKE / HOMEPAGE ===================== -->
<section class="stage active landing" id="landingStage">
  <header class="landing-header">
    <div class="nav-pill-bar">
      <div class="nav-logo-mark">
        <div class="logo-icon-badge">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0E1617" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <path d="M9 15l2 2 4-4"></path>
          </svg>
        </div>
        <span class="logo-wordmark">Shortlistr</span>
      </div>
      <ul class="nav-links">
        <li><a href="#howItWorks">Features</a></li>
      </ul>
      <button class="nav-cta-btn" onclick="document.getElementById('jdCard').scrollIntoView({behavior:'smooth'})">Get Started</button>
    </div>
  </header>

  <main class="landing-content">
    <!-- HERO 2-COLUMN GRID -->
    <div class="hero-grid">

      <!-- LEFT COLUMN: headline + subhead + CTAs + badges -->
      <div class="hero-left">
        <h1 class="hero-title">
          <span class="hero-title-line">No resume</span>
          <span class="hero-title-line">left unread.</span>
        </h1>

        <p class="hero-subhead">Screen candidates with complete transparency. Shortlistr combines precision keywords with context-aware AI so you never miss top talent — and always know why they matched.</p>

        <div class="hero-cta-row">
          <button class="hero-btn-primary" onclick="document.getElementById('jdCard').scrollIntoView({behavior:'smooth'})">Start Screening Free</button>
          <button class="hero-btn-outline" onclick="document.getElementById('howItWorks').scrollIntoView({behavior:'smooth'})">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="6 3 20 12 6 21 6 3"></polygon></svg>
            Watch 1-min demo
          </button>
        </div>
      </div>

      <!-- RIGHT COLUMN: Card-catalog drawer with fanned resume cards -->
      <div class="hero-right-pin-wrap" id="cardPinWrap">
      <div class="hero-right" id="cardStickyZone">
        <div class="fan-glow"></div>
        <div class="card-catalog" id="cardCatalog">
          <div class="catalog-guide-tab" id="catalogGuideTab">CV</div>

          <div class="catalog-fan">
            <div class="catalog-card layer-1"></div>
            <div class="catalog-card layer-2"></div>
            <div class="catalog-card layer-3"></div>
            <div class="catalog-card front">
              <div class="catalog-card-row">
                <span class="catalog-card-name">Candidate Match</span>
                <span class="catalog-card-badge" id="catalogBadge" data-target="92">92%</span>
              </div>
              <div class="catalog-card-role">Senior Backend Engineer</div>
              <div class="catalog-card-divider"></div>
              <div class="catalog-card-line"><span>Keyword Match</span><span>95%</span></div>
              <div class="catalog-bar-track"><div class="catalog-bar-fill keyword" data-target="95" style="width:95%"></div></div>
              <div class="catalog-card-line"><span>Semantic Context</span><span>88%</span></div>
              <div class="catalog-bar-track"><div class="catalog-bar-fill semantic" data-target="88" style="width:88%"></div></div>
              <div class="catalog-card-tags" id="catalogTags">
                <span class="catalog-tag">✓ Python — exact match</span>
                <span class="catalog-tag">✓ Distributed systems — implied</span>
              </div>
            </div>
          </div>

          <div class="catalog-drawer-box">
            <div class="catalog-drawer-label">Resumes — R&ndash;Z</div>
          </div>
        </div>
      </div>
      </div>

    </div><!-- /hero-grid -->

    <!-- TRUST BAR — feature tags, subtle, below the fold -->
    <div class="trust-bar" data-reveal-group>
      <div class="trust-item" data-reveal="up" style="transition-delay:0ms">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--gold)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        <span>Keyword Matching</span>
      </div>
      <div class="trust-item" data-reveal="up" style="transition-delay:100ms">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--gold)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 10 10H12V2z"></path></svg>
        <span>Semantic Search</span>
      </div>
      <div class="trust-item" data-reveal="up" style="transition-delay:200ms">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--gold)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
        <span>Explainable AI</span>
      </div>
    </div>

    <!-- HERO IMAGE CARD (RESUME PEDESTAL SCENE) -->
    <div class="hero-image-card" data-reveal-group>
      <!-- UPLOAD CARDS -->
      <div class="upload-grid">
        <div class="upload-card" id="jdCard" data-reveal="up" style="transition-delay:0ms">
          <div class="upload-card-header">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 3h7l4 4v14H7z"/><path d="M14 3v4h4"/><line x1="9.5" y1="12" x2="15.5" y2="12"/><line x1="9.5" y1="15.5" x2="15.5" y2="15.5"/></svg>
            <span>Job description</span>
          </div>

          <label class="upload-dropzone" for="jdFileInput">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--gold)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12"/><path d="M7 8l5-5 5 5"/><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/></svg>
            <strong>Import Job Description</strong>
            <span>Drop a file or click here to choose one</span>
          </label>
          <input id="jdFileInput" type="file" accept=".pdf,.doc,.docx,.txt" hidden>

          <div class="upload-file-list" id="jdFileList"></div>

          <textarea id="jobDescription" class="upload-textarea" rows="3" placeholder="…or paste the job description text here"></textarea>

          <button type="button" class="upload-action-btn" onclick="document.getElementById('jdFileInput').click()">Upload File</button>
          <span class="upload-status-line" id="jdStatus">Paste text or upload a file</span>
        </div>

        <div class="upload-card" id="resumeCard" data-reveal="up" style="transition-delay:120ms">
          <div class="upload-card-header">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h9l5 5v13H6z"/><path d="M15 3v5h5"/><circle cx="11.5" cy="13" r="2"/><path d="M8.5 18.5c.6-1.8 2-2.7 3-2.7s2.4.9 3 2.7"/></svg>
            <span>Resumes</span>
          </div>

          <label class="upload-dropzone" for="fileInput">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--gold)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12"/><path d="M7 8l5-5 5 5"/><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/></svg>
            <strong>Import Resume Files</strong>
            <span>Drop files or click here to choose (PDF or JPG)</span>
          </label>
          <input id="fileInput" type="file" accept=".pdf,.jpg,.jpeg" multiple hidden>

          <div class="upload-file-list" id="resumeFileList"></div>

          <button type="button" class="upload-action-btn" onclick="document.getElementById('fileInput').click()">Upload File</button>
          <span class="upload-status-line" id="resumeStatus">Upload PDF or JPG files</span>
        </div>
      </div>

      <button class="start-button" id="runButton" disabled>Start matching</button>
      <span class="start-hint" id="startHint">Add a job description and at least one resume to continue</span>
    </div>
  </main>

  <!-- DARK BAND SECTION -->
  <!-- anchor for 'See how it works' scroll -->
  <section class="dark-band-section" id="howItWorks">
    <div class="dark-band-content" data-reveal-group>
      <div class="dark-band-accent-badge" data-reveal="pop" style="transition-delay:0ms">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#0E1617" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12h4l3-9 5 18 3-9h5"/></svg>
      </div>
      <h2 class="dark-band-title" data-reveal="up" style="transition-delay:180ms">How it works</h2>
      <div class="dark-band-labels">
        <span data-reveal="up" style="transition-delay:380ms">Upload JD & Resumes</span>
        <span class="dark-band-label-arrow" data-reveal="arrow" style="transition-delay:560ms">
          <svg width="28" height="14" viewBox="0 0 28 14" fill="none">
            <path class="arrow-line" d="M1 7h20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path class="arrow-head" d="M17 2l6 5-6 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
          </svg>
        </span>
        <span data-reveal="up" style="transition-delay:680ms">Semantic Match</span>
        <span class="dark-band-label-arrow" data-reveal="arrow" style="transition-delay:860ms">
          <svg width="28" height="14" viewBox="0 0 28 14" fill="none">
            <path class="arrow-line" d="M1 7h20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            <path class="arrow-head" d="M17 2l6 5-6 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
          </svg>
        </span>
        <span data-reveal="up" style="transition-delay:980ms">Explainable Report</span>
      </div>
    </div>
  </section>

  <main class="landing-content" style="padding-top: 0;">
    <!-- FOOTER CARD -->
    <div class="footer-card" data-reveal-group>
      <div class="footer-info" data-reveal="up" style="transition-delay:0ms">
        <h3>Shortlistr</h3>
        <p>Hybrid keyword and semantic resume matching with transparent, explainable candidate scoring — no black-box AI decisions.</p>
      </div>
      <button class="footer-cta-btn" data-reveal="up" style="transition-delay:150ms" onclick="document.getElementById('jdCard').scrollIntoView({behavior:'smooth'})">Try it now &rarr;</button>
    </div>
  </main>
</section>

<!-- ===================== STAGE 2 — REPORT ===================== -->
<section class="stage" id="reportStage">
<div class="app">
<aside class="sidebar">
  <button class="back-link" id="backLink" type="button">&larr; New search</button>
  <div class="brand">
    <div class="logo-icon-badge">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0E1617" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
        <polyline points="14 2 14 8 20 8"></polyline>
        <path d="M9 15l2 2 4-4"></path>
      </svg>
    </div>
    <div><span class="brand-name">Shortlistr</span><small>Candidate shortlisting report</small></div>
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
      <span class="toggle-hint">Off by default. Scores already exclude name-recognition — this only reveals the signal, it never changes rank.</span>
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

/* ---------- Scroll reveal ---------- */
(function(){
  const groups=document.querySelectorAll('[data-reveal-group]');
  if(!groups.length)return;
  const reduceMotion=window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if(reduceMotion){groups.forEach(g=>g.classList.add('in-view'));return;}
  const io=new IntersectionObserver((entries)=>{
    entries.forEach(entry=>{
      if(entry.isIntersecting){
        entry.target.classList.add('in-view');
        io.unobserve(entry.target);
      }
    });
  },{threshold:0.2,rootMargin:'0px 0px -60px 0px'});
  groups.forEach(g=>io.observe(g));
})();

/* ---------- Hero card-catalog: scroll-jacked intro sequence + cursor tilt ---------- */
(function(){
  const pinWrap=document.getElementById('cardPinWrap');
  const stickyZone=document.getElementById('cardStickyZone');
  const cardCatalog=document.getElementById('cardCatalog');
  if(!pinWrap||!stickyZone||!cardCatalog)return;

  const reduceMotion=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const isDesktop=()=>window.matchMedia('(min-width: 901px)').matches;
  if(reduceMotion||!isDesktop())return; // static resting layout stays exactly as-is

  const cardEls=[
    document.querySelector('.catalog-card.layer-1'),
    document.querySelector('.catalog-card.layer-2'),
    document.querySelector('.catalog-card.layer-3'),
    document.querySelector('.catalog-card.front')
  ].filter(Boolean);
  const openVals=cardEls.map(el=>({
    tx: parseFloat(getComputedStyle(el).getPropertyValue('--tx'))||0,
    rot: parseFloat(getComputedStyle(el).getPropertyValue('--rot'))||0
  }));

  const badge=document.getElementById('catalogBadge');
  const bars=[...document.querySelectorAll('.catalog-bar-fill')];
  const barTargets=bars.map(b=>parseFloat(b.dataset.target)||0);
  const tags=document.getElementById('catalogTags');
  const frontCard=document.querySelector('.catalog-card.front');
  const guideTab=document.getElementById('catalogGuideTab');
  const badgeTarget=parseFloat(badge&&badge.dataset.target)||92;

  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
  const lerp=(a,b,t)=>a+(b-a)*t;
  const easeOutCubic=t=>1-Math.pow(1-t,3);

  function apply(progress){
    const p1=clamp(progress/0.55,0,1); // fan-out phase
    const p2=clamp((progress-0.55)/0.45,0,1); // zoom + data-reveal phase

    cardEls.forEach((el,i)=>{
      const delay=i*0.12;
      const local=easeOutCubic(clamp((p1-delay)/(1-delay*0.6),0,1));
      const tx=lerp(0,openVals[i].tx,local);
      const rot=lerp(0,openVals[i].rot,local);
      const ry=lerp(-18,0,local); // softened closed angle (was -70, read as a broken sliver)
      el.style.setProperty('--tx',tx.toFixed(2)+'px');
      el.style.setProperty('--rot',rot.toFixed(2)+'deg');
      el.style.setProperty('--ry',ry.toFixed(2)+'deg');
    });

    if(guideTab){
      guideTab.style.opacity=clamp((p1-0.55)/0.45,0,1); // only appears once the stack has mostly opened
    }
    if(frontCard){
      const scale=lerp(1,1.045,easeOutCubic(p2));
      frontCard.style.setProperty('--scale',scale.toFixed(3));
    }
    if(badge){
      badge.textContent=Math.round(lerp(0,badgeTarget,easeOutCubic(p2)))+'%';
    }
    bars.forEach((b,i)=>{
      b.style.width=lerp(0,barTargets[i],easeOutCubic(p2)).toFixed(1)+'%';
    });
    if(tags){
      tags.style.opacity=clamp(p2/0.35,0,1);
    }
  }

  /* ---- True scroll-jack: intercept scroll input and drive a virtual
     progress value until the sequence completes, THEN release real
     page scrolling. Re-engages if the user scrolls back to the top. ---- */
  let progress=0;
  let locked=true;
  apply(0);

  function onWheel(e){
    if(!locked)return;
    e.preventDefault();
    progress=clamp(progress+e.deltaY*0.0007,0,1);
    apply(progress);
    if(progress>=1&&e.deltaY>0)locked=false;
  }
  function onKey(e){
    if(!locked)return;
    const downKeys=['ArrowDown','PageDown',' '];
    const upKeys=['ArrowUp','PageUp'];
    if(downKeys.includes(e.key)){
      e.preventDefault();
      progress=clamp(progress+0.18,0,1);
      apply(progress);
      if(progress>=1)locked=false;
    }else if(upKeys.includes(e.key)){
      e.preventDefault();
      progress=clamp(progress-0.18,0,1);
      apply(progress);
    }
  }
  function enforceLock(){
    if(locked&&window.scrollY>0){
      window.scrollTo(0,0);
    }else if(!locked&&window.scrollY<=0){
      locked=true;
      progress=1;
      apply(1);
    }
  }

  window.addEventListener('wheel',onWheel,{passive:false});
  window.addEventListener('keydown',onKey,{passive:false});
  window.addEventListener('scroll',enforceLock,{passive:true});
  window.addEventListener('resize',()=>{if(!isDesktop())locked=false;});

  /* Cursor-reactive tilt on the whole card tableau */
  stickyZone.addEventListener('mousemove',e=>{
    if(!isDesktop())return;
    const r=stickyZone.getBoundingClientRect();
    const px=(e.clientX-r.left)/r.width-0.5;
    const py=(e.clientY-r.top)/r.height-0.5;
    cardCatalog.style.setProperty('--tiltX',(px*9).toFixed(2)+'deg');
    cardCatalog.style.setProperty('--tiltY',(py*-9).toFixed(2)+'deg');
  });
  stickyZone.addEventListener('mouseleave',()=>{
    cardCatalog.style.setProperty('--tiltX','0deg');
    cardCatalog.style.setProperty('--tiltY','0deg');
  });
})();


let selectedSkills=new Set(),prestigeEnabled=false;
const norm=v=>String(v||"").toLowerCase(),loc=c=>c.location||c.city||"Not specified",status=c=>c.employment_status||c.status||"Not specified",skills=c=>(c.matched_required||[]).concat(c.matched_preferred||[],c.missing_required||[],c.missing_preferred||[]);

/* ---------- Stage 1 behaviour ---------- */
let resumeFiles=[];

function formatFileSize(bytes){
  if(bytes<1024)return bytes+" B";
  if(bytes<1024*1024)return (bytes/1024).toFixed(0)+" KB";
  return (bytes/(1024*1024)).toFixed(1)+" MB";
}
function fileRowHTML(name,size,onRemoveAttr){
  return '<div class="upload-file-row">'
    +'<div class="upload-file-icon"><svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 3h7l4 4v14H7z"/><path d="M14 3v4h4"/></svg></div>'
    +'<div class="upload-file-meta"><div class="upload-file-name">'+name+'</div>'
    +'<div class="upload-file-sub"><span>'+size+'</span><span>&middot;</span><span class="done">&check; Completed</span></div></div>'
    +'<button type="button" class="upload-file-remove" '+onRemoveAttr+' aria-label="Remove file">'
    +'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>'
    +'</div>';
}

function jdProvided(){return byId("jobDescription").value.trim().length>0||byId("jdFileInput").files.length>0}
function refreshStart(){
  const ready=jdProvided()&&resumeFiles.length>0;
  byId("runButton").disabled=!ready;
  byId("startHint").textContent=ready?"Ready to match "+resumeFiles.length+" resume(s) against the listing":"Add a job description and at least one resume to continue";
}
byId("jobDescription").oninput=()=>{byId("jdStatus").textContent=byId("jobDescription").value.trim()?byId("jobDescription").value.trim().split(/\s+/).length+" words pasted":"Paste text or upload a file";refreshStart()};

function clearJdFile(){
  byId("jdFileInput").value="";
  byId("jdFileList").innerHTML="";
  byId("jdStatus").textContent=byId("jobDescription").value.trim()?byId("jobDescription").value.trim().split(/\s+/).length+" words pasted":"Paste text or upload a file";
  refreshStart();
}
byId("jdFileInput").onchange=e=>{
  const file=e.target.files[0];
  if(!file)return;
  byId("jdFileList").innerHTML=fileRowHTML(file.name,formatFileSize(file.size),'onclick="clearJdFile()"');
  byId("jdStatus").textContent=file.name;
  if(file.name.toLowerCase().endsWith(".txt")){
    const reader=new FileReader();
    reader.onload=r=>{byId("jobDescription").value=r.target.result;byId("jdStatus").textContent=byId("jobDescription").value.trim().split(/\s+/).length+" words loaded"};
    reader.readAsText(file);
  }
  refreshStart();
};

function renderResumeFileList(){
  byId("resumeFileList").innerHTML=resumeFiles.map((f,i)=>fileRowHTML(f.name,formatFileSize(f.size),'onclick="removeResumeFile('+i+')"')).join("");
  byId("resumeStatus").textContent=resumeFiles.length?resumeFiles.length+" resume(s) added":"Upload PDF or JPG files";
}
function removeResumeFile(i){
  resumeFiles.splice(i,1);
  renderResumeFileList();
  refreshStart();
}
byId("fileInput").onchange=e=>{
  resumeFiles=[...resumeFiles,...e.target.files];
  e.target.value="";
  renderResumeFileList();
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