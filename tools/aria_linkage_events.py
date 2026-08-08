"""Command line interface for Aria AI linkage events."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from Aria.ai_linkage import AriaAiLinkage, LinkageEvent, LinkageEventStore


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

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())

