import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from Aria.command_center import build_snapshot, render_text


class AriaCommandCenterTests(unittest.TestCase):
    def test_snapshot_prioritizes_open_external_gates(self) -> None:
        snapshot = build_snapshot()

        self.assertEqual(snapshot["project"], "Aria PC")
        self.assertEqual(snapshot["goal_status"], "incomplete")
        self.assertGreaterEqual(snapshot["ready_count"], 8)
        self.assertEqual(
            [item["name"] for item in snapshot["next_actions"]],
            ["circleback", "close"],
        )
        self.assertIn("Circleback", snapshot["next_actions"][0]["next_action"])
        self.assertIn("Close", snapshot["next_actions"][1]["next_action"])

    def test_render_text_is_terminal_friendly(self) -> None:
        text = render_text(build_snapshot())

        self.assertIn("Aria PC Command Center", text)
        self.assertIn("[NEXT] circleback", text)
        self.assertIn("[NEXT] close", text)
        self.assertIn("[OK] github", text)
        self.assertIn("Last linkage event:", text)

    def test_cli_can_print_json_snapshot(self) -> None:
        result = subprocess.run(
            [sys.executable, "tools/aria_command_center.py", "--json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )

        snapshot = json.loads(result.stdout)
        self.assertEqual(snapshot["project"], "Aria PC")
        self.assertEqual(snapshot["open_count"], 2)
        self.assertEqual(snapshot["next_actions"][0]["name"], "circleback")

    def test_snapshot_accepts_explicit_source_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            status = tmp / "status.json"
            audit = tmp / "audit.json"
            events = tmp / "events.jsonl"
            status.write_text(
                json.dumps(
                    {
                        "project": "Aria PC",
                        "updated": "2026-08-12",
                        "local_package": {"status": "complete", "evidence": []},
                        "integrations": [
                            {
                                "name": "local-console",
                                "status": "complete",
                                "evidence": ["tests"],
                                "next_verification": "Keep tests green.",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            audit.write_text(
                json.dumps(
                    {
                        "project": "Aria PC",
                        "status": "complete",
                        "results": [
                            {
                                "name": "local-console",
                                "status": "complete",
                                "completion": "proved",
                                "evidence": ["tests"],
                                "next_verification": "Keep tests green.",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            events.write_text(
                '{"event_id":"demo","summary":"Command center demo","source":"aria","type":"evidence","timestamp":"2026-08-12T00:00:00+00:00","payload":{},"evidence":[]}\n',
                encoding="utf-8",
            )

            snapshot = build_snapshot(status_path=status, audit_path=audit, events_path=events)

        self.assertEqual(snapshot["open_count"], 0)
        self.assertEqual(snapshot["last_event"]["event_id"], "demo")


if __name__ == "__main__":
    unittest.main()
