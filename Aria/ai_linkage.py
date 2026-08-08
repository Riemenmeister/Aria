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
