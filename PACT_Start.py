# PLUGIN AUTO CLEANING TOOL (PACT) | By Poet (The Sound Of Snow)
import configparser
import datetime
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Union

import psutil
import requests

'''AUTHOR NOTES (POET)
- Comments marked as RESERVED in all scripts are intended for future updates or tests, do not edit / move / remove.
- (..., encoding="utf-8", errors="ignore") needs to go with every opened file because unicode errors are a bitch.
'''


# =================== PACT INI FILE ===================
def pact_ini_create():
    if not os.path.exists("PACT Settings.ini"):
        INI_Settings = ["[MAIN]\n",
                        "# This file contains settings for both source scripts and Plugin Auto Cleaning Tool.exe \n",
                        "# Set to true if you want PACT to check that you have the latest version of PACT. \n",
                        "Update Check = true\n \n",
                        "# Set to true if you want PACT to show extra stats about cleaned plugins in the command line window. \n",
                        "Stat Logging = true\n \n",
                        "# In seconds, set below how long should PACT wait for xedit to clean any plugin. \n",
                        "# If it takes longer than the set amount, the plugin will be immediately skipped. \n",
                        "Cleaning Timeout = 300\n \n",
                        "# In days, set below how long should PACT wait until the logging journal is cleared. \n",
                        "# If PACT Journal.txt is older than the set amount, it is immediately deleted. \n",
                        "Journal Expiration = 7\n \n",
                        "# Set or copy-paste your load order (loadorder.txt / plugins.txt) file path below. \n",
                        "# See the PACT Nexus Page for instructions on where you can find these files. \n",
                        "LoadOrder TXT = \n \n",
                        "# Set or copy-paste your XEdit (FNVEdit.exe / FO4Edit.exe / SSEEdit.exe) executable file path below. \n",
                        "# xEdit.exe is also supported, but requires that you set LoadOrder TXT path to loadorder.txt only. \n",
                        "XEDIT EXE = \n \n",
                        "# Set or copy-paste your MO2 (ModOrganizer.exe) executable file path below. \n",
                        "# Required if MO2 is your main mod manager. Otherwise, leave this blank. \n",
                        "MO2 EXE = "]
        with open("PACT Settings.ini", "w+", encoding="utf-8", errors="ignore") as INI_PACT:
            INI_PACT.writelines(INI_Settings)


pact_ini_create()
# Use optionxform = str to preserve INI formatting. | Set comment_prefixes to unused char to keep INI comments.
PACT_config = configparser.ConfigParser(allow_no_value=True, comment_prefixes="$")
PACT_config.optionxform = str  # type: ignore
PACT_config.read("PACT Settings.ini")
PACT_Date = "290323"  # DDMMYY
PACT_Current = "PACT v1.75"


def pact_ini_update(section: str, value: str):  # Convenience function for checking & writing to INI.
    PACT_config["MAIN"][section] = value

    with open("PACT Settings.ini", "w+", encoding="utf-8", errors="ignore") as INI_PACT:
        PACT_config.write(INI_PACT)


def pact_log_update(log_message):
    with open("PACT Journal.log", "a", encoding="utf-8", errors="ignore") as LOG_PACT:
        LOG_PACT.write(log_message)

    # Delete journal if older than set amount of days.
    PACT_folder = os.getcwd()
    journal_name = "PACT Journal.log"
    journal_path = os.path.join(PACT_folder, journal_name)
    journal_age = time.time() - os.path.getmtime(journal_path)
    journal_age_days = journal_age / (24 * 3600)
    if journal_age_days > info.Journal_Expiration:
        os.remove(journal_path)


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
Err_Invalid_LO_File = """
❌ ERROR : CANNOT PROCESS LOAD ORDER FILE FOR XEDIT IN THIS SITUATION!")
   You have to set your load order file path to loadorder.txt and NOT plugins.txt")
   This is so PACT can detect the right game. Change the load order file path and try again.")
"""


def pact_update_check(PACT_config, PACT_Current):
    if PACT_config.getboolean("MAIN", "Update Check"):
        print("❓ CHECKING FOR ANY NEW PLUGIN AUTO CLEANING TOOL (PACT) UPDATES...")
        print("   (You can disable this check in the EXE or PACT Settings.ini) \n")
        try:
            response = requests.get("https://api.github.com/repos/GuidanceOfGrace/XEdit-PACT/releases/latest")  # type: ignore
            PACT_Received = response.json()["name"]
            if PACT_Received == PACT_Current:
                print("\n✔️ You have the latest version of PACT!")
                return True
            else:
                print(Warn_Outdated_PACT)
                return False
        except (OSError, requests.exceptions.RequestException):
            print(Warn_PACT_Update_Failed)
        print("===============================================================================")
    else:
        print("\n❌ NOTICE: UPDATE CHECK IS DISABLED IN PACT INI SETTINGS \n")
    return False


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
    Journal_Expiration = 7
    Cleaning_Timeout = 300

    MO2Mode = FNVMode = FO4Mode = SSEMode = False
    xedit_list_newvegas = ("fnvedit.exe", "fnvedit64.exe")
    xedit_list_fallout4 = ("fo4edit.exe", "fo4edit64.exe", "fo4vredit.exe")
    xedit_list_skyrimse = ("sseedit.exe", "sseedit64.exe", "tes5vredit.exe")
    xedit_list_universal = ("xedit.exe", "xedit64.exe", "xfoedit.exe", "xfoedit64.exe")
    xedit_list_specific = xedit_list_newvegas + xedit_list_fallout4 + xedit_list_skyrimse

    clean_results_UDR = []  # Undisabled References
    clean_results_ITM = []  # Identical To Master
    clean_results_NVM = []  # Deleted Navmeshes
    clean_failed_list = []  # Cleaning Failed
    plugins_processed = 0
    plugins_cleaned = 0

    LCL_skip_list = []
    if not os.path.exists("PACT Ignore.txt"):  # Local plugin skip / ignore list.
        with open("PACT Ignore.txt", "w+", encoding="utf-8", errors="ignore") as PACT_Ignore:
            PACT_Ignore.write("Write plugin names you want PACT to ignore here. (ONE PLUGIN PER LINE)\n")
    else:
        with open("PACT Ignore.txt", "r+", encoding="utf-8", errors="ignore") as PACT_Ignore:
            LCL_skip_list = [line.strip() for line in PACT_Ignore.readlines()[1:]]

    # HARD EXCLUDE PLUGINS PER GAME HERE
    FNV_skip_list = ["", "FalloutNV.esm", "DeadMoney.esm", "OldWorldBlues.esm", "HonestHearts.esm", "LonesomeRoad.esm", "TribalPack.esm", "MercenaryPack.esm",
                     "ClassicPack.esm", "CaravanPack.esm", "GunRunnersArsenal.esm", "Unofficial Patch NVSE Plus.esp"]

    FO4_skip_list = ["", "Fallout4.esm", "DLCCoast.esm", "DLCNukaWorld.esm", "DLCRobot.esm", "DLCworkshop01.esm", "DLCworkshop02.esm", "DLCworkshop03.esm",
                     "Unofficial Fallout 4 Patch.esp", "PPF.esm", "PRP.esp", "PRP-Compat", "SS2.esm", "SS2_XPAC_Chapter2.esm"]

    SSE_skip_list = ["", "Skyrim.esm", "Update.esm", "HearthFires.esm", "Dragonborn.esm", "Dawnguard.esm", "Unofficial Skyrim Special Edition Patch.esp"]

    VIP_skip_list = FNV_skip_list + FO4_skip_list + SSE_skip_list


info = Info()


def pact_update_settings():
    set_info_values_from_config()
    validate_cleaning_timeout()
    validate_journal_expiration()


def set_info_values_from_config():
    info.LOAD_ORDER_PATH = PACT_config["MAIN"]["LoadOrder TXT"]
    info.LOAD_ORDER_TXT = os.path.basename(info.LOAD_ORDER_PATH)
    info.XEDIT_PATH = PACT_config["MAIN"]["XEDIT EXE"]
    info.XEDIT_EXE = os.path.basename(info.XEDIT_PATH)
    info.MO2_PATH = PACT_config["MAIN"]["MO2 EXE"]
    info.MO2_EXE = os.path.basename(info.MO2_PATH)
    info.Cleaning_Timeout = int(PACT_config["MAIN"]["Cleaning Timeout"])
    info.Journal_Expiration = int(PACT_config["MAIN"]["Journal Expiration"])


def validate_cleaning_timeout():
    if not isinstance(info.Cleaning_Timeout, int):
        print_error_and_exit_settings("CLEANING TIMEOUT VALUE", "a valid positive number")
    elif info.Cleaning_Timeout < 30:
        print_error_and_exit_settings("CLEANING TIMEOUT VALUE", "at least 30 seconds or more")


def validate_journal_expiration():
    if not isinstance(info.Journal_Expiration, int):
        print_error_and_exit_settings("JOURNAL EXPIRATION VALUE", "a valid positive number")
    elif info.Journal_Expiration < 1:
        print_error_and_exit_settings("JOURNAL EXPIRATION VALUE", "at least 1 day or more")


def print_error_and_exit_settings(value_name, required_value):
    print(f"❌ ERROR : {value_name} IN PACT SETTINGS IS NOT VALID.")
    print(f"   Please change {value_name} to {required_value}.")
    os.system("pause")
    sys.exit()


pact_update_settings()
XEDIT_LOG_TXT = str(info.XEDIT_PATH).replace('.exe', '_log.txt')
XEDIT_EXC_LOG = str(info.XEDIT_PATH).replace('.exe', 'Exception.log')


# Make sure Mod Organizer 2 is not already running.
def check_process_mo2():
    pact_update_settings()
    if os.path.exists(info.MO2_PATH):
        mo2_procs = [proc for proc in psutil.process_iter(attrs=['pid', 'name']) if str(info.MO2_EXE).lower() in proc.info['name'].lower()]  # type: ignore
        for proc in mo2_procs:
            if str(info.MO2_EXE).lower() in proc.info['name'].lower():  # type: ignore
                print("\n❌ ERROR : CANNOT START PACT WHILE MOD ORGANIZER 2 IS ALREADY RUNNING!")
                print("   PLEASE CLOSE MO2 AND RUN PACT AGAIN! (DO NOT RUN PACT THROUGH MO2)")
                os.system("pause")
                sys.exit()


# Clear xedit log files to check them for each plugin separately.
def clear_xedit_logs(XEDIT_LOG_TXT, XEDIT_EXC_LOG):
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


# Make sure right XEDIT is running for the right game.
def check_settings_integrity():
    pact_update_settings()
    check_required_file_paths()
    check_mo2_mode()
    check_xedit_exe()


def check_required_file_paths():
    if os.path.exists(info.LOAD_ORDER_PATH) and os.path.exists(info.XEDIT_PATH):
        print("✔️ REQUIRED FILE PATHS FOUND! CHECKING IF INI SETTINGS ARE CORRECT...")
    else:
        print(Warn_Invalid_INI_Path)
        os.system("pause")
        sys.exit()


def check_mo2_mode():
    if os.path.exists(info.MO2_PATH):
        info.MO2Mode = True
    else:
        info.MO2Mode = False


def check_xedit_exe():
    if str(info.XEDIT_EXE).lower() not in info.xedit_list_universal:
        with open(info.LOAD_ORDER_PATH, "r", encoding="utf-8", errors="ignore") as LO_Check:
            LO_Plugins = LO_Check.read()
            check_game_exe(LO_Plugins, "FalloutNV.esm", info.xedit_list_newvegas)
            check_game_exe(LO_Plugins, "Fallout4.esm", info.xedit_list_fallout4)
            check_game_exe(LO_Plugins, "Skyrim.esm", info.xedit_list_skyrimse)
    elif "loadorder" not in str(info.LOAD_ORDER_PATH) and str(info.XEDIT_EXE).lower() in info.xedit_list_universal:
        print(Err_Invalid_LO_File)
        os.system("pause")
        sys.exit()


def check_game_exe(LO_Plugins, esm_file, xedit_list):
    if esm_file in LO_Plugins and str(info.XEDIT_EXE).lower() not in xedit_list:
        print(Warn_Invalid_INI_Setup)
        os.system("pause")
        sys.exit()


def generate_bat_command(plugin_name):
    bat_command = ""

    if info.MO2Mode and str(info.XEDIT_EXE).lower() in info.xedit_list_specific:
        bat_command = f'"{info.MO2_PATH}" run "{info.XEDIT_PATH}" -a "-QAC -autoexit -autoload \\"{plugin_name}\\""'

    elif not info.MO2Mode and str(info.XEDIT_EXE).lower() in info.xedit_list_specific:
        bat_command = f'"{info.XEDIT_PATH}" -a -QAC -autoexit -autoload "{plugin_name}"'

    if "loadorder" in str(info.LOAD_ORDER_PATH) and str(info.XEDIT_EXE).lower() in info.xedit_list_universal:
        mode = check_mode()

        if mode:
            if info.MO2Mode:
                bat_command = f'"{info.MO2_PATH}" run "{info.XEDIT_PATH}" -a "-{mode} -QAC -autoexit -autoload \\"{plugin_name}\\""'
            else:
                bat_command = f'"{info.XEDIT_PATH}" -a -{mode} -QAC -autoexit -autoload "{plugin_name}"'

    elif "loadorder" not in str(info.LOAD_ORDER_PATH).lower() and str(info.XEDIT_EXE).lower() in info.xedit_list_universal:
        print(Err_Invalid_LO_File)
        os.system("pause")
        sys.exit()

    if not bat_command:
        print_error_and_exit_cleaning()

    return bat_command


"""# Define custom exceptions
class XEditError(Exception):
    pass

class XEditTimeout(XEditError):
    pass

class XEditEmptyOrMissingRequirements(XEditError):
    pass"""


def get_xedit_procs() -> List[psutil.Process]:
    return [proc for proc in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent', 'create_time']) if 'edit.exe' in proc.info['name'].lower()]  # type: ignore


def handle_low_cpu_usage(proc: psutil.Process, plugin_name: str) -> bool:
    if proc.is_running():
        cpu_percent = proc.cpu_percent()
        if cpu_percent < 1:
            proc.kill()
            time.sleep(1)
            clear_xedit_logs(XEDIT_LOG_TXT, XEDIT_EXC_LOG)
            info.plugins_processed -= 1
            info.clean_failed_list.append(plugin_name)
            print("❌ ERROR: PLUGIN IS DISABLED OR HAS MISSING REQUIREMENTS! KILLING XEDIT AND ADDING PLUGIN TO IGNORE LIST...")
            with open("PACT Ignore.txt", "a", encoding="utf-8", errors="ignore") as PACT_IGNORE:
                PACT_IGNORE.write(f"\n{plugin_name}\n")
            return True
    return False


def handle_timeout(proc: psutil.Process, plugin_name: str) -> bool:
    create_time = proc.info['create_time']  # type: ignore
    if (time.time() - create_time) > info.Cleaning_Timeout:
        print("❌ ERROR: XEDIT TIMED OUT (CLEANING PROCESS TOOK TOO LONG)! KILLING XEDIT...")
        info.clean_failed_list.append(plugin_name)
        info.plugins_processed -= 1
        proc.kill()
        time.sleep(1)
        clear_xedit_logs(XEDIT_LOG_TXT, XEDIT_EXC_LOG)
        return True
    return False


def handle_missing_requirements(proc: psutil.Process, plugin_name: str, XEDIT_EXC_LOG: str) -> bool:
    try:
        xedit_exc_out = subprocess.check_output(['pwsh', '-command', f'Get-Content {XEDIT_EXC_LOG}'])
    except FileNotFoundError:
        xedit_exc_out = subprocess.check_output(['powershell', '-command', f'Get-Content {XEDIT_EXC_LOG}'])
    exception_check = xedit_exc_out.decode()
    if "which can not be found" in exception_check or "which it does not have" in exception_check:
        print("❌ ERROR: PLUGIN IS EMPTY OR HAS MISSING REQUIREMENTS! KILLING XEDIT AND ADDING PLUGIN TO IGNORE LIST...")
        with open("PACT Ignore.txt", "a", encoding="utf-8", errors="ignore") as PACT_IGNORE:
            PACT_IGNORE.write(f"\n{plugin_name}\n")
        info.clean_failed_list.append(plugin_name)
        info.plugins_processed -= 1
        proc.kill()
        time.sleep(1)
        clear_xedit_logs(XEDIT_LOG_TXT, XEDIT_EXC_LOG)
        return True
    return False


def check_mode():
    with open(info.LOAD_ORDER_PATH, "r", encoding="utf-8", errors="ignore") as lo_check:
        for elem in lo_check.readlines():
            if "Skyrim.esm" in elem:
                return "sse"
            elif "FalloutNV.esm" in elem:
                return "fnv"
            elif "Fallout4.esm" in elem:
                return "fo4"

    return None


def print_error_and_exit_cleaning():
    print("\n❓ ERROR : UNABLE TO START THE CLEANING PROCESS! WRONG INI SETTINGS OR FILE PATHS?")
    print("   If you're seeing this, make sure that your load order / xedit paths are correct.")
    print("   If problems continue, try a different load order file or xedit executable.")
    print("   If nothing works, please report this error to the PACT Nexus page.")
    os.system("pause")
    sys.exit()


def run_auto_cleaning(plugin_name, XEDIT_EXC_LOG):

    bat_command = generate_bat_command(plugin_name)

    clear_xedit_logs(XEDIT_LOG_TXT, XEDIT_EXC_LOG)
    print(f"\nCURRENTLY RUNNING : {bat_command}")
    bat_process = subprocess.Popen(bat_command)
    time.sleep(1)
    while bat_process.poll() is None:
        xedit_procs = get_xedit_procs()
        for proc in xedit_procs:
            if proc.info['name'].lower() == str(info.XEDIT_EXE).lower():  # type: ignore
                time.sleep(5)
                try:
                    if handle_low_cpu_usage(proc, plugin_name):
                        break
                except (PermissionError, psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, subprocess.CalledProcessError):
                    pass

            if proc.info['name'] == str(info.XEDIT_EXE):  # type: ignore
                if handle_timeout(proc, plugin_name):
                    break

                if proc.info['name'] == str(info.XEDIT_EXE) and os.path.exists(XEDIT_EXC_LOG):  # Check if xedit cannot clean. # type: ignore
                    try:
                        if handle_missing_requirements(proc, plugin_name, XEDIT_EXC_LOG):
                            break
                    except (PermissionError, psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, subprocess.CalledProcessError):
                        pass
        time.sleep(3)
    info.plugins_processed += 1


def check_cleaning_results(plugin_name, XEDIT_LOG_TXT):
    time.sleep(1)  # Wait to make sure xedit generates the logs.

    if os.path.exists(XEDIT_LOG_TXT):
        cleaned_something = False
        with open(XEDIT_LOG_TXT, "r", encoding="utf-8", errors="ignore") as XE_Check:
            Cleaning_Check = XE_Check.read()
            cleaned_something |= process_log_line(Cleaning_Check, "Undeleting:", plugin_name, info.clean_results_UDR, "Cleaned UDRs")
            cleaned_something |= process_log_line(Cleaning_Check, "Removing:", plugin_name, info.clean_results_ITM, "Cleaned ITMs")
            process_log_line(Cleaning_Check, "Skipping:", plugin_name, info.clean_results_NVM, "Found Deleted Navmeshes")

        if cleaned_something:
            info.plugins_cleaned += 1
        else:
            process_nothing_to_clean(plugin_name)
        clear_xedit_logs(XEDIT_LOG_TXT, XEDIT_EXC_LOG)


def process_log_line(Cleaning_Check, keyword, plugin_name, result_list, log_message):
    if keyword in Cleaning_Check:
        pact_log_update(f"\n{plugin_name} -> {log_message}")
        result_list.append(plugin_name)
        return True
    return False


def process_nothing_to_clean(plugin_name):
    pact_log_update(f"\n{plugin_name} -> NOTHING TO CLEAN")
    print("NOTHING TO CLEAN ! Adding plugin to PACT Ignore file...")
    with open("PACT Ignore.txt", "a", encoding="utf-8", errors="ignore") as PACT_IGNORE:
        PACT_IGNORE.write(f"\n{plugin_name}")
        info.LCL_skip_list.append(plugin_name)


def read_plugins(file_path, is_plugins_txt):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        file.seek(0)
        lines = file.readlines()[1:]
        if is_plugins_txt:
            return [line.strip().replace("*", "") for line in lines if "*" in line]
        else:
            return [line.strip() for line in lines if ".ghost" not in line]


def plugins_count():
    all_skip_list = info.VIP_skip_list + info.LCL_skip_list
    is_plugins_txt = "plugins.txt" in str(info.LOAD_ORDER_PATH)
    lo_plugin_list = read_plugins(info.LOAD_ORDER_PATH, is_plugins_txt)

    count_plugins = len(set(lo_plugin_list) - set(all_skip_list))
    return count_plugins, lo_plugin_list


def display_cleaning_results(title, items):
    if len(items) > 1:
        print(f"\n{title}:")
        for item in items:
            print(item)


def clean_plugins():
    all_skip_list = info.VIP_skip_list + info.LCL_skip_list

    pact_update_settings()

    if info.MO2Mode:
        print("✔️ MO2 EXECUTABLE WAS FOUND! SWITCHING TO MOD ORGANIZER 2 MODE...")
    else:
        print("❌ MO2 EXECUTABLE NOT SET OR FOUND. SWITCHING TO VORTEX MODE...")

    count_plugins, lo_plugin_list = plugins_count()

    print(f"✔️ CLEANING STARTED... ( PLUGINS TO CLEAN: {count_plugins} )")
    log_start = time.perf_counter()
    log_time = datetime.datetime.now()
    pact_log_update(f"\nSTARTED CLEANING PROCESS AT : {log_time}")
    count_cleaned = 0
    valid_extensions = ['.esl', '.esm', '.esp']

    for plugin in lo_plugin_list:
        if not any(plugin in elem for elem in all_skip_list) and any(ext in plugin.lower() for ext in valid_extensions):
            count_cleaned += 1
            run_auto_cleaning(plugin, XEDIT_EXC_LOG)
            check_cleaning_results(plugin, XEDIT_LOG_TXT)
            print(f"Finished cleaning : {plugin} ({count_cleaned} / {count_plugins})")

    elapsed_time = str(time.perf_counter() - log_start)[:3]
    summary = f"\n✔️ CLEANING COMPLETE! {info.XEDIT_EXE} processed all available plugins in {elapsed_time} seconds."
    details = f"\n   {info.XEDIT_EXE} successfully processed {info.plugins_processed} plugins and cleaned {info.plugins_cleaned} of them.\n"
    pact_log_update(summary + details)
    print(summary + details)

    display_cleaning_results(f"❌ {str(info.XEDIT_EXE).upper()} WAS UNABLE TO CLEAN THESE PLUGINS (Invalid Plugin Name or {str(info.XEDIT_EXE)} Timed Out)", info.clean_failed_list)
    display_cleaning_results(f"✔️ The following plugins had Undisabled Records and {info.XEDIT_EXE} properly disabled them", info.clean_results_UDR)
    display_cleaning_results(f"✔️ The following plugins had Identical To Master Records and {info.XEDIT_EXE} successfully cleaned them", info.clean_results_ITM)

    if len(info.clean_results_NVM) > 1:
        print("\n❌ CAUTION : The following plugins contain Deleted Navmeshes!")
        print("   Such plugins may cause navmesh related problems or crashes.")
        for elem in info.clean_results_NVM:
            print(elem)
    return True  # Required for running function check in PACT_Interface.


if __name__ == "__main__":  # AKA only autorun / do the following when NOT imported.
    pact_update_settings()
    check_process_mo2()
    check_settings_integrity()
    clean_plugins()
    os.system("pause")
