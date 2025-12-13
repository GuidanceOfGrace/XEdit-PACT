# Change: Rename PACT to AutoQAC across the codebase

## Why
The project has been rebranded from "PACT" (Plugin Auto Cleaning Tool) to "AutoQAC" (Auto Quick Auto Clean). All references to the old name should be updated for consistency, and the configuration structure should reflect the new naming scheme.

## What Changes
- Rename all user-facing PACT references to AutoQAC in documentation
- Update YAML configuration keys from `PACT_*` to `AutoQAC_*` prefixes
- **BREAKING**: Move ignore file from `PACT Ignore.yaml` to `AutoQAC Data/AutoQAC Ignore.yaml`
- Update internal code references to use new configuration key names
- Remove legacy `PACT Settings.yaml` and `PACT Ignore.yaml` references from documentation
- Preserve historical PACT references in `AutoQAC Changelog.md` (changelog history should not be rewritten)

## Impact
- Affected documentation: `README.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `openspec/project.md`
- Affected code: `AutoQACLib/config_manager.py`
- Affected configs: `AutoQAC Data/AutoQAC Main.yaml`
- Migration required: Users with existing `PACT Ignore.yaml` will need to move their ignore lists to the new location