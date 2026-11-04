#!/usr/bin/env python3
"""Build a preview of the timeline from posts/ plus drafts/, without publishing.

Drafts live in drafts/ in exactly the same format as posts/ but are never
compiled into posts.jsonl, so the deployed site never sees them. This script
renders them next to the published entries, marked with a "draft" badge, into
preview/ and can serve that directory for a browser check.

    python3 preview.py              # build preview/ and print lint warnings
    python3 preview.py --serve      # build, then serve on http://0.0.0.0:8765
    python3 preview.py --serve --port 9000
"""
import argparse
import glob
import http.server
import json
import os
import re
import socket
import socketserver
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR = os.path.join(ROOT, "posts")
DRAFTS_DIR = os.path.join(ROOT, "drafts")
OUT_DIR = os.path.join(ROOT, "preview")

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


def split_frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        return None, text
    return yaml.safe_load(m.group(1)) or {}, m.group(2).strip()


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


def load_dir(directory, is_draft):
    """Compile a directory of post markdown files into post dicts."""
    entries = []
    for path in sorted(glob.glob(os.path.join(directory, "*.md"))):
        name = os.path.basename(path)
        with open(path, encoding="utf-8") as f:
            fm, body = split_frontmatter(f.read())
        if fm is None:
            print(f"  ! {name}: no YAML frontmatter, skipping", file=sys.stderr)
            continue
        slug = os.path.splitext(name)[0]
        m = re.match(r"^(\d{4}-\d{2}-\d{2})", slug)
        entry = {
            "date": norm_date(fm.get("date"), m.group(1) if m else None),
            "title": fm.get("title") or slug,
            "url": fm.get("url"),
            "description": fm.get("description"),
            "body": body or None,
            "tags": fm.get("tags"),
            "links": norm_links(fm.get("links")),
            "image": fm.get("image"),
        }
        if is_draft:
            entry["draft"] = True
        entries.append((name, entry))
    return entries


# Style-guide checks from Skill - Giorgos Logiotatidis.md. Warnings only.
def lint(name, post):
    warn = []
    title = post.get("title") or ""
    desc = post.get("description") or ""
    body = post.get("body") or ""
    if not post.get("description"):
        warn.append("no description (the hook is the entry's first line)")
    if len(title) > 60:
        warn.append(f"title is {len(title)} chars, guide says <= 60")
    if title.endswith("."):
        warn.append("title ends with a period")
    if len(desc.split()) > 45:
        warn.append(f"description is {len(desc.split())} words, guide says <= 45")
    text = f"{title}\n{desc}\n{body}"
    if re.search(r"[—–]", text):
        warn.append("em/en dash (the corpus has none)")
    if re.search(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", text):
        warn.append("emoji")
    if re.search(r"(^|\s)#\w", text):
        warn.append("hashtag")
    if text.count("!") > 1:
        warn.append(f"{text.count('!')} exclamation marks, guide says at most 1")
    for word in ("dive in", "deep dive", "delve", "leverage", "seamless", "robust",
                 "game-changer", "unlock", "empower", "journey", "cutting-edge",
                 "excited to", "thrilled to", "in conclusion", "here's the thing"):
        if word in text.lower():
            warn.append(f"marketing word: '{word}'")
    for line in body.split("\n"):
        if re.match(r"^\s*\d+\.\s+", line):
            warn.append("numbered list (renderer only does bullets)")
            break
    for line in body.split("\n"):
        if re.match(r"^\s*>", line):
            warn.append("blockquote (not rendered)")
            break
    if re.search(r"(?<!\*)\*[^*\n]+\*(?!\*)", body):
        warn.append("italics (not rendered, use bold)")
    if "<" in body and re.search(r"<[a-zA-Z/][^>]*>", body):
        warn.append("raw HTML (not rendered)")
    return warn


def build():
    os.makedirs(DRAFTS_DIR, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    published = load_dir(POSTS_DIR, is_draft=False)
    drafts = load_dir(DRAFTS_DIR, is_draft=True)

    posts = [p for _, p in published] + [p for _, p in drafts]
    posts.sort(key=lambda p: p.get("date") or "", reverse=True)
    with open(os.path.join(OUT_DIR, "posts.jsonl"), "w", encoding="utf-8") as f:
        for p in posts:
            f.write(json.dumps(p, ensure_ascii=False, separators=(",", ":")) + "\n")

    # Derive the preview page from the real one so they cannot drift apart.
    with open(os.path.join(ROOT, "index.html"), encoding="utf-8") as f:
        html = f.read()
    swaps = [
        ('href="./style.css"', 'href="../style.css"'),
        ('src="./app.js"', 'src="../app.js"'),
        ('href="./about.html"', 'href="../about.html"'),
        ('href="./old-blog/"', 'href="../old-blog/"'),
        ('href="./rss.xml"', 'href="../rss.xml"'),
        ('href="./index.html"', 'href="index.html"'),
        ("<title>micro-blog</title>", "<title>micro-blog · preview</title>"),
        ('<meta name="viewport"',
         '<meta name="robots" content="noindex" />\n  <meta name="viewport"'),
        ('<div id="timeline"',
         '<div class="preview-banner">preview · %d published · %d draft%s · drafts are not on the site yet</div>\n    <div id="timeline"'),
    ]
    for old, new in swaps:
        if old not in html:
            print(f"preview: index.html no longer contains {old!r}, template changed",
                  file=sys.stderr)
            return 1
        html = html.replace(old, new, 1)
    html = html % (len(published), len(drafts), "" if len(drafts) == 1 else "s")
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    print(f"preview: {len(published)} published + {len(drafts)} draft -> preview/")
    problems = 0
    for name, post in drafts:
        warn = lint(name, post)
        if warn:
            problems += len(warn)
            print(f"  {name}")
            for w in warn:
                print(f"    - {w}")
    if not problems:
        print("  drafts pass the style checks")
    return 0


def serve(port):
    os.chdir(ROOT)

    class Handler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            super().end_headers()

        def log_message(self, format, *args):
            pass

    class Server(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    with Server(("0.0.0.0", port), Handler) as httpd:
        print(f"preview served at http://127.0.0.1:{port}/preview/ (ctrl-c to stop)")
        for ip in lan_ips():
            print(f"  also http://{ip}:{port}/preview/")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")


def lan_ips():
    ips = []
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ips.append(s.getsockname()[0])
    except OSError:
        pass
    finally:
        s.close()
    try:
        out = os.popen("hostname -I").read().split()
    except OSError:
        out = []
    for ip in out:
        if ip not in ips and not ip.startswith("127."):
            ips.append(ip)
    return ips


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--serve", action="store_true", help="serve the preview after building")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    rc = build()
    if rc == 0 and args.serve:
        serve(args.port)
    return rc


if __name__ == "__main__":
    sys.exit(main())
