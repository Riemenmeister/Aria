import csv
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
      self.assertEqual(vercel["rewrites"][0]["destination"], "/index.html")
   def test_status_model_counts_external_proof(self):
      data = json.loads((ROOT / "integrations" / "status.json").read_text(encoding="utf-8"))
      markers = {item["name"]: item for item in data["integrations"]}
      report = (ROOT / "reports" / "aria_pc_status.html").read_text(encoding="utf-8")

      self.assertEqual(markers["airtable"]["status"], "external_synced_airtable")
      self.assertEqual(markers["data-analytics"]["status"], "production_report_published")
      self.assertEqual(markers["vercel"]["status"], "production_deployed_sites")
      self.assertIn("<strong>3</strong><span>externally complete</span>", report)
      self.assertIn("Production report published", report)

   def test_static_site_build_configuration_exists(self):
      package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
      vercel = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
      build_tool = ROOT / "tools" / "build_static_site.js"
      build_source = build_tool.read_text(encoding="utf-8")

      self.assertEqual(package["scripts"]["build"], "node tools/build_static_site.js")
      self.assertEqual(package["scripts"]["check"], "node tools/build_static_site.js --check")
      self.assertEqual(vercel["outputDirectory"], "dist")
      self.assertIn("server", build_source)
      self.assertIn("hosting.json", build_source)
      self.assertTrue(build_tool.exists())

   def test_external_service_exports_exist(self):
      airtable = ROOT / "exports" / "airtable_integration_status.csv"
      notion = ROOT / "exports" / "notion_aria_pc_status.md"
      slack = ROOT / "exports" / "slack_status_update.md"
      heygen = ROOT / "exports" / "heygen_status_video_brief.md"
      circleback = ROOT / "exports" / "circleback_meeting_brief.md"

      rows = list(csv.DictReader(airtable.read_text(encoding="utf-8").splitlines()))
      self.assertEqual(len(rows), 8)
      self.assertEqual(rows[0]["Project"], "Aria PC")
      self.assertIn("# Aria PC Completion Status", notion.read_text(encoding="utf-8"))
      self.assertIn("*Aria PC status update*", slack.read_text(encoding="utf-8"))
      self.assertIn("# HeyGen Video Brief", heygen.read_text(encoding="utf-8"))
      self.assertIn("# Circleback Meeting Brief", circleback.read_text(encoding="utf-8"))

   def test_external_readiness_report_tracks_blockers(self):
      readiness = json.loads((ROOT / "reports" / "external_readiness.json").read_text(encoding="utf-8"))

      self.assertEqual(readiness["project"], "Aria PC")
      self.assertIn("git_remote", readiness["checks"])
      self.assertIn("github_cli", readiness["checks"])
      self.assertIn("vercel_cli", readiness["checks"])
      self.assertIn("node", readiness["checks"])
      self.assertIn("npm", readiness["checks"])
      self.assertIn("blockers", readiness)
      self.assertIn(readiness["status"], {"ready_for_external_configuration", "external_cli_ready"})

   def test_deployment_receipt_records_success(self):
      receipt = json.loads((ROOT / "reports" / "deployment_receipt.json").read_text(encoding="utf-8"))

      self.assertEqual(receipt["status"], "succeeded")
      self.assertTrue(receipt["url"].startswith("https://aria-pc-status-20260713"))
      self.assertEqual(receipt["version_number"], 5)
   def test_airtable_receipt_records_success(self):
      receipt = json.loads((ROOT / "reports" / "airtable_receipt.json").read_text(encoding="utf-8"))

      self.assertEqual(receipt["status"], "succeeded")
      self.assertEqual(receipt["base_id"], "apprXVtcJBWQJXl5n")
      self.assertEqual(receipt["table_id"], "tbl16tPYsvz97KWlh")
      self.assertEqual(receipt["record_count"], 8)
      self.assertEqual(receipt["last_sync"]["operation"], "update_records_for_table")
      self.assertEqual(receipt["last_sync"]["updated_record_count"], 8)
      self.assertIn("Production report published", receipt["last_sync"]["verification"])
   def test_connector_availability_report_records_remaining_blockers(self):
      report = json.loads((ROOT / "reports" / "connector_availability.json").read_text(encoding="utf-8"))
      connectors = report["connectors"]

      self.assertEqual(report["status"], "partial_external_connectors_available")
      self.assertEqual(connectors["airtable"]["status"], "available_and_synced")
      self.assertEqual(connectors["github"]["status"], "available_existing_repo_only")
      self.assertEqual(connectors["notion"]["status"], "tool_unavailable_in_thread")
      self.assertEqual(connectors["slack"]["status"], "tool_unavailable_in_thread")
      self.assertEqual(connectors["heygen"]["status"], "tool_unavailable_in_thread")
      self.assertEqual(connectors["circleback"]["status"], "tool_unavailable_in_thread")
   def test_git_repair_receipt_records_clean_status(self):
      receipt = json.loads((ROOT / "reports" / "git_repair_receipt.json").read_text(encoding="utf-8"))

      self.assertEqual(receipt["status"], "repaired")
      self.assertEqual(len(receipt["repaired_objects"]), 2)
      self.assertIn("git status --short --branch: ## master", receipt["verification"])
      self.assertTrue(any("git fsck --full" in item for item in receipt["verification"]))


if __name__ == "__main__":
   unittest.main()

