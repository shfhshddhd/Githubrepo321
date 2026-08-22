---
name: Published app badge
description: The source and plan boundary for the Made with Replit badge on published apps
---

The “Made with Replit” badge is added by Replit to published apps on the Starter plan. It is not part of the project HTML, CSS, proxy response, or artifact metadata.

**Why:** A Mini App source and its served HTML were inspected and contained no badge markup, while Replit documentation identifies the badge as a publishing-plan feature.

**How to apply:** Do not add CSS or DOM hacks to hide it. Removing the badge requires upgrading the Replit account to Core; it should disappear automatically from published apps after the plan change.