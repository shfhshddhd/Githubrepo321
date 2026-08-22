---
name: AI provider selection
description: Provider selection for Telegram AI replies
---

Telegram AI replies support Gemini and OpenRouter through a per-hosted-account provider setting. Each provider uses its own independent key list; OpenAI is not part of the runtime path. Gemini model aliases may need updating when Google retires a model for new users.

**Why:** Provider selection must persist independently for each hosted account while quota failures rotate only within the selected provider.

**How to apply:** Keep provider secrets out of URLs and chat, use the selected provider for AI mode and auto-replies, and report provider/key availability without exposing raw keys.