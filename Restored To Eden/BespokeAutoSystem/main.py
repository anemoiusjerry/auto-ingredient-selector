from __future__ import print_function
import os
import sys
import json
from PySide2.QtCore import Qt
from PySide2.QtGui import QKeySequence, QPalette, QColor
from PySide2.QtWidgets import *

# Own .py files
from config.configParser import FigMe
import faulthandler; faulthandler.enable()
from .landingTab import LandingTab
from .infoSheetTab import InfoTab
from .prefTab import PrefTab

class TabDialog(QTabWidget):

    def __init__(self, app, parent=None):
        super(TabDialog, self).__init__(parent)
        self.config = FigMe()
        self.setWindowTitle("RTE Automatron")

        self.landingTab = LandingTab(self.config, app)
        self.InfoModuleTab = InfoTab(self.config)
        self.PrefTab = PrefTab(self.config)

        self.addTab(self.landingTab, "General")
        self.addTab(self.InfoModuleTab, "Info Paragraphs")
        self.addTab(self.PrefTab, "Preferences")

    def closeEvent(self, *args, **kwargs):
        """ Save browsed paths to config
        """
        self.config.saveConfig()

def main():
    """ Central control point for all modules.
    """
    # # This line changes cwd to RTE folder (for Windows)
    # if os.name == "nt":
    #     os.chdir(os.getcwd() + "/Restored To Eden")
    # Load UI
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = TabDialog(app)
    window.show()
    sys.exit(app.exec_())
