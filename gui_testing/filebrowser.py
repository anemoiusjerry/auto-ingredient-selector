from PySide2.QtCore import QDir, QFile, Signal
from PySide2.QtWidgets import QWidget, QFileDialog, QGridLayout, QLineEdit, QPushButton, QDialog, QLabel, QFrame, QMessageBox


class FileBrowser(QDialog):

    def __init__(self, type, label, parent=None):
        super(FileBrowser,self).__init__(parent)

        frameStyle = QFrame.Sunken | QFrame.StyledPanel
        self.type = type

        if type == "csv":
            self.label = QLabel(label)
            self.button = self.createCsvButton()
            self.display = QLineEdit("")
        else:
            self.label = QLabel(label)
            self.button = self.createDirButton()
            self.display = QLineEdit("")

        self.display.editingFinished.connect(self.checkPath)

        layout = QGridLayout()
        layout.addWidget(self.label,0,0)
        layout.addWidget(self.display,1,0)
        layout.addWidget(self.button,1,1)
        self.setLayout(layout)
        self.setMinimumWidth(500)
        self.setFixedHeight(80)

    def createCsvButton(self):
        button = QPushButton("&Browse")
        button.clicked.connect(self.findCSV)
        return button

    def createDirButton(self):
        button = QPushButton("&Browse")
        button.clicked.connect(self.findDir)
        return button

    def findDir(self):
        directory = QFileDialog.getExistingDirectory(self, "Save Location")
        if directory:
            self.display.setText(directory)

    def findCSV(self):
        directory = QFileDialog.getOpenFileName(self, "Select .csv file", "", "csv file (*.csv)")
        if directory:
            self.display.setText(directory[0])

    def checkPath(self):
        file = self.display.text()
        path = QDir(file)

        if self.type == "dir":
            if not QDir.exists(path):
                message = "sorry the directory  '" + file + "'  does not exist.\nPlease select a valid directory."
                self.displayWarningDialog(message)
                self.display.setText("")

        elif self.type == "csv":
            if not QFile.exists(file):
                message = "File does not exist in the specified directory.\nPlease select a valid csv file."
                self.displayWarningDialog(message)
                self.display.setText("")

            elif file[-4:] != ".csv":
                message = "File is not a .csv file\nPlease select a valid csv file."
                self.displayWarningDialog(message)
                self.display.setText("")

    def displayWarningDialog(self, text):
        warning = QMessageBox(QMessageBox.Warning, "Invalid Filepath", text, QMessageBox.NoButton)
        warning.addButton("Ok", QMessageBox.AcceptRole)
        warning.exec_()
