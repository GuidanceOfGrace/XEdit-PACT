import os
import sys
import psutil
import shutil
import hashlib
import datetime
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QUrl, QTimer, QThread
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QFileDialog, QLabel, QLineEdit, QPushButton, QStyleFactory
from PACT_Start import (info, PACT_config, PACT_Current, pact_ini_update, pact_update_check, pact_update_settings, check_process_mo2, check_settings_integrity, clean_plugins)

import platform

current_platform = platform.system()
if current_platform == 'Windows':
    version = platform.release()
    if version.startswith('10') or version.startswith('11'):
        sys.argv += ['-platform', 'windows:darkmode=2']

'''TEMPLATES
QMessageBox.NoIcon | Question | Information | Warning | Critical
'''


class UiPACTMainWin(object):
    def __init__(self):
        super().__init__()  # Allow subclasses to inherit & extend behavior of parent class.
        QApplication.setStyle(QStyleFactory.create("Fusion"))
        self.InputField_JE = None
        self.InputLabel_JE = None
        self.InputField_CT = None
        self.InputLabel_CT = None
        self.configured_LO = False
        self.configured_MO2 = False
        self.configured_XEDIT = False

        self.ChkBT_UPDATE = None
        self.ChkBT_STATS = None
        self.LINE_SEPARATOR1 = None
        self.LBL_SETTINGS1 = None
        self.LBL_SETTINGS2 = None
        self.RegBT_BROWSE_LO = None
        self.RegBT_BROWSE_MO2 = None
        self.RegBT_BROWSE_XEDIT = None
        self.RegBT_CHECK_UPDATES = None
        self.RegBT_CLEAN_PLUGINS = None
        self.RegBT_RESTORE_BACKUP = None
        self.RegBT_BACKUP_PLUGINS = None
        self.RegBT_UPDATE_SETTINGS = None

        self.RegBT_HELP = None
        self.RegBT_EXIT = None
        self.RegBT_CHECK_UPDATES = None

        self.timer = QTimer()  # For CLEAN PLUGINS button auto check.
        self.timer.timeout.connect(self.timed_states)  # type: ignore
        self.timer.start(3000)  # In ms, will override QTimer.singleShot
        self.thread = None

    def setup_ui(self, PACT_WINDOW):
        # MAIN WINDOW
        PACT_WINDOW.setObjectName("PACT_WINDOW")
        PACT_WINDOW.setWindowTitle(f"Plugin Auto Cleaning Tool {PACT_Current[-4:]}")
        PACT_WINDOW.resize(640, 640)
        PACT_WINDOW.setMinimumSize(QtCore.QSize(640, 480))
        PACT_WINDOW.setMaximumSize(QtCore.QSize(640, 480))
        PACT_WINDOW.setWindowFlags(PACT_WINDOW.windowFlags() | Qt.WindowMinimizeButtonHint)  # type: ignore
        QApplication.setStyle(QStyleFactory.create("Fusion"))
        font_bold = QtGui.QFont()
        font_bold.setPointSize(10)
        font_bold.setBold(True)

        # ==================== MAIN WINDOW ITEMS =====================
        # TOP

        # Button - Check Updates
        self.RegBT_CHECK_UPDATES = QtWidgets.QPushButton(PACT_WINDOW)
        self.RegBT_CHECK_UPDATES.setGeometry(QtCore.QRect(80, 50, 230, 32))
        self.RegBT_CHECK_UPDATES.setObjectName("RegBT_CHECK_UPDATES")
        self.RegBT_CHECK_UPDATES.setText("CHECK FOR UPDATES")
        self.RegBT_CHECK_UPDATES.clicked.connect(self.update_popup)

        # Button - Update Settings
        self.RegBT_UPDATE_SETTINGS = QPushButton("UPDATE SETTINGS", PACT_WINDOW)
        self.RegBT_UPDATE_SETTINGS.setGeometry(QtCore.QRect(330, 50, 230, 32))
        self.RegBT_UPDATE_SETTINGS.setObjectName("RegBT_UPDATE_SETTINGS")
        self.RegBT_UPDATE_SETTINGS.clicked.connect(self.update_settings)

        # Button - Browse Load Order
        self.RegBT_BROWSE_LO = QtWidgets.QPushButton(PACT_WINDOW)
        self.RegBT_BROWSE_LO.setGeometry(QtCore.QRect(80, 100, 150, 32))
        self.RegBT_BROWSE_LO.setObjectName("RegBT_BROWSE_LO")
        self.RegBT_BROWSE_LO.setText("SET LOAD ORDER FILE")
        self.RegBT_BROWSE_LO.setStyleSheet("color: black; background-color: lightyellow; border-radius: 5px; border: 1px solid gray;")
        self.RegBT_BROWSE_LO.clicked.connect(self.select_file_lo)  # type: ignore
        if "loadorder" in PACT_config["MAIN"]["LoadOrder TXT"] or "plugins" in PACT_config["MAIN"]["LoadOrder TXT"]:
            self.RegBT_BROWSE_LO.setStyleSheet("color: black; background-color: lightgreen; border-radius: 5px; border: 1px solid gray;")
            self.RegBT_BROWSE_LO.setText("✔️ LOAD ORDER FILE SET")
            self.configured_LO = True

        # Button - Browse MO2 EXE
        self.RegBT_BROWSE_MO2 = QtWidgets.QPushButton(PACT_WINDOW)
        self.RegBT_BROWSE_MO2.setGeometry(QtCore.QRect(245, 100, 150, 32))
        self.RegBT_BROWSE_MO2.setObjectName("RegBT_BROWSE_MO2")
        self.RegBT_BROWSE_MO2.setText("SET MO2 EXECUTABLE")
        self.RegBT_BROWSE_MO2.setStyleSheet("color: black; background-color: lightyellow; border-radius: 5px; border: 1px solid gray;")
        self.RegBT_BROWSE_MO2.clicked.connect(self.select_file_mo2)  # type: ignore
        if "ModOrganizer" in PACT_config["MAIN"]["MO2 EXE"]:
            self.RegBT_BROWSE_MO2.setStyleSheet("color: black; background-color: lightgreen; border-radius: 5px; border: 1px solid gray;")
            self.RegBT_BROWSE_MO2.setText("✔️ MO2 EXECUTABLE SET")
            self.configured_MO2 = True

        # Button - Browse XEDIT EXE
        self.RegBT_BROWSE_XEDIT = QtWidgets.QPushButton(PACT_WINDOW)
        self.RegBT_BROWSE_XEDIT.setGeometry(QtCore.QRect(410, 100, 150, 32))
        self.RegBT_BROWSE_XEDIT.setObjectName("RegBT_BROWSE_XEDIT")
        self.RegBT_BROWSE_XEDIT.setText("SET XEDIT EXECUTABLE")
        self.RegBT_BROWSE_XEDIT.setStyleSheet("color: black; background-color: lightyellow; border-radius: 5px; border: 1px solid gray;")
        self.RegBT_BROWSE_XEDIT.clicked.connect(self.select_file_xedit)  # type: ignore
        if "Edit" in PACT_config["MAIN"]["XEDIT EXE"]:
            self.RegBT_BROWSE_XEDIT.setStyleSheet("color: black; background-color: lightgreen; border-radius: 5px; border: 1px solid gray;")
            self.RegBT_BROWSE_XEDIT.setText("✔️ XEDIT EXECUTABLE SET")
            self.configured_XEDIT = True

        # SEPARATOR LINE 1
        self.LINE_SEPARATOR1 = QtWidgets.QFrame(PACT_WINDOW)
        self.LINE_SEPARATOR1.setGeometry(QtCore.QRect(80, 150, 480, 20))
        self.LINE_SEPARATOR1.setFrameShape(QtWidgets.QFrame.Shape.HLine)  # type: ignore
        self.LINE_SEPARATOR1.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)  # type: ignore
        self.LINE_SEPARATOR1.setObjectName("LINE_SEPARATOR1")

        # SEPARATOR TEXT 1
        self.LBL_SETTINGS1 = QtWidgets.QLabel(PACT_WINDOW)
        self.LBL_SETTINGS1.setGeometry(QtCore.QRect(50, 175, 550, 24))
        self.LBL_SETTINGS1.setText("YOU NEED TO SET YOUR LOAD ORDER FILE AND XEDIT EXECUTABLE BEFORE CLEANING")
        self.LBL_SETTINGS1.setFont(font_bold)
        self.LBL_SETTINGS1.setObjectName("LBL_NOTE_SET")

        # SEPARATOR TEXT 2
        self.LBL_SETTINGS2 = QtWidgets.QLabel(PACT_WINDOW)
        self.LBL_SETTINGS2.setGeometry(QtCore.QRect(120, 200, 550, 24))
        self.LBL_SETTINGS2.setText("( MOD ORGANIZER 2 USERS ALSO NEED TO SET MO2 EXECUTABLE )")
        self.LBL_SETTINGS2.setFont(font_bold)
        self.LBL_SETTINGS2.setObjectName("LBL_NOTE_MO2")

        # MAIN

        # Button - Backup Plugins
        self.RegBT_BACKUP_PLUGINS = QPushButton("BACKUP PLUGINS", PACT_WINDOW)
        self.RegBT_BACKUP_PLUGINS.setGeometry(QtCore.QRect(80, 250, 230, 32))
        self.RegBT_BACKUP_PLUGINS.setObjectName("RegBT_BACKUP_PLUGINS")
        self.RegBT_BACKUP_PLUGINS.clicked.connect(self.backup_popup)
        self.RegBT_BACKUP_PLUGINS.setFont(font_bold)

        # Button - Restore Backup
        self.RegBT_RESTORE_BACKUP = QPushButton("RESTORE BACKUP", PACT_WINDOW)
        self.RegBT_RESTORE_BACKUP.setGeometry(QtCore.QRect(330, 250, 230, 32))
        self.RegBT_RESTORE_BACKUP.setObjectName("RegBT_RESTORE_BACKUP")
        self.RegBT_RESTORE_BACKUP.clicked.connect(self.restore_popup)
        self.RegBT_RESTORE_BACKUP.setFont(font_bold)

        # Input - Cleaning Timeout
        self.InputLabel_CT = QLabel("Cleaning Timeout\n     (in seconds)", PACT_WINDOW)
        self.InputLabel_CT.setGeometry(QtCore.QRect(105, 300, 100, 48))
        self.InputField_CT = QLineEdit(PACT_WINDOW)
        self.InputField_CT.setGeometry(QtCore.QRect(130, 350, 50, 24))
        self.InputField_CT.setValidator(QtGui.QIntValidator())
        self.InputField_CT.setText(str(info.Cleaning_Timeout))

        # Input - Journal Expiration
        self.InputLabel_JE = QLabel("Journal Expiration\n         (in days)", PACT_WINDOW)
        self.InputLabel_JE.setGeometry(QtCore.QRect(440, 300, 100, 48))
        self.InputField_JE = QLineEdit(PACT_WINDOW)
        self.InputField_JE.setGeometry(QtCore.QRect(465, 350, 50, 24))
        self.InputField_JE.setValidator(QtGui.QIntValidator())
        self.InputField_JE.setText(str(info.Journal_Expiration))

        # Button - CLEAN PLUGINS
        self.RegBT_CLEAN_PLUGINS = QtWidgets.QPushButton(PACT_WINDOW)
        self.RegBT_CLEAN_PLUGINS.setGeometry(QtCore.QRect(245, 325, 150, 32))
        self.RegBT_CLEAN_PLUGINS.setObjectName("RegBT_CLEAN_PLUGINS")
        self.RegBT_CLEAN_PLUGINS.setFont(font_bold)
        self.RegBT_CLEAN_PLUGINS.setEnabled(False)  # type: ignore
        self.RegBT_CLEAN_PLUGINS.setText("START CLEANING")
        self.RegBT_CLEAN_PLUGINS.setStyleSheet("background-color: lightgray; border-radius: 5px; border: 1px solid gray;")  # type: ignore
        self.RegBT_CLEAN_PLUGINS.clicked.connect(self.start_cleaning)  # type: ignore

        # BOTTOM

        # Button - HELP
        self.RegBT_HELP = QtWidgets.QPushButton(PACT_WINDOW)
        self.RegBT_HELP.setGeometry(QtCore.QRect(20, 440, 110, 24))
        self.RegBT_HELP.setObjectName("RegBT_HELP")
        self.RegBT_HELP.setText("HELP")
        self.RegBT_HELP.setToolTip("How To Use PACT GUI")
        self.RegBT_HELP.clicked.connect(self.help_popup)  # type: ignore

        # Button - EXIT
        self.RegBT_EXIT = QtWidgets.QPushButton(PACT_WINDOW)
        self.RegBT_EXIT.setGeometry(QtCore.QRect(510, 440, 110, 24))
        self.RegBT_EXIT.setObjectName("RegBT_EXIT")
        self.RegBT_EXIT.setText("EXIT")
        self.RegBT_EXIT.setToolTip("Exit PACT GUI")
        self.RegBT_EXIT.clicked.connect(PACT_WINDOW.close)  # type: ignore

    # ============== CLEAN PLUGINS BUTTON STATES ================

    def timed_states(self):
        xedit_procs = [proc for proc in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent', 'create_time']) if 'edit.exe' in proc.info['name'].lower()]
        xedit_running = False
        for proc in xedit_procs:
            if proc.info['name'].lower() == str(info.XEDIT_EXE).lower():
                xedit_running = True

        if self.thread is None:
            self.RegBT_BROWSE_LO.setEnabled(True)
            self.RegBT_BROWSE_MO2.setEnabled(True)
            self.RegBT_BROWSE_XEDIT.setEnabled(True)
            self.RegBT_EXIT.setEnabled(True)
            if self.configured_LO and self.configured_XEDIT and xedit_running is False:
                self.RegBT_CLEAN_PLUGINS.setEnabled(True)
                self.RegBT_CLEAN_PLUGINS.setText("START CLEANING")
                self.RegBT_CLEAN_PLUGINS.setStyleSheet("color: black; background-color: lightblue; border-radius: 5px; border: 1px solid gray;")
                self.RegBT_CLEAN_PLUGINS.clicked.disconnect()
                self.RegBT_CLEAN_PLUGINS.clicked.connect(self.start_cleaning)
        else:
            self.RegBT_BROWSE_LO.setEnabled(False)
            self.RegBT_BROWSE_MO2.setEnabled(False)
            self.RegBT_BROWSE_XEDIT.setEnabled(False)
            self.RegBT_EXIT.setEnabled(False)
            thread = PactThread()
            if thread.cleaning_done is True:
                thread.terminate()
                thread.wait()
                self.thread = None
            if "STOP CLEANING" not in self.RegBT_CLEAN_PLUGINS.text() and xedit_running is False:
                self.RegBT_CLEAN_PLUGINS.setText("START CLEANING")
                self.RegBT_CLEAN_PLUGINS.setStyleSheet("color: black; background-color: lightblue; border-radius: 5px; border: 1px solid gray;")

    def start_cleaning(self):
        if self.thread is None:
            self.thread = PactThread()
            self.thread.start()
            self.RegBT_CLEAN_PLUGINS.setText("STOP CLEANING")
            self.RegBT_CLEAN_PLUGINS.setStyleSheet("color: black; background-color: pink; border-radius: 5px; border: 1px solid gray;")  # type: ignore
            self.RegBT_CLEAN_PLUGINS.clicked.disconnect()
            self.RegBT_CLEAN_PLUGINS.clicked.connect(self.stop_cleaning)

    def stop_cleaning(self):
        if self.thread is not None:
            self.thread.terminate()
            self.thread.wait()
            self.thread = None
            self.RegBT_CLEAN_PLUGINS.setEnabled(False)
            self.RegBT_CLEAN_PLUGINS.setText("...STOPPING...")
            self.RegBT_CLEAN_PLUGINS.setStyleSheet("color: black; background-color: orange; border-radius: 5px; border: 1px solid gray;")  # type: ignore
            print("\n❌ CLEANING STOPPED! PLEASE WAIT UNTIL ALL RUNNING PROGRAMS ARE CLOSED BEFORE STARTING AGAIN!\n")

    # ================== POP-UPS / WARNINGS =====================

    backup_box_msg = """Press OK to select the ROOT FOLDER that contains all plugins you want to create a backup of. (Example: Fallout 4 / DATA folder.) This is how BACKUP works:

FIRST BACKUP : PACT will look through all subfolders from the selected folder and copy all esm / esp / esl files to PACT BACKUP / Primary Backup folder.

ALL BACKUPS AFTER : PACT will compare plugin file hashes with the primary backup. If any plugin has been modified/cleaned, it will create a new backup
and remove the plugin name from the ignore list in PACT Ignore.txt file.

NOTE that this method will NOT backup any NEW plugins to Primary Backup.
If you want to do this, you need to manually take plugins from other backup
folders and move them to the Primary Backup folder yourself."""

    restore_box_msg = """Press OK to select the ROOT FOLDER where you want to restore plugins from Primary Backup. (Example: Fallout 4 / DATA folder.) This is how RESTORE works:

PACT will take all esm/esp/esl plugins from the PACT BACKUP / Primary Backup folder and look them up in all subfolders from the selected folder.

IF a plugin match is found, PACT will replace that plugin with the one from the Primary Backup folder. The original backup of that plugin will still remain.

NOTE that this method will NOT restore plugins from OTHER backup folders.
If you want to do this, you need to manually copy plugins from other backup
folders to the Primary Backup folder, overwrite plugins and then run RESTORE."""

    help_box_msg = """If you have trouble running this program or wish to submit your PACT logs for additional help, join the Collective Modding Discord server.
    Please READ the #👋-welcome2 channel, react with the '2' emoji on the bot message there and leave your feedback in #💡-poet-guides-mods channel.
    Press OK to open the server link in your internet browser."""

    # ================= PLUGIN BACKUP / RESTORE =================
    # @staticmethod recommended for func that don't call "self".

    @staticmethod
    def backup_popup():
        Box_Backup = QtWidgets.QMessageBox()
        Box_Backup.setIcon(QtWidgets.QMessageBox.Question)  # type: ignore
        Box_Backup.setWindowTitle("PACT Backup")
        Box_Backup.setText(UiPACTMainWin.backup_box_msg)  # RESERVED | Box_Backup.setInformativeText("...")
        Box_Backup.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)  # type: ignore
        if Box_Backup.exec() != QtWidgets.QMessageBox.Cancel:  # type: ignore
            UiPACTMainWin.pact_create_backup()

    @staticmethod
    def pact_create_backup():
        plugins_folder = QFileDialog.getExistingDirectory()
        if plugins_folder:
            primary_backup = os.path.join("PACT BACKUP", "Primary Backup")
            if not os.path.exists(primary_backup):
                os.makedirs(primary_backup, exist_ok=True)
                print("CREATING PRIMARY BACKUP, PLEASE WAIT...")
                for root, dirs, files in os.walk(plugins_folder):
                    for file in files:
                        if file.endswith('.esm') or file.endswith('.esp') or file.endswith('.esl'):
                            try:
                                plugin_path = os.path.join(root, file)
                                copy_path = os.path.join(primary_backup, file)
                                shutil.copy2(plugin_path, copy_path)
                            except (PermissionError, OSError):
                                print(f"❌ ERROR : Unable to create a backup for {file}")
                                print("   You can run PACT in admin mode and try again.")
                                continue
                print("PRIMARY BACKUP CREATED!")
            else:
                print("PROCESSING ADDITIONAL BACKUP, PLEASE WAIT...")
                for root, dirs, files in os.walk(plugins_folder):
                    for file in files:
                        if file.endswith('.esm') or file.endswith('.esp') or file.endswith('.esl'):
                            plugin_backup = os.path.join("PACT BACKUP", "Primary Backup", file)
                            plugin_current = os.path.join(root, file)
                            if os.path.exists(plugin_backup):
                                with open(plugin_current, 'rb') as plugin1:
                                    with open(plugin_backup, 'rb') as plugin2:
                                        hash1 = hashlib.sha256(plugin1.read()).hexdigest()
                                        hash2 = hashlib.sha256(plugin2.read()).hexdigest()
                                if hash1 != hash2:  # Compare hashes between current and backup plugins.
                                    current_date = datetime.date.today().strftime('%y-%m-%d')
                                    dated_backup = os.path.join("PACT BACKUP", f"BACKUP {current_date}")
                                    if not os.path.exists(dated_backup):
                                        os.makedirs(dated_backup, exist_ok=True)
                                    shutil.copy2(plugin_current, dated_backup)
                                    # Remove plugin name from PACT Ignore list if hashes are different.
                                    with open("PACT Ignore.txt", "r", encoding="utf-8", errors="ignore") as Ignore_List:
                                        Ignore_Check = Ignore_List.read()
                                        if str(file) in Ignore_Check:
                                            Ignore_Check = Ignore_Check.replace(str(file), "")
                                    with open("PACT Ignore.txt", "w", encoding="utf-8", errors="ignore") as Ignore_List:
                                        Ignore_List.write(Ignore_Check)
                            else:  # Create plugin backup if not already in Primary Backup.
                                current_date = datetime.date.today().strftime('%y-%m-%d')
                                dated_backup = os.path.join("PACT BACKUP", f"BACKUP {current_date}")
                                if not os.path.exists(dated_backup):
                                    os.makedirs(dated_backup, exist_ok=True)
                                shutil.copy2(plugin_current, dated_backup)
                print("ADDITIONAL BACKUP PROCESSED!")

    @staticmethod
    def restore_popup():
        Box_Restore = QtWidgets.QMessageBox()
        Box_Restore.setIcon(QtWidgets.QMessageBox.Question)  # type: ignore
        Box_Restore.setWindowTitle("PACT Restore")
        Box_Restore.setText(UiPACTMainWin.restore_box_msg)  # RESERVED | Box_Restore.setInformativeText("...")
        Box_Restore.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)  # type: ignore
        if Box_Restore.exec() != QtWidgets.QMessageBox.Cancel:  # type: ignore
            UiPACTMainWin.pact_restore_backup()

    @staticmethod
    def pact_restore_backup():
        plugins_folder = QFileDialog.getExistingDirectory()
        if plugins_folder:
            primary_backup = os.path.join("PACT BACKUP", "Primary Backup")
            if not os.path.exists(primary_backup):
                print("❌ ERROR : You need to create a backup before you can restore it!")
            else:
                print("RESTORING PRIMARY BACKUP, PLEASE WAIT...")
                for root, dirs, files in os.walk(plugins_folder):
                    for file in files:
                        if file.endswith('.esm') or file.endswith('.esp') or file.endswith('.esl'):
                            plugin_backup = os.path.join("PACT BACKUP", "Primary Backup", file)
                            plugin_current = os.path.join(root, file)
                            if os.path.exists(plugin_backup):
                                try:
                                    shutil.copy2(plugin_backup, plugin_current)
                                except (PermissionError, OSError):
                                    print(f"❌ ERROR : Unable to restore a backup for {file}")
                                    print("   You can run PACT in admin mode and try again.")
                                    continue
                print("PRIMARY BACKUP RESTORED!")

    @staticmethod
    def help_popup():
        Box_Help = QtWidgets.QMessageBox()
        Box_Help.setIcon(QtWidgets.QMessageBox.Question)  # type: ignore
        Box_Help.setWindowTitle("Need Help?")
        Box_Help.setText(UiPACTMainWin.help_box_msg)  # RESERVED | Box_Help.setInformativeText("...")
        Box_Help.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)  # type: ignore
        if Box_Help.exec() != QtWidgets.QMessageBox.Cancel:  # type: ignore
            QDesktopServices.openUrl(QUrl("https://discord.com/invite/7ZZbrsGQh4"))

    @staticmethod
    def update_popup():
        if pact_update_check():
            QtWidgets.QMessageBox.information(PACT_WINDOW, "PACT Update", "You have the latest version of PACT!")
        else:
            QtWidgets.QMessageBox.warning(PACT_WINDOW, "PACT Update", "New PACT version is available!\nPress OK to open the PACT Nexus Page.")
            QDesktopServices.openUrl(QUrl("https://www.nexusmods.com/fallout4/mods/56255"))

    # ================= MAIN BUTTON FUNCTIONS ===================

    def update_settings(self):
        pact_update_settings()
        value_CT = self.InputField_CT.text()
        value_JE = self.InputField_JE.text()
        pact_ini_update("Cleaning Timeout", value_CT)
        pact_ini_update("Journal Expiration", value_JE)
        QtWidgets.QMessageBox.information(PACT_WINDOW, "PACT Settings", "All PACT settings have been updated and refreshed!")

    def select_file_lo(self):
        LO_file, _ = QFileDialog.getOpenFileName(filter="*.txt")  # type: ignore
        if os.path.exists(LO_file) and ("loadorder" in LO_file or "plugins" in LO_file):
            QtWidgets.QMessageBox.information(PACT_WINDOW, "New Load Order File Set", f"You have set the new path to: {LO_file} \n")  # type: ignore
            pact_ini_update("LoadOrder TXT", LO_file)
            self.RegBT_BROWSE_LO.setStyleSheet("color: black; background-color: lightgreen; border-radius: 5px; border: 1px solid gray;")  # type: ignore
            self.RegBT_BROWSE_LO.setText("✔️ LOAD ORDER FILE SET")  # type: ignore
            self.configured_LO = True
        elif os.path.exists(LO_file) and "loadorder" not in LO_file and "plugins" not in LO_file:
            self.RegBT_BROWSE_LO.setStyleSheet("color: black; background-color: orange; border-radius: 5px; border: 1px solid gray;")  # type: ignore
            self.RegBT_BROWSE_LO.setText("❌ WRONG LO FILE")  # type: ignore

    def select_file_mo2(self):
        MO2_EXE, _ = QFileDialog.getOpenFileName(filter="*.exe")  # type: ignore
        if os.path.exists(MO2_EXE):
            QtWidgets.QMessageBox.information(PACT_WINDOW, "New MO2 Executable Set", "You have set MO2 to: \n" + MO2_EXE)  # type: ignore
            pact_ini_update("MO2 EXE", MO2_EXE)
            self.RegBT_BROWSE_MO2.setStyleSheet("color: black; background-color: lightgreen; border-radius: 5px; border: 1px solid gray;")  # type: ignore
            self.RegBT_BROWSE_MO2.setText("✔️ MO2 EXECUTABLE SET")  # type: ignore
            self.configured_MO2 = True

    def select_file_xedit(self):
        XEDIT_EXE, _ = QFileDialog.getOpenFileName(filter="*.exe")  # type: ignore
        if os.path.exists(XEDIT_EXE) and "edit" in XEDIT_EXE.lower():
            QtWidgets.QMessageBox.information(PACT_WINDOW, "New MO2 Executable Set", "You have set XEDIT to: \n" + XEDIT_EXE)  # type: ignore
            pact_ini_update("XEDIT EXE", XEDIT_EXE)
            self.RegBT_BROWSE_XEDIT.setStyleSheet("color: black; background-color: lightgreen; border-radius: 5px; border: 1px solid gray;")  # type: ignore
            self.RegBT_BROWSE_XEDIT.setText("✔️ XEDIT EXECUTABLE SET")  # type: ignore
            self.configured_XEDIT = True
        elif os.path.exists(XEDIT_EXE) and "edit" not in XEDIT_EXE.lower():
            self.RegBT_BROWSE_XEDIT.setText("❌ WRONG XEDIT EXE")  # type: ignore
            self.RegBT_BROWSE_XEDIT.setStyleSheet("color: black; background-color: orange; border-radius: 5px; border: 1px solid gray;")  # type: ignore


# CLEANING NEEDS A SEPARATE THREAD SO IT DOESN'T FREEZE PACT GUI
class PactThread(QThread):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cleaning_done = False

    def run(self):  # def Plugins_CLEAN():
        check_process_mo2()
        check_settings_integrity()
        while not self.cleaning_done:
            self.cleaning_done = clean_plugins()
            self.msleep(1000)


if __name__ == "__main__":
    gui_prompt = """\

SET YOUR LOAD ORDER FILE AND XEDIT EXECUTABLE TO ENABLE CLEANING
(MOD ORGANIZER 2 USERS ALSO NEED TO SET THE MO2 EXECUTABLE PATH)

PRESS 'START CLEANING' BUTTON TO CLEAN ALL ACTIVE GAME PLUGINS
(IF REQUIRED FILES ARE SET, BUTTON WILL BE ENABLED IN 3 SECONDS)

YOU CAN ALSO CREATE AND RESTORE PLUGIN BACKUPS (READ THE INFO CAREFULLY)
DON'T FORGET TO CHECK THE PACT README FOR MORE DETAILS AND INSTRUCTIONS
"""
    print(gui_prompt)
    app = QtWidgets.QApplication(sys.argv)
    PACT_WINDOW = QtWidgets.QDialog()
    ui = UiPACTMainWin()
    ui.setup_ui(PACT_WINDOW)
    PACT_WINDOW.show()
    sys.exit(app.exec())
