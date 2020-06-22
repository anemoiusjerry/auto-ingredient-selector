import pandas as pd
from PySide2.QtWidgets import *

from .fileBrowser import FileBrowser
from .Gdriver import Gdriver
from .Modules import IngredientSelector
from .Modules import FormulationFiller

class LandingTab(QWidget):

    def __init__(self, config):
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

        self.run_button = QPushButton("&Run")
        self.run_button.clicked.connect(self.runDLX)
        self.run_button.setFixedWidth(70)

        # Display widgets in layout
        layout = QVBoxLayout()
        for wid in self.widgets.values():
            layout.addWidget(wid)
        layout.addWidget(self.run_button)

        self.setLayout(layout)

    def runDLX(self):
        # Load spreadsheets into pandas DataFrames
        self.dataframes = self.createDataFrames()

        # Start ingredient selection process
        results = IngredientSelector.IngredientSelector(self.dataframes["Orders Spreadsheet"],
                                                        self.dataframes["Ingredients Spreadsheet"],
                                                        self.dataframes["Customer Questionnaire"],
                                                        self.dataframes["Product Catalog"])

        # Start formulation calculations for all orders
        filler = FormulationFiller.FormulationFiller(self.dataframes["Ingredients Spreadsheet"], self.gdriveAPI)
        filler.process_all(results)


    def createDataFrames(self):
        # Store all dataframes in dictionary
        dataframes = {}

        for key in self.widgets.keys():
            # Only process to df if widget stores a spreadsheet
            if "sheet" in key:
                try:
                    # Retrieve from gdrive
                    fh, file_id = self.gdriveAPI.fetch_file(self.widgets[key].label.text())
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
                    df.set_index("INGREDIENT COMMON NAME", inplace=True)

                # Replace all nan with empty string
                df.fillna("", inplace=True)
                dataframes[key.getLabel()] = df

        return dataframes
