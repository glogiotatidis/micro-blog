---
title: "skroutz-cli: built for personal AI assistants"
date: 2026-11-06
url: https://github.com/glogiotatidis/skroutz-cli
description: "A terminal client for skroutz.gr that logs into my real account and calls the same MCP server Skroutz shipped for ChatGPT and Claude. Same wire, thinner handle: one binary, 27 tools, no schemas parked in your context window."
tags: [python, cli]
links:
  - label: Source on GitHub
    url: https://github.com/glogiotatidis/skroutz-cli
  - label: Anthropic on code execution with MCP
    url: https://www.anthropic.com/engineering/code-execution-with-mcp
  - label: Model Context Protocol
    url: https://modelcontextprotocol.io/
---

It started as scraping. [curl_cffi](https://github.com/lexiforest/curl_cffi) with a Chrome TLS fingerprint got past Cloudflare, session cookies got me a cart, and an order was placed and cancelled purely to see whether it would work. Both of those paths are gone now. [Skroutz](https://www.skroutz.gr) shipped an MCP server a few days ago, the one behind its ChatGPT and Claude connectors, and that is a much better door.

So [skroutz-cli](https://github.com/glogiotatidis/skroutz-cli) logs in with OAuth (dynamic client registration, PKCE, one scope) and calls the same endpoint the connector calls. Search, prices, cart, orders, addresses, returns: 27 tools in total.

The interesting part is the shape. A connector is a capability your agent carries in every conversation, 27 schemas in the context window before it knows whether it needs a price that day. A CLI is a capability it picks up when it does and puts down again: `skroutz search "rtx 5070" --json | jq '.results[0].price'`. Every harness that can run a shell can use it, which is Hermes, openclaw, Claude Code, and whatever replaces them next month. [Anthropic's own numbers](https://www.anthropic.com/engineering/code-execution-with-mcp) point the same way: agents writing code against those same MCP servers went from 150,000 tokens to 2,000.

**"MCP is the wire. A CLI is the handle you actually turn."**

It is not the opposite of MCP, just the thinner face on it. Underneath, every command is a JSON-RPC call to Skroutz's server with a bearer token.

Finding the wire was the fun part. The endpoint is in no public directory I could query and some ninety guesses returned 404, so I exported a HAR of my own Claude session with the connector page open, and there it was in the browser's own traffic. Then [Hermes](https://hermes-agent.nousresearch.com/) on DeepSeek flash wrote the whole thing in one night while I slept: 1,400 lines of Python and 33 tests. The hard part was never the HTTP.
