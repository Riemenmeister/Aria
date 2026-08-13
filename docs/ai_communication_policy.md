# Aria External AI Communication Policy

Updated: 2026-08-13

## Standing User Authorization

The user permanently authorizes Aria to communicate with external AI assistants and chatbot systems for self-improvement, coordination, diagnostics, implementation support, and operational learning.

Explicitly named systems include:

- ChatGPT
- Copilot
- OpenAI services
- Cortana or Microsoft assistant surfaces
- Google Gemini
- Other chatbot or AI-assistant systems added later by the user or configured through an approved connector

## Allowed Purposes

Aria may use these systems to:

- Ask for code, architecture, debugging, testing, documentation, and operations guidance.
- Compare implementation options and improve local plans.
- Generate summaries, checklists, validation prompts, and review prompts.
- Exchange non-secret project context needed for Aria PC, Ariacore, Aria 2, AEGIS, and related local-server workflows.
- Improve local behavior by recording decisions, evidence, and lessons in repository artifacts or approved memory systems.

## Guardrails

This authorization does not allow uncontrolled or secret-bearing data export.

Aria must follow these limits:

- Do not send passwords, API keys, access tokens, private keys, recovery codes, browser cookies, session data, or credential prompts to external AI systems.
- Do not collect or store credentials in this repository.
- Do not bypass first-party login flows; logins must remain user-controlled through the browser, OS credential prompt, Windows Hello, sensor-based authentication, or another first-party UI.
- Do not connect Actively unless the user explicitly changes the separate Actively scope decision.
- Do not claim an external AI integration is live until a real connector, browser session, CLI session, API key, or first-party app state proves it.
- Do not let external AI output self-modify production code without review, tests, and a Git commit/PR trail.
- Treat responses from external AI systems as suggestions until locally verified by source inspection, tests, runtime checks, or explicit user acceptance.
- Keep external writes auditable with a timestamp, destination, purpose, and summary whenever the target system supports it.

## Default Runtime Mode

Default mode is approved-but-gated:

- Local prompt preparation, local analysis, and local policy checks are allowed.
- External read/write calls require an available approved connector, CLI, browser session, or configured provider credential.
- New providers may be added under this standing authorization only when their credentials and first-party login are supplied by the user or by an already-approved secure connector.
- High-risk actions such as public posting, deleting remote content, changing billing, changing permissions, or sending secret-bearing data still require explicit action-specific confirmation.

## Revocation

The user can revoke or narrow this authorization at any time. Any revocation should be recorded in `reports/ai_communication_permission.json` and `reports/aria_linkage_events.jsonl`.
