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
         "actively",
         "close",
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
      self.assertEqual(markers["notion"]["status"], "external_synced_notion")
      self.assertEqual(markers["heygen"]["status"], "external_generated_heygen")
      self.assertEqual(markers["slack"]["status"], "external_drafted_slack")
      self.assertIn("<strong>7</strong><span>externally complete</span>", report)
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
      self.assertEqual(len(rows), 10)
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
      self.assertIn("github_auth", readiness["checks"])
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
      self.assertEqual(receipt["record_count"], 10)
      self.assertEqual(receipt["last_sync"]["operation"], "upsert_records_for_table")
      self.assertEqual(receipt["last_sync"]["updated_record_count"], 10)
      self.assertIn("Generated in HeyGen", receipt["last_sync"]["verification"])
      self.assertEqual(receipt["last_attempt"]["status"], "rejected_by_connector_risk_policy")

   def test_connector_availability_report_records_remaining_blockers(self):
      report = json.loads((ROOT / "reports" / "connector_availability.json").read_text(encoding="utf-8"))
      connectors = report["connectors"]

      self.assertEqual(report["status"], "partial_external_connectors_available")
      self.assertEqual(connectors["airtable"]["status"], "available_and_synced")
      self.assertEqual(connectors["github"]["status"], "available_and_synced")
      self.assertEqual(connectors["notion"]["status"], "available_and_synced")
      self.assertEqual(connectors["slack"]["status"], "available_and_drafted")
      self.assertEqual(connectors["heygen"]["status"], "available_and_generated")
      self.assertEqual(connectors["circleback"]["status"], "available_no_artifact_found")
      self.assertEqual(connectors["actively"]["status"], "connector_not_connected")
      self.assertEqual(connectors["close"]["status"], "connector_invalid_argument")

   def test_new_connector_receipts_record_current_evidence(self):
      notion = json.loads((ROOT / "reports" / "notion_receipt.json").read_text(encoding="utf-8"))
      slack = json.loads((ROOT / "reports" / "slack_receipt.json").read_text(encoding="utf-8"))
      heygen = json.loads((ROOT / "reports" / "heygen_receipt.json").read_text(encoding="utf-8"))
      circleback = json.loads((ROOT / "reports" / "circleback_receipt.json").read_text(encoding="utf-8"))
      actively = json.loads((ROOT / "reports" / "actively_receipt.json").read_text(encoding="utf-8"))
      close = json.loads((ROOT / "reports" / "close_receipt.json").read_text(encoding="utf-8"))

      self.assertEqual(notion["status"], "succeeded")
      self.assertTrue(notion["page_url"].startswith("https://app.notion.com/"))
      self.assertEqual(notion["last_attempt"]["status"], "rejected_by_connector_risk_policy")
      self.assertEqual(slack["status"], "draft_created")
      self.assertEqual(slack["draft_id"], "Dr0BJC668XFU")
      self.assertEqual(heygen["status"], "completed")
      self.assertEqual(heygen["video_id"], "8e1fec9f71d04826b2f7b4cafe39d570")
      self.assertEqual(circleback["status"], "connector_available_no_event")
      self.assertEqual(actively["error_code"], "USER_NOT_LOGGED_IN")
      self.assertEqual(close["status"], "connector_invalid_argument")


   def test_external_sync_approval_request_records_options(self):
      approval = json.loads((ROOT / "reports" / "external_sync_approval_request.json").read_text(encoding="utf-8"))
      redacted = json.loads((ROOT / "reports" / "external_sync_redacted_payload.json").read_text(encoding="utf-8"))
      approval_doc = (ROOT / "docs" / "external_sync_approval.md").read_text(encoding="utf-8")

      services = {item["service"] for item in approval["external_writes_requiring_explicit_approval"]}
      self.assertEqual(services, {"airtable", "notion"})
      self.assertTrue(any("Approve full Airtable resync" in option for option in approval["approval_options"]))
      self.assertEqual(redacted["redaction_policy"].startswith("Keep integration names"), True)
      self.assertIn("Writes Awaiting Approval", approval_doc)

   def test_goal_completion_audit_records_unfinished_requirements(self):
      audit = json.loads((ROOT / "reports" / "goal_completion_audit.json").read_text(encoding="utf-8"))
      required = {
         "github",
         "actively",
         "airtable",
         "data-analytics",
         "notion",
         "heygen",
         "circleback",
         "slack",
         "vercel",
         "close",
      }
      results = {item["name"]: item for item in audit["results"]}

      self.assertEqual(audit["status"], "incomplete")
      self.assertEqual(set(audit["required_markers"]), required)
      self.assertEqual(set(results), required)
      self.assertEqual(results["heygen"]["completion"], "proved")
      self.assertEqual(results["github"]["completion"], "proved")
      self.assertNotIn("github", audit["unfinished_required_markers"])
      self.assertNotIn("airtable", audit["approval_required_for"])
      self.assertNotIn("notion", audit["approval_required_for"])

   def test_external_resync_plan_is_dry_run(self):
      plan = json.loads((ROOT / "reports" / "external_resync_plan.json").read_text(encoding="utf-8"))
      audit = json.loads((ROOT / "reports" / "goal_completion_audit.json").read_text(encoding="utf-8"))

      self.assertEqual(plan["service"], "airtable")
      self.assertEqual(plan["payload"], "redacted")
      self.assertEqual(plan["approval_required"], True)
      self.assertEqual(plan["external_write_performed"], False)
      self.assertEqual(audit["prepared_resync_plan"]["external_write_performed"], False)
   def test_git_repair_receipt_records_clean_status(self):
      receipt = json.loads((ROOT / "reports" / "git_repair_receipt.json").read_text(encoding="utf-8"))

      self.assertEqual(receipt["status"], "repaired")
      self.assertGreaterEqual(len(receipt["repaired_objects"]), 2)
      self.assertTrue(any("git status --short --branch: ## master" in item for item in receipt["verification"]))
      self.assertTrue(any("git fsck --full" in item for item in receipt["verification"]))


if __name__ == "__main__":
   unittest.main()









