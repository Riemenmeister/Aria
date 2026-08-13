import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DeviceMeshClientChecklistTests(unittest.TestCase):
   def test_client_checklist_tracks_zephyr_and_honor(self):
      checklist = json.loads((ROOT / "reports" / "device_mesh_client_checklist.json").read_text(encoding="utf-8"))
      clients = {client["id"]: client for client in checklist["clients"]}

      self.assertEqual(checklist["status"], "remote_client_checks_pending")
      self.assertEqual(set(clients), {"aria-laptop-zephyr", "aria-smartphone-honor-x5c"})
      self.assertIn("--host 0.0.0.0", checklist["server"]["safe_start_command"])
      self.assertIn("/api/device/aria-laptop-zephyr", " ".join(clients["aria-laptop-zephyr"]["checks"]))
      self.assertIn("/api/device/aria-smartphone-honor-x5c", " ".join(clients["aria-smartphone-honor-x5c"]["checks"]))
      self.assertIn("No device passwords", " ".join(checklist["guardrails"]))
      self.assertIn("Do not connect Actively", " ".join(checklist["guardrails"]))

   def test_lan_access_guide_keeps_connection_read_only(self):
      guide = (ROOT / "docs" / "device_mesh_lan_access.md").read_text(encoding="utf-8")

      self.assertIn("py tools\\aria_pc_server.py --host 0.0.0.0 --port 8787", guide)
      self.assertIn("http://<aria-pc-lan-ip>:8787/api/device/aria-laptop-zephyr", guide)
      self.assertIn("http://<aria-pc-lan-ip>:8787/api/device/aria-smartphone-honor-x5c", guide)
      self.assertIn("read-only", guide)
      self.assertIn("Do not store device passwords", guide)


if __name__ == "__main__":
   unittest.main()