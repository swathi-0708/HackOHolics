import os
import re
import shutil
from collections import defaultdict

SOURCE_DIR = "."
OUTPUT_DIR = "curated"

EXT_PRIORITY = [".pdf", ".docx", ".txt"]  # .xml intentionally excluded - unsupported

# Role -> fit tier for a "Junior Full Stack Developer Intern" JD.
# Adjust this dict for a different JD.
ROLE_FIT = {
    "web_dev": "strong", "webdev": "strong",
    "app_dev": "strong", "appdev": "strong",
    "sde": "strong",
    "python_dev": "strong", "python": "strong",
    "full_stack": "strong", "fullstack": "strong",
    "ai_dev": "partial", "ai_developer": "partial",
    "data_scientist": "partial", "ds_resume": "partial",
    "cloud": "partial", "devops": "partial", "qa": "partial",
    "cyber_sec": "partial", "cybersec": "partial",
    "marketing": "weak", "hr": "weak", "sales": "weak",
    "video_editing": "weak", "video_editor": "weak",
    "content_creation": "weak", "content_creator": "weak",
    "social_media_intern": "weak", "founders_office": "weak",
    "finance": "weak", "operations": "weak", "business": "weak",
    "graphic_designer": "weak", "designer": "weak", "design": "weak",
    "customer_success": "weak", "it_support": "weak",
    "blockchain": "partial", "game_developer": "partial",
    "embedded_systems": "partial", "ml_engineer": "partial",
    "devrel": "weak", "product_manager": "weak", "technical_writer": "weak",
    "ui_ux": "weak", "data_analyst": "partial",
}

# How many resumes to pull into the final curated demo set per tier.
TIER_QUOTA = {"strong": 8, "partial": 6, "weak": 5}


def stem_key(filename: str) -> str:
    """Filename without extension, lowercased, for duplicate detection."""
    return os.path.splitext(filename)[0].lower()


def classify_role(filename: str) -> str:
    """Best-effort role tag from filename, for fit-tier assignment."""
    lower = filename.lower()
    for role in ROLE_FIT:
        if role.replace("_", "") in lower.replace("_", "").replace(" ", "").replace("-", ""):
            return role
    return "unknown"


def main():
    files = [f for f in os.listdir(SOURCE_DIR) if os.path.isfile(f)]

    # --- Step 1: dedupe by stem, keep the highest-priority extension ---
    groups = defaultdict(list)
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext in EXT_PRIORITY:
            groups[stem_key(f)].append(f)

    deduped = []
    for stem, variants in groups.items():
        variants.sort(key=lambda f: EXT_PRIORITY.index(os.path.splitext(f)[1].lower()))
        deduped.append(variants[0])
        if len(variants) > 1:
            print(f"[dedupe] '{stem}': kept {variants[0]}, dropped {variants[1:]}")

    print(f"\n{len(files)} files -> {len(deduped)} after format-dedupe\n")

    # --- Step 2: classify by role, bucket into fit tiers ---
    buckets = defaultdict(list)
    for f in deduped:
        role = classify_role(f)
        tier = ROLE_FIT.get(role, "unknown")
        buckets[tier].append(f)

    for tier in ("strong", "partial", "weak", "unknown"):
        print(f"{tier}: {len(buckets[tier])} files")
        for f in buckets[tier][:5]:
            print(f"   - {f}")

    # --- Step 3: pick a demo-sized subset and copy into a clean folder ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    selected = []
    for tier, quota in TIER_QUOTA.items():
        chosen = sorted(buckets[tier])[:quota]
        selected.extend(chosen)

    print(f"\nCopying {len(selected)} curated resumes into '{OUTPUT_DIR}/':")
    for f in selected:
        shutil.copy(f, os.path.join(OUTPUT_DIR, f))
        print(f"   + {f}")

    if buckets["unknown"]:
        print(f"\n{len(buckets['unknown'])} file(s) couldn't be auto-classified "
              f"(not included above) - review manually if you want them included:")
        for f in buckets["unknown"]:
            print(f"   ? {f}")

    return deduped, buckets


if __name__ == "__main__":
    main()