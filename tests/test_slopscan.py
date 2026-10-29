import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import slopscan  # noqa: E402

CHROME = slopscan.find_chrome()
NAMED = {"black": "#000000", "white": "#ffffff"}


def table_rows():
    """Rows of anti-slop's own reference table (skills/antislop-human/SKILL.md, MIT)."""
    for line in (ROOT / "tests/fixtures/antislop-contrast-table.md").read_text(encoding="utf-8").splitlines()[2:]:
        pairing, ratio, normal, large = [c.strip() for c in line.strip("|").split("|")]
        fg, bg = (NAMED.get(t.strip().lower(), t.strip()) for t in pairing.split(" on "))
        yield pairing, slopscan.hex_rgb(fg), slopscan.hex_rgb(bg), ratio, normal, large


class Contrast(unittest.TestCase):
    def test_matches_antislop_reference_table(self):
        rows = list(table_rows())
        self.assertEqual(len(rows), 9)
        for pairing, fg, bg, ratio, normal, large in rows:
            raw = slopscan.contrast(fg, bg)
            with self.subTest(pairing):
                self.assertEqual(f"{raw:.2f}", ratio)
                self.assertEqual("Pass" if raw >= 4.5 else "Fail", normal)
                self.assertEqual("Pass" if raw >= 3.0 else "Fail", large)

    def test_near_threshold_is_not_rounded_up(self):
        # anti-slop's own warning: 4.4983:1 displays as 4.50 and still fails 4.5:1
        self.assertLess(slopscan.contrast(slopscan.hex_rgb("#777777"), slopscan.hex_rgb("#070707")), 4.5)

    def test_parses_css_colors(self):
        self.assertEqual(slopscan.css_rgba("rgb(1, 2, 3)"), (1, 2, 3, 1.0))
        self.assertEqual(slopscan.css_rgba("rgba(10, 20, 30, 0.5)"), (10, 20, 30, 0.5))
        self.assertEqual(slopscan.css_rgba("transparent"), (0, 0, 0, 0.0))


@unittest.skipUnless(CHROME, "needs Chrome, Chromium or Edge")
class Scan(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.slop = slopscan.scan(str(ROOT / "examples/saas-landing.html"), CHROME)
        cls.clean = slopscan.scan(str(ROOT / "examples/clean-docs.html"), CHROME)

    def ids(self, result):
        return {t["id"] for t in result["traces"]}

    def test_slop_page_shows_the_known_tells(self):
        expected = {"AS-01", "AS-02", "AS-03", "AS-05", "AS-06", "AS-07", "AS-08", "AS-09", "AS-10",
                    "AS-12", "AS-13", "AS-14", "AS-15"}
        self.assertTrue(expected <= self.ids(self.slop), sorted(expected - self.ids(self.slop)))

    def test_clean_page_has_no_traces(self):
        self.assertEqual(self.clean["traces"], [], [t["id"] for t in self.clean["traces"]])

    def test_every_check_reports_its_coverage(self):
        # Zero-Breach's contract: each check says it ran, or why it could not run
        for result in (self.slop, self.clean):
            self.assertEqual(len(result["checks"]), len(slopscan.SIGNATURES))
            for c in result["checks"]:
                self.assertIn(c["state"], ("hit", "clean", "could-not-run"))

    def test_low_contrast_text_is_found_with_its_colors(self):
        hits = [t for t in self.slop["traces"] if t["id"] == "AS-15"][0]["evidence"]
        self.assertTrue(any("#9ca3af on #ffffff" in e for e in hits), hits)

    def test_boxes_point_at_real_elements(self):
        for t in self.slop["traces"]:
            for b in t["boxes"]:
                self.assertGreater(b["w"], 0)
                self.assertGreater(b["h"], 0)


@unittest.skipUnless(CHROME, "needs Chrome, Chromium or Edge")
class Cli(unittest.TestCase):
    def run_cli(self, *args):
        env = {k: v for k, v in os.environ.items() if k not in ("PYTHONUTF8", "PYTHONIOENCODING")}
        return subprocess.run([sys.executable, str(ROOT / "slopscan.py"), *args], capture_output=True, env=env, cwd=ROOT)

    def test_writes_picture_report_and_json(self):
        with tempfile.TemporaryDirectory() as out:
            p = self.run_cli("examples/saas-landing.html", "-o", out)
            self.assertEqual(p.returncode, 0, p.stderr.decode("utf-8", "replace"))
            text = p.stdout.decode("utf-8")  # must be UTF-8 even on a cp949/cp1252 console
            self.assertRegex(text, r"slop traces: \d+ of \d+ signatures")
            self.assertEqual(Path(out, "slop-report.png").read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
            data = json.loads(Path(out, "traces.json").read_text(encoding="utf-8"))
            self.assertTrue(data["traces"])
            self.assertIn("🚀", Path(out, "report.md").read_text(encoding="utf-8"))

    def test_fail_on_turns_traces_into_exit_code(self):
        with tempfile.TemporaryDirectory() as out:
            self.assertEqual(self.run_cli("examples/saas-landing.html", "-o", out, "--fail-on", "medium").returncode, 1)
            self.assertEqual(self.run_cli("examples/clean-docs.html", "-o", out, "--fail-on", "low").returncode, 0)


if __name__ == "__main__":
    unittest.main()
