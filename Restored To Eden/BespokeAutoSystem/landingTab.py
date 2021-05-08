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
from .WarningRaiser import WarningRaiser

class LandingTab(QWidget):

    def __init__(self, config, app):
        QWidget.__init__(self)
        self.threadpool = QThreadPool()
        self.config = config
        self.gdriveAPI = Gdriver()
        self.defaultmode, self.darkmode = self.define_palettes()
        self.warn = WarningRaiser()

        # Dict of widget { wid_name: widget object }
        self.widgets = {}
        # UI Datasheets
        self.widgets["orders_sheet"] = FileBrowser("csv", "Orders Spreadsheet", self.config)
        self.widgets["patient_sheet"] = FileBrowser("csv", "Customer Questionnaire", self.config)
        self.widgets["catalog_sheet"] = FileBrowser("csv", "Product Catalog", self.config, Gdrive=True)
        self.widgets["ingredient_sheet"] = FileBrowser("csv", "Ingredients Spreadsheet", self.config, Gdrive=True)
        # Directories
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

        # Google drive toggle button
        gdrive_toggle_layout = self.create_toggle_button("G-Drive")
        footer_layout.addLayout(gdrive_toggle_layout, 0, 1)
        self.gdrive_slider = gdrive_toggle_layout.itemAt(1).widget()
        # Set val from config
        self.gdrive_slider.setValue(config.masterDict["gdrive"])
        self.gdrive_slider.valueChanged.connect(lambda: config.setter("gdrive", self.gdrive_slider.value()))

        # Dark mode toggle button
        dark_toggle_layout = self.create_toggle_button("Go Dark")
        footer_layout.addLayout(dark_toggle_layout, 0, 2)
        self.dark_slider = dark_toggle_layout.itemAt(1).widget()
        # Set last value from config
        self.dark_slider.setValue(config.masterDict["darkmode"])
        self.dark_slider.valueChanged.connect(lambda: self.toggleDark(app))
        self.toggleDark(app)

        layout.addLayout(footer_layout)
        self.setLayout(layout)

    def create_toggle_button(self, label):
        toggle_label = QLabel(label)
        toggle_label.setFixedWidth(50)

        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(1)
        slider.setFixedWidth(40)
        # Package into layout
        toggle_layout = QGridLayout()
        toggle_layout.addWidget(toggle_label, 0, 0)
        toggle_layout.addWidget(slider, 0, 1)
        return toggle_layout

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
        if self.dark_slider.value() == 0:
            app.setPalette(self.defaultmode)
        else:
            app.setPalette(self.darkmode)
        self.config.setter("darkmode", self.dark_slider.value())

    def runDLX(self):
        self.config.saveConfig()
        # Load spreadsheets into pandas DataFrames
        self.dataframes = self.createDataFrames()

        # Start ingredient selection process
        self.ingredient_selector = IngredientSelector(self.dataframes["Orders Spreadsheet"],
                                    self.dataframes["Ingredients Spreadsheet"],
                                    self.dataframes["Customer Questionnaire"],
                                    self.dataframes["Product Catalog"])

        self.ingredient_selector.launched.connect(self.launchProgress)
        self.ingredient_selector.stateChanged.connect(self.progStateChanged)
        self.ingredient_selector.error.connect(self.showError)

        try:
            worker = Worker(self.ingredient_selector.selectIngredients)
        except Exception as e:
            print(e)
        worker.signals.result.connect(self.processResults)
        self.threadpool.start(worker)

    @Slot(object)
    def processResults(self, results):
        # Start formulation calculations for all orders
        if not results == None:
            filler = FormulationFiller.FormulationFiller(self.dataframes["Ingredients Spreadsheet"], self.gdriveAPI)
            #filler.process_all(results)
            self.prog.canceled.connect(filler.stop_)
            filler.stateChanged.connect(self.progStateChanged)
            filler.error.connect(self.showError)
            
            worker = Worker(lambda: filler.process_all(results))
            worker.signals.result.connect(self.closeProg)
            self.threadpool.start(worker)

        else:
            self.warn.displayWarningDialog("No Orders Fulfilled",
                "No Orders Fulfilled\n\nError can occur when:\n- Searching and sorting operation was cancelled.\n- No Matching orders and questionnaires were found.")
        self.closeProg()

    @Slot()
    def closeProg(self):
        self.prog.cancel()

    @Slot(str)
    def showError(self, errors):
        self.warn.displayWarningDialog("Error", errors)

    def createDataFrames(self):
        # Store all dataframes in dictionary
        dataframes = {}

        for key in self.widgets.keys():
            # Only process to df if widget stores a spreadsheet
            if not ("dir" in key):
                fetch_name = self.widgets[key].label.text()
                df = self.config.getDF(fetch_name)
                dataframes[self.widgets[key].label.text()] = df

        return dataframes

    @Slot(int)
    def launchProgress(self, end):

        self.primaryMsg = "Running Ingredient Sorter\n"
        self.prog = QProgressDialog(self.primaryMsg, "Cancel", 0, end)
        self.prog.canceled.connect(self.ingredient_selector.stop_)
        self.prog.setMinimumDuration(1)
        self.prog.setFixedSize(400, 150)
        self.prog.exec_()

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

        # Formulation filler
        if state == "writing":
            text = self.primaryMsg + "Writing formulation sheet: \n" + info

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
