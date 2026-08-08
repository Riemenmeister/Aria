from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from validate_aria_ai_linkage import load_manifest, validate_manifest  # noqa: E402


class AriaAiLinkageTest(unittest.TestCase):
    def test_manifest_is_complete(self) -> None:
        manifest = load_manifest()
        errors = validate_manifest(manifest)
        self.assertEqual(errors, [])
        self.assertEqual(manifest["project"], "Aria PC")
        self.assertEqual(
            {layer["id"] for layer in manifest["layers"]},
            {"aria", "ariacore", "aria2", "aegis"},
        )


if __name__ == "__main__":
    unittest.main()
