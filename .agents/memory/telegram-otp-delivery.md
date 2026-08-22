---
name: Telegram OTP delivery
description: Telegram login-code delivery can be app-based rather than SMS, and Telethon's force_sms option is deprecated.
---

Telethon's successful `send_code_request` response identifies where Telegram sent the code through its `SentCode.type`. A `SentCodeTypeApp` result means the code is delivered to an already logged-in Telegram session, commonly the verified Telegram service chat, not necessarily by SMS.

**Why:** Users can interpret a successful generic "code sent" message as an SMS failure when Telegram intentionally selected in-app delivery.

**How to apply:** Keep the auth flow delivery-aware and tell the user the returned channel. Do not depend on `force_sms`; Telethon marks it deprecated and Telegram no longer guarantees it.