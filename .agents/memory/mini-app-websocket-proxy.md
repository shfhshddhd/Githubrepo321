---
name: Mini App WebSocket proxy
description: The transport rule for browser live-audio WebSockets routed through the shared API service.
---

The browser live-audio endpoint must be proxied as a raw WebSocket upgrade, preserving binary frames end-to-end; an ordinary HTTP `fetch` proxy cannot carry the connection or PCM audio.

**Why:** The Mini App is served through the shared API artifact, while the Python aiohttp server owns Telegram authentication and PyTgCalls. Without an upgrade tunnel the browser receives HTTP 400 before any PCM reaches the Python process.

**How to apply:** Keep the public live path explicitly listed in the API artifact routing paths, attach an upgrade handler to the Node HTTP server, rewrite the public prefix to the Python `/mini-app` prefix, and pipe both sockets without decoding frames.