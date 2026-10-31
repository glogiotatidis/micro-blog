# mini-blog

A personal activity log by Giorgos Logiotatidis — things I build, in order.

A zero-build, Twitter-like timeline. Hosted on GitHub Pages.

## How it works

- `index.html` + `app.js` + `style.css` render `posts.jsonl` (one JSON object per line, newest first).
- No build step, no dependencies, no framework. LLMs can't break a build that doesn't exist.

## Add a post (for humans)

Append one line to `posts.jsonl`:

```json
{"date":"2026-10-31","title":"my thing","url":"https://...","description":"one-liner","tags":["rust","cli"],"body":"optional markdown","links":[{"label":"GitHub","url":"https://github.com/..."}],"image":null}
```

## Add a post (for an LLM)

Give your LLM this instruction:

> Append exactly one JSON line to `posts.jsonl` in this repo (no trailing comma, valid JSON, one object per line). Fields: `date` (ISO YYYY-MM-DD), `title` (string, required), `url` (string or null), `description` (string or null), `body` (markdown string or null), `tags` (array of strings), `links` (optional array of {label,url} or URL strings for a "See also" list), `image` (url string or null). Newest posts sort first by `date`. Do not edit other lines. Write in the voice described in `style.md` and follow its checklist. Then run `python3 gen_rss.py` (set `SITE_URL` env var to your site URL) to regenerate `rss.xml`.

Validate before committing:

```sh
python3 -c "import json,sys; [json.loads(l) for l in open('posts.jsonl') if l.strip()]; print('ok')"
```

## Deploy (GitHub Pages)

1. Push to GitHub.
2. Repo → Settings → Pages → Source: "Deploy from a branch" → branch `main`, folder `/ (root)`.
3. Site appears at `https://<user>.github.io/<repo>/`.

## Local preview

```sh
python3 -m http.server 8000
# open http://localhost:8000
```

(`fetch()` needs a server; opening `index.html` via `file://` won't load posts.)
