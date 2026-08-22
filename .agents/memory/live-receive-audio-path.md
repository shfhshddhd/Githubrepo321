---
name: Live receive audio path
description: The separation boundary for Telegram Voice Chat incoming audio in the Mini App.
---

Telegram playback audio is already exposed by PyTgCalls as `StreamFrames` updates with `INCOMING` direction and `SPEAKER` device. The Mini App receive path must forward those PCM bytes unchanged through bounded per-session queues and play them in a separate browser AudioContext.

**Why:** Reusing the microphone sender or applying its gain changes remote participants' audio and can create latency, clipping, or feedback.

**How to apply:** Keep receive subscribers independent from the external microphone queue. Bound the receive queue by dropping the oldest queued frame when necessary, and keep browser echo cancellation confined to microphone capture.