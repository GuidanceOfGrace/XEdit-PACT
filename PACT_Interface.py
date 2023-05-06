import os
import sys

import psutil
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QThread, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QApplication, QFileDialog, QLabel, QLineEdit,
                               QPushButton, QStyleFactory)

from PACT_Start import (PACT_config, PACT_Current, check_process_mo2,
                        check_settings_integrity, clean_plugins, info,
                        pact_ini_update, pact_update_check,
                        pact_update_settings)

'''TEMPLATES
QMessageBox.NoIcon | Question | Information | Warning | Critical
'''
sys.argv += ['-platform', 'windows:darkmode=2']


def create_button_lo(parent, geometry, object_name, text, style_sheet, callback, config_check, config_key, success_text):
    button = QtWidgets.QPushButton(parent)
    button.setGeometry(geometry)
    button.setObjectName(object_name)
    button.setText(text)
    button.setStyleSheet(style_sheet)
    button.clicked.connect(callback)

    if config_check in PACT_config["MAIN"][config_key]:
        button.setStyleSheet("color: black; background-color: lightgreen; border-radius: 5px; border: 1px solid gray;")
        button.setText(success_text)

    return button


def create_separator(parent, geometry, object_name):
    separator = QtWidgets.QFrame(parent)
    separator.setGeometry(geometry)
    separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
    separator.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
    separator.setObjectName(object_name)
    return separator


def create_label(parent, geometry, text, font_size, font_bold, object_name):
    label = QtWidgets.QLabel(parent)
    label.setGeometry(geometry)
    label.setText(text)
    font = QtGui.QFont()
    font.setPointSize(font_size)
    font.setBold(font_bold)
    label.setFont(font)
    label.setObjectName(object_name)
    return label


def create_input_label(parent, geometry, text):
    label = QLabel(text, parent)
    label.setGeometry(geometry)
    return label


def create_input_field(parent, geometry, validator, text):
    input_field = QLineEdit(parent)
    input_field.setGeometry(geometry)
    input_field.setValidator(validator)
    input_field.setText(text)
    return input_field


def create_button_input(parent, geometry, object_name, text, style_sheet, font, callback, enabled=True):
    button = QPushButton(text, parent)
    button.setGeometry(geometry)
    button.setObjectName(object_name)
    button.setFont(font)
    button.setEnabled(enabled)
    button.setStyleSheet(style_sheet)
    button.clicked.connect(callback)
    return button


def create_simple_button(parent, geometry, object_name, text, tooltip, callback):
    button = QtWidgets.QPushButton(parent)
    button.setGeometry(geometry)
    button.setObjectName(object_name)
    button.setText(text)
    button.setToolTip(tooltip)
    button.clicked.connect(callback)
    return button


class UiPACTMainWin(object):
    def __init__(self):
        super().__init__()  # Allow subclasses to inherit & extend behavior of parent class.
        QApplication.setStyle(QStyleFactory.create("Fusion"))
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
        self.RegBT_CHECKUPDATES = None
        self.RegBT_CLEAN_PLUGINS = None

        self.RegBT_HELP = None
        self.RegBT_EXIT = None
        self.RegBT_CHECKUPDATES = None

        self.timer = QTimer()  # For CLEAN PLUGINS button auto check.
        self.timer.timeout.connect(self.timed_states)  # type: ignore
        self.timer.start(3000)  # In ms, will override QTimer.singleShot
        self.thread = None

    def setup_ui(self, PACT_WINDOW):
        # MAIN WINDOW
        PACT_WINDOW.setObjectName("PACT_WINDOW")
        PACT_WINDOW.setWindowTitle(f"Plugin Auto Cleaning Tool {PACT_Current[-4:]}")
        PACT_WINDOW.resize(640, 640)
        PACT_WINDOW.setMinimumSize(QtCore.QSize(640, 320))
        PACT_WINDOW.setMaximumSize(QtCore.QSize(640, 320))
        PACT_WINDOW.setWindowFlags(PACT_WINDOW.windowFlags() | Qt.WindowMinimizeButtonHint)  # type: ignore
        QApplication.setStyle(QStyleFactory.create("Fusion"))

        # ==================== MAIN WINDOW ITEMS =====================
        # TOP

        # Button - Browse Load Order
        self.RegBT_BROWSE_LO = create_button_lo(
            PACT_WINDOW,
            QtCore.QRect(80, 50, 150, 32),
            "RegBT_BROWSE_LO",
            "SET LOAD ORDER FILE",
            "color: black; background-color: lightyellow; border-radius: 5px; border: 1px solid gray;",
            self.select_file_lo,
            "loadorder",
            "LoadOrder TXT",
            "✔️ LOAD ORDER FILE SET"
        )
        self.configured_LO = "loadorder" in PACT_config["MAIN"]["LoadOrder TXT"] or "plugins" in PACT_config["MAIN"]["LoadOrder TXT"]

        # Button - Browse MO2 EXE
        self.RegBT_BROWSE_MO2 = create_button_lo(
            PACT_WINDOW,
            QtCore.QRect(245, 50, 150, 32),
            "RegBT_BROWSE_MO2",
            "SET MO2 EXECUTABLE",
            "color: black; background-color: lightyellow; border-radius: 5px; border: 1px solid gray;",
            self.select_file_mo2,
            "ModOrganizer",
            "MO2 EXE",
            "✔️ MO2 EXECUTABLE SET"
        )
        self.configured_MO2 = "ModOrganizer" in PACT_config["MAIN"]["MO2 EXE"]

        # Button - Browse XEDIT EXE
        self.RegBT_BROWSE_XEDIT = create_button_lo(
            PACT_WINDOW,
            QtCore.QRect(410, 50, 150, 32),
            "RegBT_BROWSE_XEDIT",
            "SET XEDIT EXECUTABLE",
            "color: black; background-color: lightyellow; border-radius: 5px; border: 1px solid gray;",
            self.select_file_xedit,
            "Edit",
            "XEDIT EXE",
            "✔️ XEDIT EXECUTABLE SET"
        )
        self.configured_XEDIT = "Edit" in PACT_config["MAIN"]["XEDIT EXE"]

       # Separator 1
        self.LINE_SEPARATOR1 = create_separator(PACT_WINDOW, QtCore.QRect(80, 100, 480, 20), "LINE_SEPARATOR1")

        # Separator Text 1
        self.LBL_SETTINGS1 = create_label(
            PACT_WINDOW,
            QtCore.QRect(50, 120, 550, 24),
            "YOU NEED TO SET YOUR LOAD ORDER FILE AND XEDIT EXECUTABLE BEFORE CLEANING",
            10,
            True,
            "LBL_NOTE_SET"
        )

        # Separator Text 2
        self.LBL_SETTINGS2 = create_label(
            PACT_WINDOW,
            QtCore.QRect(120, 140, 550, 24),
            "( MOD ORGANIZER 2 USERS ALSO NEED TO SET MO2 EXECUTABLE )",
            10,
            True,
            "LBL_NOTE_MO2"
        )

        # MAIN

       # Input - Cleaning Timeout
        self.InputLabel_CT = create_input_label(PACT_WINDOW, QtCore.QRect(105, 175, 100, 48), "Cleaning Timeout\n     (in seconds)")
        self.InputField_CT = create_input_field(PACT_WINDOW, QtCore.QRect(130, 225, 50, 24), QtGui.QIntValidator(), str(info.Cleaning_Timeout))

        # Input - Journal Expiration
        self.InputLabel_JE = create_input_label(PACT_WINDOW, QtCore.QRect(440, 175, 100, 48), "Journal Expiration\n         (in days)")
        self.InputField_JE = create_input_field(PACT_WINDOW, QtCore.QRect(465, 225, 50, 24), QtGui.QIntValidator(), str(info.Journal_Expiration))

        # Button - UPDATE SETTINGS
        self.RegBT_UPDATE_SETTINGS = create_button_input(
            PACT_WINDOW,
            QtCore.QRect(245, 280, 150, 24),
            "RegBT_UPDATE_SETTINGS",
            "UPDATE SETTINGS",
            "",
            QtGui.QFont(),
            self.update_settings
        )

        # Button - CLEAN PLUGINS
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)

        self.RegBT_CLEAN_PLUGINS = create_button_input(
            PACT_WINDOW,
            QtCore.QRect(245, 200, 150, 32),
            "RegBT_CLEAN_PLUGINS",
            "START CLEANING",
            "background-color: lightgray; border-radius: 5px; border: 1px solid gray;",
            font,
            self.start_cleaning,
            enabled=False
        )

        # BOTTOM

        # Button - HELP
        self.RegBT_HELP = create_simple_button(PACT_WINDOW, QtCore.QRect(20, 280, 110, 24), "RegBT_HELP", "HELP", "How To Use PACT GUI", self.help_popup)

        # Button - Check Updates
        self.RegBT_CHECKUPDATES = create_simple_button(PACT_WINDOW, QtCore.QRect(245, 10, 150, 24), "RegBT_CHECKUPDATES", "CHECK FOR UPDATES", "", self.update_popup)

        # Button - EXIT
        self.RegBT_EXIT = create_simple_button(PACT_WINDOW, QtCore.QRect(510, 280, 110, 24), "RegBT_EXIT", "EXIT", "Exit PACT GUI", PACT_WINDOW.close)

    # ============== CLEAN PLUGINS BUTTON STATES ================

    def _set_button_state(self, button, enabled, text, color):
        button.setEnabled(enabled)
        button.setText(text)
        button.setStyleSheet(f"color: black; background-color: {color}; border-radius: 5px; border: 1px solid gray;")

    def is_xedit_running(self):
        xedit_procs = [proc for proc in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent', 'create_time']) if 'edit.exe' in proc.info['name'].lower()]  # type: ignore
        return any(proc.info['name'].lower() == str(info.XEDIT_EXE).lower() for proc in xedit_procs)  # type: ignore

    def timed_states(self):
        xedit_running = self.is_xedit_running()
        if self.thread is None:
            self._set_button_state(self.RegBT_CLEAN_PLUGINS, self.configured_LO and self.configured_XEDIT and not xedit_running, "START CLEANING", "lightblue")
            self.RegBT_CLEAN_PLUGINS.clicked.disconnect() # type: ignore
            self.RegBT_CLEAN_PLUGINS.clicked.connect(self.start_cleaning) # type: ignore

            for button in [self.RegBT_BROWSE_LO, self.RegBT_BROWSE_MO2, self.RegBT_BROWSE_XEDIT, self.RegBT_EXIT]:
                button.setEnabled(True) # type: ignore
        else:
            for button in [self.RegBT_BROWSE_LO, self.RegBT_BROWSE_MO2, self.RegBT_BROWSE_XEDIT, self.RegBT_EXIT]:
                button.setEnabled(False) # type: ignore

            if self.thread.cleaning_done:
                self.thread.finished_signal.connect(self.thread.quit)  # type: ignore
                self.thread.finished_signal.connect(self.thread.wait)  # type: ignore
                self.thread = None
            elif not xedit_running:
                self._set_button_state(self.RegBT_CLEAN_PLUGINS, True, "START CLEANING", "lightblue")

    def start_cleaning(self):
        if self.thread is None:
            self.thread = PactThread()
            self.thread.start()
            self._set_button_state(self.RegBT_CLEAN_PLUGINS, True, "STOP CLEANING", "pink")
            self.RegBT_CLEAN_PLUGINS.clicked.disconnect() # type: ignore
            self.RegBT_CLEAN_PLUGINS.clicked.connect(self.stop_cleaning) # type: ignore

    def stop_cleaning(self):
        if self.thread is not None:
            self.thread.terminate()
            self.thread.wait()
            self.thread = None
            self._set_button_state(self.RegBT_CLEAN_PLUGINS, False, "...STOPPING...", "orange")
            print("\n❌ CLEANING STOPPED! PLEASE WAIT UNTIL ALL RUNNING PROGRAMS ARE CLOSED BEFORE STARTING AGAIN!\n")

    # ================== POP-UPS / WARNINGS =====================
    # @staticmethod recommended for func that don't call "self".

    help_popup_msg = """If you have trouble running this program or wish to submit your PACT logs for additional help, join the Collective Modding Discord server.
    Please READ the #👋-welcome2 channel, react with the "2" emoji on the bot message there and leave your feedback in #💡-poet-guides-mods channel.
    Press OK to open the server link in your internet browser."""

    @staticmethod
    def help_popup():
        msgBox = QtWidgets.QMessageBox()
        msgBox.setIcon(QtWidgets.QMessageBox.Question)  # type: ignore
        msgBox.setWindowTitle("Need Help?")
        msgBox.setText(UiPACTMainWin.help_popup_msg)  # RESERVED | msgBox.setInformativeText("...")
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)  # type: ignore
        if msgBox.exec() != QtWidgets.QMessageBox.Cancel:  # type: ignore
            QDesktopServices.openUrl(QUrl("https://discord.com/invite/7ZZbrsGQh4"))

    @staticmethod
    def update_popup():
        if pact_update_check():
            QtWidgets.QMessageBox.information(PACT_WINDOW, "PACT Update", "You have the latest version of PACT!")
        else:
            QtWidgets.QMessageBox.warning(PACT_WINDOW, "PACT Update", "New PACT version is available!\nPress OK to open the PACT Nexus Page.")
            QDesktopServices.openUrl(QUrl("https://www.nexusmods.com/fallout4/mods/56255"))

    # ================= MAIN BUTTON FUNCTIONS ===================

    def _select_file(self, filters, button, key, success_text, error_text, check_fn=None):
        selected_file, _ = QFileDialog.getOpenFileName(filter=filters)  # type: ignore
        if check_fn is not None and not check_fn(selected_file):
            button.setStyleSheet("color: black; background-color: orange; border-radius: 5px; border: 1px solid gray;")
            button.setText(error_text)
            return

        if os.path.exists(selected_file):
            QtWidgets.QMessageBox.information(PACT_WINDOW, success_text.split(" ")[-2] + " Set", f"You have set {success_text.split(' ')[-2]} to: \n{selected_file}")
            pact_ini_update(key, selected_file)
            button.setStyleSheet("color: black; background-color: lightgreen; border-radius: 5px; border: 1px solid gray;")
            button.setText(success_text)
            return True
        return False

    def update_settings(self):
        pact_update_settings()
        value_CT = int(self.InputField_CT.text())
        value_JE = int(self.InputField_JE.text())
        pact_ini_update("Cleaning Timeout", str(value_CT))
        pact_ini_update("Journal Expiration", str(value_JE))

    def select_file_lo(self):
        def check_fn(file_path):
            return "loadorder" in file_path or "plugins" in file_path

        self.configured_LO = self._select_file("*.txt", self.RegBT_BROWSE_LO, "LoadOrder TXT", "✔️ LOAD ORDER FILE SET", "❌ WRONG LO FILE", check_fn)

    def select_file_mo2(self):
        self.configured_MO2 = self._select_file("*.exe", self.RegBT_BROWSE_MO2, "MO2 EXE", "✔️ MO2 EXECUTABLE SET", "❌ WRONG MO2 EXE")

    def select_file_xedit(self):
        def check_fn(file_path):
            return "edit" in file_path.lower()

        self.configured_XEDIT = self._select_file("*.exe", self.RegBT_BROWSE_XEDIT, "XEDIT EXE", "✔️ XEDIT EXECUTABLE SET", "❌ WRONG XEDIT EXE", check_fn)


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
-----
SET YOUR LOAD ORDER FILE AND XEDIT EXECUTABLE TO ENABLE CLEANING
     (MOD ORGANIZER 2 USERS ALSO NEED TO SET MO2 EXECUTABLE)

PRESS 'START CLEANING' BUTTON TO CLEAN ALL ACTIVE GAME PLUGINS
(IF REQUIRED FILES ARE SET, IT WILL ENABLE ITSELF IN 3 SECONDS)
-----
    """
    print(gui_prompt)
    app = QtWidgets.QApplication(sys.argv)
    PACT_WINDOW = QtWidgets.QDialog()
    ui = UiPACTMainWin()
    ui.setup_ui(PACT_WINDOW)
    PACT_WINDOW.show()
    sys.exit(app.exec())
