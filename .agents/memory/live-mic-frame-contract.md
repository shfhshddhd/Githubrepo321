---
name: Live microphone frame contract
description: The NTgCalls external microphone input contract used by the Telegram live mic path.
---

NTgCalls external audio is fixed to 10 ms PCM frames. For the live microphone's 48 kHz mono PCM16 stream, every frame must contain exactly 480 samples and 960 bytes.

**Why:** The native AudioSink computes `numberOfFrames` from a 10 ms frame size. Sending 20 ms payloads while it declares 10 ms causes timing distortion, robotic audio, and stutter.

**How to apply:** Keep browser framing, server validation, and any native send path aligned at 480 samples / 960 bytes. Do not change only one boundary.