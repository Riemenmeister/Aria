from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from Aria.ai_linkage import AriaAiLinkage, LinkageEvent


class AriaAiLinkageRuntimeTest(unittest.TestCase):
    def test_health_snapshot_contains_all_layers(self) -> None:
        linkage = AriaAiLinkage()
        snapshot = linkage.health_snapshot()

        self.assertEqual(snapshot["project"], "Aria PC")
        self.assertEqual(
            set(snapshot["layers"]),
            {"aria", "ariacore", "aria2", "aegis"},
        )
        self.assertEqual(
            snapshot["layers"]["ariacore"]["role"],
            "runtime_and_event_backbone",
        )

    def test_valid_event_matches_manifest_contract(self) -> None:
        linkage = AriaAiLinkage()
        event = LinkageEvent.create(
            event_id="test-event",
            source="aria2",
            type="goal",
            summary="Route the goal into the four-layer linkage contract.",
            payload={"goal": "link Aria, AriaCore, Aria 2, and AEGIS"},
            evidence=("integrations/aria_ai_linkage.json",),
        )

        self.assertEqual(linkage.validate_event(event), [])

    def test_invalid_event_reports_errors(self) -> None:
        linkage = AriaAiLinkage()

        errors = linkage.validate_event(
            {
                "event_id": "bad-event",
                "timestamp": "2026-08-08T00:00:00Z",
                "source": "unknown",
                "type": "unsupported",
                "summary": "",
                "payload": {},
                "evidence": [],
            }
        )

        self.assertIn("unknown event source: unknown", errors)
        self.assertIn("unknown event type: unsupported", errors)
        self.assertIn("event summary must not be empty", errors)


if __name__ == "__main__":
    unittest.main()
