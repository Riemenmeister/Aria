"""Read-only local web server for the Aria PC status website."""
from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from .device_mesh import (
   DEFAULT_DEVICE_MESH_PATH,
   build_device_mesh_snapshot,
   build_device_snapshot,
)
from .command_center import (
   DEFAULT_AUDIT_PATH,
   DEFAULT_EVENTS_PATH,
   DEFAULT_STATUS_PATH,
   build_snapshot,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
DEFAULT_REPORT_PATH = ROOT / "reports" / "aria_pc_status.html"
DEFAULT_NAS_ROOT = ROOT
DEFAULT_DEVICE_CLIENT_CHECKLIST_PATH = ROOT / "reports" / "device_mesh_client_checklist.json"

STATIC_REPORTS = {
   "/reports/aria_pc_status.html": DEFAULT_REPORT_PATH,
   "/reports/external_readiness.json": ROOT / "reports" / "external_readiness.json",
   "/reports/goal_completion_audit.json": DEFAULT_AUDIT_PATH,
   "/reports/deployment_receipt.json": ROOT / "reports" / "deployment_receipt.json",
}


class AriaPcServerConfig:
   def __init__(
      self,
      *,
      report_path: Path = DEFAULT_REPORT_PATH,
      status_path: Path = DEFAULT_STATUS_PATH,
      audit_path: Path = DEFAULT_AUDIT_PATH,
      events_path: Path = DEFAULT_EVENTS_PATH,
      nas_root: Path = DEFAULT_NAS_ROOT,
      device_mesh_path: Path = DEFAULT_DEVICE_MESH_PATH,
      device_client_checklist_path: Path = DEFAULT_DEVICE_CLIENT_CHECKLIST_PATH,
   ) -> None:
      self.report_path = report_path
      self.status_path = status_path
      self.audit_path = audit_path
      self.events_path = events_path
      self.nas_root = nas_root
      self.device_mesh_path = device_mesh_path
      self.device_client_checklist_path = device_client_checklist_path


def _json_default(value: Any) -> str:
   if isinstance(value, Path):
      return str(value)
   return str(value)


def build_nas_health(config: AriaPcServerConfig) -> dict[str, Any]:
   root = config.nas_root
   required_paths = {
      "workspace": root,
      "status_model": config.status_path,
      "status_report": config.report_path,
      "goal_audit": config.audit_path,
      "events_log": config.events_path,
   }
   path_checks = {}
   for name, path in required_paths.items():
      path_checks[name] = {
         "path": str(path),
         "exists": path.exists(),
         "is_dir": path.is_dir(),
         "is_file": path.is_file(),
      }

   can_list = False
   sample_entries: list[str] = []
   if root.exists() and root.is_dir():
      try:
         sample_entries = sorted(child.name for child in root.iterdir())[:8]
         can_list = True
      except OSError:
         can_list = False

   ready = (
      root.exists()
      and root.is_dir()
      and can_list
      and path_checks["status_model"]["exists"]
      and path_checks["status_report"]["exists"]
      and path_checks["goal_audit"]["exists"]
   )

   return {
      "status": "ok" if ready else "degraded",
      "root": str(root),
      "exists": root.exists(),
      "is_dir": root.is_dir(),
      "can_list": can_list,
      "sample_entries": sample_entries,
      "required_paths": path_checks,
   }


def build_health(config: AriaPcServerConfig) -> dict[str, Any]:
   snapshot = build_snapshot(
      status_path=config.status_path,
      audit_path=config.audit_path,
      events_path=config.events_path,
   )
   nas = build_nas_health(config)
   device_mesh = build_device_mesh_snapshot(config.device_mesh_path)
   return {
      "status": "ok" if nas["status"] == "ok" else "degraded",
      "service": "aria-pc-server",
      "project": snapshot["project"],
      "ready_count": snapshot["ready_count"],
      "open_count": snapshot["open_count"],
      "nas": nas,
      "device_mesh": device_mesh,
   }


def _safe_static_path(request_path: str, config: AriaPcServerConfig) -> Path | None:
   if request_path in {"/", "/index.html"}:
      return config.report_path
   return STATIC_REPORTS.get(request_path)


def make_handler(config: AriaPcServerConfig) -> type[BaseHTTPRequestHandler]:
   class AriaPcRequestHandler(BaseHTTPRequestHandler):
      server_version = "AriaPcServer/1.0"

      def do_GET(self) -> None:
         parsed = urlparse(self.path)
         path = unquote(parsed.path)

         if path == "/api/health":
            self._send_json(build_health(config))
            return
         if path == "/api/nas":
            self._send_json(build_nas_health(config))
            return
         if path == "/api/device-mesh":
            self._send_json(build_device_mesh_snapshot(config.device_mesh_path))
            return
         if path == "/api/device-client-checklist":
            self._send_file(config.device_client_checklist_path)
            return
         if path.startswith("/api/device/"):
            device_id = path.removeprefix("/api/device/")
            device = build_device_snapshot(device_id, config.device_mesh_path)
            if device is None:
               self._send_json({"error": "device_not_found", "device_id": device_id}, status=HTTPStatus.NOT_FOUND)
               return
            self._send_json(device)
            return
         if path == "/api/command-center":
            self._send_json(
               build_snapshot(
                  status_path=config.status_path,
                  audit_path=config.audit_path,
                  events_path=config.events_path,
               )
            )
            return

         static_path = _safe_static_path(path, config)
         if static_path is not None:
            self._send_file(static_path)
            return

         self._send_json(
            {"error": "not_found", "path": path},
            status=HTTPStatus.NOT_FOUND,
         )

      def log_message(self, format: str, *args: Any) -> None:
         return

      def _send_json(
         self,
         payload: dict[str, Any],
         *,
         status: HTTPStatus = HTTPStatus.OK,
      ) -> None:
         body = json.dumps(payload, default=_json_default, indent=2).encode("utf-8")
         self.send_response(status)
         self.send_header("Content-Type", "application/json; charset=utf-8")
         self.send_header("Content-Length", str(len(body)))
         self.send_header("Cache-Control", "no-store")
         self.end_headers()
         self.wfile.write(body)

      def _send_file(self, path: Path) -> None:
         if not path.exists() or not path.is_file():
            self._send_json(
               {"error": "missing_file", "path": str(path)},
               status=HTTPStatus.NOT_FOUND,
            )
            return

         body = path.read_bytes()
         content_type = "text/html; charset=utf-8"
         if path.suffix == ".json":
            content_type = "application/json; charset=utf-8"

         self.send_response(HTTPStatus.OK)
         self.send_header("Content-Type", content_type)
         self.send_header("Content-Length", str(len(body)))
         self.send_header("Cache-Control", "no-store")
         self.end_headers()
         self.wfile.write(body)

   return AriaPcRequestHandler


def build_server(
   *,
   host: str = DEFAULT_HOST,
   port: int = DEFAULT_PORT,
   config: AriaPcServerConfig | None = None,
) -> ThreadingHTTPServer:
   server_config = config or AriaPcServerConfig()
   return ThreadingHTTPServer((host, port), make_handler(server_config))


def main(argv: list[str] | None = None) -> int:
   parser = argparse.ArgumentParser(description="Serve the local Aria PC status website.")
   parser.add_argument("--host", default=DEFAULT_HOST)
   parser.add_argument("--port", type=int, default=DEFAULT_PORT)
   parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
   parser.add_argument("--status", type=Path, default=DEFAULT_STATUS_PATH)
   parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT_PATH)
   parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS_PATH)
   parser.add_argument("--nas-root", type=Path, default=DEFAULT_NAS_ROOT)
   parser.add_argument("--device-mesh", type=Path, default=DEFAULT_DEVICE_MESH_PATH)
   parser.add_argument("--device-client-checklist", type=Path, default=DEFAULT_DEVICE_CLIENT_CHECKLIST_PATH)
   args = parser.parse_args(argv)

   config = AriaPcServerConfig(
      report_path=args.report,
      status_path=args.status,
      audit_path=args.audit,
      events_path=args.events,
      nas_root=args.nas_root,
      device_mesh_path=args.device_mesh,
      device_client_checklist_path=args.device_client_checklist,
   )
   server = build_server(host=args.host, port=args.port, config=config)
   print(f"Serving Aria PC at http://{args.host}:{server.server_port}/")
   print(f"NAS root: {config.nas_root}")
   try:
      server.serve_forever()
   except KeyboardInterrupt:
      print("\nStopping Aria PC server.")
   finally:
      server.server_close()
   return 0


if __name__ == "__main__":
   raise SystemExit(main())
