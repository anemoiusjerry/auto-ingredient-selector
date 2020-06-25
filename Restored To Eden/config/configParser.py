import json
import os
import sys
import re
import pandas as pd
from BespokeAutoSystem.Gdriver import Gdriver


class FigMe:

    def __init__(self):
        # Get the filepath of the config file
        # getting correct path of the application
        if getattr(sys, 'frozen', False):
            app_path = sys._MEIPASS
        else:
            app_path = os.path.dirname(os.path.abspath(__file__))

        self.path = app_path + "/config/config.json"
        self.gdriveAPI = Gdriver()
        # open the config file in read only mode and retrieve dictionary
        with open(self.path, "r") as config:
            self.masterDict = json.load(config)

    def getDF(self, dfname):

        try:
            # Retrieve from gdrive
            list(3)
            fh, file_id = self.gdriveAPI.fetch_file(dfname)
            df = pd.read_excel(fh)
        # Try to get df locally if google drive fails
        except:
            try:
                dfpath = self.masterDict["Directories"][dfname]
                file_type = dfpath.split(".")[-1]
                if file_type == "csv":
                    df = pd.read_csv(dfpath)
                else:
                    df = pd.read_excel(dfpath)
            except:
                # Pop up dialog that errors when not all df are browsed
                print(f"{dfname} Not browsed")
                return None

        df.fillna("", inplace=True)
        df = df.applymap(lambda x:str(x).lower())

        if dfname == "Ingredients Spreadsheet":
            typeCol = self.getColname("Ingredients Spreadsheet", "type")
            skinProbCol = self.getColname("Ingredients Spreadsheet", "skin problem")
            contrainsCol = self.getColname("Ingredients Spreadsheet", "contraindications")
            nameCol = self.getColname("Ingredients Spreadsheet", "name")

            for colname in [typeCol, skinProbCol, contrainsCol]:
                df[colname] = df[colname].apply(lambda x: re.split("\s*[,]\s*", x))
            df.set_index(nameCol, drop=False, inplace=True)

        elif dfname == "Orders Spreadsheet":
            customerCol = self.getColname("Orders Spreadsheet", "customer")
            df[customerCol] = df[customerCol].apply(lambda x:" ".join(x.split()))

        elif dfname == "Customer Questionnaire":
            nameCol = self.getColname("Customer Questionnaire", "name")
            ailmentCols = self.getColname("Customer Questionnaire", "skin problem")
            pregnancyCol = self.getColname("Customer Questionnaire", "pregnancy")
            cusContrainCol = self.getColname("Customer Questionnaire", "contraindications")

            df[nameCol] = df[nameCol].apply(lambda x:" ".join(x.split()))
            for colname in ailmentCols + [pregnancyCol, cusContrainCol]:
                df[colname] = df[colname].apply(lambda x: re.split("\s*[,]\s*", x))

        elif dfname == "Product Catalog":
            itemCol = self.getColname("Product Catalog", "item")
            productCol = self.getColname("Product Catalog", "products")

            df[productCol] = df[productCol].apply(lambda x: re.split("\s*[,]\s*", x[3:-5]) if x and "privacy policy" not in x else [])
            df.set_index(itemCol, inplace=True)

        return df

    def getVal(self,variable):
        return self.masterDict["Values"][variable]

    def getColname(self,dataframe, col):
        return self.masterDict["Column names"][dataframe][col]

    def getConst(self,key):
        # Constants are stored as a list of values, key refers to the constant name
        return self.masterDict["Constants"][key]

    def getProduct(self,product, var):
        return self.masterDict["Product"][product][var]

    def getDir(self,directory):
        return self.masterDict["Directories"][directory]

    def setDir(self, directory, new_path):
        self.masterDict["Directories"][directory] = new_path

    def getTarget(self,product):
        # Returns the integer values in the format [como, visc, absorb]
        dic = self.masterDict["Product"][product]
        constants = self.masterDict["Constants"]

        como = dic["comedogenic"]
        visc = constants["viscosity"].index(dic["viscosity"])
        absorb = constants["absorbency"].index(dic["absorbency"])

        return [como, visc, absorb]

    def saveConfig(self):
        json_obj = json.dumps(self.masterDict, indent=4)
        with open(self.path, "w") as outfile:
            outfile.write(json_obj)
