---
title: "Greek TV Streamio: Greek on-demand TV in Stremio"
date: 2026-11-04
url: https://github.com/glogiotatidis/greektv-streamio/
description: Greek stations publish their shows on six different webtv sites with no shared catalog. This addon scrapes all of them, resolves every episode to a direct stream, and serves it to Stremio and Nuvio as static JSON.
tags: [python, ci]
links:
  - label: Install the manifest
    url: https://glogiotatidis.github.io/greektv-streamio/manifest.json
  - label: Source on GitHub
    url: https://github.com/glogiotatidis/greektv-streamio
---

Six stations, six webtv sites, no shared catalog: Skai hides the episode list in a JSON blob inside the page, ERT has a real API, the rest are somewhere in between. So I wrote one adapter per station and a [Stremio](https://www.stremio.com/) addon on top.

It currently exports **385 shows and 20,019 episodes**. It answers the three protocol calls, catalog, meta and stream, and every episode resolves to a direct MP4 or HLS URL.

There is no server. A static export writes it all as JSON under `catalog/`, `meta/` and `stream/`, and [GitHub Actions](https://docs.github.com/en/actions) publishes that to Pages: 20,414 files, 10.2 MiB. Every four hours, one job per station, then a merge. A normal run reuses the previous show list and stream URLs, so only new episodes cost a request:

```sh
python static_export.py                          # every station
GREEKTV_STATIONS=skai python static_export.py    # just one
```

Requests go through [curl_cffi](https://github.com/lexiforest/curl_cffi) with a Chrome TLS fingerprint, and the helper honours `Retry-After` on a 429. A daily smoke test resolves a stream, follows the redirect and pulls one segment, which is how I find out a station redesigned its site before a viewer does. Nineteen of those 20,019 episodes come back empty. The rest resolve.

Add the [manifest](https://glogiotatidis.github.io/greektv-streamio/manifest.json) to Stremio and the shows are there, by station or all together.
