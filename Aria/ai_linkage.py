"""AI linkage primitives for Aria, AriaCore, Aria 2, and AEGIS."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "integrations" / "aria_ai_linkage.json"
READY_STATUSES = {"ready", "partially_ready", "contract_defined"}

LINKAGE_MANIFEST_EVIDENCE = "integrations/aria_ai_linkage.json"


def _with_linkage_manifest_evidence(evidence: tuple[str, ...] | None) -> tuple[str, ...]:
    items = list(evidence or ())
    if LINKAGE_MANIFEST_EVIDENCE not in items:
        items.append(LINKAGE_MANIFEST_EVIDENCE)
    return tuple(items)


@dataclass(frozen=True)
class LinkageLayer:
    """One layer in the Aria AI linkage contract."""

    id: str
    name: str
    role: str
    status: str
    required_capabilities: tuple[str, ...]
    evidence: tuple[str, ...]
    next_verification: str

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "LinkageLayer":
        return cls(
            id=str(value["id"]),
            name=str(value["name"]),
            role=str(value["role"]),
            status=str(value["status"]),
            required_capabilities=tuple(value.get("required_capabilities", [])),
            evidence=tuple(value.get("evidence", [])),
            next_verification=str(value["next_verification"]),
        )

    @property
    def is_operational_seed(self) -> bool:
        return self.status in READY_STATUSES


@dataclass(frozen=True)
class LinkageEvent:
    """Append-only event shape shared by all Aria AI layers."""

    event_id: str
    timestamp: str
    source: str
    type: str
    summary: str
    payload: dict[str, Any]
    evidence: tuple[str, ...]

    @classmethod
    def create(
        cls,
        *,
        event_id: str,
        source: str,
        type: str,
        summary: str,
        payload: dict[str, Any] | None = None,
        evidence: tuple[str, ...] | None = None,
    ) -> "LinkageEvent":
        timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        return cls(
            event_id=event_id,
            timestamp=timestamp,
            source=source,
            type=type,
            summary=summary,
            payload=payload or {},
            evidence=evidence or (),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "source": self.source,
            "type": self.type,
            "summary": self.summary,
            "payload": self.payload,
            "evidence": list(self.evidence),
        }


class AriaAiLinkage:
    """Read and evaluate the Aria AI linkage manifest."""

    def __init__(self, manifest_path: Path | None = None) -> None:
        self.manifest_path = manifest_path or DEFAULT_MANIFEST
        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.layers = tuple(
            LinkageLayer.from_mapping(layer) for layer in self.manifest["layers"]
        )

    def layer_ids(self) -> tuple[str, ...]:
        return tuple(layer.id for layer in self.layers)

    def layer(self, layer_id: str) -> LinkageLayer:
        for layer in self.layers:
            if layer.id == layer_id:
                return layer
        raise KeyError(layer_id)

    def health_snapshot(self) -> dict[str, Any]:
        layers = {
            layer.id: {
                "name": layer.name,
                "role": layer.role,
                "status": layer.status,
                "operational_seed": layer.is_operational_seed,
                "next_verification": layer.next_verification,
            }
            for layer in self.layers
        }
        return {
            "project": self.manifest["project"],
            "linkage_version": self.manifest["linkage_version"],
            "layers": layers,
            "completion_gates": list(self.manifest.get("completion_gates", [])),
        }

    def validate_event(self, event: LinkageEvent | dict[str, Any]) -> list[str]:
        event_data = event.as_dict() if isinstance(event, LinkageEvent) else event
        contract = self.manifest["event_contract"]
        errors: list[str] = []

        for field in contract["required_fields"]:
            if field not in event_data:
                errors.append(f"missing event field: {field}")

        if event_data.get("source") not in contract["sources"]:
            errors.append(f"unknown event source: {event_data.get('source')}")

        if event_data.get("type") not in contract["types"]:
            errors.append(f"unknown event type: {event_data.get('type')}")

        if not event_data.get("summary"):
            errors.append("event summary must not be empty")

        return errors


class LinkageEventStore:
    """Append-only JSONL store for validated linkage events."""

    def __init__(self, path: Path, linkage: AriaAiLinkage | None = None) -> None:
        self.path = path
        self.linkage = linkage or AriaAiLinkage()

    def append(self, event: LinkageEvent) -> dict[str, Any]:
        errors = self.linkage.validate_event(event)
        if errors:
            raise ValueError("; ".join(errors))

        self.path.parent.mkdir(parents=True, exist_ok=True)
        event_data = event.as_dict()
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event_data, sort_keys=True) + "\n")
        return event_data

    def read_all(self) -> tuple[dict[str, Any], ...]:
        if not self.path.exists():
            return ()

        events: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    event = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"invalid JSONL event at {self.path}:{line_number}"
                    ) from exc
                errors = self.linkage.validate_event(event)
                if errors:
                    raise ValueError(
                        f"invalid event at {self.path}:{line_number}: "
                        f"{'; '.join(errors)}"
                    )
                events.append(event)
        return tuple(events)

    def health_snapshot(self) -> dict[str, Any]:
        events = self.read_all()
        return {
            "path": str(self.path),
            "event_count": len(events),
            "last_event": events[-1] if events else None,
        }


class LinkageOrchestrator:
    """Create persisted linkage event sequences for goals and follow-up work."""

    def __init__(self, store: LinkageEventStore) -> None:
        self.store = store

    def start_goal(
        self,
        *,
        goal_id: str,
        summary: str,
        owner: str = "aria2",
        evidence: tuple[str, ...] | None = None,
    ) -> tuple[dict[str, Any], ...]:
        goal_evidence = tuple(evidence or ())
        plan_evidence = _with_linkage_manifest_evidence(goal_evidence)
        goal_event = LinkageEvent.create(
            event_id=f"{goal_id}:goal",
            source=owner,
            type="goal",
            summary=summary,
            payload={"goal_id": goal_id, "phase": "started"},
            evidence=goal_evidence,
        )
        action_event = LinkageEvent.create(
            event_id=f"{goal_id}:action:plan",
            source="ariacore",
            type="action",
            summary=f"Plan execution path for {goal_id}.",
            payload={
                "goal_id": goal_id,
                "action": "plan",
                "layers": list(self.store.linkage.layer_ids()),
            },
            evidence=plan_evidence,
        )
        return (self.store.append(goal_event), self.store.append(action_event))

    def record_evidence(
        self,
        *,
        goal_id: str,
        evidence_id: str,
        summary: str,
        evidence: tuple[str, ...],
        source: str = "aria",
    ) -> dict[str, Any]:
        event = LinkageEvent.create(
            event_id=f"{goal_id}:evidence:{evidence_id}",
            source=source,
            type="evidence",
            summary=summary,
            payload={"goal_id": goal_id, "evidence_id": evidence_id},
            evidence=evidence,
        )
        return self.store.append(event)

    def record_blocker(
        self,
        *,
        goal_id: str,
        blocker_id: str,
        summary: str,
        next_action: str,
        source: str = "aegis",
    ) -> dict[str, Any]:
        event = LinkageEvent.create(
            event_id=f"{goal_id}:blocker:{blocker_id}",
            source=source,
            type="blocker",
            summary=summary,
            payload={"goal_id": goal_id, "blocker_id": blocker_id, "next_action": next_action},
            evidence=(),
        )
        return self.store.append(event)
