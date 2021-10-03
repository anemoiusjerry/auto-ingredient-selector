from __future__ import print_function
import os

from PySide2 import QtGui
os.environ["QT_MAC_WANTS_LAYER"] = "1"
import sys
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

    def center(self):
        """ Get location of screen center """
        qRect = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qRect.moveCenter(centerPoint)
        self.move(qRect.topLeft())

def main():
    """ Central control point for all modules.
    """
    # Load UI
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QtGui.QFont("SF Pro Display", 12))
    window = TabDialog(app)
    window.show()
    # Center window
    qRect = window.frameGeometry()
    centerPoint = QDesktopWidget().availableGeometry().center()
    qRect.moveCenter(centerPoint)
    window.move(qRect.topLeft())
    sys.exit(app.exec_())
