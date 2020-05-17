from PySide2.QtCore import QDir, Qt, Signal
from PySide2.QtWidgets import QWidget, QFileSystemModel, QTreeView, QGridLayout
import os

class Browser(QWidget):


    FILE_DOUBLE_CLICKED = Signal(str)

    def __init__(self,filter):
        QWidget.__init__(self)
        self.filter = filter
        self.init_UI()

    def init_UI(self,path="/Users/HG/Desktop"):
        self.model = QFileSystemModel()
        self.model.setRootPath(path)
        self.model.setNameFilters(self.filter)
        self.model.setNameFilterDisables(False)
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(path))
        self.tree.setAnimated(False)
        self.tree.setIndentation(20)
        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(0,Qt.AscendingOrder)
        self.tree.setColumnWidth(0,200)
        self.tree.setColumnWidth(1,100)
        self.tree.setColumnWidth(2,100)
        self.tree.doubleClicked.connect(self.open_file)
        self.UIgrid = QGridLayout()
        self.UIgrid.addWidget(self.tree,0,0)
        self.UIgrid.setContentsMargins(0,0,2,0)
        self.setLayout(self.UIgrid)
        self.show()

    def open_file(self,index):
        item = self.tree.selectedIndexes()[0]
        path = item.model().filePath(index)
        if os.path.isfile(path):
            self.FILE_DOUBLE_CLICKED.emit(path)

    def tree_update(self,path):
        dir = os.path.dirname(path)
        self.model.setRootPath(dir)
        self.tree.setRootIndex(self.model.index(dir))
