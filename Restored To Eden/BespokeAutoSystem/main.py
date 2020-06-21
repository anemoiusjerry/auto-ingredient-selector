from __future__ import print_function
import sys
import json
from PySide2.QtCore import Qt
from PySide2.QtGui import QKeySequence, QPalette, QColor
from PySide2.QtWidgets import *

# Own .py files
import faulthandler; faulthandler.enable()
from .landingTab import LandingTab
from .infoSheetTab import InfoTab

class TabDialog(QTabWidget):

    def __init__(self, config, parent=None):
        super(TabDialog, self).__init__(parent)
        self.config = config
        self.setWindowTitle("RTE Automatron")

        self.landingTab = LandingTab(self.config)
        self.InfoModuleTab = InfoTab(self.config)

        self.addTab(self.landingTab, "General")
        self.addTab(self.InfoModuleTab, "Info Paragraphs")

    def toggleDarkMode(self, app):
        # Dark mode
        app.setStyle("Fusion")
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white) 
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        app.setPalette(dark_palette)

    def closeEvent(self, *args, **kwargs):
        """ Save browsed paths to config
        """
        json_obj = json.dumps(self.config, indent=4)
        with open("config.json", "w") as outfile:
            outfile.write(json_obj)

def main():
    """ Central control point for all modules.
    """
    # Load config
    with open("config.json") as json_file:
        config = json.load(json_file)
    # Load UI
    app = QApplication(sys.argv)
    window = TabDialog(config)
    window.toggleDarkMode(app)
    window.show()
    sys.exit(app.exec_())    

  