"""Read-only device mesh helpers for Aria PC remote clients."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEVICE_MESH_PATH = ROOT / "integrations" / "device_mesh.json"


def load_device_mesh(path: Path = DEFAULT_DEVICE_MESH_PATH) -> dict[str, Any]:
   return json.loads(path.read_text(encoding="utf-8"))


def devices_by_id(mesh: dict[str, Any]) -> dict[str, dict[str, Any]]:
   return {str(device["id"]): device for device in mesh.get("devices", [])}


def build_device_mesh_snapshot(path: Path = DEFAULT_DEVICE_MESH_PATH) -> dict[str, Any]:
   mesh = load_device_mesh(path)
   devices = mesh.get("devices", [])
   verified = [device for device in devices if str(device.get("status", "")).startswith("verified")]
   pending = [device for device in devices if device not in verified]
   return {
      "project": mesh.get("project", "Aria Device Mesh"),
      "updated": mesh.get("updated"),
      "status": "ok" if devices and not pending else mesh.get("status", "configured_pending_remote_client_verification"),
      "server": mesh.get("server", {}),
      "device_count": len(devices),
      "verified_count": len(verified),
      "pending_count": len(pending),
      "devices": devices,
      "guardrails": mesh.get("guardrails", []),
      "next_verification": mesh.get("next_verification", []),
      "source_file": str(path),
   }


def build_device_snapshot(device_id: str, path: Path = DEFAULT_DEVICE_MESH_PATH) -> dict[str, Any] | None:
   snapshot = build_device_mesh_snapshot(path)
   device = devices_by_id(snapshot).get(device_id)
   if device is None:
      return None
   return {
      "project": snapshot["project"],
      "updated": snapshot["updated"],
      "server": snapshot["server"],
      "device": device,
      "guardrails": snapshot["guardrails"],
      "source_file": snapshot["source_file"],
   }
