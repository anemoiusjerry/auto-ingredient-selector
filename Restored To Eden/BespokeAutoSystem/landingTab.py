import io, traceback, sys
import pandas as pd
from PySide2.QtCore import Qt, QObject, Signal, Slot, QRunnable, QThreadPool
from PySide2.QtWidgets import *
from PySide2.QtGui import QKeySequence, QPalette, QColor

from .fileBrowser import FileBrowser
from .Gdriver import Gdriver
from .Modules.IngredientSelector import IngredientSelector
from .Modules import FormulationFiller
from config.configParser import FigMe

class LandingTab(QWidget):

    def __init__(self, config, app):
        QWidget.__init__(self)
        self.threadpool = QThreadPool()
        self.config = config
        self.gdriveAPI = Gdriver()
        self.defaultmode, self.darkmode = self.define_palettes()

        # Dict of widget { wid_name: widget object }
        self.widgets = {}
        # UI Datasheets
        self.widgets["patient_sheet"] = FileBrowser("csv", "Customer Questionnaire", self.config)
        self.widgets["catalog_sheet"] = FileBrowser("csv", "Product Catalog", self.config)
        self.widgets["ingredient_sheet"] = FileBrowser("csv", "Ingredients Spreadsheet", self.config)
        self.widgets["orders_sheet"] = FileBrowser("csv", "Orders Spreadsheet", self.config)

        self.widgets["formulation_dir"] = FileBrowser("dir", "Formulation Sheets Directory", self.config)
        self.widgets["save_dir"] = FileBrowser("dir", "Export Directory", self.config)

        # Display widgets in layout
        layout = QVBoxLayout()
        for wid in self.widgets.values():
            layout.addWidget(wid)

        footer_layout = QGridLayout()
        self.run_button = QPushButton("&Run")
        self.run_button.clicked.connect(self.runDLX)
        self.run_button.setFixedWidth(70)
        footer_layout.addWidget(self.run_button, 0, 0)

        # Dark mode toggle button
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1)
        self.slider.setValue(config.getVal("darkmode"))
        self.slider.setFixedWidth(40)
        self.slider.valueChanged.connect(lambda: self.toggleDark(app))
        self.toggleDark(app)
        toggle_label = QLabel("Go Dark")
        toggle_label.setFixedWidth(50)

        toggle_layout = QGridLayout()
        toggle_layout.addWidget(toggle_label, 0, 0)
        toggle_layout.addWidget(self.slider, 0, 1)
        footer_layout.addLayout(toggle_layout, 0, 1)

        layout.addLayout(footer_layout)
        self.setLayout(layout)

    def define_palettes(self):
        default_palette = QPalette()
        # Dark mode
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
        return default_palette, dark_palette

    def toggleDark(self, app):
        if self.slider.value() == 0:
            app.setPalette(self.defaultmode)
        else:
            app.setPalette(self.darkmode)
        self.config.setVal("darkmode", self.slider.value())

    def runDLX(self):
        self.config.saveConfig()
        # Load spreadsheets into pandas DataFrames
        self.dataframes = self.createDataFrames()

        # Start ingredient selection process
        ingredient_selector = IngredientSelector(self.dataframes["Orders Spreadsheet"],
                                    self.dataframes["Ingredients Spreadsheet"],
                                    self.dataframes["Customer Questionnaire"],
                                    self.dataframes["Product Catalog"])

        ingredient_selector.launched.connect(self.launchProgress)
        ingredient_selector.stateChanged.connect(self.progStateChanged)

        worker = Worker(ingredient_selector.selectIngredients)
        worker.signals.result.connect(self.processResults)

        self.threadpool.start(worker)

    @Slot(object)
    def processResults(self, results):
        # Start formulation calculations for all orders
        filler = FormulationFiller.FormulationFiller(self.dataframes["Ingredients Spreadsheet"], self.gdriveAPI)
        filler.process_all(results)

    def createDataFrames(self):
        # Store all dataframes in dictionary
        #config = FigMe()
        dataframes = {}

        for key in self.widgets.keys():
            # Only process to df if widget stores a spreadsheet
            fetch_name = self.widgets[key].label.text()
            df = self.config.getDF(fetch_name)
            dataframes[self.widgets[key].label.text()] = df

        return dataframes

    @Slot(int)
    def launchProgress(self, end):

        self.primaryMsg = "Running Ingredient Sorter\n"
        self.prog = QProgressDialog(self.primaryMsg, "Cancel", 0, end)

        self.prog.setMinimumDuration(1)
        self.prog.setFixedSize(300, 150)
        print("launching progress dialog")
        self.prog.exec_()#worker = Worker(self.prog.exec_)
        #self.threadpool.start(worker)
        print("dialog launched")


    @Slot(str, str, int)
    def progStateChanged(self, state, info, i):
        # Set the new value of the progress bar
        self.prog.setValue(i)

        if state == "retrieve":
            # The info should be the order number followed by the name
            text = self.primaryMsg + "Retrieving order: " + info

        if state == "finding":
            # The info should be the number of solutions found so far
            text = self.primaryMsg + "Finding ingredient combinations: " + info

        if state == "sorting":
            text = self.primaryMsg + "Finding the best solution.\nSolutions sorted: " + info

        self.prog.setLabelText(text)

class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        # fn = function to be run in the thread
        # *args = list of arguments the function uses
        # **kwargs = any signals the function will use. e.g.
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        #self.kwargs['cancel_signal'] = self.signals.cancel

    @Slot()
    def run(self):
        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done

class WorkerSignals(QObject):
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    cancel = Signal()
