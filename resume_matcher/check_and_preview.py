import sys
sys.path.insert(0, 'resume_matcher/src')
from ui_generator import HTML_TEMPLATE

print("=== SOURCE FILE CHECKS ===")
print(f"  [{'OK' if 'nav-cta-btn' not in HTML_TEMPLATE or HTML_TEMPLATE.count('onclick') < 2 else 'MISSING'}] Nav CTA button removed from HTML body")

btn_count = HTML_TEMPLATE.count('class="fan-card"')
print(f"  [{'OK' if btn_count == 4 else 'WRONG: ' + str(btn_count)}] Exactly 4 fan-cards (found {btn_count})")

print(f"  [{'OK' if 'overflow: visible' in HTML_TEMPLATE else 'MISSING'}] overflow: visible on cards (tab clip fix)")
print(f"  [{'OK' if 'z-index: 4' in HTML_TEMPLATE else 'MISSING'}] Front card z-index: 4")
print(f"  [{'OK' if '>89%<' in HTML_TEMPLATE else 'MISSING'}] Gold tab 89%")
print(f"  [{'OK' if '>82%<' in HTML_TEMPLATE else 'MISSING'}] Muted tab 82%")
print(f"  [{'OK' if 'padding-top: 40px' in HTML_TEMPLATE else 'MISSING'}] padding-top: 40px tab clearance")
print(f"  [{'OK' if '300px' in HTML_TEMPLATE else 'MISSING'}] fan-stack width 300px")
print(f"  [{'OK' if 'height: 280px' in HTML_TEMPLATE else 'MISSING'}] fan-card height 280px")

print()
print("=== WRITING FRESH PREVIEW ===")
html = HTML_TEMPLATE
html = html.replace('{{JD_TITLE}}', 'Preview')
html = html.replace('{{CANDIDATES_JSON}}', '[]')
html = html.replace('{{JD_TEXT}}', '')
html = html.replace('{{RENDER_TS}}', '2026-09-12')
html = html.replace('{{PIPELINE_MS}}', '0')
html = html.replace('{{DATA_JSON}}', '{"jd_required_skills":[],"candidates":[]}')

with open('resume_matcher/output/preview.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Done! Open http://localhost:8000/preview.html to see the result.")