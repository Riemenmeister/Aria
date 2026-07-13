# Exports

These files are generated from `integrations/status.json` for manual or connector-assisted handoff into external services.

- `airtable_integration_status.csv`: import-ready table rows for Airtable.
- `notion_aria_pc_status.md`: page-ready status documentation for Notion.
- `slack_status_update.md`: concise update text for Slack.
- `heygen_status_video_brief.md`: presenter-video brief and script for HeyGen.
- `circleback_meeting_brief.md`: closeout meeting agenda and capture checklist for Circleback.

Regenerate all exports with:

```powershell
py tools\export_integration_status.py
```

Verify they are current with:

```powershell
py tools\export_integration_status.py --check
```
