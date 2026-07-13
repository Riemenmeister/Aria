import argparse
import csv
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = ROOT / "integrations" / "status.json"
EXPORT_DIR = ROOT / "exports"
AIRTABLE_PATH = EXPORT_DIR / "airtable_integration_status.csv"
NOTION_PATH = EXPORT_DIR / "notion_aria_pc_status.md"
SLACK_PATH = EXPORT_DIR / "slack_status_update.md"

STATUS_LABELS = {
   "complete": "Complete",
   "local_export_ready": "Local export ready",
   "local_ready_remote_missing": "Local ready, remote missing",
   "local_report_ready": "Local report ready",
   "local_static_report_ready": "Local static report ready",
   "target_missing": "Target missing",
}


def load_status():
   return json.loads(STATUS_PATH.read_text(encoding="utf-8"))


def render_airtable_csv(data):
   buffer = io.StringIO(newline="")
   writer = csv.DictWriter(
      buffer,
      fieldnames=["Project", "Updated", "Integration", "Status", "Evidence", "Next Verification"],
      lineterminator="\n",
   )
   writer.writeheader()
   for item in data["integrations"]:
      writer.writerow(
         {
            "Project": data["project"],
            "Updated": data["updated"],
            "Integration": item["name"],
            "Status": STATUS_LABELS.get(item["status"], item["status"]),
            "Evidence": " | ".join(item.get("evidence", [])),
            "Next Verification": item.get("next_verification", ""),
         }
      )
   return buffer.getvalue()


def bullet_list(items, empty="No current evidence recorded."):
   if not items:
      return f"- {empty}\n"
   return "".join(f"- {item}\n" for item in items)


def render_notion_markdown(data):
   lines = [
      f"# {data['project']} Completion Status",
      "",
      f"Updated: {data['updated']}",
      "",
      "## Summary",
      "",
      "The local Aria PC package is prepared, tested, and documented. External service completion still requires connected-service targets and verification evidence.",
      "",
      "## Local Package Evidence",
      "",
      f"Status: {STATUS_LABELS.get(data['local_package']['status'], data['local_package']['status'])}",
      "",
      bullet_list(data["local_package"].get("evidence", [])),
      "## Integration Readiness",
      "",
   ]
   for item in data["integrations"]:
      lines.extend(
         [
            f"### {item['name']}",
            "",
            f"Status: {STATUS_LABELS.get(item['status'], item['status'])}",
            "",
            "Evidence:",
            bullet_list(item.get("evidence", [])),
            f"Next verification: {item.get('next_verification', 'No next verification recorded.')}",
            "",
         ]
      )
   return "\n".join(lines).replace("\n\n\n", "\n\n")


def render_slack_update(data):
   integrations = data["integrations"]
   missing = [item["name"] for item in integrations if item["status"] == "target_missing"]
   local_ready = [item["name"] for item in integrations if item["status"].startswith("local_")]
   return f"""*{data['project']} status update* ({data['updated']})

Local package baseline is ready: tests pass, package metadata dry-run succeeds, and the status report is generated from `integrations/status.json`.

*Locally prepared:* {', '.join(local_ready) if local_ready else 'none'}
*Targets still needed:* {', '.join(missing) if missing else 'none'}

Next: choose a GitHub remote, push the local commits, configure Vercel for the static report, then connect Airtable/Notion/Slack/HeyGen/Circleback targets with one verification artifact each.
"""


def expected_outputs(data):
   return {
      AIRTABLE_PATH: render_airtable_csv(data),
      NOTION_PATH: render_notion_markdown(data),
      SLACK_PATH: render_slack_update(data),
   }


def main():
   parser = argparse.ArgumentParser(description="Export Aria PC integration status for external tools.")
   parser.add_argument("--check", action="store_true", help="Fail if exports are not up to date.")
   args = parser.parse_args()

   data = load_status()
   outputs = expected_outputs(data)

   if args.check:
      stale = [
         str(path.relative_to(ROOT))
         for path, content in outputs.items()
         if not path.exists() or path.read_text(encoding="utf-8") != content
      ]
      if stale:
         raise SystemExit("exports are not up to date: " + ", ".join(stale))
      print("exports-ok")
      return

   EXPORT_DIR.mkdir(exist_ok=True)
   for path, content in outputs.items():
      path.write_text(content, encoding="utf-8")
      print(f"wrote {path}")


if __name__ == "__main__":
   main()
