import argparse
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reports" / "external_readiness.json"


def run_command(args):
   try:
      resolved = shutil.which(args[0]) if args else None
      if resolved:
          args = [resolved, *args[1:]]
      result = subprocess.run(
         args,
         cwd=ROOT,
         capture_output=True,
         text=True,
         timeout=15,
         check=False,
      )
   except FileNotFoundError:
      return {"available": False, "ok": False, "output": "command not found"}
   except subprocess.TimeoutExpired:
      return {"available": True, "ok": False, "output": "command timed out"}

   output = (result.stdout + result.stderr).strip()
   return {"available": True, "ok": result.returncode == 0, "output": output}


def git_remote_status():
   result = run_command(["git", "remote", "-v"])
   remotes = [line for line in result["output"].splitlines() if line.strip()] if result["ok"] else []
   return {
      "ok": bool(remotes),
      "remotes": remotes,
      "detail": "remote configured" if remotes else "no git remote configured",
   }


def command_status(command, version_args):
   executable = shutil.which(command)
   if not executable:
      return {"ok": False, "available": False, "path": None, "detail": f"{command} not found in PATH"}
   result = run_command([command, *version_args])
   return {
      "ok": result["ok"],
      "available": True,
      "path": executable,
      "detail": result["output"].splitlines()[0] if result["output"] else f"{command} is available",
   }


def github_auth_status():
   if not shutil.which("gh"):
      return {"ok": False, "available": False, "detail": "gh not found in PATH"}
   result = run_command(["gh", "auth", "status"])
   return {
      "ok": result["ok"],
      "available": True,
      "detail": result["output"] or "gh auth status returned no output",
   }


def build_report():
   checks = {
      "git_remote": git_remote_status(),
      "github_cli": command_status("gh", ["--version"]),
      "github_auth": github_auth_status(),
      "vercel_cli": command_status("vercel", ["--version"]),
      "node": command_status("node", ["--version"]),
      "npm": command_status("npm", ["--version"]),
   }
   blockers = [name for name, check in checks.items() if not check["ok"]]
   return {
      "project": "Aria PC",
      "generated_by": "tools/audit_external_readiness.py",
      "status": "ready_for_external_configuration" if blockers else "external_cli_ready",
      "checks": checks,
      "blockers": blockers,
      "next_actions": [
         "Configure a GitHub remote and push local commits.",
         "Authenticate GitHub CLI or provide an existing repository target for connector-based publishing.",
         "Install or authenticate Vercel CLI, or deploy through a connected Vercel/Sites workflow.",
         "Install Node.js/npm locally if local static-site build verification is required.",
         "Record external deployment/import/post/video/meeting evidence in integrations/status.json.",
      ],
   }


def main():
   parser = argparse.ArgumentParser(description="Audit local external-service readiness for Aria PC.")
   parser.add_argument("--check", action="store_true", help="Fail if reports/external_readiness.json is stale.")
   args = parser.parse_args()

   report = build_report()
   rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"

   if args.check:
      if not REPORT_PATH.exists() or REPORT_PATH.read_text(encoding="utf-8") != rendered:
         raise SystemExit("reports/external_readiness.json is not up to date; run py tools/audit_external_readiness.py")
      print("readiness-ok")
      return

   REPORT_PATH.write_text(rendered, encoding="utf-8")
   print(f"wrote {REPORT_PATH}")


if __name__ == "__main__":
   main()


