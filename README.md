# micro-blog

A personal activity log by Giorgos Logiotatidis — things I build, in order.

A zero-build, Twitter-like timeline. Hosted on GitHub Pages.

## How it works

- Write posts as Markdown files in `posts/` with YAML frontmatter.
- Run `python3 build.py` to compile them into `posts.jsonl` (and regenerate `rss.xml`).
- `index.html` + `app.js` + `style.css` render `posts.jsonl` (one JSON object per line, newest first).
- No runtime build step, no browser dependencies. Build-time needs Python 3 + PyYAML.

## Permalinks

Each post has its own page at `p/<slug>/`, e.g.
`https://giorgos.sealabs.net/p/2026-11-04-greek-tv-streamio/`. The slug is the
filename without `.md`, so the URL is fixed by the post file.

`build.py` prerenders those pages (`sitepage.py`) and bakes the rendered HTML into
`posts.jsonl` as an `html` field, so the timeline and the permalink page show the
same markup. The page carries title, description and Open Graph tags, so a shared
link previews properly. `p/` is generated, gitignored and rebuilt on every CI run.

On the timeline the date of each card links to that page, and `/#<slug>` scrolls
to the entry in place, so there are two ways to point at one post.

`sitepage.render_markdown()` is a port of `renderMarkdown()` in `app.js` (app.js
only falls back to it when a post has no `html`). After touching either one, diff
the two:

```sh
node check_render.js > /tmp/js.json   # needs node, renders every post
```

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

## Preview before publishing

Write the entry in `drafts/` instead of `posts/`. Same format, same frontmatter; the directory is gitignored so a draft never reaches the site or the repo.

```sh
python3 preview.py            # build preview/ and lint the drafts
python3 preview.py --serve    # same, then serve it on :8765
```

`preview.py` compiles `posts/` and `drafts/` into `preview/posts.jsonl`, and derives `preview/index.html` from `index.html` so the preview cannot drift from the real page. Entries from `drafts/` render with a `draft` badge and an amber rule down the left side, newest first, mixed in with what is already published.

Publishing is a move:

```sh
mv drafts/2026-11-04-my-thing.md posts/
python3 build.py && git add -A && git commit -m "post: my thing" && git push
```

The lint printed by `preview.py` runs the style checks: title length, description length, em dashes, emoji, hashtags, exclamation marks, and the constructs the renderer does not handle (numbered lists, blockquotes, italics, raw HTML).

## Add a post (for an LLM)

Give your LLM this instruction:

> Post schema: `posts/YYYY-MM-DD-<slug>.md` with YAML frontmatter (`title`, `date`, `url`, `description`, `tags`, `links`, `image`) plus a Markdown body. Do not edit other files. Then run `python3 build.py` (set `SITE_URL`) to regenerate `posts.jsonl` and `rss.xml`.

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
