# PLUGIN AUTO CLEANING TOOL (PACT) | By Poet (The Sound Of Snow)
import datetime
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union

import psutil
import requests
import tomlkit
from PySide6.QtCore import QObject, Signal, Slot

'''AUTHOR NOTES (POET)
- Comments marked as RESERVED in all scripts are intended for future updates or tests, do not edit / move / remove.
- (..., encoding="utf-8", errors="ignore") needs to go with every opened file because unicode errors are a bitch.
'''

# =================== PACT TOML FILE ===================


def pact_ini_create():
    if not os.path.exists("PACT Settings.toml"):
        INI_Settings = """[MAIN]
# This file contains settings for both source scripts and Plugin Auto Cleaning Tool.exe 
# Set to true if you want PACT to check that you have the latest version of PACT. 
Update_Check = true

# Set to true if you want PACT to show extra stats about cleaned plugins in the command line window. 
Stat_Logging = true

# In seconds, set below how long should PACT wait for xedit to clean any plugin. 
# If it takes longer than the set amount, the plugin will be immediately skipped. 
Cleaning_Timeout = 300

# In days, set below how long should PACT wait until the logging journal is cleared. 
# If PACT Journal.txt is older than the set amount, it is immediately deleted. 
Journal_Expiration = 7

# Set or copy-paste your load order (loadorder.txt / plugins.txt) file path below. 
# See the PACT Nexus Page for instructions on where you can find these files. 
LoadOrder_TXT = ""

# Set or copy-paste your XEdit (FO3Edit.exe / FNVEdit.exe / FO4Edit.exe / SSEEdit.exe) executable file path below. 
# xEdit.exe is also supported, but requires that you set LoadOrder TXT path to loadorder.txt only. 
XEDIT_EXE = ""

# Set or copy-paste your MO2 (ModOrganizer.exe) executable file path below. 
# Required if MO2 is your main mod manager. Otherwise, leave this blank. 
MO2_EXE = ""
"""
        toml_tmp = tomlkit.parse(INI_Settings)  # Do it the same way it is done in CLAS.
        with open("PACT Settings.toml", "w", encoding="utf-8", errors="ignore") as INI_PACT:
            INI_PACT.write(toml_tmp.as_string())


pact_ini_create()

with open("PACT Settings.toml", "r", encoding="utf-8", errors="ignore") as INI_PACT:
    PACT_config: tomlkit.TOMLDocument = tomlkit.parse(INI_PACT.read())  # type: ignore
PACT_Date = "140423"  # DDMMYY
PACT_Current = "PACT v1.80"
PACT_Updated = False


def pact_ini_update(section: str, value: Union[str, int, float, bool]):  # Convenience function for checking & writing to INI.
    if " " in section:
        raise ValueError

    if isinstance(value, Path):
        value = str(value)

    PACT_config["MAIN"][section] = value  # type: ignore

    with open("PACT Settings.toml", "w+", encoding="utf-8", errors="ignore") as INI_PACT:
        tomlkit.dump(PACT_config, INI_PACT)


def pact_journal_expire():
    # Delete journal if older than set amount of days.

    PACT_folder = os.getcwd()
    journal_name = "PACT Journal.log"
    journal_path = os.path.join(PACT_folder, journal_name)
    if os.path.isfile(journal_path):
        journal_age = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(journal_path))
        journal_age_days = journal_age.days
        if journal_age_days > info.Journal_Expiration:
            os.remove(journal_path)


def pact_log_update(log_message):
    pact_journal_expire()

    with open("PACT Journal.log", "a", encoding="utf-8", errors="ignore") as LOG_PACT:
        LOG_PACT.write(log_message)


def pact_ignore_update(plugin, numnewlinesbefore=1, numnewlinesafter=1):
    with open("PACT Ignore.txt", "a", encoding="utf-8", errors="ignore") as IGNORE_PACT:
        IGNORE_PACT.write("\n" * numnewlinesbefore + plugin + "\n" * numnewlinesafter)
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
    Please run the PACT program or open PACT Settings.toml
    And make sure that file / folder paths are correctly set!
"""
Warn_Invalid_INI_Setup = """
❌  WARNING : YOUR PACT INI SETUP IS INCORRECT!
    You likely set the wrong XEdit version for your game.
    Check your EXE or PACT Settings.toml settings and try again.
"""
Err_Invalid_LO_File = """
❌ ERROR : CANNOT PROCESS LOAD ORDER FILE FOR XEDIT IN THIS SITUATION!
   You have to set your load order file path to loadorder.txt and NOT plugins.txt
   This is so PACT can detect the right game. Change the load order file path and try again.
"""
Err_Invalid_XEDIT_File = """
❌ ERROR : CANNOT DETERMINE THE SET XEDIT EXECUTABLE FROM PACT SETTINGS!
   Make sure that you have set XEDIT EXE path to a valid .exe file!
   OR try changing XEDIT EXE path to a different XEdit version.
"""
PAUSE_MESSAGE = "Press Enter to continue..."

# =================== UPDATE FUNCTION ===================


def pact_update_check():
    if PACT_config["MAIN"]["Update_Check"] is True:  # type: ignore
        print("❓ CHECKING FOR ANY NEW PLUGIN AUTO CLEANING TOOL (PACT) UPDATES...")
        print("   (You can disable this check in the EXE or PACT Settings.toml) \n")
        try:
            response = requests.get("https://api.github.com/repos/GuidanceOfGrace/XEdit-PACT/releases/latest")
            PACT_Received = response.json()["name"]
            if PACT_Received == PACT_Current:
                print("\n✔️ You have the latest version of PACT!")
                return True
            else:
                print(Warn_Outdated_PACT)
                print("===============================================================================")
        except (OSError, requests.exceptions.RequestException):
            print(Warn_PACT_Update_Failed)
            print("===============================================================================")
    else:
        print("\n ❌ NOTICE: UPDATE CHECK IS DISABLED IN PACT INI SETTINGS \n")
        print("===============================================================================")
    return False


# =================== TERMINAL OUTPUT START ====================
print("Hello World! | Plugin Auto Cleaning Tool (PACT) | Version", PACT_Current[-4:], "| FO3, FNV, FO4, SSE")
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
    Journal_Expiration = 7
    Cleaning_Timeout = 300

    MO2Mode = False
    xedit_list_fallout3 = ("fo3edit.exe", "fo3edit64.exe")
    xedit_list_newvegas = ("fnvedit.exe", "fnvedit64.exe")
    xedit_list_fallout4 = ("fo4edit.exe", "fo4edit64.exe", "fo4vredit.exe")
    xedit_list_skyrimse = ("sseedit.exe", "sseedit64.exe", "tes5vredit.exe")
    xedit_list_universal = ("xedit.exe", "xedit64.exe", "xfoedit.exe", "xfoedit64.exe")
    xedit_list_specific = xedit_list_fallout3 + xedit_list_newvegas + xedit_list_fallout4 + xedit_list_skyrimse

    clean_results_UDR = []  # Undisabled References
    clean_results_ITM = []  # Identical To Master
    clean_results_NVM = []  # Deleted Navmeshes
    clean_failed_list = []  # Cleaning Failed
    plugins_processed = 0
    plugins_cleaned = 0

    plugins_pattern = re.compile(r"(?:.+?)(?:\.(?:esp|esm|esl)+)$", re.IGNORECASE | re.MULTILINE)
    LCL_skip_list = []
    if not os.path.exists("PACT Ignore.txt"):  # Local plugin skip / ignore list.
        with open("PACT Ignore.txt", "w", encoding="utf-8", errors="ignore") as PACT_Ignore:
            PACT_Ignore.write("Write plugin names you want CLAS to ignore here. (ONE PLUGIN PER LINE)\n")
    else:
        with open("PACT Ignore.txt", "r", encoding="utf-8", errors="ignore") as PACT_Ignore:
            LCL_skip_list = [line.group() for line in plugins_pattern.finditer(PACT_Ignore.read())]

    # HARD EXCLUDE PLUGINS PER GAME HERE
    FO3_skip_list = ["", "Fallout3.esm", "Anchorage.esm", "ThePitt.esm", "BrokenSteel.esm", "PointLookout.esm", "Zeta.esm", "Unofficial Fallout 3 Patch.esm"]

    FNV_skip_list = ["", "FalloutNV.esm", "DeadMoney.esm", "OldWorldBlues.esm", "HonestHearts.esm", "LonesomeRoad.esm", "TribalPack.esm", "MercenaryPack.esm",
                     "ClassicPack.esm", "CaravanPack.esm", "GunRunnersArsenal.esm", "Unofficial Patch NVSE Plus.esp"]

    TTW_skip_list = ["", "TaleOfTwoWastelands.esm", "TTWInteriors_Core.esm", "TTWInteriorsProject_Combo.esm", "TTWInteriorsProject_ComboHotfix.esm", "TTWInteriorsProject_Merged.esm", "TTWInteriors_Core_Hotfix.esm"]  # How the hell did Github Copilot know the file names for TTW?

    FO4_skip_list = ["", "Fallout4.esm", "DLCCoast.esm", "DLCNukaWorld.esm", "DLCRobot.esm", "DLCworkshop01.esm", "DLCworkshop02.esm", "DLCworkshop03.esm",
                     "Unofficial Fallout 4 Patch.esp", "PPF.esm", "PRP.esp", "PRP-Compat", "SS2.esm", "SS2_XPAC_Chapter2.esm", "SS2_XPAC_Chapter3.esm"]

    SSE_skip_list = ["", "Skyrim.esm", "Update.esm", "HearthFires.esm", "Dragonborn.esm", "Dawnguard.esm", "Unofficial Skyrim Special Edition Patch.esp"]

    VIP_skip_list = FO3_skip_list + FNV_skip_list + TTW_skip_list + FO4_skip_list + SSE_skip_list

    XEDIT_LOG_TXT: str = field(default_factory=str)
    XEDIT_EXC_LOG: str = field(default_factory=str)


info = Info()


def update_load_order_path(info, load_order_path):
    info.LOAD_ORDER_PATH = load_order_path
    info.LOAD_ORDER_TXT = os.path.basename(load_order_path)


def update_xedit_path(info, xedit_path):
    info.XEDIT_PATH = xedit_path
    if ".exe" in xedit_path:
        info.XEDIT_EXE = os.path.basename(xedit_path)
    elif os.path.exists(xedit_path):
        for file in os.listdir(xedit_path):
            if file.endswith(".exe") and "edit" in str(file).lower():
                info.XEDIT_PATH = os.path.join(xedit_path, file)
                info.XEDIT_EXE = os.path.basename(info.XEDIT_PATH)


def update_mo2_path(info, mo2_path):
    info.MO2_PATH = mo2_path
    if ".exe" in mo2_path:
        info.MO2_EXE = os.path.basename(mo2_path)
    elif os.path.exists(mo2_path):
        for file in os.listdir(mo2_path):
            if file.endswith(".exe") and ("mod" in str(file).lower() or "mo2" in str(file).lower()):
                info.MO2_PATH = os.path.join(mo2_path, file)
                info.MO2_EXE = os.path.basename(info.MO2_PATH)


def pact_update_settings(info, pact_config):
    update_load_order_path(info, pact_config["MAIN"]["LoadOrder_TXT"])
    update_xedit_path(info, pact_config["MAIN"]["XEDIT_EXE"])
    update_mo2_path(info, pact_config["MAIN"]["MO2_EXE"])
    info.Cleaning_Timeout = int(pact_config["MAIN"]["Cleaning_Timeout"])
    info.Journal_Expiration = int(pact_config["MAIN"]["Journal_Expiration"])

    if not isinstance(info.Cleaning_Timeout, int) or info.Cleaning_Timeout <= 0:
        raise ValueError("""❌ ERROR : CLEANING TIMEOUT VALUE IN PACT SETTINGS IS NOT VALID.)
Please change Cleaning Timeout to a valid positive number.""")
    elif info.Cleaning_Timeout < 30:
        raise ValueError("""❌ ERROR : CLEANING TIMEOUT VALUE IN PACT SETTINGS IS TOO SMALL.)
Cleaning Timeout must be set to at least 30 seconds or more.""")

    if not isinstance(info.Journal_Expiration, int) or info.Journal_Expiration <= 0:
        raise ValueError("""❌ ERROR : JOURNAL EXPIRATION VALUE IN PACT SETTINGS IS NOT VALID.)
Please change Journal Expiration to a valid positive number.""")
    elif info.Journal_Expiration < 1:
        raise ValueError("""❌ ERROR : JOURNAL EXPIRATION VALUE IN PACT SETTINGS IS TOO SMALL.)
Journal Expiration must be set to at least 1 day or more.""")


pact_update_settings(info, PACT_config)
if ".exe" in str(info.XEDIT_PATH) and info.XEDIT_EXE in info.xedit_list_specific:
    xedit_path = Path(info.XEDIT_PATH)
    info.XEDIT_LOG_TXT = str(xedit_path.with_name(xedit_path.stem.upper() + '_log.txt'))
    info.XEDIT_EXC_LOG = str(xedit_path.with_name(xedit_path.stem.upper() + 'Exception.log'))
elif info.XEDIT_PATH and not ".exe" in str(info.XEDIT_PATH):
    print(Err_Invalid_XEDIT_File)
    input(PAUSE_MESSAGE)
    raise ValueError


# Make sure Mod Organizer 2 is not already running.
def check_process_mo2(progress_emitter):
    pact_update_settings(info, PACT_config)
    if os.path.exists(info.MO2_PATH):
        mo2_procs = [proc for proc in psutil.process_iter(attrs=['pid', 'name']) if str(info.MO2_EXE).lower() in proc.name().lower()]
        for proc in mo2_procs:
            if str(info.MO2_EXE).lower() in proc.name().lower():
                print("""❌ ERROR : CANNOT START PACT WHILE MOD ORGANIZER 2 IS ALREADY RUNNING!
PLEASE CLOSE MO2 AND RUN PACT AGAIN! (DO NOT RUN PACT THROUGH MO2)""")
                progress_emitter.report_done()


# Clear xedit log files to check them for each plugin separately.
def clear_xedit_logs():
    try:
        if os.path.exists(info.XEDIT_LOG_TXT):
            os.remove(info.XEDIT_LOG_TXT)
        if os.path.exists(info.XEDIT_EXC_LOG):
            os.remove(info.XEDIT_EXC_LOG)
    except (PermissionError, OSError):
        print("❌ ERROR : CANNOT CLEAR XEDIT LOGS. Try running PACT in Admin Mode.")
        print("   If problems continue, please report this to the PACT Nexus page.")
        raise


# Make sure right XEDIT is running for the right game.
def check_settings_integrity():
    pact_update_settings(info, PACT_config)
    if os.path.exists(info.LOAD_ORDER_PATH) and os.path.exists(info.XEDIT_PATH):
        print("✔️ REQUIRED FILE PATHS FOUND! CHECKING IF INI SETTINGS ARE CORRECT...")
    else:
        print(Warn_Invalid_INI_Path)
        input(PAUSE_MESSAGE)
        raise ValueError

    if os.path.exists(info.MO2_PATH):
        info.MO2Mode = True
    else:
        info.MO2Mode = False

    valid_xedit_executables = {
        "Fallout3.esm": info.xedit_list_fallout3,
        "FalloutNV.esm": info.xedit_list_newvegas,
        "Fallout4.esm": info.xedit_list_fallout4,
        "Skyrim.esm": info.xedit_list_skyrimse
    }

    if str(info.XEDIT_EXE).lower() not in info.xedit_list_universal:
        with open(info.LOAD_ORDER_PATH, "r", encoding="utf-8", errors="ignore") as LO_Check:
            LO_Plugins = LO_Check.read()
            if not any(game in LO_Plugins and str(info.XEDIT_EXE).lower() in executables for game, executables in valid_xedit_executables.items()):
                print(Warn_Invalid_INI_Setup)
                input(PAUSE_MESSAGE)
                raise ValueError
    elif "loadorder" not in str(info.LOAD_ORDER_PATH) and str(info.XEDIT_EXE).lower() in info.xedit_list_universal:
        print(Err_Invalid_LO_File)
        input(PAUSE_MESSAGE)
        raise ValueError


def update_log_paths(info, game_mode=None):
    path = Path(info.XEDIT_PATH)
    if game_mode:
        info.XEDIT_LOG_TXT = str(path.with_name(f"{game_mode.upper()}Edit_log.txt"))
        info.XEDIT_EXC_LOG = str(path.with_name(f"{game_mode.upper()}EditException.log"))
    else:
        info.XEDIT_LOG_TXT = str(path.with_name(f"{path.stem.upper()}_log.txt"))
        info.XEDIT_EXC_LOG = str(path.with_name(f"{path.stem.upper()}Exception.log"))


def create_bat_command(info, plugin_name):
    xedit_exe_lower = str(info.XEDIT_EXE).lower()
    xedit_path_str = str(info.XEDIT_PATH)

    if xedit_exe_lower in info.xedit_list_specific:
        update_log_paths(info)
        bat_command = create_specific_xedit_command(info, plugin_name)
        if bat_command:
            return bat_command

    if "loadorder" in str(info.LOAD_ORDER_PATH).lower() and xedit_exe_lower in info.xedit_list_universal:
        game_mode = get_game_mode(info)
        if game_mode is None:
            print(Err_Invalid_LO_File)
            input(PAUSE_MESSAGE)
            raise ValueError

        update_log_paths(info, game_mode)
        bat_command = create_universal_xedit_command(info, plugin_name, game_mode)
        if bat_command:
            return bat_command

    print("""❓ ERROR : UNABLE TO START THE CLEANING PROCESS! WRONG INI SETTINGS OR FILE PATHS?
    If you're seeing this, make sure that your load order / xedit paths are correct.
    If problems continue, try a different load order file or xedit executable.
    If nothing works, please report this error to the PACT Nexus page.""")
    input(PAUSE_MESSAGE)
    raise RuntimeError("Unable to start the cleaning process")

    # Additional helper functions


def create_specific_xedit_command(info, plugin_name):
    xedit_exe_lower = str(info.XEDIT_EXE).lower()
    if info.MO2Mode and xedit_exe_lower in info.xedit_list_specific:
        return f'"{info.MO2_PATH}" run "{info.XEDIT_PATH}" -a "-QAC -autoexit -autoload \\"{plugin_name}\\""'
    elif not info.MO2Mode and xedit_exe_lower in info.xedit_list_specific:
        return f'"{info.XEDIT_PATH}" -a -QAC -autoexit -autoload "{plugin_name}"'
    else:
        print("Invalid xedit executable specified")
        return None


def create_universal_xedit_command(info, plugin_name, game_mode):
    if info.MO2Mode:
        return f'"{info.MO2_PATH}" run "{info.XEDIT_PATH}" -a "-{game_mode} -QAC -autoexit -autoload \\"{plugin_name}\\""'
    else:
        return f'"{info.XEDIT_PATH}" -a -{game_mode} -QAC -autoexit -autoload "{plugin_name}"'


def get_game_mode(info):
    # Read the load order file line by line to determine the game mode
    try:
        with open(info.LOAD_ORDER_PATH, "r", encoding="utf-8", errors="ignore") as LO_Check:
            for line in LO_Check:
                if "Skyrim.esm" in line:
                    return "sse"
                elif "Fallout3.esm" in line:
                    return "fo3"
                elif "FalloutNV.esm" in line:
                    return "fnv"
                elif "Fallout4.esm" in line:
                    return "fo4"
    except FileNotFoundError:
        print(f"Load order file not found: {info.LOAD_ORDER_PATH}")
        raise
    except Exception as e:
        print(f"Error reading load order file: {info.LOAD_ORDER_PATH}, error: {str(e)}")
        raise
    return None


def check_cpu_usage(proc):
    """
    Checks the CPU usage of a process.

    If CPU usage is below 1% for 10 seconds, returns True, indicating a likely error. 

    Args:
        proc (psutil.Process): The process to check.

    Returns:
        bool: True if CPU usage is low, False otherwise.
    """
    if proc.is_running() and proc.cpu_percent() < 1:
        time.sleep(10)  # Previous versions of this script were a bit trigger happy on the kill switch and I think the cpu usage code was the reason why.
        if proc.is_running() and proc.cpu_percent() < 1:
            return True
    return False


def check_process_timeout(proc, info):
    """
    Checks if a process has run longer than a specified timeout.

    Args:
        proc (psutil.Process): The process to check.
        info (Info): An object containing the timeout value.

    Returns:
        bool: True if the process has run longer than the timeout, False otherwise.
    """
    create_time = proc.create_time()
    if (time.time() - create_time) > info.Cleaning_Timeout:
        return True
    return False


def check_process_exceptions(info):
    """
    Checks a process for exceptions.

    Args:
        info (Info): An object containing the path to the exception log.

    Returns:
        bool: True if exceptions were found, False otherwise.
    """
    if os.path.exists(info.XEDIT_EXC_LOG):
        xedit_exc_out = subprocess.check_output(['powershell', '-command', f'Get-Content {info.XEDIT_EXC_LOG}'])
        Exception_Check = xedit_exc_out.decode()
        if "which can not be found" in Exception_Check or "which it does not have" in Exception_Check:
            return True
    return False


def handle_error(proc, plugin_name, info, error_message, add_ignore=True):
    """
    Handles an error case.

    Kills the process, clears logs, and updates relevant info.

    Args:
        proc (psutil.Process): The process to kill.
        plugin_name (str): The name of the plugin being processed.
        info (Info): An object containing relevant information.
        error_message (str): The error message to print.
        add_ignore (bool, optional): Whether or not to add the plugin to the ignore list. Defaults to True.
    """
    try:
        proc.kill()
    except (PermissionError, psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, subprocess.CalledProcessError):
        pass
    finally:
        time.sleep(1)
        clear_xedit_logs()
        info.plugins_processed -= 1
        info.clean_failed_list.append(plugin_name)
        print(error_message)
        if add_ignore:
            pact_ignore_update(plugin_name)


def run_auto_cleaning(plugin_name):
    """
    Runs the automatic cleaning process.

    Args:
        plugin_name (str): The name of the plugin to clean.
    """
    # Create command to run in subprocess
    bat_command = create_bat_command(info, plugin_name)

    # Clear logs and start subprocess
    clear_xedit_logs()
    print(f"\nCURRENTLY RUNNING : {bat_command}".replace("\\", "").replace('"', ""))
    bat_process = subprocess.Popen(bat_command)
    time.sleep(1)

    # Check subprocess for errors until it finishes
    while bat_process.poll() is None:
        xedit_procs = [proc for proc in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent', 'create_time']) if 'edit.exe' in proc.name().lower()]
        for proc in xedit_procs:
            if proc.name().lower() == str(info.XEDIT_EXE).lower():
                # Check for low CPU usage (indicative of an error)
                if check_cpu_usage(proc):
                    handle_error(proc, plugin_name, info, "❌ ERROR : PLUGIN IS DISABLED OR HAS MISSING REQUIREMENTS! KILLING XEDIT AND ADDING PLUGIN TO IGNORE LIST...")
                    pact_log_update(f"{plugin_name} -> Disabled or missing requirements")
                    break
                # Check for process running longer than specified timeout
                if check_process_timeout(proc, info):
                    handle_error(proc, plugin_name, info, "❌ ERROR : XEDIT TIMED OUT (CLEANING PROCESS TOOK TOO LONG)! KILLING XEDIT...", add_ignore=False)
                    pact_log_update(f"{plugin_name} -> XEdit timed out")
                    break
                # Check for exceptions in process
                if check_process_exceptions(info):
                    handle_error(proc, plugin_name, info, "❌ ERROR : PLUGIN IS EMPTY OR HAS MISSING REQUIREMENTS! KILLING XEDIT AND ADDING PLUGIN TO IGNORE LIST...")
                    pact_log_update(f"{plugin_name} -> Empty or missing requirements")
                    break
        time.sleep(3)
    # Increment processed plugins count
    info.plugins_processed += 1


# Compile the patterns outside the function
udr_pattern = re.compile(r"Undeleting:\s*(.*)")
itm_pattern = re.compile(r"Removing:\s*(.*)")
nvm_pattern = re.compile(r"Skipping:\s*(.*)")


def check_cleaning_results(plugin_name):
    time.sleep(1)  # Wait to make sure xedit generates the logs.
    if os.path.exists(info.XEDIT_LOG_TXT):
        cleaned_something = False
        with open(info.XEDIT_LOG_TXT, "r", encoding="utf-8", errors="ignore") as XE_Check:
            # Define the patterns and associated actions
            patterns = {
                udr_pattern: ("Cleaned UDRs", info.clean_results_UDR),
                itm_pattern: ("Cleaned ITMs", info.clean_results_ITM),
                nvm_pattern: ("Found Deleted Navmeshes", info.clean_results_NVM),
            }
            for line in XE_Check:
                for pattern, (message, results_list) in patterns.items():
                    if pattern.search(line):
                        pact_log_update(f"\n{plugin_name} -> {message}")
                        results_list.append(plugin_name)
                        cleaned_something = True
            if cleaned_something:
                info.plugins_cleaned += 1
            else:
                pact_log_update(f"\n{plugin_name} -> NOTHING TO CLEAN")
                print("NOTHING TO CLEAN ! Adding plugin to PACT Ignore file...")
                pact_ignore_update(plugin_name, numnewlinesafter=0)
                info.LCL_skip_list.append(plugin_name)
        clear_xedit_logs()


def get_plugin_list(load_order_path):
    with open(load_order_path, "r", encoding="utf-8", errors="ignore") as lo_file:
        next(lo_file)  # Skip the first line
        if "plugins.txt" in load_order_path:
            plugin_list = [line.strip().replace("*", "") for line in lo_file if "*" in line.strip()]
        else:
            plugin_list = [line.strip() for line in lo_file if ".ghost" not in line]
    return plugin_list


def clean_plugin(plugin):
    run_auto_cleaning(plugin)
    check_cleaning_results(plugin)


def init_plugins_info():
    ALL_skip_list = info.VIP_skip_list + info.LCL_skip_list
    plugin_list = get_plugin_list(info.LOAD_ORDER_PATH)
    count_plugins = len(set(plugin_list) - set(ALL_skip_list))
    return plugin_list, count_plugins, ALL_skip_list


class ProgressEmitter(QObject):  # type: ignore
    progress = Signal(int)
    max_value = Signal(int)
    plugin_value = Signal(str)
    done = Signal()
    visible = Signal(bool)
    is_done = False

    def report_max_value(self):
        count = init_plugins_info()[1]
        self.max_value.emit(count)

    def report_progress(self, count):
        self.progress.emit(count)

    def report_plugin(self, plugin):
        self.plugin_value.emit(f"Cleaning {plugin} %v/%m - %p%")

    def report_done(self):
        self.done.emit()
        self.is_done = True

    def set_visible(self):
        self.visible.emit(True)


def clean_plugins(progress_emitter: ProgressEmitter):
    progress_emitter.is_done = False
    print(f"❓ LOAD ORDER TXT is set to : {info.LOAD_ORDER_PATH}")
    print(f"❓ XEDIT EXE is set to : {info.XEDIT_PATH}")
    print(f"❓ MO2 EXE is set to : {info.MO2_PATH}")
    # progress_emitter.is_done = False
    if info.MO2Mode:
        print("✔️ MO2 EXECUTABLE WAS FOUND! SWITCHING TO MOD ORGANIZER 2 MODE...")
    else:
        print("❌ MO2 EXECUTABLE NOT SET OR FOUND. SWITCHING TO VORTEX MODE...")

    plugin_list, plugin_count, ALL_skip_list = init_plugins_info()
    progress_emitter.report_max_value()
    progress_emitter.set_visible()

    print(f"✔️ CLEANING STARTED... ( PLUGINS TO CLEAN: {plugin_count} )")
    log_start = time.perf_counter()
    log_time = datetime.datetime.now()
    pact_log_update(f"\nSTARTED CLEANING PROCESS AT : {log_time}")
    count_cleaned = 0

    for plugin in plugin_list:
        if not any(plugin in elem for elem in ALL_skip_list) and re.search(r"(?:.+?)(?:\.(?:esl|esm|esp)+)$", plugin, re.IGNORECASE):
            progress_emitter.report_plugin(plugin)
            clean_plugin(plugin)
            count_cleaned += 1
            print(f"Finished cleaning : {plugin} ({count_cleaned} / {plugin_count})")
            progress_emitter.report_progress(count_cleaned)
    completion_time = (str(time.perf_counter() - log_start))[:3]
    pact_log_update(f"\n✔️ CLEANING COMPLETE! {info.XEDIT_EXE} processed all available plugins in {completion_time} seconds.")
    pact_log_update(f"\n   {info.XEDIT_EXE} successfully processed {info.plugins_processed} plugins and cleaned {info.plugins_cleaned} of them.\n")

    print(f"\n✔️ CLEANING COMPLETE! {info.XEDIT_EXE} processed all available plugins in {completion_time} seconds.")
    print(f"\n   {info.XEDIT_EXE} successfully processed {info.plugins_processed} plugins and cleaned {info.plugins_cleaned} of them.\n")

    for plugins, message in [(info.clean_failed_list, "❌ {0} WAS UNABLE TO CLEAN THESE PLUGINS: (Invalid Plugin Name or {0} Timed Out):"),
                             (info.clean_results_UDR, "✔️ The following plugins had Undisabled Records and {0} properly disabled them:"),
                             (info.clean_results_ITM, "✔️ The following plugins had Identical To Master Records and {0} successfully cleaned them:"),
                             (info.clean_results_NVM, "❌ CAUTION : The following plugins contain Deleted Navmeshes!\n   Such plugins may cause navmesh related problems or crashes.")]:
        if len(plugins) > 0:
            print(f"\n{message.format(info.XEDIT_EXE)}")
            for plugin in plugins:
                print(plugin)

    progress_emitter.report_done()

if __name__ == "__main__":
    input("This is not the main file. Press Enter to exit...")
    raise SystemExit  # This is basically what sys.exit() does, but without having to import sys