#!/usr/bin/env python3
"""Compile posts/*.md into posts.jsonl, p/<slug>/ permalink pages and rss.xml."""
import glob, json, os, re, shutil, sys

import sitepage

ROOT = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR = os.path.join(ROOT, "posts")
PAGES_DIR = os.path.join(ROOT, "p")
OUT_JSONL = os.path.join(ROOT, "posts.jsonl")
SITE_URL = os.environ.get("SITE_URL", "").strip() or "https://giorgos.sealabs.net/"

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

def split_frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    fm = yaml.safe_load(m.group(1)) or {}
    body = m.group(2).strip()
    return fm, body

def norm_date(v, fallback):
    if v is None:
        return fallback
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return str(v)

def norm_links(v):
    if not v:
        return None
    out = []
    for item in v:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict):
            out.append({"label": item.get("label") or item.get("text") or item.get("title"),
                        "url": item.get("url") or item.get("href")})
    return out or None

posts = []
os.makedirs(POSTS_DIR, exist_ok=True)
for path in sorted(glob.glob(os.path.join(POSTS_DIR, "*.md"))):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    fm, body = split_frontmatter(text)
    slug = os.path.splitext(os.path.basename(path))[0]
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", slug)
    fallback_date = m.group(1) if m else None
    date = norm_date(fm.get("date"), fallback_date)
    post = {
        "date": date,
        "slug": slug,
        "title": fm.get("title") or slug,
        "url": fm.get("url"),
        "description": fm.get("description"),
        "body": body or None,
        "html": sitepage.render_markdown(body) or None,
        "tags": fm.get("tags"),
        "links": norm_links(fm.get("links")),
        "image": fm.get("image"),
    }
    posts.append(post)
posts.sort(key=lambda p: p.get("date") or "", reverse=True)

with open(OUT_JSONL, "w", encoding="utf-8") as f:
    for p in posts:
        f.write(json.dumps(p, ensure_ascii=False, separators=(",", ":")) + "\n")

print(f"compiled {len(posts)} posts -> {OUT_JSONL}")

# One page per post, so /p/<slug>/ is a real URL. Rebuilt from scratch so a
# removed or renamed post cannot leave a stale page behind.
if os.path.isdir(PAGES_DIR):
    shutil.rmtree(PAGES_DIR)
for p in posts:
    out_dir = os.path.join(PAGES_DIR, p["slug"])
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(sitepage.post_page(p, prefix="../../", site_url=SITE_URL))
print(f"rendered {len(posts)} permalink pages -> {PAGES_DIR}")

rss_script = os.path.join(ROOT, "gen_rss.py")
if os.path.exists(rss_script):
    import subprocess
    env = dict(os.environ, SITE_URL=SITE_URL)
    subprocess.run([sys.executable, rss_script], check=False, env=env)
