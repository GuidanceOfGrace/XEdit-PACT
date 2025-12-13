## ADDED Requirements

### Requirement: Configuration File Structure
The system SHALL use YAML configuration files with `AutoQAC_*` prefixes for all configuration keys. The system SHALL load configuration from the following files:
- `AutoQAC Data/AutoQAC Main.yaml`: Game configurations, skip lists, default settings
- `AutoQAC Data/AutoQAC Config.yaml`: User-specific settings and paths
- `AutoQAC Data/AutoQAC Ignore.yaml`: User-defined plugin ignore lists

#### Scenario: Load configuration with new naming scheme
- **WHEN** the application starts
- **THEN** configuration SHALL be loaded from `AutoQAC Data/AutoQAC Main.yaml`
- **AND** user settings SHALL be loaded from `AutoQAC Data/AutoQAC Config.yaml`
- **AND** user ignore lists SHALL be loaded from `AutoQAC Data/AutoQAC Ignore.yaml`

#### Scenario: Settings key structure
- **WHEN** reading application settings
- **THEN** settings SHALL be accessed under the `AutoQAC_Settings` key
- **AND** the following settings SHALL be available:
  - `AutoQAC_Settings.Journal_Expiration` (default: 7)
  - `AutoQAC_Settings.Cleaning_Timeout` (default: 300)
  - `AutoQAC_Settings.CPU_Threshold` (default: 5)
  - `AutoQAC_Settings.MO2Mode` (default: false)
  - `AutoQAC_Settings.Max_Concurrent_Subprocesses` (default: 3)

### Requirement: Legacy Configuration Migration
The system SHALL detect and migrate legacy PACT configuration files to the new AutoQAC naming scheme.

#### Scenario: Migrate legacy PACT Ignore file
- **WHEN** the application starts
- **AND** `PACT Ignore.yaml` exists in the application directory
- **AND** `AutoQAC Data/AutoQAC Ignore.yaml` does not exist
- **THEN** the system SHALL copy contents from `PACT Ignore.yaml` to `AutoQAC Data/AutoQAC Ignore.yaml`
- **AND** a deprecation warning SHALL be logged

#### Scenario: Legacy PACT Settings migration
- **WHEN** the application starts
- **AND** `PACT Settings.yaml` exists in the application directory
- **THEN** a deprecation warning SHALL be logged indicating the file is no longer used
- **AND** users SHALL be directed to configure settings via `AutoQAC Data/AutoQAC Config.yaml`