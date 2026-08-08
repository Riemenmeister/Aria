"""Validate the Aria AI linkage manifest."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "integrations" / "aria_ai_linkage.json"
REQUIRED_LAYERS = {"aria", "ariacore", "aria2", "aegis"}
REQUIRED_CAPABILITIES = {"identity", "health", "events", "memory", "safety"}
REQUIRED_EVENT_FIELDS = {
    "event_id",
    "timestamp",
    "source",
    "type",
    "summary",
    "payload",
    "evidence",
}


def load_manifest(path: Path = MANIFEST) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_manifest(manifest: dict) -> list[str]:
    errors: list[str] = []

    layers = manifest.get("layers")
    if not isinstance(layers, list):
        return ["layers must be a list"]

    layer_ids = {layer.get("id") for layer in layers if isinstance(layer, dict)}
    missing_layers = REQUIRED_LAYERS - layer_ids
    if missing_layers:
        errors.append(f"missing layers: {', '.join(sorted(missing_layers))}")

    for layer in layers:
        if not isinstance(layer, dict):
            errors.append("layer entries must be objects")
            continue

        layer_id = layer.get("id", "<unknown>")
        capabilities = set(layer.get("required_capabilities", []))
        missing_capabilities = REQUIRED_CAPABILITIES - capabilities
        if missing_capabilities:
            errors.append(
                f"{layer_id} missing capabilities: "
                f"{', '.join(sorted(missing_capabilities))}"
            )

        if not layer.get("role"):
            errors.append(f"{layer_id} missing role")
        if not layer.get("status"):
            errors.append(f"{layer_id} missing status")
        if not layer.get("next_verification"):
            errors.append(f"{layer_id} missing next_verification")
        for evidence in layer.get("evidence", []):
            evidence_path = ROOT / evidence
            if evidence and not evidence.startswith("http") and not evidence_path.exists():
                errors.append(f"{layer_id} evidence path missing: {evidence}")

    event_contract = manifest.get("event_contract", {})
    event_fields = set(event_contract.get("required_fields", []))
    missing_event_fields = REQUIRED_EVENT_FIELDS - event_fields
    if missing_event_fields:
        errors.append(
            "event contract missing fields: "
            f"{', '.join(sorted(missing_event_fields))}"
        )

    gates = manifest.get("completion_gates", [])
    if not gates:
        errors.append("completion_gates must not be empty")

    return errors


def main() -> int:
    errors = validate_manifest(load_manifest())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("aria-ai-linkage-ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

