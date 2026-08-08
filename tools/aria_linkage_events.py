"""Command line interface for Aria AI linkage events."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from Aria.ai_linkage import (  # noqa: E402
    AriaAiLinkage,
    LinkageEvent,
    LinkageEventStore,
    LinkageOrchestrator,
)


DEFAULT_EVENT_STORE = Path("reports") / "aria_linkage_events.jsonl"


def _json_payload(value: str | None) -> dict:
    if not value:
        return {}
    loaded = json.loads(value)
    if not isinstance(loaded, dict):
        raise argparse.ArgumentTypeError("payload must decode to a JSON object")
    return loaded


def _print_json(value: dict | tuple[dict, ...]) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage Aria AI linkage events.")
    parser.add_argument(
        "--store",
        default=str(DEFAULT_EVENT_STORE),
        help="JSONL event store path. Defaults to reports/aria_linkage_events.jsonl.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("health", help="Print linkage and event-store health.")
    subparsers.add_parser("list-events", help="Print validated events from the store.")
    subparsers.add_parser("validate-store", help="Validate all stored events.")

    append = subparsers.add_parser("append-event", help="Append a validated event.")
    append.add_argument("--event-id", required=True)
    append.add_argument("--source", required=True)
    append.add_argument("--type", required=True)
    append.add_argument("--summary", required=True)
    append.add_argument("--payload", default="{}", help="JSON object payload.")
    append.add_argument(
        "--evidence",
        action="append",
        default=[],
        help="Evidence path or URL. Can be passed more than once.",
    )

    start_goal = subparsers.add_parser("start-goal", help="Persist a goal start sequence.")
    start_goal.add_argument("--goal-id", required=True)
    start_goal.add_argument("--summary", required=True)
    start_goal.add_argument("--owner", default="aria2")
    start_goal.add_argument(
        "--evidence",
        action="append",
        default=[],
        help="Evidence path or URL for the goal and generated planning event.",
    )

    record_evidence = subparsers.add_parser(
        "record-evidence", help="Persist a goal evidence event."
    )
    record_evidence.add_argument("--goal-id", required=True)
    record_evidence.add_argument("--evidence-id", required=True)
    record_evidence.add_argument("--summary", required=True)
    record_evidence.add_argument("--source", default="aria")
    record_evidence.add_argument("--evidence", action="append", required=True)

    record_blocker = subparsers.add_parser(
        "record-blocker", help="Persist a goal blocker event."
    )
    record_blocker.add_argument("--goal-id", required=True)
    record_blocker.add_argument("--blocker-id", required=True)
    record_blocker.add_argument("--summary", required=True)
    record_blocker.add_argument("--next-action", required=True)
    record_blocker.add_argument("--source", default="aegis")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    linkage = AriaAiLinkage()
    store = LinkageEventStore(Path(args.store), linkage)

    if args.command == "health":
        _print_json(
            {
                "linkage": linkage.health_snapshot(),
                "event_store": store.health_snapshot(),
            }
        )
        return 0

    if args.command == "list-events":
        _print_json(store.read_all())
        return 0

    if args.command == "validate-store":
        events = store.read_all()
        print(f"aria-linkage-events-ok ({len(events)} events)")
        return 0

    if args.command == "append-event":
        event = LinkageEvent.create(
            event_id=args.event_id,
            source=args.source,
            type=args.type,
            summary=args.summary,
            payload=_json_payload(args.payload),
            evidence=tuple(args.evidence),
        )
        _print_json(store.append(event))
        return 0

    orchestrator = LinkageOrchestrator(store)

    if args.command == "start-goal":
        _print_json(
            orchestrator.start_goal(
                goal_id=args.goal_id,
                summary=args.summary,
                owner=args.owner,
                evidence=tuple(args.evidence),
            )
        )
        return 0

    if args.command == "record-evidence":
        _print_json(
            orchestrator.record_evidence(
                goal_id=args.goal_id,
                evidence_id=args.evidence_id,
                summary=args.summary,
                source=args.source,
                evidence=tuple(args.evidence),
            )
        )
        return 0

    if args.command == "record-blocker":
        _print_json(
            orchestrator.record_blocker(
                goal_id=args.goal_id,
                blocker_id=args.blocker_id,
                summary=args.summary,
                next_action=args.next_action,
                source=args.source,
            )
        )
        return 0

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
