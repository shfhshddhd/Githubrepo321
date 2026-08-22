---
name: Mongo degraded startup
description: Startup behavior when the Telegram userbot cannot reach MongoDB.
---

The PTB control bot must continue polling when MongoDB is unavailable. MongoDB remains the primary store, while a local JSON fallback preserves hosted-account sessions and related state during an Atlas/network outage.

**Why:** A MongoDB Atlas TLS handshake failure previously terminated the application during post-init, and then blocked `/host` at session persistence, so users received neither `/start` nor successful hosting.

**How to apply:** Keep Mongo connection checks bounded by short timeouts, log fallback mode clearly, and ensure all database APIs used by hosting, restoration, mappings, and settings work against the local fallback.