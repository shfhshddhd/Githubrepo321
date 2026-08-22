---
name: Workflow secret injection
description: Replit secret-manager entries may not be present in a configured console workflow environment.
---

The secret manager can report required secrets as present while the running workflow's process environment is empty for those same keys.

**Why:** The Telegram userbot's fail-fast validation correctly exposed this mismatch; replacing missing credentials with fallbacks would be unsafe and would mask the deployment problem.

**How to apply:** Keep credential validation strict. When this happens, verify the workflow environment scope and have the user re-save or rebind the existing secrets before changing application code.