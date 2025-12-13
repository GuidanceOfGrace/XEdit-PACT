## 1. Documentation Updates
- [x] 1.1 Update `README.md` - rename XEdit-PACT references to AutoQAC
- [x] 1.2 Update `AGENTS.md` - rename PACT config file references
- [x] 1.3 Update `CLAUDE.md` - rename PACT config file references
- [x] 1.4 Update `GEMINI.md` - rename XEdit-PACT and PACT references
- [x] 1.5 Update `openspec/project.md` - rename PACT references

## 2. Configuration Updates
- [x] 2.1 Update `AutoQAC Data/AutoQAC Main.yaml` - rename all PACT_* keys to AutoQAC_*
- [x] 2.2 Create `AutoQAC Data/AutoQAC Ignore.yaml` template file
- [x] 2.3 Update `AutoQACLib/config_manager.py` - update config key references from PACT_Settings to AutoQAC_Settings

## 3. Backward Compatibility
- [x] 3.1 Add migration logic to detect and migrate legacy PACT Ignore.yaml to new location
- [x] 3.2 Add deprecation warning for old file locations (PACT Settings.yaml, PACT Data/)

## 4. Testing
- [x] 4.1 Verify application starts with new configuration keys
- [x] 4.2 Update any tests that reference PACT configuration keys (none found)