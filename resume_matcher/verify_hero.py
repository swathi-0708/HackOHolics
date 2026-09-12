with open('resume_matcher/output/preview.html', 'r', encoding='utf-8') as f:
    c = f.read()

checks = [
    # NAV FIX - nav-cta-btn should only appear in CSS, not as an HTML element
    ('Nav CTA button removed from HTML', 'onclick' not in c.split('nav-cta-btn')[1].split('</style>')[0] if 'nav-cta-btn' in c else True),
    ('No nav CTA button tag in body', '<button class="nav-cta-btn"' not in c),
    # CARD STACK
    ('Exactly 4 fan-cards in HTML', c.count('class="fan-card"') == 4),
    ('Gold tab 89% present', '>89%<' in c),
    ('Muted tab 82% present', '>82%<' in c),
    ('Back card opacity 0.40', '0.40' in c),
    ('Card 3 opacity 0.60', '0.60' in c),
    ('Card 2 opacity 0.85', '0.85' in c),
    ('Front card z-index 4', 'z-index: 4' in c),
    ('Overflow visible for tabs', 'overflow: visible' in c),
    ('Tab top -28px', 'top: -28px' in c),
    ('Tab z-index 5', 'z-index: 5' in c),
    ('fan-stack width 300px', '300px' in c),
    ('fan-card height 280px', 'height: 280px' in c),
    ('w-80 utility class', 'w-80' in c),
    ('Padding-top 40px for tab clearance', 'padding-top: 40px' in c),
    # LEFT COLUMN UNCHANGED
    ('Hero title No resume', 'No resume' in c),
    ('Hero title left unread', 'left unread' in c),
    ('Hero subhead present', 'Hybrid keyword' in c),
    ('Primary CTA button', 'hero-btn-primary' in c),
    ('Outline CTA button', 'hero-btn-outline' in c),
    ('Feature badges present', 'feature-badge-row' in c),
]
all_pass = True
print('=== VERIFICATION ===')
for name, result in checks:
    status = 'PASS' if result else 'FAIL'
    if not result:
        all_pass = False
    print(f'  [{status}] {name}')
print()
print('Overall:', 'ALL PASS' if all_pass else 'SOME FAILURES')
