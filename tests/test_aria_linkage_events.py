from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from Aria.ai_linkage import AriaAiLinkage, LinkageEvent, LinkageEventStore


class AriaAiLinkageEventStoreTest(unittest.TestCase):
    def test_store_appends_and_reads_valid_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LinkageEventStore(Path(tmpdir) / "events.jsonl", AriaAiLinkage())
            event = LinkageEvent.create(
                event_id="store-test",
                source="aria",
                type="evidence",
                summary="Persist an evidence event.",
                evidence=("integrations/aria_ai_linkage.json",),
            )

            written = store.append(event)
            events = store.read_all()

            self.assertEqual(written["event_id"], "store-test")
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["source"], "aria")
            self.assertEqual(store.health_snapshot()["event_count"], 1)

    def test_store_rejects_invalid_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = LinkageEventStore(Path(tmpdir) / "events.jsonl", AriaAiLinkage())
            event = LinkageEvent.create(
                event_id="bad-source",
                source="outside",
                type="evidence",
                summary="This should not be persisted.",
            )

            with self.assertRaises(ValueError):
                store.append(event)

    def test_cli_appends_and_validates_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "events.jsonl"
            append = subprocess.run(
                [
                    sys.executable,
                    "tools/aria_linkage_events.py",
                    "--store",
                    str(store_path),
                    "append-event",
                    "--event-id",
                    "cli-test",
                    "--source",
                    "aria2",
                    "--type",
                    "action",
                    "--summary",
                    "CLI appends a validated event.",
                    "--payload",
                    '{"step":"persist"}',
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

            self.assertIn('"event_id": "cli-test"', append.stdout)
            self.assertIn("aria-linkage-events-ok (1 events)", validate.stdout)

    def test_default_event_store_records_current_external_blockers(self) -> None:
        store = LinkageEventStore(ROOT / "reports" / "aria_linkage_events.jsonl", AriaAiLinkage())
        events = store.read_all()
        blocker_ids = {event["payload"]["blocker_id"] for event in events if event["type"] == "blocker"}
        decision_ids = {event["payload"]["decision_id"] for event in events if event["type"] == "decision"}

        self.assertEqual(blocker_ids, {"circleback", "close"})
        self.assertEqual(decision_ids, {"actively-not-connected", "external-ai-communication-standing-authorization"})
        self.assertEqual(len(events), 4)


if __name__ == "__main__":
    unittest.main()

