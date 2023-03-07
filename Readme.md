=====================================================================================================
# LINKS #

Mod Organizer 2 - https://github.com/ModOrganizer2/modorganizer/releases

SSEEdit - https://www.nexusmods.com/skyrimspecialedition/mods/164?tab=files

FO4Edit - https://www.nexusmods.com/fallout4/mods/2737/?tab=files

FO4 PACT - https://www.nexusmods.com/fallout4/mods/69413

=====================================================================================================
# BEFORE YOU ASK #

> Is it safe to clean plugins?

- Short answer? Yes. Long answer?
Yeeeeeeeeeeeeeeeeeeeeeeee... As long as you're not cleaning official game DLC plugins, it's all good.

Sometimes, a mod author will open a plugin record simply to investigate a field or property and not change anything.
But the CK will still flag it as edited, even if the record remains identical in every way, hence the name *Identical To Master Records (ITMs)*
These records will frequently overwrite valid changes made by other mods and should be cleaned whenever possible. Intentional ITMs are next to nonexistent.

*Undisabled Records (UDRs)* are potentially more harmful. Mod authors will sometimes delete records they no longer wish to use.
Depending on what record has been deleted, other records may try to reference it. When they can't find this record,
many things can go wrong, from broken quests to crashes. These records need to be restored and disabled.

After a discussion with many veteran game modders, it’s advised that you do not clean any ESM plugins from the official DLC content (excluding any Creation Club content).
Even if you already cleaned them, there shouldn’t be any problems, though here have been reports that cleaning them can cause weird NPC pathing and dialogue behavior.
Exact reason is unknown, could be due to certain record types being treated as false positives or simply because XEdit doesn't have full record information.

If you know any better, feel free to enlighten me.

=====================================================================================================
# CONTENTS & FILES #

*PACT Readme.md* - The file that you're reading right now.

*Plugin Auto Cleaning Tool.exe* - Main exe / tool for batch cleaning plugins with XEdit (FO4Edit, SSEEdit).
Simply run it, then set up the required file paths and click on the big CLEAN PLUGINS button.

*PACT Start.ini* - Configuration file for the main exe / tool where some parameters can be adjusted.
This file will be auto generated after running the exe for the first time. Remove it to reset settings.

*PACT Ignore.txt* - Additional file where you can exclude plugins from cleaning, simply add one plugin name to each line.
This file will be auto generated after running the exe for the first time. Remove it to reset the ignore list.

=====================================================================================================
# HOW TO USE PACT #

After running the PACT EXE, you'll have to set up the required file paths for your *loadorder.txt* file and *XEdit.exe* executable.
All paths can be set directly through PACT EXE or by manually editing *PACT Start.ini* after you run the PACT EXE at least once.

- *loadorder.txt* file contains your currently active plugins from the game you wish to clean them.
Vortex -> loadorder.txt can be found by selecting Open > Game Application Data Folder. 
MO2 -> loadorder.txt can be found in your currently active MO2 profile folder.

- *XEdit.exe* file is the main program that does the actual cleaning, where the X part of the name is different depending on the game.
Both FO4Edit (Fallout 4) and SSEEdit (Skyrim Special Edition) can be downloaded form their respective Nexus sites, linked at the top.
Make sure to run your *XEdit* tool at least once before running *PACT* to ensure that both tools are properly configured before cleaning plugins.

- *Mod Organizer 2* users also need to set the file path for the *ModOrganizer.exe* executable.
MO2 requires that you run *XEdit.exe* through it to correctly detect game plugins.

Once you set each file path, the buttons will turn green to indicate that the required files are correct.
Once at least *loadorder.txt* file and *XEdit.exe* executable are set, the *CLEAN PLUGINS* button will become enabled.

Pressing on *CLEAN PLUGINS* will start the cleaning process, at which point *CLEAN PLUGINS* button will be disabled until it completes.
You can still exit / close PACT EXE which will terminate the cleaning process and all other programs should also close shortly after.

PACT will show the number of plugins it found that need to be processed, then auto run the cleaning command for each of them.

- If anything gets cleaned, PACT will tell you about it and any ITMs, URDs and other records it found after the whole cleaning session completes.
- If nothing gets cleaned, PACT will automatically add that plugin name to the ignore / exclude list, which is the *PACT Ignore.txt* file.

You can add or remove plugin names from *PACT Ignore.txt* if you wish to include or exclude certain plugins from cleaning.

PACT will add to *PACT Ignore.txt* file any plugin which is already clean (no ITMs or UDRs found to clean).
PACT will skip and add to ignore list any plugin that *XEdit* cannot load because of missing plugin requirements.
PACT will also skip other invalid plugins, though it will take *5 minutes* for the process to time out, unless you close *XEdit* manually.

=====================================================================================================
# KNOWN ISSUES #

- PACT currently cannot clean plugins that have "&" or "+" in their name. Other special characters likely also apply.
(For now, you can clean these plugins manually with QAC from the respective *XEdit* program you downloaded.)

- If any plugin takes longer than *5 minutes* to clean, PACT will automatically close *XEdit* and skip that plugin.

=====================================================================================================
# CHANGELOG #

1.11
* MAIN SCRIPT *
- Initial Nexus Release
