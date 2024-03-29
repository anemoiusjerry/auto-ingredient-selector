from PySide2.QtCore import QDir, QFile, Signal
from PySide2.QtWidgets import *


class FileBrowser(QDialog):

    def __init__(self, type, label, config, parent=None, **kwargs):
        super(FileBrowser,self).__init__(parent)

        frameStyle = QFrame.Sunken | QFrame.StyledPanel
        self.type = type

        self.label = QLabel(label)
        # try to get saved path
        try:
            save_path = config.getDir(label)
        except:
            save_path = ""
        self.display = QLineEdit(save_path)

        self.button = self.createButton(type, config)
        self.display.editingFinished.connect(self.checkPath)

        layout = QGridLayout()
        layout.addWidget(self.label,0,0)

        # Check whether google drive for this property is enabled
        if kwargs.get("Gdrive"):
            self.gdriveName = QLineEdit(config.getGdrive(label))
            self.gdriveName.setPlaceholderText("Google Drive filename")
            self.gdriveName.editingFinished.connect(lambda: config.setGdrive(label, self.gdriveName.text()))
            layout.addWidget(self.gdriveName,1,0)
            layout.addWidget(self.display,1,1)
            layout.addWidget(self.button,1,2)
        else:
            layout.addWidget(self.display,1,0)
            layout.addWidget(self.button,1,1)

        self.setLayout(layout)
        self.setMinimumWidth(200)
        self.setFixedHeight(80)

    def createButton(self, type, config):
        button = QPushButton("&Browse")

        if type == "csv":
            button.clicked.connect(lambda: self.findCSV(config))
        else:
            button.clicked.connect(lambda: self.findDir(config))
        return button

    def findDir(self, config):
        directory = QFileDialog.getExistingDirectory(self, "Save Location")
        if directory:
            self.display.setText(directory)
            # Save new path to master config
            config.setDir(self.label.text(), directory)

    def findCSV(self, config):
        directory = QFileDialog.getOpenFileName(self, "Select .csv file", "", "Excel Files (*.csv *.xlsx);; All Files (*)")
        if directory:
            self.display.setText(directory[0])
            # Save new path to master config
            config.setDir(self.label.text(), directory[0])

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

    def getLabel():
        return self.label.text()
