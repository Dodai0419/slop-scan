# slop-scan report: PulseOps dashboard

Source: `examples/ai-dashboard.html`  
slop traces: 8 of 16 signatures

## 1. AS-07 Emoji as decoration (high, 5x)

Fix: Remove emoji from UI text; use a real icon with a reason, or nothing.

- a: "📊 Overview"
- a: "⚙️ Pipelines"
- a: "👥 Team"
- a: "🔔 Alerts"
- h2: "🚀 Performance"

## 2. AS-15 Low-contrast text (high, 8x)

Fix: Meet WCAG AA: 4.5:1 for normal text, 3:1 for large text (18px+).

- #6b7280 on #0b0b12 = 4.06:1 (needs 4.5) at 14px (1x, e.g. div: "Live: all systems operational")
- #6b7280 on #151524 = 3.73:1 (needs 4.5) at 11px (4x, e.g. div: "REVENUE")
- #6b7280 on #151524 = 3.73:1 (needs 4.5) at 14px (3x, e.g. div: "Sarah deployed v2.4.1 to production")

## 3. AS-02 Glass on every surface (medium, 7x)

Fix: Blur at most 1-2 surfaces; the rest stay solid.

- nav: "📊 Overview ⚙️ Pipelines 👥 Team 🔔 Alerts"
- div: "REVENUE $48.2k +12.5% ↑"
- div: "ACTIVE USERS 2,847 +8.1% ↑"
- div: "CONVERSION 3.24% +0.4% ↑"
- div: "UPTIME 99.9% +0.1% ↑"
- div: "🚀 Performance"
- div: "Recent activity Sarah deployed v2.4.1 to pr…"

## 4. AS-05 Glow everywhere (medium, 5x)

Fix: Keep glow for 1-2 focus elements, or none.

- span
- div: "REVENUE $48.2k +12.5% ↑"
- div: "ACTIVE USERS 2,847 +8.1% ↑"
- div: "CONVERSION 3.24% +0.4% ↑"
- div: "UPTIME 99.9% +0.1% ↑"

## 5. AS-13 Endless animation (medium, 1x)

Fix: Motion needs a trigger and an end; nothing pulses or floats forever.

- span

## 6. AS-06 Background grid or dots (low, 1x)

Fix: Use a pattern only when it is part of the product's identity.

- body: "📊 Overview ⚙️ Pipelines 👥 Team 🔔 Alerts …"

## 7. AS-09 Colored left stripe (low, 3x)

Fix: A left edge must mark a real state (active, warning, new) or go.

- a: "📊 Overview"
- div: "🚀 Performance"
- div: "Recent activity Sarah deployed v2.4.1 to pr…"

## 8. AS-12 Template typography (low, 5x)

Fix: No wide-tracked uppercase labels or monospace headings by default.

- div: "REVENUE"
- div: "ACTIVE USERS"
- div: "CONVERSION"
- div: "UPTIME"
- h1: "Overview"

## Coverage

| Check | State | Note |
|---|---|---|
| AS-01 Blue-purple gradient | clean | 0 elements |
| AS-02 Glass on every surface | hit | 7 blurred surfaces (cap 2) |
| AS-03 Everything is a pill | clean | 1 of 2 controls and badges are pills |
| AS-04 Whole page floats | clean | 0 elements with large soft shadows |
| AS-05 Glow everywhere | hit | 5 glowing elements (cap 2) |
| AS-06 Background grid or dots | hit | 1 patterned backgrounds |
| AS-07 Emoji as decoration | hit | 5 text elements carry emoji |
| AS-08 Arrow on every button | clean | 0 of 1 buttons end in an arrow |
| AS-09 Colored left stripe | hit | 3 left stripes |
| AS-10 Eyebrow badge above the headline | clean |  |
| AS-11 AI capsule badge | clean | 0 capsule badges |
| AS-12 Template typography | hit | 4 wide-tracked uppercase labels, 1 monospace headings |
| AS-13 Endless animation | hit | 1 elements animate forever |
| AS-14 Unsized media | clean | 0 of 0 media elements have no size |
| AS-15 Low-contrast text | hit | 23 text elements checked, 0 over images or gradients not checked |
| AS-16 'Trusted by' logo bar | clean | 0 logo-bar headings |
