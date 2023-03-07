# PLUGIN AUTO CLEANING TOOL (PACT) | By Poet (The Sound Of Snow)
import configparser
import os
import sys
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
import requests
import psutil

'''
AUTHOR NOTES (POET):
- CURRENTLY SUPPORTED: SKYRIM | FALLOUT 4 | PLANNED: NEW VEGAS | OLD SKYRIM
- Module importing is disabled as this is only meant to be run through exe. Will also likely disable for Buffout CLAS.
- Comments marked as RESERVED in all scripts are intended for future updates or tests, do not edit / move / remove.
- (..., encoding="utf-8", errors="ignore") needs to go with every opened file because unicode errors are a bitch.
'''


# =================== PACT INI FILE ===================
def pact_ini_create():
    if not os.path.exists("PACT Start.ini"):  # INI FILE FOR AUTO-SCANNER
        INI_Settings = ["[MAIN]\n",
                        "# This file contains configuration settings for both PACT_Start.py and Plugin Auto Cleaning Tool.exe \n",
                        "# Set to true if you want PACT to check if you have the latest version of PACT. \n",
                        "Update Check = true\n\n",
                        "# Set to true if you want PACT to show extra stats about cleaned plugins in the command line window. \n",
                        "Stat Logging = true\n\n",
                        "# Set or copy-paste your loadorder file path below, PACT will use it to determine activated plugins. \n",
                        "# Vortex -> loadorder txt can be found by selecting Open > Game Application Data Folder. \n",
                        "# MO2 -> loadorder txt can be found in your currently active MO2 profile folder. \n",
                        "LoadOrder TXT = \n\n",
                        "# Set or copy-paste your XEdit (FO4Edit.exe, SSEEdit.exe) executable file path below. \n",
                        "# Make sure the XEdit version you set is for the actual plugins you wish to clean. \n",
                        "XEDIT EXE = \n\n",
                        "# Set or copy-paste your MO2 (ModOrganizer.exe) executable file path below. \n",
                        "# Only required if using Mod Organizer 2. Otherwise, leave this blank. \n",
                        "MO2 EXE = "]
        with open("PACT Start.ini", "w+", encoding="utf-8", errors="ignore") as INI_PACT:
            INI_PACT.writelines(INI_Settings)


pact_ini_create()
# Use optionxform = str to preserve INI formatting. | Set comment_prefixes to unused char to keep INI comments.
PACT_config = configparser.ConfigParser(allow_no_value=True, comment_prefixes="$")
PACT_config.optionxform = str  # type: ignore
PACT_config.read("PACT Start.ini")
PACT_Date = "060323"  # DDMMYY
PACT_Current = "PACT v1.11"
PACT_Updated = False


def pact_ini_update(section: str, value: str):  # Convenience function for checking & writing to INI.
    if isinstance(section, str) and isinstance(value, str):
        PACT_config["MAIN"][section] = value
    else:
        PACT_config["MAIN"][str(section)] = str(value)

    with open("PACT Start.ini", "w+", encoding="utf-8", errors="ignore") as INI_PACT:
        PACT_config.write(INI_PACT)


# =================== WARNING MESSAGES ==================
Warn_PACT_Update_Failed = """
❌  WARNING : PACT WAS UNABLE TO CHECK FOR UPDATES, BUT WILL CONTINUE RUNNING
    CHECK FOR ANY PACT UPDATES HERE: https://www.nexusmods.com/fallout4/mods/69413
"""
Warn_Outdated_PACT = """
❌  WARNING : YOUR PACT VERSION IS OUT OF DATE!
    Please download the latest version from here:
    https://www.nexusmods.com/fallout4/mods/69413
"""
Warn_Invalid_INI_Path = """
❌  WARNING : YOUR PACT INI PATHS ARE INCORRECT!
    Please run the PACT program or open Pact Start.ini
    And make sure that file / folder paths are correctly set!
"""
Warn_Invalid_INI_Setup = """
❌  WARNING : YOUR PACT INI SETUP IS INCORRECT!
    You likely set the wrong XEdit version for your game.
    Check your EXE or Pact Start.ini settings and try again.
"""


# =================== UPDATE FUNCTION ===================
def pact_update_check():
    global PACT_Current
    global PACT_Updated
    print("✔️ CHECKING FOR ANY NEW PLUGIN AUTO CLEANING TOOL UPDATES...")
    print("   (You can disable this check in the EXE or Pact Start.ini) \n")
    response = requests.get("https://api.github.com/repos/GuidanceOfGrace/XEdit-PACT/releases/latest")  # type: ignore
    PACT_Received = response.json()["name"]
    if PACT_Received == PACT_Current:
        PACT_Updated = True
        print("✔️ You have the latest version of PACT! \n")
    else:
        print(Warn_Outdated_PACT)
        print("===============================================================================")
    return PACT_Updated


def pact_update_run():
    if PACT_config.getboolean("MAIN", "Update Check") is True:
        try:
            pact_update_check()
            print("===============================================================================")
        except (OSError, requests.exceptions.RequestException):
            print(Warn_PACT_Update_Failed)
            print("===============================================================================")
    else:
        print("\n ❌ NOTICE: UPDATE CHECK IS DISABLED IN PACT INI SETTINGS \n")


# =================== TERMINAL OUTPUT START ====================
print("Hello World! | Plugin Auto Cleaning Tool (PACT) | Version", PACT_Current[-4:], "| For SSE & FO4")
print("MAKE SURE TO SET THE CORRECT LOAD ORDER AND XEDIT PATHS BEFORE CLEANING PLUGINS")
print("===============================================================================")


@dataclass
class Info:
    MO2_EXE: Path = field(default_factory=Path)
    XEdit_EXE: Path = field(default_factory=Path)
    XEdit_Path: Path = field(default_factory=Path)
    LoadOrder_TXT: Path = field(default_factory=Path)
    LoadOrder_Path: Path = field(default_factory=Path)


info = Info()
MO2Mode = False
''' # TEMPLATES | Only access INI just before needed to prevent missing file errors.
info.LoadOrder_TXT = PACT_config["MAIN"]["LoadOrder TXT"]
info.LoadOrder_Path = os.path.dirname(info.LoadOrder_TXT)
info.XEdit_EXE = PACT_config["MAIN"]["XEDIT EXE"]
info.XEdit_Path = os.path.dirname(info.XEdit_EXE)
info.MO2_EXE = PACT_config["MAIN"]["MO2 EXE"]
'''


# Make sure required file and folder paths exist.
def check_settings_paths():
    info.XEdit_EXE = PACT_config["MAIN"]["XEDIT EXE"]
    info.LoadOrder_TXT = PACT_config["MAIN"]["LoadOrder TXT"]
    if os.path.exists(info.LoadOrder_TXT) and os.path.exists(info.XEdit_EXE):
        print("✔️ REQUIRED FILE PATHS FOUND! CHECKING IF YOUR INI SETUP IS CORRECT...")
    else:
        print(Warn_Invalid_INI_Path)
        os.system("pause")
        sys.exit()


# Make sure right XEdit version is running for the right game.
def check_settings_integrity(xedit_version, game_esm):
    global MO2Mode
    info.MO2_EXE = PACT_config["MAIN"]["MO2 EXE"]
    info.XEdit_EXE = PACT_config["MAIN"]["XEDIT EXE"]
    info.LoadOrder_TXT = PACT_config["MAIN"]["LoadOrder TXT"]
    if os.path.exists(info.MO2_EXE):
        MO2Mode = True
    with open(info.LoadOrder_TXT, "r+", encoding="utf-8", errors="ignore") as LO_Check:
        LO_Plugins = LO_Check.read()
        if game_esm.lower() in LO_Plugins.lower():
            if xedit_version.lower() in str(info.XEdit_EXE).lower():
                pass
            else:
                print(Warn_Invalid_INI_Setup)
                os.system("pause")
                sys.exit()


LCL_skip_list = []
if not os.path.exists("PACT_Ignore.txt"):  # Local plugin skip / ignore list.
    with open("PACT_Ignore.txt", "w+", encoding="utf-8", errors="ignore") as PACT_Ignore:
        PACT_Ignore.write("Write plugin names you want PACT to ignore here. (ONE PLUGIN PER LINE)\n")
else:
    with open("PACT_Ignore.txt", "r+", encoding="utf-8", errors="ignore") as PACT_Ignore:
        LCL_skip_list = [line.strip() for line in PACT_Ignore.readlines()[1:]]

# HARD EXCLUDE PLUGINS PER GAME HERE
FO4_skip_list = ["", "Unofficial Fallout 4 Patch.esp", "Fallout4.esm", "DLCCoast.esm", "DLCNukaWorld.esm", "DLCRobot.esm", "DLCworkshop01.esm", "DLCworkshop02.esm", "DLCworkshop03.esm"]
SSE_skip_list = ["", "Unofficial Skyrim Special Edition Patch.esp", "Skyrim.esm", "Update.esm", "HearthFires.esm", "Dragonborn.esm", "Dawnguard.esm"]
VIP_skip_list = FO4_skip_list + SSE_skip_list

info.XEdit_EXE = PACT_config["MAIN"]["XEDIT EXE"]
xedit_process = os.path.basename(info.XEdit_EXE)
clean_results_UDR = []  # Undisabled Records
clean_results_ITM = []  # Identical To Master
clean_results_NVM = []  # Deleted Navmeshes
clean_failed_list = []  # Cleaning Failed
plugins_processed = 0
plugins_cleaned = 0


def run_xedit(xedit_exc_log, plugin_name):
    global MO2Mode
    global xedit_process
    global plugins_processed
    global clean_failed_list
    info.MO2_EXE = PACT_config["MAIN"]["MO2 EXE"]
    info.XEdit_EXE = PACT_config["MAIN"]["XEDIT EXE"]
    if os.path.exists("PACT_Cleaning.bat"):
        os.remove("PACT_Cleaning.bat")
    with open("PACT_Cleaning.bat", "w+") as PACT_Cleaning:
        if MO2Mode:  # Command will not work if plugin has "&" or "+" in name. Other special characters likely also apply.
            PACT_Cleaning.write(f'"{info.MO2_EXE}" run "{info.XEdit_EXE}" -a "-QAC -autoexit -autoload \\"{plugin_name}\\""')
        else:
            PACT_Cleaning.write(f'"{info.XEdit_EXE}" -a -QAC -autoexit -autoload "{plugin_name}"')

    bat_process = subprocess.Popen("PACT_Cleaning.bat")  # Subprocess waits for instance to finish before running again.

    while bat_process.poll() is None:  # Check if xedit encountered errors with this while loop.
        xedit_procs = [proc for proc in psutil.process_iter(attrs=['pid', 'name', 'create_time']) if 'Edit.exe' in proc.info['name']]
        for proc in xedit_procs:
            if proc.info['name'] == str(xedit_process):
                create_time = proc.info['create_time']
                # Kill if runtime is >5 minutes.
                if (time.time() - create_time) > 300:
                    print("❌ ERROR ENCOUNTERED! KILLING XEDIT...")
                    clean_failed_list.append(plugin_name)
                    plugins_processed -= 1
                    proc.kill()
                    break

            if proc.info['name'] == str(xedit_process) and os.path.exists(xedit_exc_log):  # Check if xedit cannot clean.
                xedit_exc_out = subprocess.check_output(['powershell', '-command', f'Get-Content {xedit_exc_log}'])
                Exception_Check = xedit_exc_out.decode()  # This method this since xedit is actively writing to it.
                if "which can not be found" in Exception_Check:
                    print("❌ ERROR ENCOUNTERED! KILLING XEDIT AND ADDING PLUGIN TO PACT IGNORE FILE...")
                    with open("PACT_Ignore.txt", "a", encoding="utf-8", errors="ignore") as PACT_Ignore:
                        PACT_Ignore.write(f"{plugin_name}\n")
                        clean_failed_list.append(plugin_name)
                    plugins_processed -= 1
                    proc.kill()
                    time.sleep(1)
                    os.remove(xedit_exc_log)
                    break
        time.sleep(1)
    plugins_processed += 1
    os.remove("PACT_Cleaning.bat")


def check_results(xedit_log, plugin_name):
    time.sleep(1)  # Wait to make sure xedit generates its log.
    global clean_results_UDR, clean_results_ITM, clean_results_NVM
    global plugins_cleaned
    global LCL_skip_list
    if os.path.exists(xedit_log):
        cleaned_something = False
        with open(xedit_log, "r", encoding="utf-8", errors="ignore") as XE_Check:
            Cleaning_Check = XE_Check.read()
            if "Undeleting:" in Cleaning_Check:
                clean_results_UDR.append(plugin_name)
                cleaned_something = True
            if "Removing:" in Cleaning_Check:
                clean_results_ITM.append(plugin_name)
                cleaned_something = True
            if "Skipping:" in Cleaning_Check:
                clean_results_NVM.append(plugin_name)
            if cleaned_something is True:
                plugins_cleaned += 1
            else:
                print("Nothing to clean! Adding plugin to PACT Ignore file...")
                with open("PACT_Ignore.txt", "a", encoding="utf-8", errors="ignore") as PACT_Ignore:
                    PACT_Ignore.write(f"{plugin_name}\n")
                    LCL_skip_list.append(plugin_name)
        os.remove(xedit_log)


def clean_plugins():
    global MO2Mode
    global xedit_process
    global VIP_skip_list, LCL_skip_list
    info.XEdit_EXE = PACT_config["MAIN"]["XEDIT EXE"]
    xedit_log_exe = str(info.XEdit_EXE)
    xedit_log_path = xedit_log_exe.replace('.exe', '_log.txt')
    xedit_exc_path = xedit_log_exe.replace('.exe', 'Exception.log')
    # Clear xedit log files to check logs for each plugin separately.
    if os.path.exists(xedit_log_path):
        os.remove(xedit_log_path)
    if os.path.exists(xedit_exc_path):
        os.remove(xedit_exc_path)

    if MO2Mode is True:
        print("✔️ MO2 EXECUTABLE WAS FOUND! SWITCHING TO MOD ORGANIZER 2 MODE...")
    else:
        print("❌ MO2 EXECUTABLE NOT SET OR FOUND. SWITCHING TO VORTEX MODE...")

    with open("PACT_Ignore.txt", "r", encoding="utf-8", errors="ignore") as IG_List:  # RESERVED
        IG_Plugins = [line.strip() for line in IG_List.readlines()[1:]]  # type: ignore
    info.LoadOrder_TXT = PACT_config["MAIN"]["LoadOrder TXT"]
    with open(info.LoadOrder_TXT, "r", encoding="utf-8", errors="ignore") as LO_List:
        ALL_skip_list = VIP_skip_list + LCL_skip_list
        LO_List.seek(0)  # Return line pointer to first line.
        LO_Plugins = [line.strip() for line in LO_List.readlines()[1:]]

    count_plugins = len(set(LO_Plugins) - set(ALL_skip_list))
    #count_test = set(LO_Plugins) - set(ALL_skip_list)
    #for item in count_test:
    #    print(item)
    print(f"✔️ CLEANING STARTED... ( PLUGINS TO CLEAN: {count_plugins} )\n")
    count_cleaned = 0
    for plugin in LO_Plugins:  # Run XEdit and log checks for each valid plugin in loadorder.txt file.
        if not any(plugin in elem for elem in ALL_skip_list) and any(ext in plugin.lower() for ext in ['.esl', '.esm', '.esp']):
            count_cleaned += 1
            run_xedit(xedit_exc_path, plugin)
            check_results(xedit_log_path, plugin)
            print(f"Finished cleaning: {plugin} ({count_cleaned} / {count_plugins})")

    print(f"✔️ CLEANING COMPLETE ! {xedit_process} successfully processed {plugins_processed} plugins and cleaned {plugins_cleaned} of them.")
    if len(clean_failed_list) > 1:
        print(f"\n❌ {xedit_process.upper()} WAS UNABLE TO CLEAN THESE PLUGINS: (Invalid Plugin Name or {xedit_process} Timed Out):")
        for elem in clean_failed_list:
            print(elem)
    if len(clean_results_UDR) > 1:
        print(f"\n✔️ The following plugins had Undisabled Records and {xedit_process} properly disabled them:")
        for elem in clean_results_UDR:
            print(elem)
    if len(clean_results_ITM) > 1:
        print(f"\n✔️ The following plugins had Identical To Master Records and {xedit_process} successfully cleaned them:")
        for elem in clean_results_ITM:
            print(elem)
    if len(clean_results_NVM) > 1:
        print("\n❌ CAUTION : The following plugins contain Deleted Navmeshes!")
        print("   Such plugins may cause navmesh related problems or crashes.")
        for elem in clean_results_NVM:
            print(elem)


if __name__ == "__main__":  # AKA only autorun / do the following when NOT imported.
    check_settings_paths()
    check_settings_integrity("FO4Edit", "Fallout4.esm")
    check_settings_integrity("SSEEdit", "Skyrim.esm")
    pact_update_check()
    clean_plugins()
    os.system("pause")
