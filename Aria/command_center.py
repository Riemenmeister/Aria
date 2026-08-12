"""Local command center for the Aria PC status and communication workflow."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATUS_PATH = ROOT / "integrations" / "status.json"
DEFAULT_AUDIT_PATH = ROOT / "reports" / "goal_completion_audit.json"
DEFAULT_EVENTS_PATH = ROOT / "reports" / "aria_linkage_events.jsonl"

PROVED_COMPLETIONS = {"proved"}
READY_STATUSES = {
    "complete",
    "external_synced_airtable",
    "external_synced_notion",
    "external_drafted_slack",
    "external_generated_heygen",
    "production_deployed_sites",
    "production_report_published",
    "waived_by_user_decision",
}


@dataclass(frozen=True)
class CommandCenterItem:
    """One service or local gate shown in the command center."""

    name: str
    status: str
    completion: str
    next_action: str
    evidence: tuple[str, ...]
    priority: int

    @property
    def is_done(self) -> bool:
        return self.completion in PROVED_COMPLETIONS or self.status in READY_STATUSES


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> tuple[dict[str, Any], ...]:
    if not path.exists():
        return ()
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            events.append(json.loads(stripped))
    return tuple(events)


def _status_by_name(status_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item["name"]): item for item in status_data.get("integrations", [])}


def _audit_by_name(audit_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item["name"]): item for item in audit_data.get("results", [])}


def _priority_for(name: str, status: str, completion: str) -> int:
    if completion not in PROVED_COMPLETIONS and status not in READY_STATUSES:
        return 10
    if name in {"slack", "notion", "airtable"}:
        return 30
    return 50


def build_snapshot(
    *,
    status_path: Path = DEFAULT_STATUS_PATH,
    audit_path: Path = DEFAULT_AUDIT_PATH,
    events_path: Path = DEFAULT_EVENTS_PATH,
) -> dict[str, Any]:
    """Build a read-only command-center snapshot from local evidence files."""

    status_data = _read_json(status_path)
    audit_data = _read_json(audit_path)
    events = _read_jsonl(events_path)
    statuses = _status_by_name(status_data)
    audits = _audit_by_name(audit_data)

    names = tuple(dict.fromkeys([*statuses.keys(), *audits.keys()]))
    items: list[CommandCenterItem] = []
    for name in names:
        status_item = statuses.get(name, {})
        audit_item = audits.get(name, {})
        status = str(audit_item.get("status") or status_item.get("status") or "unknown")
        completion = str(audit_item.get("completion") or "unverified")
        next_action = str(
            audit_item.get("next_verification")
            or status_item.get("next_verification")
            or "Record evidence or define the next verification."
        )
        evidence = tuple(
            str(item)
            for item in (
                audit_item.get("evidence")
                or status_item.get("evidence")
                or ()
            )
        )
        items.append(
            CommandCenterItem(
                name=name,
                status=status,
                completion=completion,
                next_action=next_action,
                evidence=evidence,
                priority=_priority_for(name, status, completion),
            )
        )

    items.sort(key=lambda item: (item.priority, item.name))
    open_items = [item for item in items if not item.is_done]
    ready_items = [item for item in items if item.is_done]
    last_event = events[-1] if events else None

    return {
        "project": status_data.get("project", audit_data.get("project", "Aria PC")),
        "updated": status_data.get("updated", audit_data.get("checked_at")),
        "goal_status": audit_data.get("status", "unknown"),
        "open_count": len(open_items),
        "ready_count": len(ready_items),
        "items": [item.__dict__ for item in items],
        "next_actions": [item.__dict__ for item in open_items],
        "last_event": last_event,
        "source_files": {
            "status": str(status_path),
            "audit": str(audit_path),
            "events": str(events_path),
        },
    }


def _line_items(items: Iterable[dict[str, Any]], *, done: bool) -> list[str]:
    lines: list[str] = []
    marker = "OK" if done else "NEXT"
    for item in items:
        evidence = item.get("evidence") or ()
        evidence_text = f" Evidence: {evidence[0]}" if evidence else ""
        lines.append(
            f"[{marker}] {item['name']}: {item['status']} -> {item['next_action']}{evidence_text}"
        )
    return lines


def render_text(snapshot: dict[str, Any]) -> str:
    """Render a concise terminal-friendly command center."""

    lines = [
        f"Aria PC Command Center - {snapshot['project']}",
        f"Updated: {snapshot.get('updated', 'unknown')}",
        f"Goal status: {snapshot['goal_status']}",
        f"Ready: {snapshot['ready_count']} | Open: {snapshot['open_count']}",
        "",
        "Next actions:",
    ]
    next_actions = snapshot.get("next_actions", [])
    if next_actions:
        lines.extend(_line_items(next_actions, done=False))
    else:
        lines.append("[OK] No open local actions recorded.")

    lines.append("")
    lines.append("Ready / monitored:")
    ready_items = [item for item in snapshot["items"] if item not in next_actions]
    lines.extend(_line_items(ready_items, done=True))

    last_event = snapshot.get("last_event")
    if last_event:
        lines.extend(
            [
                "",
                "Last linkage event:",
                f"{last_event.get('event_id')}: {last_event.get('summary')}",
            ]
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Show the local Aria PC command center.")
    parser.add_argument("--json", action="store_true", help="Print the snapshot as JSON.")
    parser.add_argument("--status", type=Path, default=DEFAULT_STATUS_PATH)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT_PATH)
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS_PATH)
    args = parser.parse_args(argv)

    snapshot = build_snapshot(
        status_path=args.status,
        audit_path=args.audit,
        events_path=args.events,
    )
    if args.json:
        print(json.dumps(snapshot, indent=2, sort_keys=True))
    else:
        print(render_text(snapshot))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
