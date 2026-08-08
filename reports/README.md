# Reports

`aria_pc_status.html` is a self-contained local status report generated from `integrations/status.json`.

Regenerate it with:

```powershell
py tools\render_status_report.py
```

Verify it is current with:

```powershell
py tools\render_status_report.py --check
```

Additional report:

- `blocker_resolution_handoff.json` records the exact remaining Circleback and Close resolution inputs and acceptance criteria.
