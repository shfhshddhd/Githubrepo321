---
name: Provider key-state security
description: How environment-backed provider keys are represented in persistent cooldown state
---

Environment-backed provider keys may participate in cooldown tracking, but their raw values must never be written to the persistent key-state file; store only a non-reversible fingerprint and status metadata.

**Why:** The state file is project storage and can be inspected independently of the Replit secret store. Persisting an environment secret there would expand its exposure.

**How to apply:** Keep explicitly added provider keys compatible with the product's key-state storage requirement, but always sanitize environment-sourced records before persistence and migrate older records that contain raw environment values.