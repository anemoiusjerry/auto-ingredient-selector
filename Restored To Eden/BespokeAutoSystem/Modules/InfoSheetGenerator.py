import os
import sys
import logging
import pandas as pd
import jinja2
import pdfkit
import json
import copy
import docx
import argparse

from PySide2.QtWidgets import *
from datetime import *
from openpyxl import load_workbook
from pathlib import Path
from config.configParser import FigMe

class InfoSheetGenerator:

    def __init__(self, infoSheet_df, gdriveObject, config):
        self.config = config
        self.contents_df = infoSheet_df
        self.gdriveObject = gdriveObject

        # Open html template as string
        if getattr(sys, 'frozen', False):
            app_path = sys._MEIPASS
        else:
            app_path = os.getcwd()

        tmpPath =  app_path + "/Assets/InfoSheetTemplate.html"
        html_tmp = open(tmpPath, 'r')

        # Jinja2 Setup
        self.template = jinja2.Environment(loader=jinja2.BaseLoader).from_string(html_tmp.read())
        # Allow use of len method in html
        self.template.globals["len"] = len
        wkhtml_path = os.path.abspath("wkhtmltopdf")
        self.pdfkitConfig = pdfkit.configuration(wkhtmltopdf=wkhtml_path)
        self.options = {
            "orientation":"Landscape",
            "enable-local-file-access":None
        }

    def process_all(self):
        print("process all")
        # Get all formulation sheets from output dir
        path = self.config.getDir("Export Directory") + "/Formulation Sheets/"

        # Create list of all formlation sheet files
        sheet_paths = []
        for f in os.listdir(path):
            if os.path.isfile(os.path.join(path, f)):
                sheet_paths.append(path + f)

        # Retrieve all info. needed for pdf
        for f in sheet_paths:
            workbook = load_workbook(filename=f)
            sheet = workbook.active

            name = sheet["B1"].value
            prod_type = sheet["B2"].value

            df = self.extract_incis(sheet, self.contents_df)
            df = self.fill_dates(sheet, df)
            df = self.fill_instructions(name, prod_type, df)
            headings, paragraphs = self.split_sections(df)

            # Pass all info to gen brochure
            print("calling generate report")
            self.generateReport(headings, paragraphs, name, prod_type)

    def fill_instructions(self, name, prod_type, df):
        # Get product instructions
        instructions_path = self.config.getDir("Product Instructions Directory") + f"/{prod_type.title()} Instructions.docx"
        try:
            f = open(instructions_path, "rb")
        # If failed to open instructions then return straightaway
        except:
            return df

        fullText = name + ", "
        doc = docx.Document(f)
        for para in doc.paragraphs:
            fullText += para.text

        df.insert(0, "Recommedations For Use", fullText)
        return df

    def fill_dates(self, sheet, df):
        date_blended = sheet["B3"].value
        df[[list(df)[-1]]] += f"\n\nDate Blended: {date_blended}"
        return df

    def extract_incis(self, sheet, df):
        """ Returns df with ingredients INCI section inserted
        """
        # make an deep copy of df
        df = copy.deepcopy(df)

        inci_str = "Batch No. " + sheet["A4"].value + "\n\n"
        i=7
        while sheet[f"C{i}"].value != None:
            inci = sheet[f"A{i}"].value
            if inci != None:
                inci_str += inci + ", "
            i+=1
        inci_str = inci_str[:-2] + "."

        # insert position at second to last column
        pos = df.shape[1] - 1
        df.insert(pos, "Ingredients", inci_str)
        return df

    def generateReport(self, headings, paragraphs, name, prod_type):

        if getattr(sys, 'frozen', False):
            app_path = sys._MEIPASS
        else:
            app_path = os.getcwd()

        assets_path = app_path + "/Assets"

        html_str = self.template.render(headings=headings, paragraphs=paragraphs,
                                        name=name, prod_type=prod_type, assets_path=assets_path)

        sheet = open("Information & Ingredients Sheet.html", "w")
        sheet.write(html_str)
        sheet.close()

        # get output path
        """
        with open(str(Path(os.path.dirname(os.path.realpath(__file__))).parent.parent) + "/config.json") as j:
            config = json.load(j)
        output_path = config["Export Directory"] + "/Reports"
        """
        # Hayden chnaged this ^^ to this \/ . feel free to throw potatoes at him if he messed it up

        output_path = self.config.getDir("Export Directory") + "/Reports"
        print("generate report at" , output_path)
        # Create reports folder if it doesnt exist
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        pdfkit.from_string(html_str, output_path + f"/{name}-{prod_type}-report.pdf", configuration=self.pdfkitConfig, options=self.options)

    def split_sections(self, df):
        headings = list(df)
        paragraphs = []
        for i in range(df.shape[1]):
            paragraphs.append(df.iloc[0,i])
        return headings, paragraphs
