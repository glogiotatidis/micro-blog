# micro-blog

A personal activity log by Giorgos Logiotatidis — things I build, in order.

A zero-build, Twitter-like timeline. Hosted on GitHub Pages.

## How it works

- Write posts as Markdown files in `posts/` with YAML frontmatter.
- Run `python3 build.py` to compile them into `posts.jsonl` (and regenerate `rss.xml`).
- `index.html` + `app.js` + `style.css` render `posts.jsonl` (one JSON object per line, newest first).
- No runtime build step, no browser dependencies. Build-time needs Python 3 + PyYAML.

## Add a post (for humans)

Create `posts/YYYY-MM-DD-my-thing.md`:

```markdown
---
title: my thing
date: 2026-10-31
url: https://github.com/...
description: one-liner
tags: [rust, cli]
links:
  - label: GitHub
    url: https://github.com/...
---

Optional body markdown. Paragraphs, fenced code, bullet lists, ## headings.
```

Then run `python3 build.py`.

## Add a post (for an LLM)

Give your LLM this instruction:

> See the Obsidian note `Style - Giorgos Logiotatidis.md` for the full voice, shape, and checklist. The post schema: `posts/YYYY-MM-DD-<slug>.md` with YAML frontmatter (`title`, `date`, `url`, `description`, `tags`, `links`, `image`) plus a Markdown body. Do not edit other files. Then run `python3 build.py` (set `SITE_URL`) to regenerate `posts.jsonl` and `rss.xml`.

Validate before committing:

```sh
python3 build.py && python3 -c "import json; [json.loads(l) for l in open('posts.jsonl') if l.strip()]; print('ok')"
```

## Deploy (GitHub Pages)

1. Push to GitHub.
2. Repo → Settings → Pages → Source: "Deploy from a branch" → branch `main`, folder `/ (root)`.
3. Site appears at `https://<user>.github.io/<repo>/`.

The included GitHub Action regenerates `posts.jsonl` and `rss.xml` on push.

## Local preview

```sh
python3 build.py && python3 -m http.server 8000
# open http://localhost:8000
```

(`fetch()` needs a server; opening `index.html` via `file://` won't load posts.)
