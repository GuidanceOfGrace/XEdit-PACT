from contextlib import contextmanager
import os
import sys
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QUrl, QTimer, QThread
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog
from PACT_Start import (Globals, pact_ini_update, pact_update_check, check_process_mo2, check_settings_paths, check_settings_integrity, clean_plugins)

'''TEMPLATES
QMessageBox.NoIcon | Question | Information | Warning | Critical
'''


def enable_button_if_configured(func):
    def wrapper(self, *args, **kwargs):
        func(self, *args, **kwargs)
        self.RegBT_CLEAN_PLUGINS.setEnabled(self.configured_LO and self.configured_XEDIT)
    return wrapper


@contextmanager
def button_enabled(button, enabled=True):
    button.setEnabled(enabled)
    yield
    button.setEnabled(not enabled)


def update_file_button(filepath: str, button: QtWidgets.QPushButton, valid_text: str, invalid_text: str):
    if os.path.exists(filepath):
        button.setStyleSheet("background-color: lightgreen; border-radius: 5px; border: 1px solid gray;")
        button.setText(valid_text)
        return True
    else:
        button.setStyleSheet("background-color: orange; border-radius: 5px; border: 1px solid gray;")
        button.setText(invalid_text)
        return False

class UiPACTMainWin(object):
    def __init__(self):
        super().__init__()  # Allow subclasses to inherit & extend behavior of parent class.
        self.configured_LO = False
        self.configured_MO2 = False
        self.configured_XEDIT = False

        self.ChkBT_Update = None
        self.ChkBT_Stats = None
        self.Line_Separator_1 = None
        self.LBL_Settings1 = None
        self.LBL_Settings2 = None
        self.RegBT_Browse_LO = None
        self.RegBT_Browse_MO2 = None
        self.RegBT_Browse_XEDIT = None
        self.RegBT_CheckUpdates = None
        self.RegBT_CLEAN_PLUGINS = None

        self.RegBT_Help = None
        self.RegBT_Exit = None
        self.RegBT_CheckUpdates = None

        self.timer = QTimer()  # For CLEAN PLUGINS button auto check.
        self.timer.timeout.connect(self.check_config)  # type: ignore
        self.timer.start(3000)  # In ms, will override QTimer.singleShot
        self.thread = None

    def setup_ui(self, PACT_MainWin):
        # MAIN WINDOW
        PACT_MainWin.setObjectName("PACT_MainWin")
        PACT_MainWin.setWindowTitle(f"Plugin Auto Cleaning Tool {Globals.PACT_Current[-4:]}")
        PACT_MainWin.resize(640, 640)
        PACT_MainWin.setMinimumSize(QtCore.QSize(640, 320))
        PACT_MainWin.setMaximumSize(QtCore.QSize(640, 320))
        PACT_MainWin.setWindowFlags(PACT_MainWin.windowFlags() | Qt.WindowMinimizeButtonHint)  # type: ignore

        # ==================== MAIN WINDOW ITEMS =====================
        # TOP

        # Button - Browse Load Order
        self.RegBT_Browse_LO = QtWidgets.QPushButton(PACT_MainWin)
        self.RegBT_Browse_LO.setGeometry(QtCore.QRect(80, 50, 150, 32))
        self.RegBT_Browse_LO.setObjectName("RegBT_Browse_LO")
        self.RegBT_Browse_LO.setText("SET LOAD ORDER FILE")
        self.RegBT_Browse_LO.setStyleSheet("background-color: lightyellow; border-radius: 5px; border: 1px solid gray;")
        self.RegBT_Browse_LO.clicked.connect(self.select_file_lo)  # type: ignore
        if "loadorder" in Globals.PACT_config["MAIN"]["LoadOrder TXT"] or "plugins" in Globals.PACT_config["MAIN"]["LoadOrder TXT"]:
            self.RegBT_Browse_LO.setStyleSheet("background-color: lightgreen; border-radius: 5px; border: 1px solid gray;")
            self.RegBT_Browse_LO.setText("✔️ LOAD ORDER FILE SET")
            self.configured_LO = True

        # Button - Browse MO2 EXE
        self.RegBT_Browse_MO2 = QtWidgets.QPushButton(PACT_MainWin)
        self.RegBT_Browse_MO2.setGeometry(QtCore.QRect(245, 50, 150, 32))
        self.RegBT_Browse_MO2.setObjectName("RegBT_Browse_MO2")
        self.RegBT_Browse_MO2.setText("SET MO2 EXECUTABLE")
        self.RegBT_Browse_MO2.setStyleSheet("background-color: lightyellow; border-radius: 5px; border: 1px solid gray;")
        self.RegBT_Browse_MO2.clicked.connect(self.select_file_mo2)  # type: ignore
        if "ModOrganizer" in Globals.PACT_config["MAIN"]["MO2 EXE"]:
            self.RegBT_Browse_MO2.setStyleSheet("background-color: lightgreen; border-radius: 5px; border: 1px solid gray;")
            self.RegBT_Browse_MO2.setText("✔️ MO2 EXECUTABLE SET")
            self.configured_MO2 = True

        # Button - Browse XEDIT EXE
        self.RegBT_Browse_XEDIT = QtWidgets.QPushButton(PACT_MainWin)
        self.RegBT_Browse_XEDIT.setGeometry(QtCore.QRect(410, 50, 150, 32))
        self.RegBT_Browse_XEDIT.setObjectName("RegBT_Browse_XEDIT")
        self.RegBT_Browse_XEDIT.setText("SET XEDIT EXECUTABLE")
        self.RegBT_Browse_XEDIT.setStyleSheet("background-color: lightyellow; border-radius: 5px; border: 1px solid gray;")
        self.RegBT_Browse_XEDIT.clicked.connect(self.select_file_xedit)  # type: ignore
        if "Edit" in Globals.PACT_config["MAIN"]["XEDIT EXE"]:
            self.RegBT_Browse_XEDIT.setStyleSheet("background-color: lightgreen; border-radius: 5px; border: 1px solid gray;")
            self.RegBT_Browse_XEDIT.setText("✔️ XEDIT EXECUTABLE SET")
            self.configured_XEDIT = True

        # SEPARATOR LINE 1
        self.Line_Separator_1 = QtWidgets.QFrame(PACT_MainWin)
        self.Line_Separator_1.setGeometry(QtCore.QRect(80, 100, 480, 20))
        self.Line_Separator_1.setFrameShape(QtWidgets.QFrame.Shape.HLine)  # type: ignore
        self.Line_Separator_1.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)  # type: ignore
        self.Line_Separator_1.setObjectName("Line_Separator_1")

        # SEPARATOR TEXT 1
        self.LBL_Settings1 = QtWidgets.QLabel(PACT_MainWin)
        self.LBL_Settings1.setGeometry(QtCore.QRect(50, 120, 550, 24))
        self.LBL_Settings1.setText("YOU NEED TO SET YOUR LOAD ORDER FILE AND XEDIT EXECUTABLE BEFORE CLEANING")
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.LBL_Settings1.setFont(font)
        self.LBL_Settings1.setObjectName("LBL_NOTE_SET")

        # SEPARATOR TEXT 2
        self.LBL_Settings2 = QtWidgets.QLabel(PACT_MainWin)
        self.LBL_Settings2.setGeometry(QtCore.QRect(120, 140, 550, 24))
        self.LBL_Settings2.setText("( MOD ORGANIZER 2 USERS ALSO NEED TO SET MO2 EXECUTABLE )")
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.LBL_Settings2.setFont(font)
        self.LBL_Settings2.setObjectName("LBL_NOTE_MO2")

        # MAIN
        # Button - CLEAN PLUGINS
        self.RegBT_CLEAN_PLUGINS = QtWidgets.QPushButton(PACT_MainWin)
        self.RegBT_CLEAN_PLUGINS.setGeometry(QtCore.QRect(245, 200, 150, 32))
        self.RegBT_CLEAN_PLUGINS.setObjectName("RegBT_CLEAN_PLUGINS")
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.RegBT_CLEAN_PLUGINS.setFont(font)
        self.RegBT_CLEAN_PLUGINS.setText("START CLEANING")
        self.RegBT_CLEAN_PLUGINS.setStyleSheet("background-color: lightblue; border-radius: 5px; border: 1px solid gray;")
        self.RegBT_CLEAN_PLUGINS.clicked.connect(self.start_cleaning)  # type: ignore

        # BOTTOM
        # Button - HELP
        self.RegBT_Help = QtWidgets.QPushButton(PACT_MainWin)
        self.RegBT_Help.setGeometry(QtCore.QRect(20, 280, 110, 24))
        self.RegBT_Help.setObjectName("RegBT_Help")
        self.RegBT_Help.setText("HELP")
        self.RegBT_Help.setToolTip("How To Use PACT GUI")
        self.RegBT_Help.clicked.connect(self.help_popup)  # type: ignore

        # Button - Check Updates
        self.RegBT_CheckUpdates = QtWidgets.QPushButton(PACT_MainWin)
        self.RegBT_CheckUpdates.setGeometry(QtCore.QRect(245, 280, 150, 24))
        self.RegBT_CheckUpdates.setObjectName("RegBT_CheckUpdates")
        self.RegBT_CheckUpdates.setText("CHECK FOR UPDATES")
        self.RegBT_CheckUpdates.clicked.connect(self.update_popup)  # type: ignore

        # Button - EXIT
        self.RegBT_Exit = QtWidgets.QPushButton(PACT_MainWin)
        self.RegBT_Exit.setGeometry(QtCore.QRect(510, 280, 110, 24))
        self.RegBT_Exit.setObjectName("RegBT_Exit")
        self.RegBT_Exit.setText("EXIT")
        self.RegBT_Exit.setToolTip("Exit PACT GUI")
        self.RegBT_Exit.clicked.connect(PACT_MainWin.close)  # type: ignore

        # Add progress bar
        self.progress = QtWidgets.QProgressBar(PACT_MainWin)
        self.progress.setGeometry(QtCore.QRect(20, 240, 600, 24))
        self.progress.setObjectName("progress")
        self.progress.setValue(0)
        self.progress.hide()
        self.progress.setFormat("CLEANING PLUGINS... PLEASE WAIT %v/%m")

    # ============== CLEAN PLUGINS BUTTON STATES ================

    def start_cleaning(self):
        if self.thread is None:
            self.thread = PactThread()
            self.thread.start()
            with button_enabled(self.RegBT_CLEAN_PLUGINS):
                self.RegBT_CLEAN_PLUGINS.setText("STOP CLEANING") # type: ignore
                self.RegBT_CLEAN_PLUGINS.setStyleSheet("background-color: pink; border-radius: 5px; border: 1px solid gray;") # type: ignore
                self.RegBT_CLEAN_PLUGINS.clicked.disconnect() # type: ignore
                self.RegBT_CLEAN_PLUGINS.clicked.connect(self.stop_cleaning) # type: ignore
            with button_enabled(self.RegBT_Exit, enabled=False):
                pass


    def stop_delay_style(self):
        with button_enabled(self.RegBT_CLEAN_PLUGINS):
            self.RegBT_CLEAN_PLUGINS.setText("START CLEANING") # type: ignore
            self.RegBT_CLEAN_PLUGINS.setStyleSheet("background-color: lightblue; border-radius: 5px; border: 1px solid gray;") # type: ignore
            self.RegBT_CLEAN_PLUGINS.clicked.disconnect() # type: ignore
            self.RegBT_CLEAN_PLUGINS.clicked.connect(self.start_cleaning) # type: ignore
        with button_enabled(self.RegBT_Exit):
            pass


    def stop_cleaning(self):
        if self.thread is not None:
            self.thread.terminate()
            self.thread.wait()
            self.thread = None
            with button_enabled(self.RegBT_CLEAN_PLUGINS, enabled=False):
                self.RegBT_CLEAN_PLUGINS.setText("...STOPPING...") # type: ignore
                self.RegBT_CLEAN_PLUGINS.setStyleSheet("background-color: orange; border-radius: 5px; border: 1px solid gray;") # type: ignore
                print("\n❌ CLEANING STOPPED! PLEASE WAIT UNTIL ALL RUNNING PROGRAMS ARE CLOSED BEFORE STARTING AGAIN!\n")
                QTimer.singleShot(5000, lambda: self.stop_delay_style())
            with button_enabled(self.RegBT_Exit):
                pass

    def check_config(self):
        button_configs = {
            (False, False): {
                "enabled": False,
                "text": "START CLEANING",
                "style": "background-color: lightgray; border-radius: 5px; border: 1px solid gray;",
                "clicked": self.start_cleaning,
            },
            (True, False): {
                "enabled": False,
                "text": "START CLEANING",
                "style": "background-color: lightgray; border-radius: 5px; border: 1px solid gray;",
                "clicked": self.start_cleaning,
            },
            (False, True): {
                "enabled": False,
                "text": "START CLEANING",
                "style": "background-color: lightgray; border-radius: 5px; border: 1px solid gray;",
                "clicked": self.start_cleaning,
            },
            (True, True): {
                "enabled": True,
                "text": "STOP CLEANING",
                "style": "background-color: pink; border-radius: 5px; border: 1px solid gray;",
                "clicked": self.stop_cleaning,
            },
        }
    
        config = (self.configured_LO, self.configured_XEDIT)
        if config in button_configs:
            button_config = button_configs[config]
            self.RegBT_CLEAN_PLUGINS.setEnabled(button_config["enabled"]) # type: ignore
            self.RegBT_CLEAN_PLUGINS.setText(button_config["text"]) # type: ignore
            self.RegBT_CLEAN_PLUGINS.setStyleSheet(button_config["style"]) # type: ignore
            self.RegBT_CLEAN_PLUGINS.clicked.disconnect() # type: ignore
            self.RegBT_CLEAN_PLUGINS.clicked.connect(button_config["clicked"]) # type: ignore
    
        if self.thread is not None:
            thread = PactThread()
            if thread.cleaning_done is True:
                thread.finished_signal.connect(thread.quit) # type: ignore
                thread.finished_signal.connect(thread.wait) # type: ignore
                self.thread = None
                QTimer.singleShot(5000, self.stop_delay_style)
    

    @enable_button_if_configured    
    def disable_config_lo(self):
        self.configured_LO = False
    
    @enable_button_if_configured
    def enable_config_lo(self):
        self.configured_LO = True
    
    @enable_button_if_configured
    def disable_config_mo2(self):
        self.configured_MO2 = False
    
    @enable_button_if_configured
    def enable_config_mo2(self):
        self.configured_MO2 = True
    
    @enable_button_if_configured
    def disable_config_xedit(self):
        self.configured_XEDIT = False
    
    @enable_button_if_configured
    def enable_config_xedit(self):
        self.configured_XEDIT = True

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
        if pact_update_check(Globals.PACT_Current):
            QtWidgets.QMessageBox.information(PACT_MainWin, "PACT Update", "You have the latest version of PACT!")
        else:
            QtWidgets.QMessageBox.warning(PACT_MainWin, "PACT Update", "New PACT version is available!\nPress OK to open the PACT Nexus Page.")
            QDesktopServices.openUrl(QUrl("https://www.nexusmods.com/fallout4/mods/56255"))

    # ================= MAIN BUTTON FUNCTIONS ===================

    def select_file_lo(self):
        LO_file, _ = QFileDialog.getOpenFileName(filter="*.txt") # type: ignore
        if "loadorder" in LO_file or "plugins" in LO_file:
            QtWidgets.QMessageBox.information(PACT_MainWin, "New Load Order File Set", f"You have set the new path to: {LO_file} \n")
            pact_ini_update("LoadOrder TXT", LO_file)
            self.enable_config_lo()
        else:
            self.disable_config_lo()
        update_file_button(LO_file, self.RegBT_Browse_LO, "✔️ LOAD ORDER FILE SET", "❌ WRONG LO FILE") # type: ignore
    
    def select_file_mo2(self):
        MO2_EXE, _ = QFileDialog.getOpenFileName(filter="*.exe") # type: ignore
        if "ModOrganizer" in MO2_EXE:
            QtWidgets.QMessageBox.information(PACT_MainWin, "New MO2 Executable Set", "You have set MO2 to: \n" + MO2_EXE)
            pact_ini_update("MO2 EXE", MO2_EXE)
            self.enable_config_mo2()
        else:
            self.disable_config_mo2()
        update_file_button(MO2_EXE, self.RegBT_Browse_MO2, "✔️ MO2 EXECUTABLE SET", "❌ WRONG MO2 EXE") # type: ignore
    
    def select_file_xedit(self):
        XEDIT_EXE, _ = QFileDialog.getOpenFileName(filter="*.exe") # type: ignore
        if "Edit" in XEDIT_EXE:
            QtWidgets.QMessageBox.information(PACT_MainWin, "New MO2 Executable Set", "You have set XEDIT to: \n" + XEDIT_EXE)
            pact_ini_update("XEDIT EXE", XEDIT_EXE)
            self.enable_config_xedit()
        else:
            self.disable_config_xedit()
        update_file_button(XEDIT_EXE, self.RegBT_Browse_XEDIT, "✔️ XEDIT EXECUTABLE SET", "❌ WRONG XEDIT EXE") # type: ignore
    


# CLEANING NEEDS A SEPARATE THREAD SO IT DOESN'T FREEZE PACT GUI
class PactThread(QThread):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cleaning_done = False

    def run(self):  # def Plugins_CLEAN():
        check_process_mo2()
        while not self.cleaning_done:
            check_settings_paths(Globals.PACT_config)
            check_settings_integrity()
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
    PACT_MainWin = QtWidgets.QDialog()
    ui = UiPACTMainWin()
    ui.setup_ui(PACT_MainWin)
    PACT_MainWin.show()
    sys.exit(app.exec())
