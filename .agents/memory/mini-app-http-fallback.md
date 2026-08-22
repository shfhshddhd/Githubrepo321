---
name: Mini App HTTP fallback
description: Public Mini App routing behavior when the Python backend is unavailable.
---

The public Mini App proxy must return a self-contained offline HTML document for the Mini App root when the Python server cannot be reached. Keep the public URL canonical with a trailing slash, and identify the mounted document request from the full public URL rather than the router-local path.

**Why:** Express removes the mount prefix from `req.path`, so checking it directly cannot distinguish `/api/mini-app/` from another mounted route. A non-document JSON 502 makes Telegram Web App show a generic load failure instead of a useful app-owned screen.

**How to apply:** Preserve `/api/mini-app` → `/api/mini-app/` normalization without matching the slash form again; use `req.originalUrl` for public-prefix checks; keep the fallback HTML self-contained and free of platform branding.