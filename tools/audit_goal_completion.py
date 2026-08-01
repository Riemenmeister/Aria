import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = ROOT / "integrations" / "status.json"
READINESS_PATH = ROOT / "reports" / "external_readiness.json"
CONNECTOR_PATH = ROOT / "reports" / "connector_availability.json"
APPROVAL_PATH = ROOT / "reports" / "external_sync_approval_request.json"
REPORT_PATH = ROOT / "reports" / "goal_completion_audit.json"

REQUIRED_MARKERS = [
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
]

COMPLETE_STATUSES = {
   "production_report_published",
   "production_deployed_sites",
   "external_generated_heygen",
   "external_drafted_slack",
}

RESYNC_PENDING_STATUSES = {
   "external_synced_airtable_resync_pending",
   "external_synced_notion_resync_pending",
}


def load_json(path):
   return json.loads(path.read_text(encoding="utf-8"))


def item_result(name, status, evidence, next_verification):
   if status in COMPLETE_STATUSES:
      completion = "proved"
      reason = "Current status has direct external or production evidence."
   elif status in RESYNC_PENDING_STATUSES:
      completion = "incomplete"
      reason = "A previous external sync exists, but the current 2026-08-01 resync requires explicit approval."
   else:
      completion = "incomplete"
      reason = "Current status still names missing targets, connector blockers, or absent artifact proof."
   return {
      "name": name,
      "status": status,
      "completion": completion,
      "reason": reason,
      "evidence": evidence,
      "next_verification": next_verification,
   }


def build_audit():
   status = load_json(STATUS_PATH)
   readiness = load_json(READINESS_PATH)
   connectors = load_json(CONNECTOR_PATH)
   approval = load_json(APPROVAL_PATH)
   markers = {item["name"]: item for item in status["integrations"]}

   missing_markers = [name for name in REQUIRED_MARKERS if name not in markers]
   extra_markers = [name for name in markers if name not in REQUIRED_MARKERS]
   results = []
   for name in REQUIRED_MARKERS:
      item = markers.get(name)
      if item is None:
         results.append(
            {
               "name": name,
               "status": "missing",
               "completion": "missing",
               "reason": "Required objective marker is absent from integrations/status.json.",
               "evidence": [],
               "next_verification": "Add this marker to integrations/status.json with evidence and next verification.",
            }
         )
      else:
         results.append(item_result(name, item["status"], item.get("evidence", []), item.get("next_verification", "")))

   incomplete = [item for item in results if item["completion"] != "proved"]
   return {
      "project": status["project"],
      "checked_at": status["updated"],
      "status": "complete" if not incomplete and not missing_markers and not extra_markers else "incomplete",
      "required_markers": REQUIRED_MARKERS,
      "missing_markers": missing_markers,
      "extra_markers": extra_markers,
      "proved_count": sum(1 for item in results if item["completion"] == "proved"),
      "incomplete_count": len(incomplete),
      "results": results,
      "local_package": status["local_package"],
      "readiness_blockers": readiness.get("blockers", []),
      "connector_status": {name: data["status"] for name, data in connectors.get("connectors", {}).items()},
      "approval_required_for": [item["service"] for item in approval.get("external_writes_requiring_explicit_approval", [])],
      "completion_gate": "Do not mark the goal complete while status is incomplete, any required marker is unproved, or approval/login/target/artifact blockers remain.",
   }


def main():
   parser = argparse.ArgumentParser(description="Audit whether the full Aria PC goal is actually complete.")
   parser.add_argument("--check", action="store_true", help="Fail if reports/goal_completion_audit.json is stale.")
   args = parser.parse_args()

   audit = build_audit()
   rendered = json.dumps(audit, indent=2, sort_keys=True) + "\n"

   if args.check:
      if not REPORT_PATH.exists() or REPORT_PATH.read_text(encoding="utf-8") != rendered:
         raise SystemExit("reports/goal_completion_audit.json is not up to date; run py tools/audit_goal_completion.py")
      print("goal-audit-ok")
      return

   REPORT_PATH.write_text(rendered, encoding="utf-8")
   print(f"wrote {REPORT_PATH}")


if __name__ == "__main__":
   main()
