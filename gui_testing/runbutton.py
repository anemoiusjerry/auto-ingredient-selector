from PySide2.QtCore import QDir, Qt, Signal, QObject
from PySide2.QtWidgets import QWidget, QPushButton, QHBoxLayout


class RunButton(QWidget):

    def __init__(self, parent=None):
        super(RunButton,self).__init__(parent)

        self.button = QPushButton("&Run")
        self.button.clicked.connect(self.runDLX)
        self.button.setFixedWidth(70)

        layout = QHBoxLayout()
        layout.addWidget(self.button)
        layout.setAlignment(Qt.AlignRight)
        self.setLayout(layout)

    def runDLX(self):
        a=1
