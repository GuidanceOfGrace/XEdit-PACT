# PLUGIN AUTO CLEANING TOOL (PACT) | By Poet (The Sound Of Snow)
import configparser
import datetime
import os
import psutil
import requests
import subprocess
import sys
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Union

'''AUTHOR NOTES (POET)
- Module try - except importing is disabled as this is only meant to be run through exe. Will also disable for CLAS.
- Comments marked as RESERVED in all scripts are intended for future updates or tests, do not edit / move / remove.
- (..., encoding="utf-8", errors="ignore") needs to go with every opened file because unicode errors are a bitch.
  IMPORTANT
- Every time any function() uses INI variable from "class Info", we need to redefine the value from that variable,
  just in case the user changed file paths while PACT is open, so function() can grab the updated values.
  This might be also required for "CHANGE INI PATH" in CLAS Interface / GUI, will implement soon.
'''
# =================== PACT INI FILE ===================


def pact_ini_create():
    if not os.path.exists("PACT Settings.ini"):  # INI FILE FOR PACT
        INI_Settings = ["[MAIN]\n",
                        "# This file contains settings for both PACT_Start.py and Plugin Auto Cleaning Tool.exe \n",
                        "# Set to true if you want PACT to check that you have the latest version of PACT. \n",
                        "Update Check = true\n\n",
                        "# Set to true if you want PACT to show extra stats about cleaned plugins in the command line window. \n",
                        "Stat Logging = true\n\n",
                        "# Set or copy-paste your load order (loadorder.txt / plugins.txt) file path below. \n",
                        "# Vortex -> Both can be found by selecting Open > Game Application Data Folder. \n",
                        "# MO2 -> Both can be found in your currently active MO2 profile folder. \n",
                        "LoadOrder TXT = \n\n",
                        "# Set or copy-paste your XEdit (FNVEdit.exe / FO4Edit.exe / SSEEdit.exe) executable file path below. \n",
                        "# xEdit.exe is also supported, but requires that you set LoadOrder TXT path to your loadorder.txt \n",
                        "XEDIT EXE = \n\n",
                        "# Set or copy-paste your MO2 (ModOrganizer.exe) executable file path below. \n",
                        "# Only required if using Mod Organizer 2. Otherwise, leave this blank. \n",
                        "MO2 EXE = "]
        with open("PACT Settings.ini", "w+", encoding="utf-8", errors="ignore") as INI_PACT:
            INI_PACT.writelines(INI_Settings)


pact_ini_create()
# Use optionxform = str to preserve INI formatting. | Set comment_prefixes to unused char to keep INI comments.
PACT_config = configparser.ConfigParser(allow_no_value=True, comment_prefixes="$")
PACT_config.optionxform = str  # type: ignore
PACT_config.read("PACT Settings.ini")
PACT_Date = "110323"  # DDMMYY
PACT_Current = "PACT v1.60"
PACT_Updated = False


def pact_ini_update(section: str, value: str):  # Convenience function for checking & writing to INI.
    if isinstance(section, str) and isinstance(value, str):
        PACT_config["MAIN"][section] = value
    else:
        PACT_config["MAIN"][str(section)] = str(value)

    with open("PACT Settings.ini", "w+", encoding="utf-8", errors="ignore") as INI_PACT:
        PACT_config.write(INI_PACT)


def pact_log_update(log_message):
    with open("PACT Journal.log", "a", encoding="utf-8", errors="ignore") as LOG_PACT:
        LOG_PACT.write(log_message)


# =================== WARNING MESSAGES ==================
# Can change first line to """\ to remove the spacing.

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
    Please run the PACT program or open PACT Settings.ini
    And make sure that file / folder paths are correctly set!
"""
Warn_Invalid_INI_Setup = """
❌  WARNING : YOUR PACT INI SETUP IS INCORRECT!
    You likely set the wrong XEdit version for your game.
    Check your EXE or PACT Settings.ini settings and try again.
"""


# =================== UPDATE FUNCTION ===================
def pact_update_check():
    global PACT_Current
    global PACT_Updated
    print("❓ CHECKING FOR ANY NEW PLUGIN AUTO CLEANING TOOL (PACT) UPDATES...")
    print("   (You can disable this check in the EXE or PACT Settings.ini) \n")
    response = requests.get("https://api.github.com/repos/GuidanceOfGrace/XEdit-PACT/releases/latest")  # type: ignore
    PACT_Received = response.json()["name"]
    if PACT_Received == PACT_Current:
        PACT_Updated = True
        print("\n✔️ You have the latest version of PACT!")
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
    elif PACT_config.getboolean("MAIN", "Update Check") is False:
        print("\n❌ NOTICE: UPDATE CHECK IS DISABLED IN PACT INI SETTINGS \n")


# =================== TERMINAL OUTPUT START ====================
print("Hello World! | Plugin Auto Cleaning Tool (PACT) | Version", PACT_Current[-4:], "| FNV, FO4, SSE")
print("MAKE SURE TO SET THE CORRECT LOAD ORDER AND XEDIT PATHS BEFORE CLEANING PLUGINS")
print("===============================================================================")


@dataclass
class Info:
    MO2_EXE: Union[str, Path] = field(default_factory=Path)
    MO2_PATH: Union[str, Path] = field(default_factory=Path)
    XEDIT_EXE: Union[str, Path] = field(default_factory=Path)
    XEDIT_PATH: Union[str, Path] = field(default_factory=Path)
    LOAD_ORDER_TXT: Union[str, Path] = field(default_factory=Path)
    LOAD_ORDER_PATH: Union[str, Path] = field(default_factory=Path)



info = Info()


def pact_update_settings():
    info.LOAD_ORDER_PATH = PACT_config["MAIN"]["LoadOrder TXT"]  # type: ignore
    info.LOAD_ORDER_TXT = os.path.basename(info.LOAD_ORDER_PATH)
    info.XEDIT_PATH = PACT_config["MAIN"]["XEDIT EXE"]  # type: ignore
    info.XEDIT_EXE = os.path.basename(info.XEDIT_PATH)
    info.MO2_PATH = PACT_config["MAIN"]["MO2 EXE"]  # type: ignore
    info.MO2_EXE = os.path.basename(info.MO2_PATH)
    print(f"Load order path is: {info.LOAD_ORDER_PATH}")
    print(f"Load order file is: {info.LOAD_ORDER_TXT}")
    print(f"XEDIT path is : {info.XEDIT_PATH}")
    print(f"XEDIT exe is : {info.XEDIT_EXE}")
    print(f"MO2 path is : {info.MO2_PATH}")
    print(f"MO2 exe is : {info.MO2_EXE}")


pact_update_settings()
XEDIT_LOG_TXT = str(info.XEDIT_PATH).replace('.exe', '_log.txt')
XEDIT_EXC_LOG = str(info.XEDIT_PATH).replace('.exe', 'Exception.log')
xedit_list_universal = ("xedit.exe", "xedit64.exe", "xfoedit.exe", "xfoedit64.exe")
xedit_list_newvegas = ("fnvedit.exe", "fnvedit64.exe")
xedit_list_fallout4 = ("fo4edit.exe", "fo4edit64.exe")
xedit_list_skyrimse = ("sseedit.exe", "sseedit64.exe")
xedit_list_specific = xedit_list_newvegas + xedit_list_fallout4 + xedit_list_skyrimse

clean_results_UDR = []  # Undisabled References
clean_results_ITM = []  # Identical To Master
clean_results_NVM = []  # Deleted Navmeshes
clean_failed_list = []  # Cleaning Failed
plugins_processed = 0
plugins_cleaned = 0
MO2Mode = False

# HARD EXCLUDE PLUGINS PER GAME HERE
FNV_skip_list = ["", "FalloutNV.esm", "DeadMoney.esm", "OldWorldBlues.esm", "HonestHearts.esm", "LonesomeRoad.esm", "TribalPack.esm", "MercenaryPack.esm",
                 "ClassicPack.esm", "CaravanPack.esm", "GunRunnersArsenal.esm", "Unofficial Patch NVSE Plus.esp"]

FO4_skip_list = ["", "Fallout4.esm", "DLCCoast.esm", "DLCNukaWorld.esm", "DLCRobot.esm", "DLCworkshop01.esm", "DLCworkshop02.esm", "DLCworkshop03.esm",
                 "Unofficial Fallout 4 Patch.esp", "PPF.esm", "PRP.esp", "PRP-Compat", "SS2.esm", "SS2_XPAC_Chapter2.esm"]

SSE_skip_list = ["", "Skyrim.esm", "Update.esm", "HearthFires.esm", "Dragonborn.esm", "Dawnguard.esm", "Unofficial Skyrim Special Edition Patch.esp"]

VIP_skip_list = FNV_skip_list + FO4_skip_list + SSE_skip_list


# Make sure Mod Organizer 2 is not already running.
def check_process_mo2():
    mo2_procs = [proc for proc in psutil.process_iter(attrs=['pid', 'name']) if 'modorganizer' in proc.info['name'].lower()]  # type: ignore
    for proc in mo2_procs:
        if proc.info['name'] == "ModOrganizer.exe":  # type: ignore
            print("\n❌ ERROR : CANNOT START PACT IF MOD ORGANIZER 2 IS ALREADY RUNNING!")
            print("\n❌ PLEASE CLOSE MOD ORGANIZER 2 AND RUN PACT AGAIN! (DO NOT RUN PACT IN MO2)")
            os.system("pause")
            sys.exit()


# Make sure required file and folder paths exist.
def check_settings_paths():
    info.XEDIT_PATH = PACT_config["MAIN"]["XEDIT EXE"]  # type: ignore
    info.LOAD_ORDER_PATH = PACT_config["MAIN"]["LoadOrder TXT"]  # type: ignore
    if os.path.exists(info.LOAD_ORDER_PATH) and os.path.exists(info.XEDIT_PATH):
        print("✔️ REQUIRED FILE PATHS FOUND! CHECKING IF YOUR INI SETUP IS CORRECT...")
    else:
        print(Warn_Invalid_INI_Path)
        os.system("pause")
        sys.exit()


# Make sure right XEdit version is running for the right game.
def check_settings_integrity():
    global MO2Mode
    global xedit_list_newvegas
    global xedit_list_fallout4
    global xedit_list_skyrimse
    global xedit_list_universal

    pact_update_settings()

    if os.path.exists(info.MO2_PATH):
        MO2Mode = True
    else:
        MO2Mode = False

    if info.XEDIT_EXE.lower() not in xedit_list_universal:  # Check if right xedit version.
        with open(info.LOAD_ORDER_PATH, "r", encoding="utf-8", errors="ignore") as LO_Check:
            LO_Plugins = LO_Check.read()
            if "FalloutNV.esm" in LO_Plugins and info.XEDIT_EXE.lower() not in xedit_list_newvegas:
                print(Warn_Invalid_INI_Setup)
                os.system("pause")
                sys.exit()

            if "Fallout4.esm" in LO_Plugins and info.XEDIT_EXE.lower() not in xedit_list_fallout4:
                print(Warn_Invalid_INI_Setup)
                os.system("pause")
                sys.exit()

            if "Skyrim.esm" in LO_Plugins and info.XEDIT_EXE.lower() not in xedit_list_skyrimse:
                print(Warn_Invalid_INI_Setup)
                os.system("pause")
                sys.exit()


LCL_skip_list = []
if not os.path.exists("PACT Ignore.txt"):  # Local plugin skip / ignore list.
    with open("PACT Ignore.txt", "w+", encoding="utf-8", errors="ignore") as PACT_Ignore:
        PACT_Ignore.write("Write plugin names you want PACT to ignore here. (ONE PLUGIN PER LINE)\n")
else:
    with open("PACT Ignore.txt", "r+", encoding="utf-8", errors="ignore") as PACT_Ignore:
        LCL_skip_list = [line.strip() for line in PACT_Ignore.readlines()[1:]]


def run_xedit(plugin_name):
    global MO2Mode
    global plugins_processed
    global clean_failed_list
    global xedit_list_universal
    global xedit_list_specific
    global XEDIT_LOG_TXT, XEDIT_EXC_LOG

    pact_update_settings()

    # Write proper bat command depending on XEDIT and MO2 selections.
    plugin_escape = plugin_name.replace("&", "^&").replace("+", "^+").replace("(", "^(").replace(")", "^)")  # Escape special characters for command line.

    bat_command = ""
    # If specific xedit (fnvedit, fo4edit, sseedit) executable is set.
    if MO2Mode and info.XEDIT_EXE.lower() in xedit_list_specific:
        bat_command = f'"{info.MO2_PATH}" run "{info.XEDIT_PATH}" -a "-QAC -autoexit -autoload \\"{plugin_escape}\\""'

    elif not MO2Mode and info.XEDIT_EXE.lower() in xedit_list_specific:
        bat_command = f'"{info.XEDIT_PATH}" -a -QAC -autoexit -autoload "{plugin_name}"'

    # If universal xedit (xedit.exe) executable is set.
    if "loadorder" in info.LOAD_ORDER_PATH and info.XEDIT_EXE.lower() in xedit_list_universal:
        with open(info.LOAD_ORDER_PATH, "r", encoding="utf-8", errors="ignore") as LO_Check:
            if "FalloutNV.esm" in LO_Check.read():
                XEDIT_LOG_TXT = str(info.XEDIT_PATH).replace('xEdit.exe', 'FNVEdit_log.txt')
                if MO2Mode:
                    bat_command = f'"{info.MO2_PATH}" run "{info.XEDIT_PATH}" -a "-fnv -QAC -autoexit -autoload \\"{plugin_escape}\\""'
                else:
                    bat_command = f'"{info.XEDIT_PATH}" -a -fnv -QAC -autoexit -autoload "{plugin_name}"'

            elif "Fallout4.esm" in LO_Check.read():
                XEDIT_LOG_TXT = str(info.XEDIT_PATH).replace('xEdit.exe', 'FO4Edit_log.txt')
                if MO2Mode:
                    bat_command = f'"{info.MO2_PATH}" run "{info.XEDIT_PATH}" -a "-fo4 -QAC -autoexit -autoload \\"{plugin_escape}\\""'
                else:
                    bat_command = f'"{info.XEDIT_PATH}" -a -fo4 -QAC -autoexit -autoload "{plugin_name}"'

            elif "Skyrim.esm" in LO_Check.read():
                XEDIT_LOG_TXT = str(info.XEDIT_PATH).replace('xEdit.exe', 'SSEEdit_log.txt')
                if MO2Mode:
                    bat_command = f'"{info.MO2_PATH}" run "{info.XEDIT_PATH}" -a "-sse -QAC -autoexit -autoload \\"{plugin_escape}\\""'
                else:
                    bat_command = f'"{info.XEDIT_PATH}" -a -sse -QAC -autoexit -autoload "{plugin_name}"'

    elif "loadorder" not in info.LOAD_ORDER_PATH and info.XEDIT_EXE.lower() in xedit_list_universal:
        print("\n❌ ERROR : CANNOT PROCESS LOAD ORDER FILE FOR XEDIT IN THIS SITUATION!")
        print("   You have to set your load order file path to loadorder.txt and NOT plugins.txt")
        print("   This is so PACT can detect the right game. Change the load order file path and try again.")
        os.system("pause")
        sys.exit()

    if bat_command == "":
        print("\n❓ ERROR : UNABLE TO START THE CLEANING PROCESS! WRONG INI SETTINGS OR FILE PATHS?")
        print("   If you're seeing this, make sure that your load order / xedit paths are correct.")
        print("   If problems continue, try a different load order file or xedit executable.")
        print("   If nothing works, please report this error to the PACT Nexus page.")
        os.system("pause")
        sys.exit()

    print(XEDIT_LOG_TXT, XEDIT_EXC_LOG)
    # Clear xedit log files to check logs for each plugin separately.
    try:
        if os.path.exists(XEDIT_LOG_TXT):
            os.remove(XEDIT_LOG_TXT)
        if os.path.exists(XEDIT_EXC_LOG):
            os.remove(XEDIT_EXC_LOG)
    except PermissionError:
        print("❌ ERROR : CANNOT CLEAR XEDIT LOGS. Try running PACT in Admin Mode.")
        print("   If problems continue, please report this to the PACT Nexus page.")
        os.system("pause")
        sys.exit()

    print(f"\nCURRENTLY RUNNING : {bat_command}") 
    bat_process = subprocess.Popen(bat_command)
    time.sleep(1)
    while bat_process.poll() is None:  # Check if xedit timed out or encountered errors while above subprocess.Popen() is running.
        xedit_procs = [proc for proc in psutil.process_iter(attrs=['pid', 'name', 'create_time']) if 'edit.exe' in proc.info['name'].lower()]  # type: ignore
        for proc in xedit_procs:
            if proc.info['name'] == str(info.XEDIT_EXE):  # type: ignore
                create_time = proc.info['create_time']  # type: ignore
                if (time.time() - create_time) > 300:  # 5 min time-out.
                    print("❌ ERROR : XEDIT TIMED OUT! KILLING XEDIT...")
                    clean_failed_list.append(plugin_name)
                    plugins_processed -= 1
                    proc.kill()
                    break

            if proc.info['name'] == str(info.XEDIT_EXE) and os.path.exists(XEDIT_EXC_LOG):  # Check if xedit cannot clean. # type: ignore
                xedit_exc_out = subprocess.check_output(['powershell', '-command', f'Get-Content {XEDIT_EXC_LOG}'])
                Exception_Check = xedit_exc_out.decode()  # Use this method since xedit is actively writing to it.
                if "which can not be found" in Exception_Check:
                    print("❌ ERROR : MISSING PLUGIN REQUIREMENTS! KILLING XEDIT AND ADDING PLUGIN TO IGNORE LIST...")
                    with open("PACT Ignore.txt", "a", encoding="utf-8", errors="ignore") as PACT_IGNORE:
                        PACT_IGNORE.write(f"\n{plugin_name}\n")
                        clean_failed_list.append(plugin_name)
                    plugins_processed -= 1
                    proc.kill()
                    time.sleep(1)
                    os.remove(XEDIT_EXC_LOG)
                    break
        time.sleep(1)
    plugins_processed += 1


def check_results(plugin_name):
    time.sleep(1)  # Wait to make sure xedit generates its log.
    global clean_results_UDR, clean_results_ITM, clean_results_NVM
    global plugins_cleaned
    global LCL_skip_list
    if os.path.exists(XEDIT_LOG_TXT):
        cleaned_something = False
        with open(XEDIT_LOG_TXT, "r", encoding="utf-8", errors="ignore") as XE_Check:
            Cleaning_Check = XE_Check.read()
            if "Undeleting:" in Cleaning_Check:
                pact_log_update(f"\n{plugin_name} -> Cleaned UDRs")
                clean_results_UDR.append(plugin_name)
                cleaned_something = True
            if "Removing:" in Cleaning_Check:
                pact_log_update(f"\n{plugin_name} -> Cleaned ITMs")
                clean_results_ITM.append(plugin_name)
                cleaned_something = True
            if "Skipping:" in Cleaning_Check:
                pact_log_update(f"\n{plugin_name} -> Found Deleted Navmeshes")
                clean_results_NVM.append(plugin_name)
            if cleaned_something is True:
                plugins_cleaned += 1
            else:
                pact_log_update(f"\n{plugin_name} -> NOTHING TO CLEAN")
                print("NOTHING TO CLEAN ! Adding plugin to PACT Ignore file...")
                with open("PACT Ignore.txt", "a", encoding="utf-8", errors="ignore") as PACT_IGNORE:
                    PACT_IGNORE.write(f"\n{plugin_name}")
                    LCL_skip_list.append(plugin_name)
        os.remove(XEDIT_LOG_TXT)


def clean_plugins():
    global MO2Mode
    global XEDIT_LOG_TXT, XEDIT_EXC_LOG
    global VIP_skip_list, LCL_skip_list
    ALL_skip_list = VIP_skip_list + LCL_skip_list

    pact_update_settings()

    # Change mod manager modes and check ignore list.
    if MO2Mode:
        print("✔️ MO2 EXECUTABLE WAS FOUND! SWITCHING TO MOD ORGANIZER 2 MODE...")
    else:
        print("❌ MO2 EXECUTABLE NOT SET OR FOUND. SWITCHING TO VORTEX MODE...")

    with open("PACT Ignore.txt", "r", encoding="utf-8", errors="ignore") as IG_File:  # RESERVED
        IG_Plugins = [line.strip() for line in IG_File.readlines()[1:]]  # type: ignore

    # Add plugins from loadorder or plugins file to separate plugin list.
    info.LOAD_ORDER_PATH = PACT_config["MAIN"]["LoadOrder TXT"]  # type: ignore
    with open(info.LOAD_ORDER_PATH, "r", encoding="utf-8", errors="ignore") as LO_File:
        LO_File.seek(0)  # Return line pointer to first line.
        LO_Plugin_List = []
        LO_List = LO_File.readlines()[1:]
        if "plugins" in info.LOAD_ORDER_PATH:
            for line in LO_List:
                line = line.strip()
                if "*" in line:
                    line = line.replace("*", "")
                    LO_Plugin_List.append(line)
        else:
            for line in LO_List:
                line = line.strip()
                if ".ghost" not in line:
                    LO_Plugin_List.append(line)

    # Start cleaning process if everything is OK.
    count_plugins = len(set(LO_Plugin_List) - set(ALL_skip_list))
    print(f"✔️ CLEANING STARTED... ( PLUGINS TO CLEAN: {count_plugins} )")
    log_start = time.perf_counter()
    log_time = datetime.datetime.now()
    pact_log_update(f"\nSTARTED CLEANING AT : {log_time}")
    count_cleaned = 0
    for plugin in LO_Plugin_List:  # Run XEdit and log checks for each valid plugin in loadorder.txt file.
        if not any(plugin in elem for elem in ALL_skip_list) and any(ext in plugin.lower() for ext in ['.esl', '.esm', '.esp']):
            count_cleaned += 1
            run_xedit(plugin)
            check_results(plugin)
            print(f"Finished cleaning : {plugin} ({count_cleaned} / {count_plugins})")

    # Show stats once cleaning is complete.
    pact_log_update(f"\n✔️ CLEANING COMPLETE! {info.XEDIT_EXE} processed all available plugins in {(str(time.perf_counter() - log_start)[:3])} seconds.")
    pact_log_update(f"\n   {info.XEDIT_EXE} successfully processed {plugins_processed} plugins and cleaned {plugins_cleaned} of them.\n")

    print(f"\n✔️ CLEANING COMPLETE! {info.XEDIT_EXE} processed all available plugins in", (str(time.perf_counter() - log_start)[:3]), "seconds.")
    print(f"\n   {info.XEDIT_EXE} successfully processed {plugins_processed} plugins and cleaned {plugins_cleaned} of them.\n")
    if len(clean_failed_list) > 1:
        print(f"\n❌ {info.XEDIT_EXE.upper()} WAS UNABLE TO CLEAN THESE PLUGINS: (Invalid Plugin Name or {info.XEDIT_EXE} Timed Out):")
        for elem in clean_failed_list:
            print(elem)
    if len(clean_results_UDR) > 1:
        print(f"\n✔️ The following plugins had Undisabled Records and {info.XEDIT_EXE} properly disabled them:")
        for elem in clean_results_UDR:
            print(elem)
    if len(clean_results_ITM) > 1:
        print(f"\n✔️ The following plugins had Identical To Master Records and {info.XEDIT_EXE} successfully cleaned them:")
        for elem in clean_results_ITM:
            print(elem)
    if len(clean_results_NVM) > 1:
        print("\n❌ CAUTION : The following plugins contain Deleted Navmeshes!")
        print("   Such plugins may cause navmesh related problems or crashes.")
        for elem in clean_results_NVM:
            print(elem)
    return True  # Required for running function check in PACT_Interface.


if __name__ == "__main__":  # AKA only autorun / do the following when NOT imported.
    pact_update_settings()
    check_process_mo2()
    check_settings_paths()
    check_settings_integrity()
    clean_plugins()
    os.system("pause")
