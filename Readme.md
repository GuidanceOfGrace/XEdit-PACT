===========================================================================
# LINKS #

Mod Organizer 2 - https://github.com/ModOrganizer2/modorganizer/releases

SSEEdit - https://www.nexusmods.com/skyrimspecialedition/mods/164?tab=files

FO4Edit - https://www.nexusmods.com/fallout4/mods/2737/?tab=files

FO4 PACT - https://www.nexusmods.com/fallout4/mods/69413

===========================================================================
# BEFORE YOU ASK #

> Is it safe to clean plugins?

Short answer? Yes. Long answer?
Yeeeeeeeeeeeeeeeeeeeeeeee... It's fine, though PACT will skip cleaning DLCs.

Sometimes, a mod author will open a plugin record simply to investigate a field or property and not change anything.
But the CK will still flag that record as edited, even if it remains identical in every way. These are *Identical To Master Records (ITMs)*
They will frequently overwrite valid changes made by other mods and should be cleaned whenever possible. Intentional ITMs are next to nonexistent.

*Undisabled Records (UDRs)* are potentially more harmful. Mod authors will sometimes delete records they no longer wish to use.
Depending on what record has been deleted, other mods may try to reference it. When they can't find this record,
this can lead to broken quests to game crashes. These records need to be restored and properly disabled.

After a discussion with many veteran game modders, it’s advised that you do not clean any ESM plugins from the official DLC content (excluding any Creation Club content).
Even if you already cleaned them, there shouldn’t be any problems, though here have been reports that cleaning them can cause weird NPC pathing and dialogue behavior.
Exact reason is unknown, could be due to certain record types being treated as false positives or simply because XEdit doesn't have full record information.

*If you know any better, feel free to enlighten me.*

===========================================================================
# CONTENTS & FILES #

*PACT Readme.md* - The file that you're reading right now.

*Plugin Auto Cleaning Tool.exe* - Main exe / tool for batch cleaning plugins with XEdit (FO4Edit, SSEEdit).
Simply run it, then set up the required file paths and click on the big CLEAN PLUGINS button.

*PACT Settings.ini* - Configuration file for the main exe / tool where some parameters can be adjusted.
This file will be auto generated after running the exe for the first time. Remove it to reset settings.

*PACT Journal.log* - Logging file where PACT records all cleaned plugins and deleted navmeshes found during each session.

*PACT Ignore.txt* - Additional file where you can exclude plugins from cleaning, simply add one plugin name to each line.
This file will be auto generated after running the exe for the first time. Remove it to reset the ignore list.

===========================================================================
# HOW TO USE PACT (DO NOT RUN PACT THROUGH MO2, RUN THE EXE NORMALLY) #

After running the PACT EXE, you'll have to set up file paths for either *loadorder.txt* or *plugins.txt* and *XEdit.exe* executable.
All paths can be set directly through PACT EXE or by manually editing *PACT Settings.ini* after you run the PACT EXE at least once.

- *plugins.txt* file contains all currently active plugins for your game.
- *loadorder.txt* file contains all currently loaded plugins for your game.

Vortex -> Both *plugins.txt* and *loadorder.txt* can be found by selecting *Open* > *Game Application Data Folder* in Vortex.

MO2 -> Both *plugins.txt* and *loadorder.txt* can be found in your current MO2 profile folder. (MO2 / profiles / <profile name>)

- *XEdit.exe* file is the main program that does the actual cleaning, where the X part of the name is different depending on the game.
You should run your *XEdit* tool at least once before running *PACT* to ensure that both tools are properly configured before cleaning plugins.
Both FO4Edit (Fallout 4) and SSEEdit (Skyrim Special Edition) are supported and can be downloaded form their respective Nexus sites, links on top.

- *Mod Organizer 2* users also need to set the file path for the *ModOrganizer.exe* executable in PACT.
Vortex and other mod manager users don't need to do this, simply leave the MO2 EXE line blank.

# MAKE SURE THAT MO2 IS COMPLETELY CLOSED BEFORE YOU START CLEANING #

Once you set each file path, the buttons will turn green to indicate that the required files are correct, though you can still change them.
Once at least *loadorder.txt* file and *XEdit.exe* executable are set, the *START CLEANING* button will become colored blue and enabled.

Press *START CLEANING* to start the cleaning process, at which point *STOP CLEANING* button will be displayed instead until cleaning completes.
You can either press *STOP CLEANING* or exit the EXE to terminate the cleaning process. All other programs should also close shortly after.

While cleaning, PACT will show the number of plugins it found that need to be processed, then auto run the cleaning command for each one.

- If anything gets cleaned, PACT will tell you about it and any ITMs, URDs and other records it found after the whole cleaning session completes.
- If NOTHING gets cleaned, PACT will automatically add that plugin name to the ignore / exclude list, which is the *PACT Ignore.txt* file.

You can add or remove plugin names from *PACT Ignore.txt* if you wish to include or exclude certain plugins from cleaning.

PACT will add to *PACT Ignore.txt* file any plugin which is already clean (no ITMs or UDRs found to clean).
PACT will skip and add to ignore list any plugin that *XEdit* cannot load because of missing plugin requirements.
PACT will also skip other invalid plugins, though it will take *5 minutes* for the process to time out, unless you close *XEdit* manually.

===========================================================================
# KNOWN ISSUES #

PACT SHOULD ONLY CLEAN ONE ( 1 ) PLUGIN AT A TIME AND ONLY HAVE ONE ( 1 ) INSTANCE OF FO4EDIT OPEN
IF IT STARTS SPAMMING MULTIPLE XEDIT WINDOWS, IMMEDIATELY CLOSE PACT AND REPORT TO PACT NEXUS SITE

- If any plugin takes longer than *5 minutes* to clean, PACT will automatically close *XEdit* and skip that plugin.
  (You can close XEdit yourself to skip the wait. PACT will add that plugin name to the ignore list in PACT Ignore.txt)

- If you get a message in XEdit saying *Exactly one module must be selected for Quick Clean mode*, this means either:

1)	The plugin name is invalid. Simply press OK to close XEdit and PACT will continue cleaning other plugins.
2)	You didn't set the ModOrganizer.exe file path correctly and PACT is running in Vortex mode instead.

- If you get an error in XEdit saying *This application failed to start because no Qt Platform...*, this means either:

1)	You are trying to run PACT with MO2 already open. Don't do that. Close all MO2 instances and run PACT normally.
2)	Your MO2 might be missing some files. Make sure to reinstall latest 2.4 version of MO2 or try the portable version.

- If you get an error in PACT saying *The system cannot find the file specified...*, this means:

1) Your antivirus is most likely messing with PACT files. Try whitelisting the whole folder where PACT exe is located.

===========================================================================
# CHANGELOG #

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
