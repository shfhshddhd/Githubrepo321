---
name: Gemini key rotation
description: Shared Gemini quota rotation and storage behavior for the Telegram bot
---

Saved Gemini keys are ordered before the `GEMINI_API_KEY` environment fallback; provider lists are independent, the selected key remains active after success, and retryable failures rotate within that provider. State uses Replit DB when available, with JSON fallback.

**Why:** The bot needs quota recovery across multiple user-managed keys without changing its existing Telegram framework or AI handlers, while manual key selection must remain meaningful.

**How to apply:** Route Gemini and OpenRouter requests through the shared provider helper, preserve each caller's prompt/history shape, and keep owner-only key commands on the existing control bot.