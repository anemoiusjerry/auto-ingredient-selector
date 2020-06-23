import pandas as pd
from PySide2.QtCore import Qt
from PySide2.QtWidgets import *
from PySide2.QtGui import QKeySequence, QPalette, QColor

from .fileBrowser import FileBrowser
from .Gdriver import Gdriver
from .runDLX3 import IngredientSelector
from .Modules import FormulationFiller

class LandingTab(QWidget):

    def __init__(self, config, app):
        QWidget.__init__(self)
        self.gdriveAPI = Gdriver()

        # Dict of widget { wid_name: widget object }
        self.widgets = {}
        # UI Datasheets
        self.widgets["patient_sheet"] = FileBrowser("csv", "Customer Questionnaire", config)
        self.widgets["catalog_sheet"] = FileBrowser("csv", "Product Catalog", config)
        self.widgets["ingredient_sheet"] = FileBrowser("csv", "Ingredients Spreadsheet", config)
        self.widgets["orders_sheet"] = FileBrowser("csv", "Orders Spreadsheet", config)

        self.widgets["formulation_dir"] = FileBrowser("dir", "Formulation Sheets Directory:", config)
        self.widgets["save_dir"] = FileBrowser("dir", "Export Directory", config)

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
        self.slider.setFixedWidth(40)
        self.slider.valueChanged.connect(lambda: self.toggleDark(app))
        toggle_layout = QGridLayout()
        toggle_label = QLabel("Go Dark")
        toggle_label.setFixedWidth(50)
        toggle_layout.addWidget(toggle_label, 0, 0)
        toggle_layout.addWidget(self.slider, 0, 1)
        footer_layout.addLayout(toggle_layout, 0, 1)

        layout.addLayout(footer_layout)
        self.setLayout(layout)

    def toggleDark(self, app):
        app.setStyle("Fusion")
        if self.slider.value() == 0:
            norm = QPalette()
            app.setPalette(norm)
        else:
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
            app.setPalette(dark_palette)

    def runDLX(self):
        # Load spreadsheets into pandas DataFrames
        self.dataframes = self.createDataFrames()

        filler = FormulationFiller.FormulationFiller(self.dataframes["Ingredients Spreadsheet"], self.gdriveAPI)
        # Start ingredient selection process
        results = IngredientSelector(self.dataframes["Orders Spreadsheet"],
                                    self.dataframes["Ingredients Spreadsheet"],
                                    self.dataframes["Customer Questionnaire"],
                                    self.dataframes["Product Catalog"], filler)

        # Start formulation calculations for all orders

        filler.process_all(results)


    def createDataFrames(self):
        # Store all dataframes in dictionary
        dataframes = {}

        for key in self.widgets.keys():
            # Only process to df if widget stores a spreadsheet
            if "sheet" in key:
                try:
                    # Retrieve from gdrive
                    fh, file_id = self.gdriveAPI.fetch_file(self.widgets[key].label.teext())
                    df = pd.read_excel(fh)
                # Try to get df locally if google drive fails
                except:
                    try:
                        df_path = self.widgets[key].display.text()
                        df = pd.read_csv(df_path)
                    except:
                        # Pop up dialog that errors when not all df are browsed
                        print("Not browsed")

                if "ingredient" in key:
                    df.set_index("INGREDIENT COMMON NAME", drop=False, inplace=True)

                # Replace all nan with empty string
                df.fillna("", inplace=True)
                dataframes[self.widgets[key].label.text()] = df

        return dataframes
