import json
import os
import re
import pandas as pd
from BespokeAutoSystem.Gdriver import Gdriver


class FigMe:

    def __init__(self, path=os.path.abspath("config/config.json")):
        # Get the filepath of the config file
        self.path = path
        self.gdriveAPI = Gdriver()
        # open the config file in read only mode and retrieve dictionary
        with open(self.path, "r") as config:
            self.masterDict = json.load(config)

    def getDF(self, dfname):

        try:
            # Retrieve from gdrive
            fh, file_id = self.gdriveAPI.fetch_file(dfname) # <------- ask jerry if this is relevant if we have the absolute filepaths from the config file already
            df = pd.read_excel(fh)
        # Try to get df locally if google drive fails
        except:
            try:
                dfpath = self.masterDict["Directories"][dfname]
                df = pd.read_csv(dfpath)
            except:
                # Pop up dialog that errors when not all df are browsed
                print("Not browsed")

        df.fillna("", inplace=True)
        df = df.applymap(lambda x:str(x).lower())

        if dfname == "Ingredients Spreadsheet":
            for colname in ["TYPE OF INGREDIENT", "SKIN PROBLEM", "CONTRAINDICATIONS"]:
                df[colname] = df[colname].apply(lambda x: re.split("\s*[,]\s*", x))
            df.set_index("INGREDIENT COMMON NAME", inplace=True)

        elif dfname == "Orders Spreadsheet":
            df["Billing Customer"] = df["Billing Customer"].apply(lambda x:" ".join(x.split()))
            df.set_index("Order #", inplace=True)

        elif dfname == "Customer Questionnaire":
            df["Full Name"] = df["Full Name"].apply(lambda x:" ".join(x.split()))
            for colname in ["Multi Selection Field", "Multi Selection Field 2", "Multi Selection Field 4", "Multi Selection Field 5"]:
                df[colname] = df[colname].apply(lambda x: re.split("\s*[,]\s*", x))
            df.set_index("Full Name", inplace=True)

        elif dfname == "Product Catalog":
            df["additionalInfoDescription6"] = df["additionalInfoDescription6"].apply(lambda x: re.split("\s*[,]\s*", x[3:-4]) if x and "privacy policy" not in x else [])
            df.set_index("name", inplace=True)

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

    def getTarget(self,product):
        # Returns the integer values in the format [como, visc, absorb]
        dic = self.masterDict["Product"][product]
        constants = self.masterDict["Constants"]

        como = dic["comedogenic"]
        visc = constants["Viscosity"].index(dic["viscosity"])
        absorb = constants["Absorbency"].index(dic["absorbency"])

        return [como, visc, absorb]
