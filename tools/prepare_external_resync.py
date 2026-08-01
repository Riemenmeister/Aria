import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPROVAL_PATH = ROOT / "reports" / "external_sync_approval_request.json"
REDACTED_PATH = ROOT / "reports" / "external_sync_redacted_payload.json"
AIRTABLE_EXPORT_PATH = ROOT / "exports" / "airtable_integration_status.csv"
NOTION_EXPORT_PATH = ROOT / "exports" / "notion_aria_pc_status.md"
PLAN_PATH = ROOT / "reports" / "external_resync_plan.json"

VALID_SERVICES = {"airtable", "notion"}
VALID_PAYLOADS = {"full", "redacted"}


def load_json(path):
   return json.loads(path.read_text(encoding="utf-8"))


def airtable_full_summary():
   rows = list(csv.DictReader(AIRTABLE_EXPORT_PATH.read_text(encoding="utf-8").splitlines()))
   return {
      "source": str(AIRTABLE_EXPORT_PATH.relative_to(ROOT)),
      "record_count": len(rows),
      "integrations": [row["Integration"] for row in rows],
      "fields": list(rows[0].keys()) if rows else [],
   }


def notion_full_summary():
   text = NOTION_EXPORT_PATH.read_text(encoding="utf-8")
   return {
      "source": str(NOTION_EXPORT_PATH.relative_to(ROOT)),
      "line_count": len(text.splitlines()),
      "contains_current_title": "# Aria PC Completion Status" in text,
   }


def build_plan(service, payload):
   approval = load_json(APPROVAL_PATH)
   redacted = load_json(REDACTED_PATH)
   approval_services = {item["service"]: item for item in approval["external_writes_requiring_explicit_approval"]}
   if service not in approval_services:
      raise SystemExit(f"{service} does not currently require approval")

   if service == "airtable":
      full_summary = airtable_full_summary()
      redacted_summary = {
         "source": f"{REDACTED_PATH.relative_to(ROOT)}:airtable",
         "record_count": len(redacted["airtable"]),
         "integrations": [row["integration"] for row in redacted["airtable"]],
         "redaction_policy": redacted["redaction_policy"],
      }
   else:
      full_summary = notion_full_summary()
      redacted_summary = {
         "source": f"{REDACTED_PATH.relative_to(ROOT)}:notion",
         "character_count": len(redacted["notion"]),
         "redaction_policy": redacted["redaction_policy"],
      }

   selected = full_summary if payload == "full" else redacted_summary
   return {
      "project": approval["project"],
      "generated_at": approval["generated_at"],
      "service": service,
      "payload": payload,
      "destination": approval_services[service]["destination"],
      "requested_action": approval_services[service]["requested_action"],
      "risk_summary": approval_services[service]["risk_summary"],
      "selected_payload_summary": selected,
      "approval_required": True,
      "external_write_performed": False,
      "execution_gate": "This tool prepares the resync plan only. External writes must be performed explicitly after user approval in the connected service tool.",
   }


def main():
   parser = argparse.ArgumentParser(description="Prepare an approved external resync plan without performing external writes.")
   parser.add_argument("--service", choices=sorted(VALID_SERVICES), required=True)
   parser.add_argument("--payload", choices=sorted(VALID_PAYLOADS), required=True)
   parser.add_argument("--check", action="store_true", help="Fail if reports/external_resync_plan.json is stale for this service/payload.")
   args = parser.parse_args()

   plan = build_plan(args.service, args.payload)
   rendered = json.dumps(plan, indent=2, sort_keys=True) + "\n"

   if args.check:
      if not PLAN_PATH.exists() or PLAN_PATH.read_text(encoding="utf-8") != rendered:
         raise SystemExit("reports/external_resync_plan.json is not up to date; run py tools/prepare_external_resync.py with the same arguments")
      print("external-resync-plan-ok")
      return

   PLAN_PATH.write_text(rendered, encoding="utf-8")
   print(f"wrote {PLAN_PATH}")


if __name__ == "__main__":
   main()
