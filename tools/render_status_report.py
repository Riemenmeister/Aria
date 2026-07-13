import argparse
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = ROOT / "integrations" / "status.json"
REPORT_PATH = ROOT / "reports" / "aria_pc_status.html"

STATUS_LABELS = {
   "complete": "Complete",
   "local_ready_remote_missing": "Local ready, remote missing",
   "local_status_model_ready": "Local status model ready",
   "local_report_ready": "Local report ready",
   "local_static_report_ready": "Local static report ready",
   "target_missing": "Target missing",
}


def esc(value):
   return html.escape(str(value), quote=True)


def status_class(status):
   if status == "complete":
      return "complete"
   if status.startswith("local_"):
      return "local"
   return "missing"


def render_list(items):
   if not items:
      return '<p class="muted">No current evidence recorded.</p>'
   rows = "".join(f"<li>{esc(item)}</li>" for item in items)
   return f"<ul>{rows}</ul>"


def render_report(data):
   integrations = data["integrations"]
   total = len(integrations)
   complete = sum(1 for item in integrations if item["status"] == "complete")
   local_ready = sum(1 for item in integrations if item["status"].startswith("local_"))
   missing = sum(1 for item in integrations if item["status"] == "target_missing")

   cards = []
   for item in integrations:
      state = item["status"]
      cards.append(
         f"""
         <article class="integration {status_class(state)}">
            <div class="integration-header">
               <h3>{esc(item['name'])}</h3>
               <span class="pill">{esc(STATUS_LABELS.get(state, state))}</span>
            </div>
            <h4>Evidence</h4>
            {render_list(item.get('evidence', []))}
            <h4>Next verification</h4>
            <p>{esc(item.get('next_verification', 'No next verification recorded.'))}</p>
         </article>
         """
      )

   package_evidence = render_list(data["local_package"].get("evidence", []))
   cards_html = "\n".join(cards)
   return f"""<!doctype html>
<html lang="en">
<head>
   <meta charset="utf-8">
   <meta name="viewport" content="width=device-width, initial-scale=1">
   <meta name="color-scheme" content="light dark">
   <title>{esc(data['project'])} Completion Status</title>
   <style>
      :root {{
         --bg: #f7f8f5;
         --panel: #ffffff;
         --text: #18201d;
         --muted: #5e6963;
         --border: #d9dfd7;
         --complete: #207856;
         --local: #2f6690;
         --missing: #9a5b22;
         --shadow: 0 1px 2px rgba(24, 32, 29, .08);
      }}
      @media (prefers-color-scheme: dark) {{
         :root {{
            --bg: #151816;
            --panel: #202521;
            --text: #eef4ef;
            --muted: #b7c1ba;
            --border: #3a443d;
            --shadow: none;
         }}
      }}
      * {{ box-sizing: border-box; }}
      body {{
         margin: 0;
         background: var(--bg);
         color: var(--text);
         font: 16px/1.5 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }}
      main {{ width: min(1120px, calc(100% - 32px)); margin: 0 auto; padding: 32px 0 44px; }}
      header {{ margin-bottom: 24px; }}
      h1 {{ font-size: clamp(2rem, 5vw, 3.25rem); line-height: 1.05; margin: 0 0 12px; letter-spacing: 0; }}
      h2 {{ margin: 0 0 12px; font-size: 1.35rem; letter-spacing: 0; }}
      h3 {{ margin: 0; font-size: 1.05rem; letter-spacing: 0; text-transform: capitalize; }}
      h4 {{ margin: 18px 0 6px; font-size: .82rem; letter-spacing: 0; color: var(--muted); text-transform: uppercase; }}
      p {{ margin: 0 0 10px; }}
      ul {{ margin: 0; padding-left: 20px; }}
      li + li {{ margin-top: 4px; }}
      .muted {{ color: var(--muted); }}
      .summary {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 22px 0; }}
      .metric, .section, .integration {{ background: var(--panel); border: 1px solid var(--border); border-radius: 8px; box-shadow: var(--shadow); }}
      .metric {{ padding: 16px; min-height: 112px; }}
      .metric strong {{ display: block; font-size: 2rem; line-height: 1; margin-bottom: 8px; }}
      .section {{ padding: 20px; margin: 16px 0; }}
      .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }}
      .integration {{ padding: 18px; border-top: 5px solid var(--missing); }}
      .integration.complete {{ border-top-color: var(--complete); }}
      .integration.local {{ border-top-color: var(--local); }}
      .integration-header {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }}
      .pill {{ display: inline-flex; align-items: center; min-height: 28px; padding: 4px 9px; border: 1px solid var(--border); border-radius: 999px; color: var(--muted); font-size: .82rem; white-space: nowrap; }}
      .bar {{ display: grid; grid-template-columns: {complete}fr {local_ready}fr {missing}fr; height: 14px; overflow: hidden; border-radius: 999px; border: 1px solid var(--border); margin-top: 10px; }}
      .bar span:nth-child(1) {{ background: var(--complete); }}
      .bar span:nth-child(2) {{ background: var(--local); }}
      .bar span:nth-child(3) {{ background: var(--missing); }}
      footer {{ color: var(--muted); font-size: .9rem; margin-top: 24px; }}
      @media (max-width: 760px) {{
         main {{ width: min(100% - 20px, 1120px); padding-top: 22px; }}
         .summary, .grid {{ grid-template-columns: 1fr; }}
         .integration-header {{ flex-direction: column; }}
         .pill {{ white-space: normal; }}
      }}
   </style>
</head>
<body>
   <main>
      <header>
         <h1>{esc(data['project'])} Completion Status</h1>
         <p class="muted">Evidence-backed local readiness snapshot updated {esc(data['updated'])}.</p>
      </header>

      <section class="summary" aria-label="Completion summary">
         <div class="metric"><strong>{total}</strong><span>tracked integrations</span></div>
         <div class="metric"><strong>{complete}</strong><span>externally complete</span></div>
         <div class="metric"><strong>{local_ready}</strong><span>locally prepared</span></div>
         <div class="metric"><strong>{missing}</strong><span>targets still missing</span></div>
      </section>

      <section class="section">
         <h2>Executive Summary</h2>
         <p><strong>The local Aria PC package is ready for a GitHub push, but the full multi-service close is not proven yet.</strong> Git, CI, tests, packaging, and a status model are in place. External services still need concrete targets and connected-service evidence.</p>
         <div class="bar" aria-label="Status mix: {complete} complete, {local_ready} local-ready, {missing} target-missing"><span></span><span></span><span></span></div>
      </section>

      <section class="section">
         <h2>Local Package Evidence</h2>
         <p>Status: <strong>{esc(STATUS_LABELS.get(data['local_package']['status'], data['local_package']['status']))}</strong></p>
         {package_evidence}
      </section>

      <section class="section">
         <h2>Integration Readiness</h2>
         <div class="grid">
            {cards_html}
         </div>
      </section>

      <footer>
         Source: integrations/status.json. Generated by tools/render_status_report.py.
      </footer>
   </main>
</body>
</html>
"""


def main():
   parser = argparse.ArgumentParser(description="Render the Aria PC status report.")
   parser.add_argument("--check", action="store_true", help="Fail if the report is not up to date.")
   args = parser.parse_args()

   data = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
   rendered = render_report(data)

   if args.check:
      if not REPORT_PATH.exists() or REPORT_PATH.read_text(encoding="utf-8") != rendered:
         raise SystemExit("reports/aria_pc_status.html is not up to date; run py tools/render_status_report.py")
      print("report-ok")
      return

   REPORT_PATH.write_text(rendered, encoding="utf-8")
   print(f"wrote {REPORT_PATH}")


if __name__ == "__main__":
   main()
