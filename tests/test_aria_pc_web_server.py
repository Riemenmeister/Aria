import json
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from Aria.web_server import AriaPcServerConfig, build_nas_health, build_server, classify_nas_access_error


ROOT = Path(__file__).resolve().parents[1]


class AriaPcWebServerTests(unittest.TestCase):
   @classmethod
   def setUpClass(cls):
      cls.config = AriaPcServerConfig()
      cls.server = build_server(port=0, config=cls.config)
      cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
      cls.thread.start()
      host, port = cls.server.server_address
      cls.base_url = f"http://{host}:{port}"

   @classmethod
   def tearDownClass(cls):
      cls.server.shutdown()
      cls.server.server_close()
      cls.thread.join(timeout=2)

   def read(self, path):
      with urllib.request.urlopen(f"{self.base_url}{path}", timeout=5) as response:
         return response.status, response.headers["Content-Type"], response.read()

   def read_json(self, path):
      status, content_type, body = self.read(path)
      self.assertIn("application/json", content_type)
      return status, json.loads(body.decode("utf-8"))

   def test_serves_status_website_from_root(self):
      status, content_type, body = self.read("/")

      self.assertEqual(status, 200)
      self.assertIn("text/html", content_type)
      self.assertIn(b"Aria PC Completion Status", body)

   def test_health_reports_command_center_and_nas_state(self):
      status, payload = self.read_json("/api/health")

      self.assertEqual(status, 200)
      self.assertEqual(payload["service"], "aria-pc-server")
      self.assertEqual(payload["project"], "Aria PC")
      self.assertEqual(payload["ready_count"], 8)
      self.assertEqual(payload["open_count"], 2)
      self.assertEqual(payload["nas"]["status"], "ok")
      self.assertTrue(payload["nas"]["required_paths"]["status_report"]["exists"])
      self.assertEqual(payload["nas"]["session_resilience"]["risk"], "fritz_nas_idle_logout_after_5_minutes")
      self.assertEqual(payload["nas"]["session_resilience"]["keepalive_interval_seconds"], 240)

   def test_command_center_endpoint_exposes_open_gates(self):
      status, payload = self.read_json("/api/command-center")
      open_names = {item["name"] for item in payload["items"] if item["completion"] == "incomplete"}

      self.assertEqual(status, 200)
      self.assertEqual(open_names, {"circleback", "close"})
      self.assertEqual(payload["goal_status"], "incomplete")

   def test_nas_endpoint_is_read_only_health_check(self):
      status, payload = self.read_json("/api/nas")

      self.assertEqual(status, 200)
      self.assertEqual(payload["status"], "ok")
      self.assertTrue(payload["exists"])
      self.assertTrue(payload["can_list"])
      self.assertTrue(payload["required_paths"]["status_report"]["exists"])
      self.assertIn("session_resilience", payload)
      self.assertIsNone(payload["can_list_error_type"])


   def test_device_mesh_endpoint_lists_pc_laptop_and_phone(self):
      status, payload = self.read_json("/api/device-mesh")
      device_ids = {device["id"] for device in payload["devices"]}

      self.assertEqual(status, 200)
      self.assertEqual(payload["project"], "Aria Device Mesh")
      self.assertEqual(payload["device_count"], 3)
      self.assertEqual(payload["verified_count"], 1)
      self.assertEqual(payload["pending_count"], 2)
      self.assertIn("aria-pc", device_ids)
      self.assertIn("aria-laptop-zephyr", device_ids)
      self.assertIn("aria-smartphone-honor-x5c", device_ids)
      self.assertIn("trusted LAN", " ".join(payload["guardrails"]))

   def test_device_client_checklist_endpoint_exposes_remote_checks(self):
      status, payload = self.read_json("/api/device-client-checklist")
      clients = {client["id"]: client for client in payload["clients"]}

      self.assertEqual(status, 200)
      self.assertEqual(payload["status"], "remote_client_checks_pending")
      self.assertIn("aria-laptop-zephyr", clients)
      self.assertIn("aria-smartphone-honor-x5c", clients)
      self.assertIn("/api/device/aria-laptop-zephyr", " ".join(clients["aria-laptop-zephyr"]["checks"]))
      self.assertIn("/api/device/aria-smartphone-honor-x5c", " ".join(clients["aria-smartphone-honor-x5c"]["checks"]))
   def test_device_endpoint_returns_one_remote_client(self):
      status, payload = self.read_json("/api/device/aria-laptop-zephyr")

      self.assertEqual(status, 200)
      self.assertEqual(payload["device"]["name"], "Aria Laptop Zephyr")
      self.assertEqual(payload["device"]["status"], "configured_pending_live_check")
      self.assertEqual(payload["server"]["port"], 8787)

   def test_unknown_device_returns_json_404(self):
      with self.assertRaises(urllib.error.HTTPError) as caught:
         urllib.request.urlopen(f"{self.base_url}/api/device/missing-device", timeout=5)

      self.assertEqual(caught.exception.code, 404)
      payload = json.loads(caught.exception.read().decode("utf-8"))
      self.assertEqual(payload["error"], "device_not_found")
   def test_unknown_routes_return_json_404(self):
      with self.assertRaises(urllib.error.HTTPError) as caught:
         urllib.request.urlopen(f"{self.base_url}/missing", timeout=5)

      self.assertEqual(caught.exception.code, 404)
      payload = json.loads(caught.exception.read().decode("utf-8"))
      self.assertEqual(payload["error"], "not_found")

   def test_nas_health_marks_missing_root_degraded(self):
      config = AriaPcServerConfig(nas_root=self.config.nas_root / "does-not-exist")
      payload = build_nas_health(config)

      self.assertEqual(payload["status"], "degraded")
      self.assertFalse(payload["exists"])



   def test_nas_access_error_classifier_marks_session_expiry(self):
      self.assertEqual(
         classify_nas_access_error("The network name is no longer available"),
         "fritz_nas_session_or_auth_expired",
      )
      self.assertEqual(
         classify_nas_access_error("Access is denied after login timeout"),
         "fritz_nas_session_or_auth_expired",
      )
      self.assertEqual(classify_nas_access_error("disk quota exceeded"), "nas_access_error")
   def test_windows_operations_scripts_are_present_but_not_executed(self):
      install_script = ROOT / "tools" / "install_aria_pc_server_task.ps1"
      health_script = ROOT / "tools" / "aria_pc_server_health.ps1"
      startup_script = ROOT / "tools" / "install_aria_pc_server_startup.ps1"
      keepalive_script = ROOT / "tools" / "aria_fritz_nas_keepalive.ps1"

      install_source = install_script.read_text(encoding="utf-8")
      health_source = health_script.read_text(encoding="utf-8")
      startup_source = startup_script.read_text(encoding="utf-8")
      keepalive_source = keepalive_script.read_text(encoding="utf-8")

      self.assertIn("Register-ScheduledTask", install_source)
      self.assertIn("New-ScheduledTaskTrigger -AtLogOn", install_source)
      self.assertIn("tools\\aria_pc_server.py", install_source)
      self.assertIn("-ErrorAction Stop", install_source)
      self.assertIn("Startup", startup_source)
      self.assertIn("AriaPcServer.cmd", startup_source)
      self.assertIn("Start-Process", startup_source)
      self.assertIn("Invoke-RestMethod", health_source)
      self.assertIn("/api/health", health_source)
      self.assertIn("/api/nas", health_source)
      self.assertIn("IntervalSeconds", keepalive_source)
      self.assertIn("/api/nas", keepalive_source)
      self.assertIn("5-minute idle logout", keepalive_source)


   def test_runtime_receipt_records_installed_startup_fallback(self):
      receipt = json.loads((ROOT / "reports" / "aria_pc_server_runtime_receipt.json").read_text(encoding="utf-8"))

      self.assertEqual(receipt["project"], "Aria PC")
      self.assertEqual(receipt["status"], "running_with_user_startup_fallback")
      self.assertEqual(receipt["url"], "http://127.0.0.1:8787/")
      self.assertEqual(receipt["fallback"]["method"], "current_user_startup_folder")
      self.assertTrue(receipt["startup_file_exists"])
      self.assertIn("denied_by_windows_policy", receipt["scheduled_task_attempt"]["status"])

if __name__ == "__main__":
   unittest.main()

