import sys
from PySide2.QtWidgets import QApplication, QStyle
from mainWindow import MainWindow

import faulthandler; faulthandler.enable()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    #app.setStyle(QStyle.QWindowsStyle())

    window = MainWindow()
    window.show()


    sys.exit(app.exec_())
