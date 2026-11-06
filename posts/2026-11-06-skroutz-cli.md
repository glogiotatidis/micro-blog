---
title: "skroutz-cli: built for personal assistants"
date: 2026-11-06
url: https://github.com/glogiotatidis/skroutz-cli
description: "A CLI for skroutz.gr that logs into my real account over OAuth and calls the exact MCP server Skroutz built for its ChatGPT and Claude connectors: 27 tools, no schemas parked in your context."
tags: [python, cli]
links:
  - label: Source on GitHub
    url: https://github.com/glogiotatidis/skroutz-cli
  - label: Anthropic on code execution with MCP
    url: https://www.anthropic.com/engineering/code-execution-with-mcp
  - label: Model Context Protocol
    url: https://modelcontextprotocol.io/
---

[skroutz-cli](https://github.com/glogiotatidis/skroutz-cli) is a terminal client for [Skroutz](https://www.skroutz.gr). It logs in with OAuth 2.1 (dynamic client registration, PKCE, one scope, `shopping_mcp`) and then talks to the same MCP server Skroutz shipped for its ChatGPT and Claude connectors: `https://api.skroutz.gr/api/agents/mcp/shopping`, JSON-RPC 2.0 over streamable HTTP, protocol 2025-06-18. 27 tools: search, cart, orders, addresses, returns.

Two earlier attempts are gone from the code now. First, scraping the storefront with [curl_cffi](https://github.com/lexiforest/curl_cffi) to fake a Chrome TLS fingerprint past Cloudflare. Then replaying browser session cookies to drive a cart, which got far enough to place a real order and cancel it just to prove the path worked. Both deleted once the MCP door turned out to be unlocked.

> A connector is a tax on every conversation. A CLI is a tool you pick up.

A connector hands your agent all 27 tool schemas before it knows it needs any of them, every single conversation. A CLI is a capability you pick up when you need it and put down again, which is why it suits a harness more than a chat window. That is true of [Hermes](https://hermes-agent.nousresearch.com/), [openclaw](https://github.com/openclaw), [Claude Code](https://code.claude.com/docs/en/overview), or anything else that can open a shell. [Anthropic measured the same shape](https://www.anthropic.com/engineering/code-execution-with-mcp): agents writing code against MCP servers instead of loading their schemas dropped from 150,000 tokens to 2,000.

**MCP is the wire. A CLI is the handle you actually turn.**

Finding the wire was the actual work. The endpoint is in no directory I could query, and about ninety guessed paths 404'd before I gave up guessing. I exported a HAR of my own Claude session with the connector page open, and the URL was sitting right there in the browser traffic. Once I had it, Hermes running DeepSeek flash wrote the whole client in one night while I slept: 1,400 lines of Python, 33 tests.

The OAuth endpoints and the MCP server both answer plain HTTP, so the CLI has zero runtime dependencies, stdlib only. Two honest limits: search returns at most 10 results per call, and the price you get is `cart_price` (plus `lowest_price`), the number Skroutz's own cart would charge you. There is no per-shop offer list on the MCP side, so don't expect this to compare sellers.
