from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from Aria.ai_linkage import AriaAiLinkage, LinkageEventStore, LinkageOrchestrator


class AriaLinkageOrchestratorTest(unittest.TestCase):
    def test_start_goal_persists_goal_and_plan_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LinkageEventStore(Path(tmpdir) / "events.jsonl", AriaAiLinkage())
            orchestrator = LinkageOrchestrator(store)

            events = orchestrator.start_goal(
                goal_id="goal-1",
                summary="Connect the four Aria AI layers.",
                evidence=("integrations/aria_ai_linkage.json",),
            )

            self.assertEqual([event["type"] for event in events], ["goal", "action"])
            self.assertEqual(store.health_snapshot()["event_count"], 2)
            self.assertEqual(store.read_all()[1]["payload"]["layers"], ["aria", "ariacore", "aria2", "aegis"])

    def test_records_evidence_and_blocker_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LinkageEventStore(Path(tmpdir) / "events.jsonl", AriaAiLinkage())
            orchestrator = LinkageOrchestrator(store)

            evidence = orchestrator.record_evidence(
                goal_id="goal-1",
                evidence_id="ci",
                summary="CI passed for the goal.",
                evidence=("https://github.com/Riemenmeister/Aria/actions",),
            )
            blocker = orchestrator.record_blocker(
                goal_id="goal-1",
                blocker_id="review",
                summary="Merge requires explicit approval.",
                next_action="Ask for approval before merging.",
            )

            self.assertEqual(evidence["type"], "evidence")
            self.assertEqual(blocker["source"], "aegis")
            self.assertEqual(blocker["payload"]["next_action"], "Ask for approval before merging.")

    def test_cli_start_goal_and_record_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "events.jsonl"
            start = subprocess.run(
                [
                    sys.executable,
                    "tools/aria_linkage_events.py",
                    "--store",
                    str(store_path),
                    "start-goal",
                    "--goal-id",
                    "cli-goal",
                    "--summary",
                    "Start goal from CLI.",
                    "--evidence",
                    "integrations/aria_ai_linkage.json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )
            evidence = subprocess.run(
                [
                    sys.executable,
                    "tools/aria_linkage_events.py",
                    "--store",
                    str(store_path),
                    "record-evidence",
                    "--goal-id",
                    "cli-goal",
                    "--evidence-id",
                    "manifest",
                    "--summary",
                    "Manifest is present.",
                    "--evidence",
                    "integrations/aria_ai_linkage.json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )
            validate = subprocess.run(
                [
                    sys.executable,
                    "tools/aria_linkage_events.py",
                    "--store",
                    str(store_path),
                    "validate-store",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )

            self.assertIn('"event_id": "cli-goal:goal"', start.stdout)
            self.assertIn('"event_id": "cli-goal:evidence:manifest"', evidence.stdout)
            self.assertIn("aria-linkage-events-ok (3 events)", validate.stdout)


if __name__ == "__main__":
    unittest.main()
