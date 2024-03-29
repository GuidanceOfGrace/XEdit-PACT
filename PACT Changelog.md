===========================================================================
# CHANGELOG #

1.70
- Increased internal timer values to prevent rare cases where PACT would skip all plugins.
- Additional optimizations to prevent more errors and ensure successful plugin cleaning.
- PACT will now disable most buttons during plugin cleaning to prevent rogue input.
- PACT will now wait for xedit to close before you can start cleaning again.
- You can now adjust *Journal Expiration* in the GUI or *PACT Settings.ini*
- You can now adjust *Cleaning Timeout* in the GUI or *PACT Settings.ini*
- Added support for *FO4VREdit.exe* and *TES5VREdit.exe*.
- Removed specific name requirements for MO2 executable.
- Dark mode / window style is now enabled by default.

1.60
- Several bugfixes and optimizations thanks to [evildarkarchon] on GitHub.
- PACT should now skip disabled plugins or if xedit CPU usage is 0% for too long.
- PACT should now automatically skip ghosted plugins (.ghost in plugin name).
- Fixed *Fallout New Vegas* support and added support for *xFOEdit.exe*.
- Streamlined most of the settings checks to prevent some issues.
- Added some additional error checks for specific situations.

1.55
- General code optimization and bug fixing, this should also resolve *UnboundLocalError*
- Fully switched cleaning process to internal commands instead of creating batch files.
- Added plugins from *FO4 | Previs Repair Pack (PRP)* to the internal ignore list.
- Added plugins from *FO4 | Sim Settlements 2 (SS2)* to the internal ignore list.
- Added support for *Fallout New Vegas*

1.50
- HOTFIX 1: I am slowly going insane | Attempt to fix [WinError 193] with some configurations.
- HOTFIX 2: Fixed wrong version, updated readme on how to hide PACT and XEDIT from the desktop.
- HOTFIX 3: Another attempt to fix [WinError 193] and quality of life improvements during batch creation.
- Removed some test messages from terminal output.

1.40
- Fixed PACT failing to process plugins with special & space characters.
- Added support for processing and cleaning plugins with *xEdit.exe*

1.30
- Changed how plugin list is read from *loadorder.txt* to fix 0 plugins found.
- Improved a few file checks to correctly trigger errors and prevent crashes.
- Changed the MO2 instance checking method so it only checks when necessary.

1.25
- Removed underscore character from *PACT Ignore.txt* to match the naming scheme.
- You can now set the Load Order File to either *loadorder.txt* or *plugins.txt*
- PACT will now log processed plugins & some other data to *PACT Journal.log*
- PACT will now stop and warn you if MO2 is already running before cleaning.
- PACT should now warn you if it gets interrupted by your antivirus.
- PACT should now support a wider range of plugin names.
- Updated PACT Readme with some more details.

1.15
- FO4 Nexus Release

1.11
- Initial Stable Release