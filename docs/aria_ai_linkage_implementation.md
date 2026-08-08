# Aria AI Linkage Implementation

Date: 2026-08-08
Branch: codex/aria-ai-linkage

## Goal

Connect Aria, AriaCore, Aria 2, and AEGIS into one reviewable AI system path without
pretending that every downstream capability is already complete.

The implementation is split into four layers:

1. Aria is the local operator interface and memory surface.
2. AriaCore is the runtime and event backbone.
3. Aria 2 is the next cognitive orchestration layer.
4. AEGIS is the mission and safety architecture layer.

This document defines the integration contract that lets those layers become one
functional AI system incrementally, with clear evidence gates.

## System Contract

Each layer must expose five capabilities before it can be treated as fully linked:

- identity: stable name, version, and role in the system
- health: machine-readable readiness and error state
- events: inputs, outputs, and audit events
- memory: what the layer can read, write, and forget
- safety: explicit limits for autonomous action

The manifest in `integrations/aria_ai_linkage.json` is the first machine-readable
version of that contract.

## Layer Responsibilities

### Aria

Aria owns the human-facing workspace:

- receives operator goals and status requests
- stores handoff notes, reports, and local evidence
- presents the current completion state
- refuses to mark completion when external proof is missing

### AriaCore

AriaCore owns the runtime backbone:

- event bus
- listener services
- knowledge bridge
- local tests and smoke checks
- GitHub CI integration once pushed to the remote repository

### Aria 2

Aria 2 owns the reasoning and orchestration upgrade path:

- decomposes goals into auditable work packets
- coordinates tools and connectors
- tracks confidence and uncertainty
- prepares next actions when blockers are external

### AEGIS

AEGIS owns mission boundaries and safety rules:

- separates cognitive planning from real-time control
- records mission assumptions
- requires explicit approval for external writes and physical-world actions
- keeps drone or hardware stabilization outside the language-model loop

## Event Spine

The shared event spine should use append-only event records. The minimum event shape is:

```json
{
  "event_id": "string",
  "timestamp": "2026-08-08T00:00:00Z",
  "source": "aria|ariacore|aria2|aegis",
  "type": "goal|status|action|evidence|blocker|approval",
  "summary": "short human-readable text",
  "payload": {},
  "evidence": []
}
```

## Safety Gates

The system is not fully functional until all of these gates have proof:

- local runtime tests pass
- external GitHub branch and PR exist
- CI runs for the PR and has a recorded result
- Airtable and Notion status surfaces are current
- Actively, Circleback, Close, Slack, HeyGen, and deployment evidence are either
  complete or explicitly marked as optional
- AEGIS has a documented split between planning and real-time control

## Current PR Scope

This PR does not claim to finish the whole AI system. It creates the first
reviewable integration surface:

- a human-readable implementation plan
- a machine-readable linkage manifest
- a GitHub reconciliation receipt

The next implementation step is to add a small validator that checks the manifest
and fails CI if required layer contracts are missing.

## Persistent Event Store

`Aria.ai_linkage` now includes `LinkageEventStore`, an append-only JSONL store for
validated linkage events. The companion CLI in `tools/aria_linkage_events.py` can:

- print linkage and store health
- append validated events
- list validated events
- validate the full event store

Default event store path:

```text
reports/aria_linkage_events.jsonl
```

Example:

```powershell
py tools\aria_linkage_events.py append-event --event-id first-linkage-event --source aria2 --type action --summary "Persist the first linkage event." --payload '{"step":"persist"}' --evidence integrations/aria_ai_linkage.json
py tools\aria_linkage_events.py validate-store
```

## Goal Orchestration

`LinkageOrchestrator` builds on the event store and creates deterministic event
sequences for higher-level work:

- `start-goal` records a `goal` event and a first `action` planning event
- `record-evidence` links proof back to a goal
- `record-blocker` records a blocker and the required next action

Example:

```powershell
py tools\aria_linkage_events.py start-goal --goal-id aria-pc-linkage --summary "Connect Aria, AriaCore, Aria 2, and AEGIS." --evidence integrations/aria_ai_linkage.json
py tools\aria_linkage_events.py record-evidence --goal-id aria-pc-linkage --evidence-id ci --summary "CI passed." --evidence https://github.com/Riemenmeister/Aria/actions
py tools\aria_linkage_events.py record-blocker --goal-id aria-pc-linkage --blocker-id approval --summary "Merge requires explicit approval." --next-action "Ask for approval before merging."
```

## Audit Blocker Events

The goal audit can be converted into persisted blocker events so the remaining
external gates are visible through the same append-only linkage event contract.
This is useful after a connector recheck: proved markers are skipped, and every
incomplete marker becomes a validated `blocker` event with its evidence and next
action.

Example:

```powershell
py tools\aria_linkage_events.py record-audit-blockers --goal-id aria-pc-completion --audit reports\goal_completion_audit.json
py tools\aria_linkage_events.py validate-store
```

For the 2026-08-08 connector recheck this records the remaining Actively,
Circleback, and Close blockers while preserving their receipt evidence.
