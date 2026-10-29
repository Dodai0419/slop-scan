---
name: slop-scan
description: Use after building or changing a web page or UI (landing page, dashboard, component demo) to find generic AI-generated design tells (blue-purple gradients, glass everywhere, emoji headings, arrows on every button, low-contrast text) and fix them. Produces a red-pen screenshot and a Markdown list of tells with fixes.
---

# slop-scan

Scans a rendered web page for 16 AI-slop design signatures from anti-slop and writes a picture and a report.

## Run
From the slop-scan folder (needs Chrome, Chromium or Edge; Python standard library only):

```bash
python slopscan.py <page.html or http://localhost:PORT> -o slop-out
```

Outputs in `slop-out/`: `slop-report.png` (page with numbered red boxes + list), `report.md`, `report.html`, `traces.json`.
Add `--fail-on medium` to exit 1 when any medium or high trace is found. Add `--json` to print traces as JSON.

## Workflow
1. Start the page (dev server or a local HTML file) and run the scan.
2. Read `slop-out/report.md`. Each trace has an id (AS-01..AS-16), a tier, evidence (element and values) and a one-line fix.
3. Fix high tiers first, then medium. Low tiers are judgment calls: keep them only with a reason tied to the brand.
4. Run the scan again and confirm the count went down. Show the user `slop-out/slop-report.png` before and after.
5. Read the coverage table: `could-not-run` checks and text over gradients were not checked, so look at those by eye.

Do not change the brand's real colors or fonts only to silence a low-tier trace; ask the user first.
