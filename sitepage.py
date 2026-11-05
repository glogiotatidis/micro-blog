#!/usr/bin/env python3
"""Post -> standalone HTML page, plus the Markdown subset renderer.

The timeline is rendered in the browser from posts.jsonl, but a permalink
needs a URL that can be shared, opened and previewed without running
JavaScript. So the build prerenders one page per post under p/<slug>/, and
bakes the same rendered HTML into posts.jsonl as an "html" field so the
timeline and the permalink page can never disagree.

render_markdown() mirrors renderMarkdown() in app.js (paragraphs, bold, inline
code, links, bare urls, fenced code, ##/### headings, bullet lists). Keep the
two in step; app.js only falls back to its own copy when "html" is missing.
"""
import re

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def escape_html(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def inline(s):
    t = escape_html(s)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
               r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    # bare urls; trailing punctuation stays outside the link
    t = re.sub(r"(^|[\s(])(https?://[^\s)]*[^\s).,;:!?])",
               r'\1<a href="\2" target="_blank" rel="noopener">\2</a>', t)
    return t


def render_markdown(src):
    if not src:
        return ""
    lines = str(src).split("\n")
    out = []
    para = []

    def flush():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()

    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"^```", line):
            flush()
            code = []
            i += 1
            while i < len(lines) and not re.match(r"^```", lines[i]):
                code.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>" + escape_html("\n".join(code)) + "</code></pre>")
            continue
        if re.match(r"^#{2,3}\s+", line):
            flush()
            level = "h4" if line.startswith("###") else "h3"
            text = inline(re.sub(r"^#{2,3}\s+", "", line))
            out.append("<%s>%s</%s>" % (level, text, level))
            i += 1
            continue
        if re.match(r"^[-*]\s+", line):
            flush()
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i]):
                items.append(re.sub(r"^[-*]\s+", "", lines[i]))
                i += 1
            out.append("<ul>" + "".join("<li>" + inline(it) + "</li>" for it in items) + "</ul>")
            continue
        if line.strip() == "":
            flush()
            i += 1
            continue
        para.append(line)
        i += 1
    flush()
    return "".join(out)


def format_date(iso):
    """'2026-11-04' -> 'Nov 4, 2026', the same shape the timeline prints."""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", str(iso or ""))
    if not m:
        return str(iso or "")
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not 1 <= mo <= 12:
        return str(iso)
    return f"{MONTHS[mo - 1]} {d}, {y}"


def permalink(post, site_url):
    base = (site_url or "").rstrip("/")
    return f"{base}/p/{post['slug']}/" if base else ""


HEADER = """  <header class="site-header">
    <div class="container">
      <div class="header-row">
        <div>
          <h1 class="site-title"><a href="{p}index.html">micro-blog</a></h1>
          <p class="site-tagline">personal activity log · Giorgos Logiotatidis</p>
        </div>
        <nav class="site-nav">
          <a href="{p}index.html">timeline</a>
          <a href="{p}about.html">about</a>
          <a href="{p}old-blog/">old blog</a>
          <a href="https://github.com/glogiotatidis" target="_blank" rel="noopener">github</a>
        </nav>
      </div>
    </div>
  </header>"""

FOOTER = """  <footer class="site-footer">
    <div class="container footer-row">
      <span class="footer-left">sealabs.net — since 1998</span>
      <a class="footer-rss" href="{p}rss.xml">RSS like it's 2010. you don't need the Algorithm</a>
    </div>
  </footer>"""


def post_page(post, prefix="../../", site_url=None, draft=False):
    """A permalink page for one post. `prefix` walks back to the site root."""
    title = post.get("title") or post.get("slug") or "(untitled)"
    parts = []
    if post.get("date"):
        parts.append(f'<span class="card-date">{escape_html(format_date(post["date"]))}</span>')
    if draft:
        parts.append('<span class="draft-badge">draft</span>')
    meta = "".join(parts)

    if post.get("url"):
        heading = (f'<h1 class="card-title"><a href="{escape_html(post["url"])}" '
                   f'target="_blank" rel="noopener">{escape_html(title)}</a></h1>')
    else:
        heading = f'<h1 class="card-title">{escape_html(title)}</h1>'

    desc = (f'<p class="card-desc">{inline(post["description"])}</p>'
            if post.get("description") else "")
    body_html = post.get("html") or render_markdown(post.get("body"))
    body = f'<div class="card-body">{body_html}</div>' if body_html else ""
    img = (f'<img class="card-image" src="{escape_html(post["image"])}" alt="" />'
           if post.get("image") else "")
    tags = "".join(f'<span class="tag">{escape_html(t)}</span>' for t in (post.get("tags") or []))
    tags_html = f'<div class="card-tags">{tags}</div>' if tags else ""
    link_items = []
    for l in (post.get("links") or []):
        if isinstance(l, str):
            label, url = l, l
        else:
            label = l.get("label") or l.get("text") or l.get("title") or l.get("url")
            url = l.get("url")
        target = (f' target="_blank" rel="noopener"' if re.match(r"^https?:", str(url or "")) else "")
        link_items.append(f'<li><a href="{escape_html(url or "")}"{target}>{escape_html(label or "")}</a></li>')
    links_html = ('<div class="see-also"><p class="see-also-title">See also</p><ul>'
                  + "".join(link_items) + "</ul></div>") if link_items else ""

    canonical = permalink(post, site_url)
    head = [
        '  <meta charset="utf-8" />',
        '  <meta name="viewport" content="width=device-width, initial-scale=1" />',
        f"  <title>{escape_html(title)} · micro-blog</title>",
    ]
    if post.get("description"):
        head.append(f'  <meta name="description" content="{escape_html(post["description"])}" />')
    if draft:
        head.append('  <meta name="robots" content="noindex" />')
    if canonical and not draft:
        head += [
            f'  <link rel="canonical" href="{escape_html(canonical)}" />',
            '  <meta property="og:type" content="article" />',
            f'  <meta property="og:title" content="{escape_html(title)}" />',
            f'  <meta property="og:url" content="{escape_html(canonical)}" />',
            '  <meta property="og:site_name" content="micro-blog" />',
        ]
        if post.get("description"):
            head.append(f'  <meta property="og:description" content="{escape_html(post["description"])}" />')
        if post.get("date"):
            head.append(f'  <meta property="article:published_time" content="{escape_html(str(post["date"])[:10])}" />')
        head.append('  <meta name="twitter:card" content="summary" />')
    head += [
        f'  <link rel="stylesheet" href="{prefix}style.css" />',
        f'  <link rel="alternate" type="application/rss+xml" title="micro-blog" href="{prefix}rss.xml" />',
    ]

    article_class = "card card-post card-draft" if draft else "card card-post"
    page = f"""<!doctype html>
<html lang="en">
<head>
{chr(10).join(head)}
</head>
<body>
{HEADER.format(p=prefix)}

  <main class="container">
    <article class="{article_class}" id="{escape_html(post.get('slug') or '')}">
      <div class="card-meta">{meta}</div>
      {heading}
      {desc}
      {body}
      {img}
      {tags_html}
      {links_html}
    </article>
    <nav class="post-nav"><a href="{prefix}index.html">all posts</a></nav>
  </main>

{FOOTER.format(p=prefix)}
</body>
</html>
"""
    return page
