import os
import sys
import logging
import pandas as pd
import jinja2
import logging
import pdfkit
import json
import copy
import docx

from PySide2.QtWidgets import *
from datetime import *
from openpyxl import load_workbook
from pathlib import Path

class InfoSheetGenerator:

    def __init__(self, infoSheet_df, gdriveObject):

        self.contents_df = infoSheet_df
        self.gdriveObject = gdriveObject

        # Open html template as string
        tmpPath =  os.path.dirname(os.path.realpath(__file__)) + "\\\\InfoSheetAssets\\InfoSheetTemplate.html"
        html_tmp = open(tmpPath, 'r')

        # Jinja2 Setup
        self.template = jinja2.Environment(loader=jinja2.BaseLoader).from_string(html_tmp.read())
        # Allow use of len method in html
        self.template.globals["len"] = len
        self.config = pdfkit.configuration(wkhtmltopdf="C:\Program Files\wkhtmltopdf\\bin\wkhtmltopdf.exe")
        self.options = {
            "orientation":"Landscape"
        }

    def process_all(self):
        # Get all formulation sheets from output dir
        path = str(Path(os.path.dirname(os.path.realpath(__file__))).parent.parent) + "\\Outputs"

        sheet_paths = []
        for f in os.listdir(path):
            if os.path.isfile(os.path.join(path, f)):
                sheet_paths.append(path + "\\" + f)
        
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
            self.generateReport(headings, paragraphs, name, prod_type)
    
    def fill_instructions(self, name, prod_type, df):
        # Get product instructions
        f = open(
            str(Path(os.path.dirname(os.path.realpath(__file__))).parent.parent) + \
            f"\\Product Information\\{prod_type} Instructions.docx", "rb")
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
                inci_str += inci
            i+=1

        # insert position at second to last column
        pos = df.shape[1] - 1
        df.insert(pos, "Ingredients", inci_str)
        return df

    def generateReport(self, headings, paragraphs, name, prod_type):
            assets_path = str(Path(os.path.dirname(os.path.realpath(__file__)))) + "\\InfoSheetAssets"

            html_str = self.template.render(headings=headings, paragraphs=paragraphs, 
                                            name=name, prod_type=prod_type, assets_path=assets_path)

            sheet = open("Information & Ingredients Sheet.html", "w")
            sheet.write(html_str)           
            sheet.close()

            # get output path
            with open(str(Path(os.path.dirname(os.path.realpath(__file__))).parent.parent) + "\\config.json") as j:
                config = json.load(j)
            output_path = config["Export Directory"] + "\\Reports"

            # Create reports folder if it doesnt exist
            if not os.path.exists(output_path):
                os.makedirs(output_path)

            pdfkit.from_string(html_str, output_path + "\\report.pdf", configuration=self.config, options=self.options)

    def split_sections(self, df):
        headings = list(df)
        paragraphs = []
        for i in range(df.shape[1]):
            paragraphs.append(df.iloc[0,i])
        return headings, paragraphs
