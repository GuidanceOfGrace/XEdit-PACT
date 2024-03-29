import datetime
import hashlib
import os
import platform
import re
import shutil
import sys
from typing import Union

import psutil
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QThread, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QApplication, QFileDialog, QFrame, QLabel,
                               QLineEdit, QMessageBox, QPushButton,
                               QStyleFactory)

from PACT_Start import (PACT_config, PACT_Current, ProgressEmitter,
                        check_process_mo2, check_settings_integrity,
                        clean_plugins, info, pact_ini_update,
                        pact_update_check, pact_update_settings)

current_platform = platform.system()
if current_platform == 'Windows':
    version = platform.release()
    if version.startswith('10') or version.startswith('11'):
        sys.argv += ['-platform', 'windows:darkmode=2']

'''TEMPLATES
QMessageBox.NoIcon | Question | Information | Warning | Critical
'''

progress_emitter = ProgressEmitter()


class UiPACTMainWin(object):
    def __init__(self, PACT_WINDOW):
        super().__init__()  # Allow subclasses to inherit & extend behavior of parent class.
        QApplication.setStyle(QStyleFactory.create("Fusion"))

        self.timer = QTimer()  # For CLEAN PLUGINS button auto check.
        self.timer.timeout.connect(self.timed_states)
        self.timer.start(3000)  # In ms, will override QTimer.singleShot
        self.thread = None

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
        def create_button(text, parent, geometry, object_name, stylesheet=None, clicked=None, font=None, enabled=True):
            button = QPushButton(text, parent)
            button.setGeometry(geometry)
            button.setObjectName(object_name)
            if stylesheet:
                button.setStyleSheet(stylesheet)
            if clicked:
                button.clicked.connect(clicked)
            if font:
                button.setFont(font)
            if not enabled:
                button.setEnabled(False)
            else:
                button.setEnabled(True)
            return button

        def create_labeled_input_field(label_text, parent, label_geometry, input_geometry, input_validator, input_text):
            label = QLabel(label_text, parent)
            label.setGeometry(label_geometry)
            input_field = QLineEdit(parent)
            input_field.setGeometry(input_geometry)
            input_field.setValidator(input_validator)
            input_field.setText(input_text)
            return label, input_field

        def create_label(text, parent, geometry, font, object_name):
            label = QLabel(text, parent)
            label.setGeometry(geometry)
            label.setFont(font)
            label.setObjectName(object_name)
            return label

        def create_horizontal_line_separator(parent, geometry, object_name):
            separator = QFrame(parent)
            separator.setGeometry(geometry)
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setFrameShadow(QFrame.Shadow.Sunken)
            separator.setObjectName(object_name)
            return separator

        def create_progress_bar(parent, geometry: QtCore.QRect, object_name, format: str = "%p%", visible=False):
            progress_bar = QtWidgets.QProgressBar(parent)
            progress_bar.setGeometry(geometry)
            progress_bar.setValue(0)
            progress_bar.setObjectName(object_name)
            progress_bar.setFormat(format)
            if visible:
                progress_bar.setVisible(True)
            else:
                progress_bar.setVisible(False)
            return progress_bar

        self.RegBT_CHECK_UPDATES = create_button("CHECK FOR UPDATES",
                                                 PACT_WINDOW,
                                                 QtCore.QRect(80, 50, 230, 32),
                                                 "RegBT_CHECK_UPDATES",
                                                 clicked=self.update_popup,
                                                 enabled=False
                                                 )

        # Button - Update Settings
        self.RegBT_UPDATE_SETTINGS = create_button("UPDATE SETTINGS",
                                                   PACT_WINDOW,
                                                   QtCore.QRect(330, 50, 230, 32),
                                                   "RegBT_UPDATE_SETTINGS",
                                                   clicked=self.update_settings
                                                   )

        # Button - Browse Load Order
        self.RegBT_BROWSE_LO = create_button("SET LOAD ORDER FILE",
                                             PACT_WINDOW,
                                             QtCore.QRect(70, 100, 165, 32),
                                             "RegBT_BROWSE_LO",
                                             "color: black; background-color: lightyellow; border-radius: 5px; border: 1px solid gray;",
                                             self.select_file_lo
                                             )
        self.configured_LO = False
        if "loadorder" in PACT_config["MAIN"]["LoadOrder_TXT"] or "plugins" in PACT_config["MAIN"]["LoadOrder_TXT"]:  # type: ignore
            if os.path.isfile(PACT_config["MAIN"]["LoadOrder_TXT"]):  # type: ignore
                self.RegBT_BROWSE_LO.setStyleSheet("color: black; background-color: lightgreen; border-radius: 5px; border: 1px solid gray;")
                self.RegBT_BROWSE_LO.setText("✔️ LOAD ORDER FILE SET")
                self.configured_LO = True
            else:
                self.RegBT_BROWSE_LO.setStyleSheet("color: black; background-color: lightyellow; border-radius: 5px; border: 1px solid gray;")
                self.RegBT_BROWSE_LO.setText("❓ LOAD ORDER FILE NOT FOUND")
                self.configured_LO = False

        # Button - Browse MO2 EXE
        self.RegBT_BROWSE_MO2 = create_button("SET MO2 EXECUTABLE",
                                              PACT_WINDOW,
                                              QtCore.QRect(245, 100, 165, 32),
                                              "RegBT_BROWSE_MO2",
                                              "color: black; background-color: lightyellow; border-radius: 5px; border: 1px solid gray;",
                                              self.select_file_mo2
                                              )
        self.configured_MO2 = False
        if "ModOrganizer" in PACT_config["MAIN"]["MO2_EXE"]:  # type: ignore
            if os.path.isfile(PACT_config["MAIN"]["MO2_EXE"]):  # type: ignore
                self.RegBT_BROWSE_MO2.setStyleSheet("color: black; background-color: lightgreen; border-radius: 5px; border: 1px solid gray;")
                self.RegBT_BROWSE_MO2.setText("✔️ MO2 EXECUTABLE SET")
                self.configured_MO2 = True
            else:
                self.RegBT_BROWSE_MO2.setStyleSheet("color: black; background-color: lightyellow; border-radius: 5px; border: 1px solid gray;")
                self.RegBT_BROWSE_MO2.setText("❓ MO2 EXECUTABLE NOT FOUND")
                self.configured_MO2 = False

        # Button - Browse XEDIT EXE
        self.RegBT_BROWSE_XEDIT = create_button("SET XEDIT EXECUTABLE",
                                                PACT_WINDOW,
                                                QtCore.QRect(420, 100, 165, 32),
                                                "RegBT_BROWSE_XEDIT",
                                                "color: black; background-color: lightyellow; border-radius: 5px; border: 1px solid gray;",
                                                self.select_file_xedit
                                                )
        self.configured_XEDIT = False
        if "Edit" in PACT_config["MAIN"]["XEDIT_EXE"]:  # type: ignore
            if os.path.isfile(PACT_config["MAIN"]["XEDIT_EXE"]):  # type: ignore
                self.RegBT_BROWSE_XEDIT.setStyleSheet("color: black; background-color: lightgreen; border-radius: 5px; border: 1px solid gray;")
                self.RegBT_BROWSE_XEDIT.setText("✔️ XEDIT EXECUTABLE SET")
                self.configured_XEDIT = True
            else:
                self.RegBT_BROWSE_XEDIT.setStyleSheet("color: black; background-color: lightyellow; border-radius: 5px; border: 1px solid gray;")
                self.RegBT_BROWSE_XEDIT.setText("❓ XEDIT EXECUTABLE NOT FOUND")
                self.configured_XEDIT = False

        # SEPARATOR LINE 1
        self.LINE_SEPARATOR1 = create_horizontal_line_separator(
            PACT_WINDOW,
            QtCore.QRect(80, 150, 480, 20),
            "LINE_SEPARATOR1"
        )

        # SEPARATOR TEXT 1
        self.LBL_SETTINGS1 = create_label(
            "YOU NEED TO SET YOUR LOAD ORDER FILE AND XEDIT EXECUTABLE BEFORE CLEANING",
            PACT_WINDOW,
            QtCore.QRect(50, 175, 550, 24),
            font_bold,
            "LBL_NOTE_SET"
        )

        # SEPARATOR TEXT 2
        self.LBL_SETTINGS2 = create_label("( MOD ORGANIZER 2 USERS ALSO NEED TO SET MO2 EXECUTABLE )",
                                          PACT_WINDOW,
                                          QtCore.QRect(120, 200, 550, 24),
                                          font_bold,
                                          "LBL_NOTE_MO2"
                                          )

        # MAIN

        # Button - Backup Plugins
        self.RegBT_BACKUP_PLUGINS = create_button("BACKUP PLUGINS",
                                                  PACT_WINDOW,
                                                  QtCore.QRect(80, 250, 230, 32),
                                                  "RegBT_BACKUP_PLUGINS",
                                                  """
                                                  QPushButton {
                                                    color: black; 
                                                    background-color: lightyellow; 
                                                    border-radius: 5px; 
                                                    border: 1px solid gray;}
                                                    QPushButton:hover {
                                                        background-color: lightblue;
                                                        }
                                                    """,
                                                  self.backup_popup
                                                  )

        # Button - Restore Backup
        self.RegBT_RESTORE_BACKUP = create_button("RESTORE BACKUP",
                                                  PACT_WINDOW,
                                                  QtCore.QRect(330, 250, 230, 32),
                                                  "RegBT_RESTORE_BACKUP",
                                                  """
                                                  QPushButton {
                                                    color: black; 
                                                    background-color: lightyellow; 
                                                    border-radius: 5px; 
                                                    border: 1px solid gray;
                                                    }
                                                    QPushButton:hover {
                                                        background-color: lightblue;
                                                        }
                                                    """,
                                                  self.restore_popup
                                                  )

        # Input - Cleaning Timeout

        self.InputLabel_CT, self.InputField_CT = create_labeled_input_field("Cleaning Timeout\n     (in seconds)",
                                                                            PACT_WINDOW, QtCore.QRect(105, 300, 100, 48),
                                                                            QtCore.QRect(130, 350, 50, 24),
                                                                            QtGui.QIntValidator(),
                                                                            str(info.Cleaning_Timeout)
                                                                            )

        # Input - Journal Expiration
        self.InputField_JE, self.InputField_JE = create_labeled_input_field("Journal Expiration\n         (in days)",
                                                                            PACT_WINDOW,
                                                                            QtCore.QRect(440, 300, 100, 48),
                                                                            QtCore.QRect(465, 350, 50, 24),
                                                                            QtGui.QIntValidator(),
                                                                            str(info.Journal_Expiration)
                                                                            )

        # Button - CLEAN PLUGINS
        self.RegBT_CLEAN_PLUGINS = create_button("START CLEANING",
                                                 PACT_WINDOW,
                                                 QtCore.QRect(245, 325, 150, 32),
                                                 "RegBT_CLEAN_PLUGINS", "color: black; background-color: lightgray; border-radius: 5px; border: 1px solid gray;",
                                                 self.start_cleaning
                                                 )

        # BOTTOM
        self.ProgressBar = create_progress_bar(PACT_WINDOW,
                                               QtCore.QRect(20, 400, 600, 24),
                                               "ProgressBar",
                                               format=""
                                               )
        # Button - HELP
        self.RegBT_HELP = create_button("HELP",
                                        PACT_WINDOW,
                                        QtCore.QRect(20, 440, 110, 24),
                                        "RegBT_HELP",
                                        """
                                        QPushButton {color: black; 
                                        background-color: lightgray; 
                                        border-radius: 5px; 
                                        border: 1px solid gray;}
                                        QPushButton:hover {background-color: lightblue;}
                                        """,
                                        self.help_popup
                                        )

        # Button - EXIT
        self.RegBT_EXIT = create_button("EXIT",
                                        PACT_WINDOW,
                                        QtCore.QRect(510, 440, 110, 24),
                                        "RegBT_EXIT",
                                        """
                                        QPushButton {
                                            color: black; 
                                            background-color: lightgray; 
                                            border-radius: 5px; 
                                            border: 1px solid gray;
                                            }
                                        QPushButton:hover {
                                            background-color: lightblue;
                                            }
                                        """,
                                        PACT_WINDOW.close
                                        )
    # ============== CLEAN PLUGINS BUTTON STATES ================

    def is_xedit_running(self):
        xedit_regex = re.compile(r"(?:xedit|fo3edit|fnvedit|sseedit|fo4edit|tes5edit|fo4vredit|tes5vredit|xfoedit)(?:64)?\.exe", re.IGNORECASE)
        xedit_procs = [proc for proc in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent', 'create_time']) if xedit_regex.search(proc.name())]
        xedit_running = False
        for proc in xedit_procs:
            if proc.name().lower() == str(info.XEDIT_EXE).lower():
                xedit_running = True
        return xedit_running

    def timed_states(self):
        xedit_running = self.is_xedit_running()

        if self.thread is None:
            self.init_start_button(xedit_running)
        else:
            self.RegBT_BROWSE_LO.setEnabled(False)
            self.RegBT_BROWSE_MO2.setEnabled(False)
            self.RegBT_BROWSE_XEDIT.setEnabled(False)
            self.RegBT_EXIT.setEnabled(False)
            if not self.thread:
                self.thread = PactThread(progress_bar=self.ProgressBar)
            if progress_emitter.is_done == True and isinstance(self.thread, PactThread):
                try:
                    self.thread.terminate()
                    self.thread.wait()
                    self.reset_thread()
                except AttributeError:
                    pass
            if "STOP CLEANING" not in self.RegBT_CLEAN_PLUGINS.text() and xedit_running is False:
                self.RegBT_CLEAN_PLUGINS.setText("START CLEANING")
                self.RegBT_CLEAN_PLUGINS.setStyleSheet("color: black; background-color: lightblue; border-radius: 5px; border: 1px solid gray;")

    def start_cleaning(self):
        if self.thread is None:
            self.thread = PactThread(progress_bar=self.ProgressBar)
            self.thread.start()
            self.thread.finished.connect(self.init_start_and_reset)
            progress_emitter.progress.connect(self.ProgressBar.setValue)
            progress_emitter.max_value.connect(self.ProgressBar.setMaximum)
            progress_emitter.plugin_value.connect(self.ProgressBar.setFormat)
            progress_emitter.visible.connect(self.ProgressBar.setVisible)
            progress_emitter.done.connect(self.thread.terminate)
            progress_emitter.done.connect(self.thread.wait)
            progress_emitter.done.connect(self.reset_thread)
            self.RegBT_CLEAN_PLUGINS.setText("STOP CLEANING")
            self.RegBT_CLEAN_PLUGINS.setStyleSheet("color: black; background-color: pink; border-radius: 5px; border: 1px solid gray;")
            self.RegBT_CLEAN_PLUGINS.clicked.disconnect()
            self.RegBT_CLEAN_PLUGINS.clicked.connect(self.stop_cleaning)

    def init_start_button(self, xedit_running=False):
        if self.RegBT_BROWSE_LO and not self.RegBT_BROWSE_LO.isEnabled():
            self.RegBT_BROWSE_LO.setEnabled(True)
        if self.RegBT_BROWSE_MO2 and not self.RegBT_BROWSE_MO2.isEnabled():
            self.RegBT_BROWSE_MO2.setEnabled(True)
        if self.RegBT_BROWSE_XEDIT and not self.RegBT_BROWSE_XEDIT.isEnabled():
            self.RegBT_BROWSE_XEDIT.setEnabled(True)
        if self.RegBT_EXIT and not self.RegBT_EXIT.isEnabled():
            self.RegBT_EXIT.setEnabled(True)
        if self.configured_LO and self.configured_XEDIT and xedit_running is False:
            self.RegBT_CLEAN_PLUGINS.setEnabled(True)
            self.RegBT_CLEAN_PLUGINS.setText("START CLEANING")
            self.RegBT_CLEAN_PLUGINS.setStyleSheet("color: black; background-color: lightblue; border-radius: 5px; border: 1px solid gray;")
            self.RegBT_CLEAN_PLUGINS.clicked.disconnect()
            self.RegBT_CLEAN_PLUGINS.clicked.connect(self.start_cleaning)

    def reset_thread(self):
        self.thread = None

    def init_start_and_reset(self):
        self.init_start_button()
        self.reset_thread()

    def stop_cleaning(self):
        if self.thread is not None:
            progress_emitter.is_done = True
            self.RegBT_CLEAN_PLUGINS.setEnabled(False)
            self.RegBT_CLEAN_PLUGINS.setText("...STOPPING...")
            self.RegBT_CLEAN_PLUGINS.setStyleSheet("color: black; background-color: orange; border-radius: 5px; border: 1px solid gray;")
            print("\n❌ CLEANING STOPPED! PLEASE WAIT UNTIL ALL RUNNING PROGRAMS ARE CLOSED BEFORE STARTING AGAIN!\n")
            self.ProgressBar.setFormat("Cleaning Stopped!")
            self.ProgressBar.setValue(0)

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
        Box_Backup = QMessageBox()
        Box_Backup.setIcon(QMessageBox.Question)  # type: ignore
        Box_Backup.setWindowTitle("PACT Backup")
        Box_Backup.setText(UiPACTMainWin.backup_box_msg)  # RESERVED | Box_Backup.setInformativeText("...")
        Box_Backup.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)  # type: ignore
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
                        if info.plugins_pattern.search(file):
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
                        if info.plugins_pattern.search(file):
                            plugin_backup = os.path.join("PACT BACKUP", "Primary Backup", file)
                            plugin_current = os.path.join(root, file)
                            if os.path.exists(plugin_backup):
                                with open(plugin_current, 'rb') as plugin1, open(plugin_backup, 'rb') as plugin2:
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
        Box_Restore = QMessageBox()
        Box_Restore.setIcon(QMessageBox.Question)  # type: ignore
        Box_Restore.setWindowTitle("PACT Restore")
        Box_Restore.setText(UiPACTMainWin.restore_box_msg)  # RESERVED | Box_Restore.setInformativeText("...")
        Box_Restore.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)  # type: ignore
        if Box_Restore.exec() != QMessageBox.Cancel:  # type: ignore
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
                        if info.plugins_pattern.search(file):
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
        pact_update_settings(info, PACT_config)
        value_CT = int(self.InputField_CT.text())
        value_JE = int(self.InputField_JE.text())
        pact_ini_update("Cleaning_Timeout", value_CT)
        pact_ini_update("Journal_Expiration", value_JE)
        QtWidgets.QMessageBox.information(PACT_WINDOW, "PACT Settings", "All PACT settings have been updated and refreshed!")

    def select_file_lo(self):
        LO_file, _ = QFileDialog.getOpenFileName(filter="*.txt")  # type: ignore
        if os.path.exists(LO_file) and ("loadorder" in LO_file or "plugins" in LO_file):
            QtWidgets.QMessageBox.information(PACT_WINDOW, "New Load Order File Set", f"You have set the new path to: {LO_file} \n")
            pact_ini_update("LoadOrder_TXT", LO_file)
            self.RegBT_BROWSE_LO.setStyleSheet("color: black; background-color: lightgreen; border-radius: 5px; border: 1px solid gray;")
            self.RegBT_BROWSE_LO.setText("✔️ LOAD ORDER FILE SET")
            self.configured_LO = True
        elif os.path.exists(LO_file) and "loadorder" not in LO_file and "plugins" not in LO_file:
            self.RegBT_BROWSE_LO.setStyleSheet("color: black; background-color: orange; border-radius: 5px; border: 1px solid gray;")
            self.RegBT_BROWSE_LO.setText("❌ WRONG LO FILE")

    def select_file_mo2(self):
        MO2_EXE, _ = QFileDialog.getOpenFileName(filter="*.exe")  # type: ignore
        if os.path.exists(MO2_EXE):
            QtWidgets.QMessageBox.information(PACT_WINDOW, "New MO2 Executable Set", "You have set MO2 to: \n" + MO2_EXE)
            pact_ini_update("MO2_EXE", MO2_EXE)
            self.RegBT_BROWSE_MO2.setStyleSheet("color: black; background-color: lightgreen; border-radius: 5px; border: 1px solid gray;")
            self.RegBT_BROWSE_MO2.setText("✔️ MO2 EXECUTABLE SET")
            self.configured_MO2 = True

    def select_file_xedit(self):
        XEDIT_EXE, _ = QFileDialog.getOpenFileName(filter="*.exe")  # type: ignore
        if os.path.exists(XEDIT_EXE) and "edit" in XEDIT_EXE.lower():
            QtWidgets.QMessageBox.information(PACT_WINDOW, "New MO2 Executable Set", "You have set XEDIT to: \n" + XEDIT_EXE)
            pact_ini_update("XEDIT_EXE", XEDIT_EXE)
            self.RegBT_BROWSE_XEDIT.setStyleSheet("color: black; background-color: lightgreen; border-radius: 5px; border: 1px solid gray;")
            self.RegBT_BROWSE_XEDIT.setText("✔️ XEDIT EXECUTABLE SET")
            self.configured_XEDIT = True
        elif os.path.exists(XEDIT_EXE) and "edit" not in XEDIT_EXE.lower():
            self.RegBT_BROWSE_XEDIT.setText("❌ WRONG XEDIT EXE")
            self.RegBT_BROWSE_XEDIT.setStyleSheet("color: black; background-color: orange; border-radius: 5px; border: 1px solid gray;")


# CLEANING NEEDS A SEPARATE THREAD SO IT DOESN'T FREEZE PACT GUI
class PactThread(QThread):
    def __init__(self, progress_bar, parent=None):
        super().__init__(parent)
        self.cleaning_done = False
        self.progress_bar = progress_bar

    def run(self):  # def Plugins_CLEAN():
        is_mo2_running = check_process_mo2(progress_emitter)
        if is_mo2_running:
            if self.progress_bar:
                self.progress_bar.setVisible(False)
            self.quit()
        check_settings_integrity()
        clean_plugins(progress_emitter)
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
    app = QtWidgets.QApplication(sys.argv)
    PACT_WINDOW = QtWidgets.QDialog()
    ui = UiPACTMainWin(PACT_WINDOW)
    print(gui_prompt)
    PACT_WINDOW.show()
    sys.exit(app.exec())
