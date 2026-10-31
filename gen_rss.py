#!/usr/bin/env python3
"""Generate rss.xml from posts.jsonl. Run after editing posts."""
import json, os, sys, email.utils, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
POSTS = os.path.join(ROOT, "posts.jsonl")
OUT = os.path.join(ROOT, "rss.xml")

if "SITE_URL" not in os.environ:
    print("warning: SITE_URL not set; using https://example.com/. Set SITE_URL to your real site URL.", file=sys.stderr)
BASE = os.environ.get("SITE_URL", "https://example.com/").rstrip("/") + "/"

def rfc822(iso):
    if not iso:
        return email.utils.formatdate(usegmt=True)
    try:
        d = datetime.date.fromisoformat(iso[:10])
    except ValueError:
        return email.utils.formatdate(usegmt=True)
    dt = datetime.datetime(d.year, d.month, d.day, tzinfo=datetime.timezone.utc)
    return email.utils.formatdate(dt.timestamp(), usegmt=True)

def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))

def main():
    posts = []
    with open(POSTS, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                posts.append(json.loads(line))
    posts.sort(key=lambda p: p.get("date", ""), reverse=True)

    items = []
    for p in posts:
        title = p.get("title") or "(untitled)"
        link = p.get("url") or BASE
        desc_parts = []
        if p.get("description"):
            desc_parts.append(p["description"])
        if p.get("body"):
            desc_parts.append(p["body"])
        links = p.get("links") or []
        if links:
            lines = ["See also:"]
            for l in links:
                if isinstance(l, str):
                    lines.append(f"- {l}")
                else:
                    label = l.get("label") or l.get("text") or l.get("title") or l.get("url")
                    url = l.get("url")
                    lines.append(f"- {label} — {url}" if url else f"- {label}")
            desc_parts.append("\n".join(lines))
        desc = "\n\n".join(desc_parts)
        items.append(f"""    <item>
      <title>{esc(title)}</title>
      <link>{esc(link)}</link>
      <guid isPermaLink="false">{esc(link)}#{esc(p.get('date',''))}</guid>
      <pubDate>{rfc822(p.get('date'))}</pubDate>
      <description><![CDATA[{desc}]]></description>
    </item>""")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>micro-blog — Giorgos Logiotatidis</title>
    <link>{BASE}</link>
    <description>Personal activity log: things I build, in order.</description>
    <language>en</language>
    <atom:link href="{BASE}rss.xml" rel="self" type="application/rss+xml" />
{chr(10).join(items)}
  </channel>
</rss>
"""
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"wrote {OUT} ({len(posts)} items)")

if __name__ == "__main__":
    main()
