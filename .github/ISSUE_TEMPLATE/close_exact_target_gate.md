---
name: Resolve Close exact target or connector gate
about: Track the exact Close target or connector fix required to complete Aria PC externally
title: "Resolve Close exact target or connector gate"
labels: external-gate, close
assignees: ''
---

## Gate

Close remains blocked because connector searches return `INVALID_ARGUMENT`.

## Current Evidence

- Close connector tools are available.
- Natural-language search for `Aria` returned `INVALID_ARGUMENT`.
- Natural-language search for `Aria PC` returned `INVALID_ARGUMENT`.
- `activity_search` for meetings returned `INVALID_ARGUMENT`.
- `activity_search` for notes returned `INVALID_ARGUMENT`.
- Structured `activity_search` for meetings, calls, notes, and emails from `2026-07-01` to `2026-08-09` returned `INVALID_ARGUMENT`.

## Accepted Resolution Input

Provide one of:

- Exact Close lead ID.
- Exact Close contact ID.
- Exact Close opportunity ID.
- Confirmation that Close connector argument handling has been fixed and should be retried.

## Acceptance Criteria

- [ ] Exact target can be queried through a specific Close fetch/search path, or connector retry succeeds without `INVALID_ARGUMENT`.
- [ ] Result is recorded in `integrations/status.json` and `reports/close_receipt.json`.
- [ ] `py tools\audit_goal_completion.py --check` passes after the status update.

## Source Handoff

- `reports/blocker_resolution_handoff.json`
- `exports/blocker_resolution_handoff.md`
