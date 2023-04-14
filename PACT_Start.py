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
from typing import Union, Any, List

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
    if isinstance(section, str) and isinstance(value, str):
        PACT_config["MAIN"][section] = value
    else:
        PACT_config["MAIN"][str(section)] = str(value)

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


# =================== UPDATE FUNCTION ===================
def pact_update_check():
    global PACT_Current
    PACT_Updated = False
    if PACT_config.getboolean("MAIN", "Update Check"):
        print("\n❓ CHECKING FOR ANY NEW PLUGIN AUTO CLEANING TOOL (PACT) UPDATES...")
        print("   (You can disable this check in the EXE or PACT Settings.ini) \n")
        try:
            response = requests.get("https://api.github.com/repos/GuidanceOfGrace/XEdit-PACT/releases/latest")  # type: ignore
            PACT_Received = response.json()["name"]
            PACT_Updated = PACT_Received == PACT_Current
            if PACT_Updated:
                print("\n✔️ You have the latest version of PACT!")
            else:
                print(Warn_Outdated_PACT)
            print("===============================================================================")
        except (OSError, requests.exceptions.RequestException):
            print(Warn_PACT_Update_Failed)
            print("===============================================================================")
    else:
        print("\n❌ NOTICE: UPDATE CHECK IS DISABLED IN PACT INI SETTINGS \n")
    return PACT_Updated

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

    clean_results_UDR: List[str] = field(default_factory=list)
    clean_results_ITM: List[str] = field(default_factory=list)
    clean_results_NVM: List[str] = field(default_factory=list)
    clean_failed_list: List[str] = field(default_factory=list)
    plugins_processed = 0
    plugins_cleaned = 0

    LCL_skip_list: List[str] = field(default_factory=list)

    FNV_skip_list: List[str] = field(init=False)
    FO4_skip_list: List[str] = field(init=False)
    SSE_skip_list: List[str] = field(init=False)
    VIP_skip_list: List[str] = field(init=False)

    def __post_init__(self):
        self.init_skip_list()
        self.init_game_skip_lists()

    def init_skip_list(self):
        if not os.path.exists("PACT Ignore.txt"):
            with open("PACT Ignore.txt", "w+", encoding="utf-8", errors="ignore") as PACT_Ignore:
                PACT_Ignore.write("Write plugin names you want PACT to ignore here. (ONE PLUGIN PER LINE)\n")
        else:
            with open("PACT Ignore.txt", "r+", encoding="utf-8", errors="ignore") as PACT_Ignore:
                self.LCL_skip_list = [line.strip() for line in PACT_Ignore.readlines()[1:]]

    def init_game_skip_lists(self):
        self.FNV_skip_list = ["", "FalloutNV.esm", "DeadMoney.esm", "OldWorldBlues.esm", "HonestHearts.esm", "LonesomeRoad.esm", "TribalPack.esm", "MercenaryPack.esm",
                              "ClassicPack.esm", "CaravanPack.esm", "GunRunnersArsenal.esm", "Unofficial Patch NVSE Plus.esp"]

        self.FO4_skip_list = ["", "Fallout4.esm", "DLCCoast.esm", "DLCNukaWorld.esm", "DLCRobot.esm", "DLCworkshop01.esm", "DLCworkshop02.esm", "DLCworkshop03.esm",
                               "Unofficial Fallout 4 Patch.esp", "PPF.esm", "PRP.esp", "PRP-Compat", "SS2.esm", "SS2_XPAC_Chapter2.esm"]

        self.SSE_skip_list = ["", "Skyrim.esm", "Update.esm", "HearthFires.esm", "Dragonborn.esm", "Dawnguard.esm", "Unofficial Skyrim Special Edition Patch.esp"]

        self.VIP_skip_list = self.FNV_skip_list + self.FO4_skip_list + self.SSE_skip_list

info = Info()


def pact_update_settings():
    info.LOAD_ORDER_PATH = PACT_config["MAIN"]["LoadOrder TXT"]  # type: ignore
    info.LOAD_ORDER_TXT = os.path.basename(info.LOAD_ORDER_PATH)
    info.XEDIT_PATH = PACT_config["MAIN"]["XEDIT EXE"]  # type: ignore
    info.XEDIT_EXE = os.path.basename(info.XEDIT_PATH)
    info.MO2_PATH = PACT_config["MAIN"]["MO2 EXE"]  # type: ignore
    info.MO2_EXE = os.path.basename(info.MO2_PATH)
    info.Cleaning_Timeout = int(PACT_config["MAIN"]["Cleaning Timeout"])  # type: ignore
    info.Journal_Expiration = int(PACT_config["MAIN"]["Journal Expiration"])  # type: ignore

    if not isinstance(info.Cleaning_Timeout, int):
        print("❌ ERROR : CLEANING TIMEOUT VALUE IN PACT SETTINGS IS NOT VALID.")
        print("   Please change Cleaning Timeout to a valid positive number.")
        os.system("pause")
        sys.exit()
    elif info.Cleaning_Timeout < 30:
        print("❌ ERROR : CLEANING TIMEOUT VALUE IN PACT SETTINGS IS TOO SMALL.")
        print("   Cleaning Timeout must be set to at least 30 seconds or more.")
        os.system("pause")
        sys.exit()

    if not isinstance(info.Journal_Expiration, int):
        print("❌ ERROR : JOURNAL EXPIRATION VALUE IN PACT SETTINGS IS NOT VALID.")
        print("   Please change Journal Expiration to a valid positive number.")
        os.system("pause")
        sys.exit()
    elif info.Journal_Expiration < 1:
        print("❌ ERROR : JOURNAL EXPIRATION VALUE IN PACT SETTINGS IS TOO SMALL.")
        print("   Journal Expiration must be set to at least 1 day or more.")
        os.system("pause")
        sys.exit()


pact_update_settings()
def get_log_filename(xedit_exe_path, suffix):
    return str(xedit_exe_path.with_name(f"{xedit_exe_path.stem}{suffix}"))

xedit_exe_path = Path(info.XEDIT_PATH)
XEDIT_LOG_TXT = get_log_filename(xedit_exe_path, "_log.txt")
XEDIT_EXC_LOG = get_log_filename(xedit_exe_path, "Exception.log")


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
def clear_xedit_logs():
    global XEDIT_LOG_TXT, XEDIT_EXC_LOG

    def remove_log(log_path, log_name):
        try:
            if os.path.exists(log_path):
                os.remove(log_path)
        except PermissionError:
            print(f"❌ ERROR: CANNOT CLEAR {log_name} LOG. Try running PACT in Admin Mode.")
            print("   If problems continue, please report this to the PACT Nexus page.")
            os.system("pause")
            sys.exit()

    remove_log(XEDIT_LOG_TXT, str(Path(XEDIT_LOG_TXT).name))
    remove_log(XEDIT_EXC_LOG, str(Path(XEDIT_EXC_LOG).name))


# Make sure right XEDIT is running for the right game.
def check_settings_integrity():
    pact_update_settings()

    if not (os.path.exists(info.LOAD_ORDER_PATH) and os.path.exists(info.XEDIT_PATH)):
        print(Warn_Invalid_INI_Path)
        os.system("pause")
        sys.exit()

    info.MO2Mode = os.path.exists(info.MO2_PATH)

    xedit_exe_lower = str(info.XEDIT_EXE).lower()

    if xedit_exe_lower not in info.xedit_list_universal:
        game_modes = {'FalloutNV.esm': info.xedit_list_newvegas,
                      'Fallout4.esm': info.xedit_list_fallout4,
                      'Skyrim.esm': info.xedit_list_skyrimse}

        with open(info.LOAD_ORDER_PATH, "r", encoding="utf-8", errors="ignore") as LO_Check:
            LO_Plugins = LO_Check.read()

            for esm, xedit_list in game_modes.items():
                if esm in LO_Plugins and xedit_exe_lower not in xedit_list:
                    print(Warn_Invalid_INI_Setup)
                    os.system("pause")
                    sys.exit()

    elif "loadorder" not in str(info.LOAD_ORDER_PATH) and xedit_exe_lower in info.xedit_list_universal:
        print(Err_Invalid_LO_File)
        os.system("pause")
        sys.exit()


def gen_bat_command(plugin_name):
    global XEDIT_LOG_TXT

    bat_command = ""
    xedit_specific = str(info.XEDIT_EXE).lower() in info.xedit_list_specific
    xedit_universal = str(info.XEDIT_EXE).lower() in info.xedit_list_universal

    if info.MO2Mode and xedit_specific:
        bat_command = f'"{info.MO2_PATH}" run "{info.XEDIT_PATH}" -a "-QAC -autoexit -autoload \\"{plugin_name}\\""'
    elif not info.MO2Mode and xedit_specific:
        bat_command = f'"{info.XEDIT_PATH}" -a -QAC -autoexit -autoload "{plugin_name}"'

    mode_found = False
    if "loadorder" in str(info.LOAD_ORDER_PATH) and xedit_universal:
        game_modes = {'Skyrim.esm': 'sse', 'FalloutNV.esm': 'fnv', 'Fallout4.esm': 'fo4'}

        with open(info.LOAD_ORDER_PATH, "r", encoding="utf-8", errors="ignore") as LO_Check:
            for line in LO_Check.readlines():
                for esm, mode in game_modes.items():
                    if esm in line:
                        XEDIT_LOG_TXT = str(info.XEDIT_PATH).replace('xEdit.exe', f'{mode.upper()}Edit_log.txt')
                        bat_option = f'"{info.XEDIT_PATH}" -a -{mode} -QAC -autoexit -autoload "{plugin_name}"'

                        if info.MO2Mode:
                            bat_command = f'"{info.MO2_PATH}" run {bat_option}'
                        else:
                            bat_command = bat_option

                        mode_found = True
                        break

                if mode_found:
                    break

    if not mode_found and xedit_universal:
        print(Err_Invalid_LO_File)
        os.system("pause")
        sys.exit()

    if not bat_command:
        print("\n❓ ERROR : UNABLE TO START THE CLEANING PROCESS! WRONG INI SETTINGS OR FILE PATHS?")
        print("   If you're seeing this, make sure that your load order / xedit paths are correct.")
        print("   If problems continue, try a different load order file or xedit executable.")
        print("   If nothing works, please report this error to the PACT Nexus page.")
        os.system("pause")
        sys.exit()

    return bat_command


def run_auto_cleaning(plugin_name):
    global XEDIT_LOG_TXT
    global XEDIT_EXC_LOG

    bat_command = gen_bat_command(plugin_name)

    clear_xedit_logs()
    print(f"\nCURRENTLY RUNNING : {bat_command}")
    bat_process = subprocess.Popen(bat_command)
    time.sleep(1)
    while bat_process.poll() is None:  # Check if xedit timed out or encountered errors while above subprocess.Popen() is running.
        xedit_procs = [proc for proc in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent', 'create_time']) if 'edit.exe' in proc.info['name'].lower()]  # type: ignore
        for proc in xedit_procs:
            if proc.info['name'].lower() == str(info.XEDIT_EXE).lower():  # type: ignore
                time.sleep(5)
                try:  # Note that xedit can stop at any moment and checking CPU usage on a dead process will crash.
                    if proc.is_running():  # Check CPU usage if xedit does nothing or gets interrupted by error.
                        cpu_percent = proc.cpu_percent()
                        if cpu_percent < 1:
                            proc.kill()
                            time.sleep(1)
                            clear_xedit_logs()
                            info.plugins_processed -= 1
                            info.clean_failed_list.append(plugin_name)
                            print("❌ ERROR : PLUGIN IS DISABLED OR HAS MISSING REQUIREMENTS! KILLING XEDIT AND ADDING PLUGIN TO IGNORE LIST...")
                            with open("PACT Ignore.txt", "a", encoding="utf-8", errors="ignore") as PACT_IGNORE:
                                PACT_IGNORE.write(f"\n{plugin_name}\n")
                            break
                except (PermissionError, psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, subprocess.CalledProcessError):
                    pass

            if proc.info['name'] == str(info.XEDIT_EXE):  # type: ignore
                try:
                    create_time = proc.info['create_time']  # type: ignore
                    if (time.time() - create_time) > info.Cleaning_Timeout:
                        print("❌ ERROR : XEDIT TIMED OUT (CLEANING PROCESS TOOK TOO LONG)! KILLING XEDIT...")
                        info.clean_failed_list.append(plugin_name)
                        info.plugins_processed -= 1
                        proc.kill()
                        time.sleep(1)
                        clear_xedit_logs()
                        break
                except (PermissionError, psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, subprocess.CalledProcessError):
                    print("❌ ERROR : COULD NOT KILL XEDIT PROCESS PLEASE RESTART THE CLEANING PROCESS...")  # Placeholder for now.
                    break

            if proc.info['name'] == str(info.XEDIT_EXE) and os.path.exists(XEDIT_EXC_LOG):  # Check if xedit cannot clean. # type: ignore
                try:
                    xedit_exc_out = subprocess.check_output(['powershell', '-command', f'Get-Content {XEDIT_EXC_LOG}'])
                    Exception_Check = xedit_exc_out.decode()  # Use this method since xedit is actively writing to it.
                    if "which can not be found" in Exception_Check or "which it does not have" in Exception_Check:
                        print("❌ ERROR : PLUGIN IS EMPTY OR HAS MISSING REQUIREMENTS! KILLING XEDIT AND ADDING PLUGIN TO IGNORE LIST...")
                        with open("PACT Ignore.txt", "a", encoding="utf-8", errors="ignore") as PACT_IGNORE:
                            PACT_IGNORE.write(f"\n{plugin_name}\n")
                            info.clean_failed_list.append(plugin_name)
                        info.plugins_processed -= 1
                        proc.kill()
                        time.sleep(1)
                        clear_xedit_logs()
                        break
                except (PermissionError, psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, subprocess.CalledProcessError):
                    pass
        time.sleep(3)
    info.plugins_processed += 1


def check_cleaning_results(plugin_name):
    global XEDIT_LOG_TXT
    global XEDIT_EXC_LOG
    time.sleep(1)  # Wait to make sure xedit generates the logs.

    if os.path.exists(XEDIT_LOG_TXT):
        cleaned_something = False
        results = {'UDRs': 'Undeleting:', 'ITMs': 'Removing:', 'NVMs': 'Skipping:'}
        categories = {'UDRs': info.clean_results_UDR, 'ITMs': info.clean_results_ITM, 'NVMs': info.clean_results_NVM}

        with open(XEDIT_LOG_TXT, "r", encoding="utf-8", errors="ignore") as XE_Check:
            Cleaning_Check = XE_Check.read()

            for result_type, keyword in results.items():
                if keyword in Cleaning_Check:
                    pact_log_update(f"\n{plugin_name} -> Cleaned {result_type}")
                    categories[result_type].append(plugin_name)
                    cleaned_something = True

            if cleaned_something:
                info.plugins_cleaned += 1
            else:
                pact_log_update(f"\n{plugin_name} -> NOTHING TO CLEAN")
                print("NOTHING TO CLEAN ! Adding plugin to PACT Ignore file...")

                with open("PACT Ignore.txt", "a", encoding="utf-8", errors="ignore") as PACT_IGNORE:
                    PACT_IGNORE.write(f"\n{plugin_name}")
                    info.LCL_skip_list.append(plugin_name)

        clear_xedit_logs()


def clean_plugins():
    all_skip_list = info.VIP_skip_list + info.LCL_skip_list
    pact_update_settings()

    if info.MO2Mode:
        print("✔️ MO2 EXECUTABLE WAS FOUND! SWITCHING TO MOD ORGANIZER 2 MODE...")
    else:
        print("❌ MO2 EXECUTABLE NOT SET OR FOUND. SWITCHING TO VORTEX MODE...")

    load_order_plugin_list = get_load_order_plugin_list(info.LOAD_ORDER_PATH)

    count_plugins = len(set(load_order_plugin_list) - set(all_skip_list))
    print(f"✔️ CLEANING STARTED... ( PLUGINS TO CLEAN: {count_plugins} )")
    log_start = time.perf_counter()
    log_time = datetime.datetime.now()
    pact_log_update(f"\nSTARTED CLEANING PROCESS AT : {log_time}")

    count_cleaned = 0
    for plugin in load_order_plugin_list:
        if not any(plugin in elem for elem in all_skip_list) and any(ext in plugin.lower() for ext in ['.esl', '.esm', '.esp']):
            count_cleaned += 1
            run_auto_cleaning(plugin)
            check_cleaning_results(plugin)
            print(f"Finished cleaning : {plugin} ({count_cleaned} / {count_plugins})")

    show_cleaning_stats(log_start, count_cleaned, count_plugins)
    show_cleaning_results()
    return True  # Required for running function check in PACT_Interface.


def get_load_order_plugin_list(load_order_path):
    with open(load_order_path, "r", encoding="utf-8", errors="ignore") as LO_File:
        LO_File.seek(0)
        load_order_plugin_list = []
        load_order_list = LO_File.readlines()[1:]

        if "plugins.txt" in str(load_order_path):
            for line in load_order_list:
                if "*" in line:
                    line = line.strip().replace("*", "")
                    load_order_plugin_list.append(line)
        else:
            for line in load_order_list:
                line = line.strip()
                if ".ghost" not in line:
                    load_order_plugin_list.append(line)

    return load_order_plugin_list


def show_cleaning_stats(log_start, count_cleaned, count_plugins):
    elapsed_time = time.perf_counter() - log_start
    print(f"\n✔️ CLEANING COMPLETE! {info.XEDIT_EXE} processed all available plugins in {elapsed_time:.3f} seconds.")
    print(f"\n   {info.XEDIT_EXE} successfully processed {info.plugins_processed} plugins and cleaned {info.plugins_cleaned} of them.\n")


def show_cleaning_results():
    if len(info.clean_failed_list) > 1:
        print(f"\n❌ {str(info.XEDIT_EXE).upper()} WAS UNABLE TO CLEAN THESE PLUGINS: (Invalid Plugin Name or {info.XEDIT_EXE} Timed Out):")
        for elem in info.clean_failed_list:
            print(elem)

    if len(info.clean_results_UDR) > 1:
        print(f"\n✔️ The following plugins had Undisabled Records and {info.XEDIT_EXE} properly disabled them:")
        for elem in info.clean_results_UDR:
            print(elem)

    if len(info.clean_results_ITM) > 1:
        print(f"\n✔️ The following plugins had Identical To Master Records and {info.XEDIT_EXE} successfully cleaned them:")
        for elem in info.clean_results_ITM:
            print(elem)

    if len(info.clean_results_NVM) > 1:
        print("\n❌ CAUTION : The following plugins contain Deleted Navmeshes!")
        print("   Such plugins may cause navmesh related problems or crashes.")
        for elem in info.clean_results_NVM:
            print(elem)


if __name__ == "__main__":  # AKA only autorun / do the following when NOT imported.
    pact_update_settings()
    check_process_mo2()
    check_settings_integrity()
    clean_plugins()
    os.system("pause")
