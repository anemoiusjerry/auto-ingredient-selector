import json
import os
import sys
import re
import pandas as pd
from BespokeAutoSystem.Gdriver import Gdriver
from BespokeAutoSystem.WarningRaiser import WarningRaiser

class FigMe:

    def __init__(self):
        self.warn = WarningRaiser()
        # getting correct path of the application
        if getattr(sys, 'frozen', False):
            path = os.path.dirname(sys.executable)
            parent = os.path.abspath(os.path.join(path, os.pardir))
        else:
            app_path = os.getcwd()

        try:
            self.path = parent + "/Resources/config.json"
        except:
            self.path = app_path + "/config/config.json"

        self.gdriveAPI = Gdriver()
        # open the config file in read only mode and retrieve dictionary
        with open(self.path, "r") as config:
            self.masterDict = json.load(config)

    def getDF(self, dfname):
        """ dfname is the label of in landing tab
        """
        # Attempt google drive retrieval for ingredients df

        if (dfname == "Ingredients Spreadsheet" or dfname == "Product Catalog") and self.masterDict["gdrive"]:
            try:
                # Retrieve from gdrive
                gdrive_name = self.getGdrive(dfname)
                fh, file_id = self.gdriveAPI.fetch_file(gdrive_name)
                try:
                    df = pd.read_excel(fh)
                except:
                    if getattr(sys, 'frozen', False):
                        path = os.path.dirname(sys.executable)
                        parent = os.path.abspath(os.path.join(path, os.pardir))
                    else:
                        app_path = os.getcwd()

                    try:
                        path = parent + "/Resources/file.csv"
                    except:
                        path = app_path + "/file.csv"
                    df = pd.read_csv(path)
            except Exception as e:
                if getattr(sys, 'frozen', False):
                    path = os.path.dirname(sys.executable)
                    parent = os.path.abspath(os.path.join(path, os.pardir))
                    with open(parent + "/Resources/debug.txt", "w") as debug:
                        debug.write(str(e) + "\n" + "configparser; getDF\n")
                self.warn.displayWarningDialog("", f"Cannot fetch {gdrive_name} from Google Drive - check filename in drive and your internet connection.")
        else:
            try:
                dfpath = self.masterDict["Directories"][dfname]
                file_type = dfpath.split(".")[-1]
                if file_type == "csv":
                    df = pd.read_csv(dfpath)
                elif file_type == "xlsx":
                    df = pd.read_excel(dfpath)
                else:
                    if not os.path.isdir(dfpath):
                        self.warn.displayWarningDialog("Load Error", f"File ({dfpath}) is not a csv or xlsx")
                        raise Exception("Incorrect filetype")
                    return None
            except:
                # Pop up dialog that errors when not all df are browsed
                print(f"{dfname} Not browsed")
                if not os.path.isdir(dfpath):
                    self.warn.displayWarningDialog("Load Error", f"Error when loading {dfname}")
                    raise Exception("Error loading dataframe")
                return None

        if self.checkCols(df, dfname):
            df.fillna("", inplace=True)

            # Save a copy of original INCI formatting
            inci_names = None
            if dfname == "Ingredients Spreadsheet":
                inciCol = self.getColname("Ingredients Spreadsheet", "inci")
                nameCol = self.getColname("Ingredients Spreadsheet", "name")
                inci_names = df[[inciCol]]
                ing_names = df[[nameCol]]


            # Convert all string to lowercase
            df = df.applymap(lambda x:str(x).lower())

            if dfname == "Ingredients Spreadsheet":
                typeCol = self.getColname("Ingredients Spreadsheet", "type")
                skinProbCol = self.getColname("Ingredients Spreadsheet", "skin problem")
                contrainsCol = self.getColname("Ingredients Spreadsheet", "contraindications")
                nameCol = self.getColname("Ingredients Spreadsheet", "name")
                # Replace with not lowercased inci
                df[[inciCol]] = inci_names
                df[[nameCol]] = ing_names

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

                # Set names as index
                df.set_index(nameCol, drop=False, inplace=True)
                
                for colname in ailmentCols + [pregnancyCol, cusContrainCol]:
                    df[colname] = df[colname].apply(lambda x: re.split("\s*[,]\s*", x))

            elif dfname == "Product Catalog":
                itemCol = self.getColname("Product Catalog", "item")
                productCol = self.getColname("Product Catalog", "products")

                df[productCol] = df[productCol].apply(lambda x: re.split("\s*[,]\s*", x[3:-5]) if x and "privacy policy" not in x else [])
                df.set_index(itemCol, inplace=True)

            # Remove duplicates
            df = df.loc[~df.index.duplicated(keep="first")]

            return df
        else:
            self.warn.displayWarningDialog("Load Error", f"({dfpath}) column names do not match")
            raise Exception("names dont match")
            #sys.exit()

    def getVal(self,variable):
        return self.masterDict["Values"][variable]
    def setVal(self, variable, new_value):
        self.masterDict["Values"][variable] = new_value

    def getColname(self,dataframe, col):
        return self.masterDict["Column names"][dataframe][col]
    def setColname(self, dataframe, col, new_value):
        self.masterDict["Column names"][dataframe][col] = new_value

    def getConst(self,key):
        # Constants are stored as a list of values, key refers to the constant name
        return self.masterDict["Constants"][key]

    def getProduct(self,product, var):
        return self.masterDict["Product"][product][var]
    def setProduct(self, product, var, new_value):
        self.masterDict["Product"][product][var] = new_value

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

    def getMisc(self, key):
        return self.masterDict["Misc"][key]
    def setMisc(self, key, new_value):
        self.masterDict["Misc"][key] = new_value

    def getGdrive(self, key):
        return self.masterDict["GoogleDrive"][key]
    def setGdrive(self, key, new_value):
        self.masterDict["GoogleDrive"][key] = new_value

    def setter(self, key, new_value):
        self.masterDict[key] = new_value

    def saveConfig(self):
        json_obj = json.dumps(self.masterDict, indent=4)
        with open(self.path, "w") as fp:
            fp.write(json_obj)

    def checkCols(self, df, dfname):
        dfCols = set(list(df.columns))
        knownCols = []
        for key, val in self.masterDict["Column names"][dfname].items():
            if type(val) == list:
                knownCols.extend(val)
            else:
                knownCols.append(val)

        return set(knownCols).issubset(dfCols)
