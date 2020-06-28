from PySide2.QtWidgets import *

class WarningRaiser:

    def displayWarningDialog(self, error_type, error_text):
        warning = QMessageBox(QMessageBox.Warning, error_type, error_text, QMessageBox.NoButton)
        warning.addButton("Ok", QMessageBox.AcceptRole)
        warning.exec_()