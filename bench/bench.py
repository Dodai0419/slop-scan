"""Time slop-scan on the bundled examples: scan only (one Chrome, no pictures) and the full CLI run.

    python bench/bench.py [runs]
"""
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import slopscan  # noqa: E402

runs = int(sys.argv[1]) if len(sys.argv) > 1 else 3
chrome = slopscan.find_chrome()
for name in ("saas-landing", "ai-dashboard", "clean-docs"):
    src = str(ROOT / "examples" / f"{name}.html")
    scan, cli = [], []
    for _ in range(runs):
        t0 = time.perf_counter()
        r = slopscan.scan(src, chrome)
        scan.append(time.perf_counter() - t0)
        with tempfile.TemporaryDirectory() as out:
            t0 = time.perf_counter()
            subprocess.run([sys.executable, str(ROOT / "slopscan.py"), src, "-o", out], check=True, capture_output=True)
            cli.append(time.perf_counter() - t0)
    texts = next(c["note"] for c in r["checks"] if c["id"] == "AS-15")
    print(f"{name}: {len(r['traces'])}/{len(slopscan.SIGNATURES)} traces, {texts}; "
          f"scan median {statistics.median(scan):.2f}s, full CLI median {statistics.median(cli):.2f}s ({runs} runs)")
