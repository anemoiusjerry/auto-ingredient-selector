from PySide2.QtWidgets import (QApplication, QLabel, QWidget, QPushButton,
    QDialog, QLineEdit, QVBoxLayout)
from PySide2.QtQuick import QQuickView
from PySide2.QtCore import QUrl
from PySide2.QtCore import Slot

import sys
import time

'''class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Optimised Ingredient Finder")
        self.setGeometry(300,300,800,600)
        self.setMinimumHeight(200)
        self.setMinimumWidth(200)
'''
#Create a window
'''
myApp = QApplication(sys.argv)
window = Window()
window.show()

myApp.exec_()
sys.exit()'''

#Using a qml file
'''app = QApplication([])
view = QQuickView()
url = QUrl("view.qml")

view.setResizeMode(QQuickView.SizeRootObjectToView)
view.setSource(url)
view.show()
app.exec_()'''

#
'''@Slot()
def say_hello():
 print("Button clicked, Hello!")

# Create the Qt Application
app = QApplication(sys.argv)
# Create a button, connect it and show it
button = QPushButton("Click me")
button.clicked.connect(say_hello)
button.show()
# Run the main Qt loop
app.exec_()
'''

class Form(QDialog):

    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        # Create widgets
        self.edit = QLineEdit("Write my name here")
        self.button = QPushButton("Show Greetings")
        # Create layout and add widgets
        layout = QVBoxLayout()
        layout.addWidget(self.edit)
        layout.addWidget(self.button)
        # Set dialog layout
        self.setLayout(layout)
        # Add button signal to greetings slot
        self.button.clicked.connect(self.greetings)

    # Greets the user
    def greetings(self):
        print ("Hello %s" % self.edit.text())

if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    form = Form()
    form.show()
    # Run the main Qt loop
    sys.exit(app.exec_())
