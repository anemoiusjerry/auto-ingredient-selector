from __future__ import print_function
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

class TabDialog(QTabWidget):

    def __init__(self, app, parent=None):
        super(TabDialog, self).__init__(parent)
        self.config = FigMe()
        self.setWindowTitle("RTE Automatron")

        self.landingTab = LandingTab(self.config, app)
        self.InfoModuleTab = InfoTab(self.config)

        self.addTab(self.landingTab, "General")
        self.addTab(self.InfoModuleTab, "Info Paragraphs")

    def closeEvent(self, *args, **kwargs):
        """ Save browsed paths to config
        """
        json_obj = json.dumps(self.config, indent=4)
        with open("config/config.json", "w") as outfile:
            outfile.write(json_obj)

def main():
    """ Central control point for all modules.
    """
    # Load UI
    app = QApplication(sys.argv)
    window = TabDialog(app)
    window.show()
    sys.exit(app.exec_())
