import json
import pathlib
import tomllib
import unittest

import Aria
from Aria.Windows import FileSystem


ROOT = pathlib.Path(__file__).resolve().parents[1]


class PackageSmokeTests(unittest.TestCase):
   def test_import_has_main_entrypoint(self):
      self.assertTrue(callable(Aria.Main))

   def test_windows_filesystem_exports_expected_paths(self):
      self.assertEqual(FileSystem.PythonExtension, ".py")
      self.assertTrue(FileSystem.Desktop.endswith("\\"))
      self.assertTrue(FileSystem.Documents.endswith("\\"))

   def test_pyproject_declares_console_script(self):
      data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
      self.assertEqual(data["project"]["scripts"]["aria"], "Aria:Main")
      self.assertGreaterEqual(data["project"]["requires-python"], ">=3.9")


class IntegrationStatusTests(unittest.TestCase):
   def test_goal_markers_are_tracked(self):
      data = json.loads((ROOT / "integrations" / "status.json").read_text(encoding="utf-8"))
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

   def test_status_report_and_vercel_route_exist(self):
      report = ROOT / "reports" / "aria_pc_status.html"
      vercel = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
      html = report.read_text(encoding="utf-8")

      self.assertIn("Aria PC Completion Status", html)
      self.assertIn("Integration Readiness", html)
      self.assertEqual(vercel["rewrites"][0]["source"], "/")
      self.assertEqual(vercel["rewrites"][0]["destination"], "/reports/aria_pc_status.html")


if __name__ == "__main__":
   unittest.main()
