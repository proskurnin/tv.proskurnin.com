import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("capture_screenshots", ROOT / "scripts" / "capture-screenshots.py")
capture = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(capture)


class ScreenshotCatalogTest(unittest.TestCase):
    def test_catalog_ids_are_unique_and_synthetic_inputs_are_allowlisted(self):
        data = capture.catalog()
        self.assertGreater(len(data["screens"]), 20)
        self.assertEqual(data["device"]["launcherVersionCode"], 82)
        self.assertEqual(data["device"]["remoteVersionCode"], 4)
        self.assertEqual(len({x["id"] for x in data["screens"]}), len(data["screens"]))
        self.assertTrue(capture.SYNTHETIC_KEYS.issuperset(data["syntheticInputs"]))

    def test_pairing_screen_privacy_masks_are_calibrated(self):
        spec = next(x for x in capture.catalog()["screens"] if x["id"] == "settings-remote")
        self.assertGreaterEqual(len(spec["masks"]), 3)
        self.assertTrue(all(len(m["rect"]) == 4 and min(m["rect"][2:]) > 0 for m in spec["masks"]))

    def test_png_validator_rejects_non_png(self):
        with tempfile.TemporaryDirectory() as temp:
            image = Path(temp) / "bad.png"
            image.write_bytes(b"not an image")
            with self.assertRaises(ValueError):
                capture.png_info(image)

    def test_dry_run_does_not_require_adb(self):
        for spec in capture.catalog()["screens"]:
            if spec["kind"] == "tv" and spec["priority"] in ("P1", "P2"):
                self.assertTrue(spec.get("steps"))


if __name__ == "__main__":
    unittest.main()
