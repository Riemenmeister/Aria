# AEGIS

AEGIS is the mission and safety architecture layer in the Aria AI linkage.

Within this repository it is represented as a contract-first subsystem:

- it defines mission boundaries before autonomous behavior is enabled
- it keeps cognitive planning separate from real-time hardware control
- it requires explicit approval for external writes and physical-world actions
- it provides evidence for the Aria, AriaCore, Aria 2, and AEGIS linkage path

The first implementation contract is documented in
`docs/aria_ai_linkage_implementation.md` and referenced by
`integrations/aria_ai_linkage.json`.
