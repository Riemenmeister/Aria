import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DeviceMeshLanProbeTests(unittest.TestCase):
   def test_lan_receipt_tracks_pending_remote_clients(self):
      receipt = json.loads((ROOT / "reports" / "device_mesh_lan_receipt.json").read_text(encoding="utf-8"))

      self.assertEqual(receipt["project"], "Aria Device Mesh")
      self.assertEqual(receipt["status"], "local_mesh_endpoints_verified_remote_clients_pending")
      self.assertEqual(receipt["probe_script"], "tools/aria_device_mesh_probe.ps1")
      self.assertIn("aria-laptop-zephyr", receipt["remote_clients_pending_live_check"])
      self.assertIn("aria-smartphone-honor-x5c", receipt["remote_clients_pending_live_check"])
      self.assertIn("--host 0.0.0.0", receipt["safe_lan_command"])
      self.assertIn("Do not store device passwords", " ".join(receipt["guardrails"]))

   def test_probe_script_checks_mesh_and_individual_devices(self):
      source = (ROOT / "tools" / "aria_device_mesh_probe.ps1").read_text(encoding="utf-8")

      self.assertIn("/api/health", source)
      self.assertIn("/api/device-mesh", source)
      self.assertIn("required_checks", source)
      self.assertIn("remote_clients_pending_live_check", source)
      self.assertIn("RecordPath", source)


if __name__ == "__main__":
   unittest.main()