import json
import pathlib
import tomllib
import unittest

import Aria
from Aria.Windows import FileSystem


class PackageSmokeTests(unittest.TestCase):
   def test_import_has_main_entrypoint(self):
      self.assertTrue(callable(Aria.Main))

   def test_windows_filesystem_exports_expected_paths(self):
      self.assertEqual(FileSystem.PythonExtension, ".py")
      self.assertTrue(FileSystem.Desktop.endswith("\\"))
      self.assertTrue(FileSystem.Documents.endswith("\\"))

   def test_pyproject_declares_console_script(self):
      pyproject = pathlib.Path(__file__).resolve().parents[1] / "pyproject.toml"
      data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
      self.assertEqual(data["project"]["scripts"]["aria"], "Aria:Main")
      self.assertGreaterEqual(data["project"]["requires-python"], ">=3.9")


class IntegrationStatusTests(unittest.TestCase):
   def test_goal_markers_are_tracked(self):
      status_path = pathlib.Path(__file__).resolve().parents[1] / "integrations" / "status.json"
      data = json.loads(status_path.read_text(encoding="utf-8"))
      markers = {item["name"]: item for item in data["integrations"]}
      expected = {
         "airtable",
         "data-analytics",
         "github",
         "notion",
         "heygen",
         "circleback",
         "slack",
         "vercel",
      }

      self.assertEqual(set(markers), expected)
      for marker in markers.values():
         self.assertIn("status", marker)
         self.assertIn("evidence", marker)
         self.assertIn("next_verification", marker)
         if marker["status"] != "target_missing":
            self.assertGreater(len(marker["evidence"]), 0)


if __name__ == "__main__":
   unittest.main()
