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
