#!/usr/bin/env python3
"""slop-scan: point it at a web page, get a red-pen screenshot of every AI-slop design tell.

The tells and the WCAG contrast rule come from anti-slop (miqdadbadjuber/anti-slop, MIT). The report
shape comes from Zero-Breach-Toolkit (interplains/Zero-Breach-Toolkit, Apache-2.0): signatures with
ids and tiers, evidence for every hit, and every check says whether it ran or why it could not.

    python slopscan.py page.html -o out            # or an http(s) URL
    python slopscan.py page.html -o out --fail-on medium

Needs Chrome, Chromium or Edge (headless, own throwaway profile). Python standard library only.
"""
import argparse
import base64
import html
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

TIERS = ("low", "medium", "high")
# id, title, tier, fix (paraphrased from anti-slop's antislop-ui / antislop-human skills)
SIGNATURES = [
    ("AS-01", "Blue-purple gradient", "medium", "Take the palette from the brand; keep a gradient only where it marks hierarchy."),
    ("AS-02", "Glass on every surface", "medium", "Blur at most 1-2 surfaces; the rest stay solid."),
    ("AS-03", "Everything is a pill", "low", "Use a small set of radii on purpose; inputs, cards and badges should not all be pills."),
    ("AS-04", "Whole page floats", "low", "Shadow marks elevation; most elements sit flat."),
    ("AS-05", "Glow everywhere", "medium", "Keep glow for 1-2 focus elements, or none."),
    ("AS-06", "Background grid or dots", "low", "Use a pattern only when it is part of the product's identity."),
    ("AS-07", "Emoji as decoration", "high", "Remove emoji from UI text; use a real icon with a reason, or nothing."),
    ("AS-08", "Arrow on every button", "medium", "Keep a direction arrow only on the action that goes somewhere."),
    ("AS-09", "Colored left stripe", "low", "A left edge must mark a real state (active, warning, new) or go."),
    ("AS-10", "Eyebrow badge above the headline", "medium", "Cut it; the headline already says it."),
    ("AS-11", "AI capsule badge", "medium", "Badges only for real status; never a decorative 'AI Powered' pill."),
    ("AS-12", "Template typography", "low", "No wide-tracked uppercase labels or monospace headings by default."),
    ("AS-13", "Endless animation", "medium", "Motion needs a trigger and an end; nothing pulses or floats forever."),
    ("AS-14", "Unsized media", "medium", "Give every img/video/iframe width and height (or aspect-ratio) so the page does not jump."),
    ("AS-15", "Low-contrast text", "high", "Meet WCAG AA: 4.5:1 for normal text, 3:1 for large text (18px+)."),
    ("AS-16", "'Trusted by' logo bar", "low", "Show real customers with a real quote, or drop the bar."),
]

COLLECT_JS = r"""
(() => {
  const S = el => getComputedStyle(el);
  const vis = el => { const r = el.getBoundingClientRect(), s = S(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  const els = [...document.querySelectorAll('body *')].filter(vis);
  const box = el => { const r = el.getBoundingClientRect(); return {x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height}; };
  const own = el => [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('').replace(/\s+/g, ' ').trim();
  const name = el => { let t = (el.innerText || el.getAttribute('alt') || '').replace(/\s+/g, ' ').trim();
    if (t.length > 44) t = t.slice(0, 43) + '\u2026'; return el.tagName.toLowerCase() + (t ? ': "' + t + '"' : ''); };
  const rgba = s => [...s.matchAll(/rgba?\(([^)]+)\)/g)].map(m => m[1].split(/[ ,\/]+/).filter(Boolean).map(Number));
  const hs = ([r, g, b]) => { r /= 255; g /= 255; b /= 255; const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
    const l = (mx + mn) / 2, s = d === 0 ? 0 : d / (1 - Math.abs(2 * l - 1));
    let h = 0; if (d) h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
    return [(h * 60 + 360) % 360, s]; };
  const saturated = c => (c.length < 4 || c[3] > 0.05) && hs(c)[1] > 0.3;
  const px = v => parseFloat(v) || 0;
  const pill = el => { const s = S(el), r = s.borderTopLeftRadius, h = el.getBoundingClientRect().height;
    return r.includes('%') ? px(r) >= 50 : px(r) >= h / 2 - 1; };
  const shadows = s => s === 'none' ? [] : s.split(/,(?![^(]*\))/).map(p => { const c = rgba(p)[0] || [0, 0, 0, 1];
    const n = p.replace(/rgba?\([^)]*\)/, '').trim().split(/\s+/).map(px); return {c, x: n[0], y: n[1], blur: n[2] || 0}; });
  const out = {}, put = (id, state, items, note) => out[id] = {state, items: items.slice(0, 12).map(el => ({box: box(el), ev: name(el)})), n: items.length, note};
  const hitIf = (id, cond, items, note) => put(id, cond ? 'hit' : 'clean', cond ? items : [], note);

  const grad = els.filter(el => { const b = S(el).backgroundImage; if (!/(^|[^-])(linear|radial|conic)-gradient/.test(b)) return false;
    const hues = rgba(b).filter(saturated).map(c => hs(c)[0]).filter(h => h >= 185 && h <= 345);
    return hues.length >= 2 && Math.max(...hues) - Math.min(...hues) >= 25; });
  hitIf('AS-01', grad.length > 0, grad, grad.length + ' elements');

  const glass = els.filter(el => /blur/.test(S(el).backdropFilter || S(el).webkitBackdropFilter || ''));
  hitIf('AS-02', glass.length > 2, glass, glass.length + ' blurred surfaces (cap 2)');

  const ctl = els.filter(el => { const s = S(el), t = el.tagName, h = el.getBoundingClientRect().height;
    return ['BUTTON', 'INPUT', 'SELECT', 'TEXTAREA'].includes(t) || (h < 80 && (t === 'A' || t === 'SPAN') &&
      (rgba(s.backgroundColor)[0]?.[3] ?? 1) > 0 && s.backgroundColor !== 'rgba(0, 0, 0, 0)'); });
  const pills = ctl.filter(pill);
  hitIf('AS-03', ctl.length >= 4 && pills.length / ctl.length >= 0.8, pills, pills.length + ' of ' + ctl.length + ' controls and badges are pills');

  const soft = els.filter(el => shadows(S(el).boxShadow).some(s => s.blur >= 20 && s.y > 0));
  hitIf('AS-04', soft.length >= 4, soft, soft.length + ' elements with large soft shadows');

  const glow = els.filter(el => [...shadows(S(el).boxShadow), ...shadows(S(el).textShadow)]
    .some(s => Math.abs(s.x) <= 2 && Math.abs(s.y) <= 2 && s.blur >= 8 && saturated(s.c)));
  hitIf('AS-05', glow.length >= 3, glow, glow.length + ' glowing elements (cap 2)');

  const grid = [document.body, document.documentElement, ...els].filter(el => { const s = S(el), r = el.getBoundingClientRect();
    if (r.width < 300 || !/gradient/.test(s.backgroundImage)) return false;
    if (/repeating-/.test(s.backgroundImage)) return true;
    const sz = s.backgroundSize.split(/\s+/).map(px); return sz[0] > 0 && sz[0] <= 64; });
  hitIf('AS-06', grid.length > 0, grid, grid.length + ' patterned backgrounds');

  const EMOJI = /(?![\u00a9\u00ae\u2122\u2190-\u21ff\u2030-\u205f])\p{Extended_Pictographic}/u;
  const emo = els.filter(el => EMOJI.test(own(el)));
  hitIf('AS-07', emo.length > 0, emo, emo.length + ' text elements carry emoji');

  const btns = els.filter(el => el.tagName === 'BUTTON' || el.getAttribute('role') === 'button' ||
    (el.tagName === 'A' && (/btn|button|cta/i.test(el.className) || (rgba(S(el).backgroundColor)[0]?.[3] ?? 1) > 0 && S(el).backgroundColor !== 'rgba(0, 0, 0, 0)')));
  const arrows = btns.filter(el => /[\u2192\u2197\u279c\u2794\u27f6\u203a\u00bb]\s*$/.test(el.innerText.trim()));
  hitIf('AS-08', btns.length >= 3 && arrows.length / btns.length >= 0.6, arrows, arrows.length + ' of ' + btns.length + ' buttons end in an arrow');

  const stripe = els.filter(el => { const s = S(el), w = px(s.borderLeftWidth);
    return w >= 2 && w <= 8 && s.borderLeftStyle !== 'none' && px(s.borderRightWidth) === 0 && saturated(rgba(s.borderLeftColor)[0] || [0, 0, 0]); });
  hitIf('AS-09', stripe.length >= 2, stripe, stripe.length + ' left stripes');

  const h1 = document.querySelector('h1');
  if (!h1) put('AS-10', 'could-not-run', [], 'page has no h1');
  else { const e = h1.previousElementSibling, ok = e && vis(e) && pill(e) && e.getBoundingClientRect().height < 48 && e.innerText.trim().length < 60;
    hitIf('AS-10', !!ok, ok ? [e] : [], ok ? 'pill directly above the h1' : ''); }

  const caps = els.filter(el => /^(new|beta)$|\bai[- ]powered\b|\bpowered by ai\b/i.test(own(el) || (el.children.length ? '' : el.innerText.trim())) &&
    (pill(el) || (el.parentElement && pill(el.parentElement))));
  hitIf('AS-11', caps.length > 0, caps, caps.length + ' capsule badges');

  const upper = els.filter(el => own(el) && S(el).textTransform === 'uppercase' && px(S(el).letterSpacing) >= 0.1 * px(S(el).fontSize));
  const mono = els.filter(el => /^H[1-3]$/.test(el.tagName) && /mono|courier|consolas/i.test(S(el).fontFamily.split(',')[0]));
  hitIf('AS-12', upper.length >= 2 || mono.length > 0, [...upper, ...mono], upper.length + ' wide-tracked uppercase labels, ' + mono.length + ' monospace headings');

  const loops = [...new Set(document.getAnimations().filter(a => a.effect && a.effect.getTiming().iterations === Infinity)
    .map(a => a.effect.target).filter(t => t && t.nodeType === 1 && vis(t)))];
  hitIf('AS-13', loops.length > 0, loops, loops.length + ' elements animate forever');

  const media = els.filter(el => ['IMG', 'VIDEO', 'IFRAME'].includes(el.tagName));
  const unsized = media.filter(el => !(el.hasAttribute('width') && el.hasAttribute('height')) && S(el).aspectRatio === 'auto');
  hitIf('AS-14', unsized.length > 0, unsized, unsized.length + ' of ' + media.length + ' media elements have no size');

  const texts = [];
  let skipped = 0;
  for (const el of els) {
    if (!own(el) || ['SCRIPT', 'STYLE', 'OPTION'].includes(el.tagName)) continue;
    const layers = []; let n = el, image = false;
    for (; n; n = n.parentElement) { const s = S(n);
      if (s.backgroundImage !== 'none' && n !== document.body && n !== document.documentElement) { image = true; break; }
      const c = rgba(s.backgroundColor)[0]; if (c && (c.length < 4 || c[3] > 0)) { layers.push(c); if (c.length < 4 || c[3] >= 1) break; } }
    if (image) { skipped++; continue; }
    const s = S(el);
    texts.push({fg: rgba(s.color)[0], layers, size: px(s.fontSize), box: box(el), ev: name(el)});
  }
  out['AS-15'] = {texts, skipped};

  const trusted = els.filter(el => /^(trusted by|loved by|used by teams at|as seen on)\b/i.test(own(el)));
  hitIf('AS-16', trusted.length > 0, trusted, trusted.length + ' logo-bar headings');
  return {out, height: document.documentElement.scrollHeight, title: document.title};
})()
"""


# ---------------------------------------------------------------- color (formula and thresholds as in anti-slop's contrast-check.py)
def hex_rgb(value):
    v = value.strip().lstrip("#")
    v = "".join(c * 2 for c in v) if len(v) == 3 else v
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


def css_rgba(value):
    if value.strip() == "transparent":
        return (0, 0, 0, 0.0)
    n = [float(x) for x in re.findall(r"[\d.]+", value)]
    return (int(n[0]), int(n[1]), int(n[2]), n[3] if len(n) > 3 else 1.0)


def luminance(rgb):
    lin = [(c / 255) / 12.92 if c / 255 <= 0.03928 else ((c / 255 + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def over(top, under):
    a = top[3] if len(top) > 3 else 1.0
    return tuple(round(top[i] * a + under[i] * (1 - a)) for i in range(3))


def hexs(rgb):
    return "#%02x%02x%02x" % tuple(rgb)


def contrast_check(raw):
    hits = {}
    for t in raw["texts"]:
        bg = (255, 255, 255)  # the canvas under every page
        for layer in reversed(t["layers"]):
            bg = over(layer, bg)
        fg = over(t["fg"], bg)
        ratio, need = contrast(fg, bg), 3.0 if t["size"] >= 18 else 4.5  # unrounded, 18px+ is large (anti-slop R-25)
        if ratio < need:
            key = f"{hexs(fg)} on {hexs(bg)} = {ratio:.2f}:1 (needs {need}) at {t['size']:g}px"
            hits.setdefault(key, []).append(t)
    items = [{"box": t["box"], "ev": f"{key}, {t['ev']}"} for key, ts in hits.items() for t in ts]
    note = f"{len(raw['texts'])} text elements checked, {raw['skipped']} over images or gradients not checked"
    if not raw["texts"]:
        return {"state": "could-not-run", "items": [], "n": 0, "note": "no text on a plain background"}
    return {"state": "hit" if items else "clean", "items": items[:12], "n": len(items), "note": note,
            "evidence": [f"{k} ({len(v)}x, e.g. {v[0]['ev']})" for k, v in hits.items()]}


# ---------------------------------------------------------------- browser (DevTools protocol over a stdlib websocket)
def find_chrome():
    for name in ("chrome", "google-chrome", "chromium", "chromium-browser", "msedge", "microsoft-edge"):
        if p := shutil.which(name):
            return p
    for p in (os.environ.get("CHROME", ""), r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
        if p and Path(p).exists():
            return p
    return None


class Chrome:
    def __init__(self, exe, width, height):
        self.prof = tempfile.mkdtemp()  # own profile: never touches the user's browser
        self.proc = subprocess.Popen([exe, "--headless=new", f"--user-data-dir={self.prof}", "--remote-debugging-port=0",
                                      "--no-first-run", "--hide-scrollbars", f"--window-size={width},{height}", "about:blank"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        port_file, t0 = Path(self.prof, "DevToolsActivePort"), time.time()
        while not (text := self._port_text(port_file)).count("\n"):
            if time.time() - t0 > 60 or self.proc.poll() is not None:
                self.close()
                raise RuntimeError("Chrome did not start")
            time.sleep(0.05)
        port = int(text.split()[0])
        while not (pages := [p for p in json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=30))
                             if p["type"] == "page"]):
            if time.time() - t0 > 60:
                raise RuntimeError("Chrome opened no page")
            time.sleep(0.05)
        ws = pages[0]["webSocketDebuggerUrl"]
        self.sock, self.id = socket.create_connection(("127.0.0.1", port), timeout=120), 0
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall(f"GET {ws.split(str(port), 1)[1]} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nUpgrade: websocket\r\n"
                          f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n".encode())
        head = b""
        while b"\r\n\r\n" not in head:
            head += self.sock.recv(1)
        if b" 101 " not in head.split(b"\r\n")[0]:
            raise RuntimeError("DevTools handshake failed")
        self.width = width
        self.call("Emulation.setDeviceMetricsOverride", width=width, height=height, deviceScaleFactor=1, mobile=False)

    @staticmethod
    def _port_text(path):
        try:
            return path.read_text()
        except OSError:  # missing, or still locked by Chrome while it writes it (Windows)
            return ""

    def _read(self, n):
        buf = b""
        while len(buf) < n:
            if not (chunk := self.sock.recv(n - len(buf))):
                raise RuntimeError("DevTools connection closed")
            buf += chunk
        return buf

    def call(self, method, **params):
        self.id += 1
        data = json.dumps({"id": self.id, "method": method, "params": params}).encode()
        n, mask = len(data), os.urandom(4)
        size = bytes([0x80 | n]) if n < 126 else bytes([0x80 | 126]) + n.to_bytes(2, "big") if n < 65536 else \
            bytes([0x80 | 127]) + n.to_bytes(8, "big")
        self.sock.sendall(b"\x81" + size + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))
        while True:  # skip events until our answer arrives
            msg = b""
            while True:
                b0, b1 = self._read(2)
                n = b1 & 0x7F
                n = int.from_bytes(self._read(2 if n == 126 else 8), "big") if n >= 126 else n
                msg += self._read(n)
                if b0 & 0x80:
                    break
            reply = json.loads(msg)
            if reply.get("id") == self.id:
                if "error" in reply:
                    raise RuntimeError(f"{method}: {reply['error']}")
                return reply["result"]

    def js(self, expr):
        r = self.call("Runtime.evaluate", expression=expr, awaitPromise=True, returnByValue=True)
        if "exceptionDetails" in r:
            raise RuntimeError(r["exceptionDetails"].get("exception", {}).get("description", "page script failed"))
        return r["result"].get("value")

    def open(self, url):
        self.call("Page.navigate", url=url)
        t0 = time.time()
        while self.js("document.readyState") != "complete" and time.time() - t0 < 60:
            time.sleep(0.05)
        self.js("document.fonts.ready.then(() => 1)")

    def full_shot(self, path, height):
        h = min(int(height), 8000)
        self.call("Emulation.setDeviceMetricsOverride", width=self.width, height=h, deviceScaleFactor=1, mobile=False)
        img = self.call("Page.captureScreenshot", format="png", captureBeyondViewport=True,
                        clip={"x": 0, "y": 0, "width": self.width, "height": h, "scale": 1})
        Path(path).write_bytes(base64.b64decode(img["data"]))

    def close(self):
        try:
            self.call("Browser.close")
            self.sock.close()
        except Exception:
            pass
        try:
            self.proc.wait(3)
        except subprocess.TimeoutExpired:  # a throwaway headless profile: nothing to lose by not waiting longer
            self.proc.kill()
        shutil.rmtree(self.prof, ignore_errors=True)


def url_of(src):
    return src if re.match(r"https?://", src) else Path(src).resolve().as_uri()


# ---------------------------------------------------------------- scan
def evaluate(raw):
    checks, traces = [], []
    for sid, title, tier, fix in SIGNATURES:
        r = contrast_check(raw["out"][sid]) if sid == "AS-15" else raw["out"][sid]
        checks.append({"id": sid, "state": r["state"], "note": r["note"]})
        if r["state"] == "hit":
            traces.append({"id": sid, "title": title, "tier": tier, "count": r["n"], "fix": fix,
                           "evidence": r.get("evidence") or [i["ev"] for i in r["items"]], "boxes": [i["box"] for i in r["items"]]})
    traces.sort(key=lambda t: (-TIERS.index(t["tier"]), t["id"]))
    return {"title": raw["title"], "height": raw["height"], "checks": checks, "traces": traces}


def scan(src, chrome, width=1280, shot=None):
    c = Chrome(chrome, width, 800)
    try:
        c.open(url_of(src))
        result = evaluate(c.js(COLLECT_JS))
        if shot:
            c.js(overlay_js(result["traces"]))
            c.full_shot(shot, result["height"])
        return result
    finally:
        c.close()


def overlay_js(traces):
    marks = [{"n": i, "box": b} for i, t in enumerate(traces, 1) for b in t["boxes"][:6]]
    return """(marks => { for (const m of marks) { const b = m.box, d = document.createElement('div');
      d.style.cssText = `position:absolute;left:${b.x - 4}px;top:${b.y - 4}px;width:${b.w + 8}px;height:${b.h + 8}px;` +
        'border:3px solid #e0301e;border-radius:10px;box-sizing:border-box;pointer-events:none;z-index:2147483647;' +
        'box-shadow:0 0 0 1px #fff;transform:rotate(-0.4deg)';
      const t = document.createElement('span'); t.textContent = m.n;
      t.style.cssText = 'position:absolute;left:-13px;top:-13px;width:24px;height:24px;border-radius:50%;background:#e0301e;' +
        'color:#fff;font:700 13px/24px system-ui,sans-serif;text-align:center;letter-spacing:0;text-transform:none';
      d.appendChild(t); document.documentElement.appendChild(d); }
      document.getAnimations().forEach(a => { try { a.pause(); a.currentTime = 0; } catch (e) {} }); return 1; })(MARKS)""".replace("MARKS", json.dumps(marks))


# ---------------------------------------------------------------- report
def summary(result):
    return f"slop traces: {len(result['traces'])} of {len(SIGNATURES)} signatures"


def write_md(result, src, path):
    lines = [f"# slop-scan report: {result['title'] or src}", "", f"Source: `{src}`  ", summary(result), ""]
    for i, t in enumerate(result["traces"], 1):
        lines += [f"## {i}. {t['id']} {t['title']} ({t['tier']}, {t['count']}x)", "", f"Fix: {t['fix']}", ""]
        lines += [f"- {e}" for e in t["evidence"][:8]] + [""]
    lines += ["## Coverage", "", "| Check | State | Note |", "|---|---|---|"]
    names = {s[0]: s[1] for s in SIGNATURES}
    lines += [f"| {c['id']} {names[c['id']]} | {c['state']} | {c['note']} |" for c in result["checks"]]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(result, src, page_png, path):
    e = html.escape
    items = "".join(
        f"<li><b class=n>{i}</b><div><div class=t>{e(t['title'])} <span class='tier {t['tier']}'>{t['tier']}</span>"
        f" <span class=c>{t['count']}x</span></div><div class=ev>{e(t['evidence'][0])}</div><div class=fix>{e(t['fix'])}</div></div></li>"
        for i, t in enumerate(result["traces"], 1))
    clean = sum(c["state"] == "clean" for c in result["checks"])
    skipped = [c for c in result["checks"] if c["state"] == "could-not-run"]
    doc = f"""<!doctype html><meta charset=utf-8><title>slop-scan: {e(result['title'] or src)}</title>
<style>
body{{margin:0;background:#f4f1ea;font:14px/1.4 system-ui,'Segoe UI',sans-serif;color:#1d1d1b;display:flex;gap:28px;padding:28px;width:max-content}}
.page{{width:860px;border:1px solid #cfc8b8;background:#fff}} .page img{{width:860px;display:block}}
aside{{width:420px}} h1{{font:700 34px/1.1 'Segoe Print','Bradley Hand','Comic Sans MS',cursive;color:#e0301e;margin:4px 0 6px;transform:rotate(-1deg)}}
.src{{color:#5a574f;font-size:13px;margin-bottom:16px;word-break:break-all}} ol{{list-style:none;padding:0;margin:0}}
li{{display:flex;gap:10px;padding:10px 0;border-top:1px dashed #cfc8b8}} .n{{flex:none;width:24px;height:24px;border-radius:50%;background:#e0301e;color:#fff;text-align:center;line-height:24px;font-size:13px}}
.t{{font-weight:700;font-size:15px}} .tier{{font-weight:600;font-size:11px;padding:1px 6px;border:1px solid;border-radius:3px;text-transform:uppercase}}
.high{{color:#b3261e}} .medium{{color:#9a5b00}} .low{{color:#5a574f}} .c{{color:#5a574f;font-weight:400}}
.ev{{color:#3b3a36;font-size:12.5px;margin-top:2px;word-break:break-word}} .fix{{margin-top:3px;font-size:13px}} .fix:before{{content:'fix: ';color:#e0301e;font-weight:700}}
.foot{{border-top:2px solid #1d1d1b;margin-top:12px;padding-top:8px;color:#5a574f;font-size:12.5px}}
</style>
<div class=page><img src="{e(page_png)}" alt="scanned page"></div>
<aside><h1>{len(result['traces'])} slop traces</h1>
<div class=src>{e(src)}<br>{len(SIGNATURES)} signatures: {len(result['traces'])} hit, {clean} clean, {len(skipped)} could not run</div>
<ol>{items or '<li>No traces. This page reads as designed, not generated.</li>'}</ol>
<div class=foot>{''.join(f"{c['id']} could not run: {e(c['note'])}<br>" for c in skipped)}rules: anti-slop (MIT) &middot; report: slop-scan</div></aside>"""
    Path(path).write_text(doc, encoding="utf-8")


def render_png(chrome, html_path, png_path):
    c = Chrome(chrome, 1400, 800)
    try:
        c.open(Path(html_path).resolve().as_uri())
        w, h = c.js("[document.body.scrollWidth + 56, document.body.scrollHeight + 56]")
        c.width = max(int(w), 1)
        c.full_shot(png_path, h)
    finally:
        c.close()


def main(argv=None):
    for s in (sys.stdout, sys.stderr):  # tool text and page text are UTF-8 even on a cp949/cp1252 console
        s.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("src", help="HTML file or http(s) URL")
    ap.add_argument("-o", "--out", default="slop-scan-out")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--fail-on", choices=TIERS, help="exit 1 if any trace is at this tier or higher")
    ap.add_argument("--json", action="store_true", help="print traces.json to stdout instead of the summary")
    a = ap.parse_args(argv)
    chrome = find_chrome()
    if not chrome:
        sys.exit("slop-scan: needs Chrome, Chromium or Edge (set CHROME=/path/to/browser)")
    if not re.match(r"https?://", a.src) and not Path(a.src).is_file():
        sys.exit(f"slop-scan: no such file: {a.src}")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    result = scan(a.src, chrome, a.width, shot=out / "page.png")
    (out / "traces.json").write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    write_md(result, a.src, out / "report.md")
    write_html(result, a.src, "page.png", out / "report.html")
    render_png(chrome, out / "report.html", out / "slop-report.png")
    if a.json:
        print(json.dumps(result, indent=1, ensure_ascii=False))
    else:
        print(summary(result))
        for i, t in enumerate(result["traces"], 1):
            print(f"  {i:>2}. {t['id']} [{t['tier']}] {t['title']} x{t['count']}: {t['evidence'][0]}")
        print(f"wrote {out / 'slop-report.png'}, report.md, report.html, traces.json in {time.perf_counter() - t0:.1f}s")
    if a.fail_on and any(TIERS.index(t["tier"]) >= TIERS.index(a.fail_on) for t in result["traces"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
