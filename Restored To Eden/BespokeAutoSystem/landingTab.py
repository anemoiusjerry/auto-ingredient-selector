import io
import pandas as pd
from PySide2.QtCore import Qt
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
        self.config = config
        self.gdriveAPI = Gdriver()
        self.defaultmode, self.darkmode = self.define_palettes()

        # Dict of widget { wid_name: widget object }
        self.widgets = {}
        # UI Datasheets
        self.widgets["patient_sheet"] = FileBrowser("csv", "Customer Questionnaire", config)
        self.widgets["catalog_sheet"] = FileBrowser("csv", "Product Catalog", config)
        self.widgets["ingredient_sheet"] = FileBrowser("csv", "Ingredients Spreadsheet", config)
        self.widgets["orders_sheet"] = FileBrowser("csv", "Orders Spreadsheet", config)

        self.widgets["formulation_dir"] = FileBrowser("dir", "Formulation Sheets Directory", self.config)
        self.widgets["save_dir"] = FileBrowser("dir", "Export Directory", config)

        # Display widgets in layout
        layout = QVBoxLayout()
        for wid in self.widgets.values():
            layout.addWidget(wid)

        footer_layout = QGridLayout()
        self.run_button = QPushButton("&Run")
        self.run_button.clicked.connect(lambda: self.runDLX(config))
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
        # Widgets for dark mode toggle button
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

    def runDLX(self, config):
        config.saveConfig()
        # Load spreadsheets into pandas DataFrames
        self.dataframes = self.createDataFrames(config)

        filler = FormulationFiller.FormulationFiller(self.dataframes["Ingredients Spreadsheet"], self.gdriveAPI)
        
        # Start ingredient selection process
        ingredient_selector = IngredientSelector(self.dataframes["Orders Spreadsheet"],
                                    self.dataframes["Ingredients Spreadsheet"],
                                    self.dataframes["Customer Questionnaire"],
                                    self.dataframes["Product Catalog"], filler)
        results = ingredient_selector.selectIngredients()
        # Start formulation calculations for all orders

        filler.process_all(results)


    def createDataFrames(self, config):
        # Store all dataframes in dictionary
        #config = FigMe()
        dataframes = {}

        for key in self.widgets.keys():
            # Only process to df if widget stores a spreadsheet
            fetch_name = self.widgets[key].label.text()
            # Dont try to gen. DF if directory path
            if "dir" in key:
                continue
            df = config.getDF(fetch_name)
            dataframes[self.widgets[key].label.text()] = df

        return dataframes
