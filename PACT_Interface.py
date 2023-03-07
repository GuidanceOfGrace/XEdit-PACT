import os
import sys
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QUrl, QTimer, QThread, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog
from PACT_Start import (PACT_config, PACT_Current, pact_ini_update, pact_update_check, check_settings_paths, check_settings_integrity, clean_plugins)

'''TEMPLATES
QMessageBox.NoIcon | Question | Information | Warning | Critical
'''

class UiPACTMainWin(object):
    def __init__(self):
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

        self.timer = QTimer()  # For CLEAN PLUGINS Button
        self.timer.timeout.connect(self.check_configured)
        self.timer.start(2000)  # In milliseconds.


    def setup_ui(self, PACT_MainWin):
        # MAIN WINDOW
        PACT_MainWin.setObjectName("PACT_MainWin")
        PACT_MainWin.setWindowTitle(f"Plugin Auto Cleaning Tool  {PACT_Current[-4:]}")
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
        if "loadorder" in PACT_config["MAIN"]["LoadOrder TXT"]:
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
        if "ModOrganizer" in PACT_config["MAIN"]["MO2 EXE"]:
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
        if "Edit" in PACT_config["MAIN"]["XEDIT EXE"]:
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
        self.RegBT_CLEAN_PLUGINS.setText("CLEAN PLUGINS")
        self.RegBT_CLEAN_PLUGINS.setStyleSheet("background-color: white; border-radius: 5px; border: 1px solid gray;")
        self.RegBT_CLEAN_PLUGINS.clicked.connect(self.start_cleaning)  # type: ignore
        self.worker = PACT_Worker()

        # BOTTOM
        # Button - HELP
        self.RegBT_Help = QtWidgets.QPushButton(PACT_MainWin)
        self.RegBT_Help.setGeometry(QtCore.QRect(20, 280, 110, 24))
        self.RegBT_Help.setObjectName("RegBT_Help")
        self.RegBT_Help.setText("HELP")
        self.RegBT_Help.setToolTip("How To Use PACT GUI")
        self.RegBT_Help.clicked.connect(self.Help_Popup)  # type: ignore
        
        # Button - Check Updates
        self.RegBT_CheckUpdates = QtWidgets.QPushButton(PACT_MainWin)
        self.RegBT_CheckUpdates.setGeometry(QtCore.QRect(245, 280, 150, 24))
        self.RegBT_CheckUpdates.setObjectName("RegBT_CheckUpdates")
        self.RegBT_CheckUpdates.setText("CHECK FOR UPDATES")
        self.RegBT_CheckUpdates.clicked.connect(self.Update_Popup)  # type: ignore
        
        # Button - EXIT
        self.RegBT_Exit = QtWidgets.QPushButton(PACT_MainWin)
        self.RegBT_Exit.setGeometry(QtCore.QRect(510, 280, 110, 24))
        self.RegBT_Exit.setObjectName("RegBT_Exit")
        self.RegBT_Exit.setText("EXIT")
        self.RegBT_Exit.setToolTip("Exit PACT GUI")
        self.RegBT_Exit.clicked.connect(PACT_MainWin.close)  # type: ignore


    # ============== CLEAN PLUGINS BUTTON STATES ================
    def start_cleaning(self):
        self.RegBT_CLEAN_PLUGINS.setEnabled(False)
        self.worker.start()

    def check_configured(self):
        if not (self.configured_LO and self.configured_XEDIT):
            self.RegBT_CLEAN_PLUGINS.setEnabled(False)

    def disable_config_lo(self):
        self.configured_LO = False
        self.RegBT_CLEAN_PLUGINS.setEnabled(self.configured_LO and self.configured_XEDIT)

    def enable_config_lo(self):
        self.configured_LO = True
        self.RegBT_CLEAN_PLUGINS.setEnabled(self.configured_LO and self.configured_XEDIT)

    def disable_config_mo2(self):
        self.configured_MO2 = False
        self.RegBT_CLEAN_PLUGINS.setEnabled(self.configured_LO and self.configured_XEDIT)

    def enable_config_mo2(self):
        self.configured_MO2 = True
        self.RegBT_CLEAN_PLUGINS.setEnabled(self.configured_LO and self.configured_XEDIT)

    def disable_config_xedit(self):
        self.configured_XEDIT = False
        self.RegBT_CLEAN_PLUGINS.setEnabled(self.configured_LO and self.configured_XEDIT)

    def enable_config_xedit(self):
        self.configured_XEDIT = True
        self.RegBT_CLEAN_PLUGINS.setEnabled(self.configured_LO and self.configured_XEDIT)

    # ================== POP-UPS / WARNINGS =====================

    help_popup_msg = """If you have trouble running this program or wish to submit your PACT logs for additional help, join the Collective Modding Discord server.
    
    Press OK to open the server link in your internet browser."""

    @staticmethod
    def Help_Popup():
        msgBox = QtWidgets.QMessageBox()
        msgBox.setIcon(QtWidgets.QMessageBox.Question)
        msgBox.setWindowTitle("Need Help?")
        msgBox.setText(UiPACTMainWin.help_popup_msg)  # RESERVED | msgBox.setInformativeText("...")
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        if msgBox.exec() != QtWidgets.QMessageBox.Cancel:
            QDesktopServices.openUrl(QUrl("https://discord.com/invite/7ZZbrsGQh4"))


    @staticmethod
    def Update_Popup():
        if pact_update_check():
            QtWidgets.QMessageBox.information(PACT_MainWin, "PACT Update", "You have the latest version of PACT!")
        else:
            QtWidgets.QMessageBox.warning(PACT_MainWin, "PACT Update", "New PACT version is available!\nPress OK to open the PACT Nexus Page.")
            QDesktopServices.openUrl(QUrl("https://www.nexusmods.com/fallout4/mods/56255"))

    # ================= MAIN BUTTON FUNCTIONS ===================
    # @staticmethod recommended for func that don't call "self".


    def select_file_lo(self):
        LO_file, _ = QFileDialog.getOpenFileName(filter="*.txt")
        if os.path.exists(LO_file) and "loadorder" in LO_file:
            QtWidgets.QMessageBox.information(PACT_MainWin, "New Load Order File Set", f"You have set the new path to: {LO_file} \n")  # type: ignore
            pact_ini_update("LoadOrder TXT", LO_file)
            self.RegBT_Browse_LO.setStyleSheet("background-color: lightgreen; border-radius: 5px; border: 1px solid gray;")
            self.RegBT_Browse_LO.setText("✔️ LOAD ORDER FILE SET")
            self.enable_config_lo()
        elif os.path.exists(LO_file) and "loadorder" not in LO_file:
            self.RegBT_Browse_LO.setStyleSheet("background-color: orange; border-radius: 5px; border: 1px solid gray;")
            self.RegBT_Browse_LO.setText("❌ WRONG LO FILE")
            self.disable_config_lo()

    def select_file_mo2(self):
        MO2_EXE, _ = QFileDialog.getOpenFileName(filter="*.exe")
        if os.path.exists(MO2_EXE) and "ModOrganizer" in MO2_EXE:
            QtWidgets.QMessageBox.information(PACT_MainWin, "New MO2 Executable Set", "You have set MO2 to: \n" + MO2_EXE)  # type: ignore
            pact_ini_update("MO2 EXE", MO2_EXE)
            self.RegBT_Browse_MO2.setStyleSheet("background-color: lightgreen; border-radius: 5px; border: 1px solid gray;")
            self.RegBT_Browse_MO2.setText("✔️ MO2 EXECUTABLE SET")
            self.enable_config_mo2()
        elif os.path.exists(MO2_EXE) and "ModOrganizer" not in MO2_EXE:
            self.RegBT_Browse_MO2.setText("❌ WRONG MO2 EXE")
            self.RegBT_Browse_MO2.setStyleSheet("background-color: orange; border-radius: 5px; border: 1px solid gray;")
            self.disable_config_mo2()

    def select_file_xedit(self):
        XEDIT_EXE, _ = QFileDialog.getOpenFileName(filter="*.exe")
        if os.path.exists(XEDIT_EXE) and "Edit" in XEDIT_EXE:
            QtWidgets.QMessageBox.information(PACT_MainWin, "New MO2 Executable Set", "You have set XEDIT to: \n" + XEDIT_EXE)  # type: ignore
            pact_ini_update("XEDIT EXE", XEDIT_EXE)
            self.RegBT_Browse_XEDIT.setStyleSheet("background-color: lightgreen; border-radius: 5px; border: 1px solid gray;")
            self.RegBT_Browse_XEDIT.setText("✔️ XEDIT EXECUTABLE SET")
            self.enable_config_xedit()
        elif os.path.exists(XEDIT_EXE) and "Edit" not in XEDIT_EXE:
            self.RegBT_Browse_XEDIT.setText("❌ WRONG XEDIT EXE")
            self.RegBT_Browse_XEDIT.setStyleSheet("background-color: orange; border-radius: 5px; border: 1px solid gray;")
            self.disable_config_xedit()


# NEEDS A SEPARATE THREAD SO IT DOESN'T FREEZE PACT GUI
class PACT_Worker(QThread):
    progress_signal = Signal(int)
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def run(self):  # def Plugins_CLEAN():
        pact_update_check()
        check_settings_paths()
        check_settings_integrity("FO4Edit", "Fallout4.esm")
        check_settings_integrity("SSEEdit", "Skyrim.esm")
        clean_plugins()
        for i in range(100):
            self.progress_signal.emit(i)
            self.msleep(100)


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
