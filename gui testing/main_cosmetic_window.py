import PySide2.QtCore
from PySide2.QtGui import QKeySequence
from PySide2.QtWidgets import QMainWindow, QAction

class MainWindow(QMainWindow):
    def __init__(self, widget):
        QMainWindow.__init__(self)

        self.setWindowTitle("This is a test")
        self.setCentralWidget(widget)

        geometry = qApp.desktop().availableGeometry(self)
        #self.setFixedSize(geometry.width(), geometry.height())
