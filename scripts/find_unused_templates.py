import os
import re
from pathlib import Path

PROJECT_ROOT = Path(r"C:\Users\55124152\OneDrive - MMU\DLS\OER_Rebirth")
TEMPLATES_ROOT = PROJECT_ROOT / "templates"
OUTPUT_DIR = PROJECT_ROOT / ".continue" / "agents"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 1. Collect all template files relative to TEMPLATES_ROOT
template_files = []

for path in TEMPLATES_ROOT.rglob("*.html"):
    rel = path.relative_to(TEMPLATES_ROOT)  # e.g. admin/resources/export.html
    template_files.append((path, rel.as_posix()))
    

# 2. Build a big searchable text corpus of all .py and .html files
search_roots = [
    PROJECT_ROOT / "resources",
    PROJECT_ROOT / "oer_rebirth",
    PROJECT_ROOT / "templates",
    PROJECT_ROOT / "scripts",
]

code_files = []
for root in search_roots:
    for ext in ("*.py", "*.html"):
        code_files.extend(root.rglob(ext))

corpus = ""
for f in code_files:
    try:
        text = f.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    corpus += "\n" + text

# 3. For each template, check if its relative path or just filename appears
unused = []
for full_path, rel_path in template_files:
    name_only = full_path.name  # e.g. export.html
    rel_str = rel_path          # e.g. admin/resources/export.html

    # Look for either full relative path or filename anywhere in corpus
    if (rel_str not in corpus) and (name_only not in corpus):
        unused.append(str(full_path))

# 4. Write results
out_file = OUTPUT_DIR / "maybe_unused_templates_clean.txt"
with out_file.open("w", encoding="utf-8") as f:
    for p in sorted(unused):
        f.write(p + "\n")

print(f"Wrote {len(unused)} candidates to {out_file}")
