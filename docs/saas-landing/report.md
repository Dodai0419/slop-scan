# slop-scan report: Nexora: AI workflow platform

Source: `examples/saas-landing.html`  
slop traces: 16 of 16 signatures

## 1. AS-07 Emoji as decoration (high, 8x)

Fix: Remove emoji from UI text; use a real icon with a reason, or nothing.

- h1: "🚀 Supercharge your workflow with AI"
- h2: "✨ Everything you need, all in one place"
- h3: "⚡ Lightning fast"
- h3: "🧠 Smart insights"
- h3: "🔒 Enterprise security"
- li: "✅ Seamless integrations with your stack"
- li: "✅ Real-time collaboration for every team"
- li: "✅ 24/7 support from real humans"

## 2. AS-15 Low-contrast text (high, 8x)

Fix: Meet WCAG AA: 4.5:1 for normal text, 3:1 for large text (18px+).

- #9ca3af on #ffffff = 2.54:1 (needs 3.0) at 20px (4x, e.g. span: "ACME")
- #9ca3af on #ffffff = 2.54:1 (needs 4.5) at 15px (3x, e.g. p: "Blazing-fast performance that scales with y…")
- #9ca3af on #ffffff = 2.54:1 (needs 4.5) at 14px (1x, e.g. footer: "© 2026 Nexora. All rights reserved.")

## 3. AS-01 Blue-purple gradient (medium, 3x)

Fix: Take the palette from the brand; keep a gradient only where it marks hierarchy.

- header: "AI-Powered Workflow Platform 🚀 Supercharge…"
- a: "Get started free →"
- a: "Start your free trial →"

## 4. AS-02 Glass on every surface (medium, 5x)

Fix: Blur at most 1-2 surfaces; the rest stay solid.

- nav: "Nexora FeaturesPricingDocs Sign in →"
- span: "AI-Powered Workflow Platform"
- div: "New ⚡ Lightning fast Blazing-fast performan…"
- div: "AI Powered 🧠 Smart insights Actionable ins…"
- div: "Beta 🔒 Enterprise security Bank-grade secu…"

## 5. AS-05 Glow everywhere (medium, 8x)

Fix: Keep glow for 1-2 focus elements, or none.

- a: "Sign in →"
- span
- a: "Get started free →"
- a: "Watch demo ↗"
- span: "New"
- span: "AI Powered"
- span: "Beta"
- a: "Start your free trial →"

## 6. AS-08 Arrow on every button (medium, 4x)

Fix: Keep a direction arrow only on the action that goes somewhere.

- a: "Sign in →"
- a: "Get started free →"
- a: "Watch demo ↗"
- a: "Start your free trial →"

## 7. AS-10 Eyebrow badge above the headline (medium, 1x)

Fix: Cut it; the headline already says it.

- span: "AI-Powered Workflow Platform"

## 8. AS-11 AI capsule badge (medium, 4x)

Fix: Badges only for real status; never a decorative 'AI Powered' pill.

- span: "AI-Powered Workflow Platform"
- span: "New"
- span: "AI Powered"
- span: "Beta"

## 9. AS-13 Endless animation (medium, 4x)

Fix: Motion needs a trigger and an end; nothing pulses or floats forever.

- span
- div: "New ⚡ Lightning fast Blazing-fast performan…"
- div: "AI Powered 🧠 Smart insights Actionable ins…"
- div: "Beta 🔒 Enterprise security Bank-grade secu…"

## 10. AS-14 Unsized media (medium, 1x)

Fix: Give every img/video/iframe width and height (or aspect-ratio) so the page does not jump.

- img: "Product screenshot"

## 11. AS-03 Everything is a pill (low, 7x)

Fix: Use a small set of radii on purpose; inputs, cards and badges should not all be pills.

- a: "Sign in →"
- span: "AI-Powered Workflow Platform"
- span
- a: "Watch demo ↗"
- span: "New"
- span: "AI Powered"
- span: "Beta"

## 12. AS-04 Whole page floats (low, 4x)

Fix: Shadow marks elevation; most elements sit flat.

- div: "New ⚡ Lightning fast Blazing-fast performan…"
- div: "AI Powered 🧠 Smart insights Actionable ins…"
- div: "Beta 🔒 Enterprise security Bank-grade secu…"
- img: "Product screenshot"

## 13. AS-06 Background grid or dots (low, 1x)

Fix: Use a pattern only when it is part of the product's identity.

- body: "Nexora FeaturesPricingDocs Sign in → AI-Pow…"

## 14. AS-09 Colored left stripe (low, 3x)

Fix: A left edge must mark a real state (active, warning, new) or go.

- div: "New ⚡ Lightning fast Blazing-fast performan…"
- div: "AI Powered 🧠 Smart insights Actionable ins…"
- div: "Beta 🔒 Enterprise security Bank-grade secu…"

## 15. AS-12 Template typography (low, 3x)

Fix: No wide-tracked uppercase labels or monospace headings by default.

- div: "TRUSTED BY"
- div: "FEATURES"
- div: "WHY NEXORA"

## 16. AS-16 'Trusted by' logo bar (low, 1x)

Fix: Show real customers with a real quote, or drop the bar.

- div: "TRUSTED BY"

## Coverage

| Check | State | Note |
|---|---|---|
| AS-01 Blue-purple gradient | hit | 3 elements |
| AS-02 Glass on every surface | hit | 5 blurred surfaces (cap 2) |
| AS-03 Everything is a pill | hit | 7 of 7 controls and badges are pills |
| AS-04 Whole page floats | hit | 4 elements with large soft shadows |
| AS-05 Glow everywhere | hit | 8 glowing elements (cap 2) |
| AS-06 Background grid or dots | hit | 1 patterned backgrounds |
| AS-07 Emoji as decoration | hit | 8 text elements carry emoji |
| AS-08 Arrow on every button | hit | 4 of 4 buttons end in an arrow |
| AS-09 Colored left stripe | hit | 3 left stripes |
| AS-10 Eyebrow badge above the headline | hit | pill directly above the h1 |
| AS-11 AI capsule badge | hit | 4 capsule badges |
| AS-12 Template typography | hit | 3 wide-tracked uppercase labels, 0 monospace headings |
| AS-13 Endless animation | hit | 4 elements animate forever |
| AS-14 Unsized media | hit | 1 of 1 media elements have no size |
| AS-15 Low-contrast text | hit | 26 text elements checked, 6 over images or gradients not checked |
| AS-16 'Trusted by' logo bar | hit | 1 logo-bar headings |
