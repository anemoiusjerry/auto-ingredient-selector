from PySide2.QtCore import Qt
from PySide2.QtGui import QKeySequence
from PySide2.QtWidgets import QMainWindow, QWidget, QAction, QPushButton, QVBoxLayout, QMessageBox
from filebrowser import FileBrowser
from runbutton import RunButton

class MainWindow(QWidget):

    def __init__(self):
        QWidget.__init__(self)

        self.setWindowTitle("This is a test")
        self.ingredient_browser = FileBrowser("csv", "Ingredient Info:")
        self.patient_browser = FileBrowser("csv", "Patient Info:")
        self.save_browser = FileBrowser("dir", "Save Location:")
        self.run_button = RunButton()

        layout = QVBoxLayout()
        layout.addWidget(self.ingredient_browser)
        layout.addWidget(self.patient_browser)
        layout.addWidget(self.save_browser)
        layout.addWidget(self.run_button)

        self.setLayout(layout)
