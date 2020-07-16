import os
import traceback, sys
import logging
import pandas as pd
import jinja2
import pdfkit
import json
import copy
import docx
import argparse
import math

from PySide2.QtWidgets import *
from datetime import *
from openpyxl import load_workbook
from pathlib import Path
from config.configParser import FigMe
from BespokeAutoSystem.WarningRaiser import WarningRaiser

class InfoSheetGenerator:

    def __init__(self, infoSheet_df, gdriveObject, config):
        self.config = config
        self.contents_df = infoSheet_df
        self.gdriveObject = gdriveObject
        self.warn = WarningRaiser()

        # Open html template as string
        if getattr(sys, 'frozen', False):
            app_path = sys._MEIPASS
        else:
            app_path = os.getcwd()

        # Normal template
        tmpPath =  app_path + "/Assets/InfoSheetTemplate.html"
        html_tmp = open(tmpPath, 'r')
        self.template = jinja2.Environment(loader=jinja2.BaseLoader).from_string(html_tmp.read())

        # Men template
        menPath = app_path + "/Assets/CourageousTemplate.html"
        cour_tmp = open(menPath, 'r')
        self.courTemplate = jinja2.Environment(loader=jinja2.BaseLoader).from_string(cour_tmp.read())

        # Allow use of len method in html
        self.template.globals["len"] = len
        self.courTemplate.globals["len"] = len

        wkhtml_path = app_path + "/wkhtmltopdf.exe"
        self.pdfkitConfig = pdfkit.configuration(wkhtmltopdf=wkhtml_path)
        self.options = {
            "orientation":"Landscape",
            "enable-local-file-access":None
        }
        self.app_path = app_path

    def process_all(self):
        # Get all formulation sheets from output dir
        path = self.config.getDir("Export Directory")

        # Pass all non-order dependent information
        self.misc_values = {}
        self.misc_values["assetsPath"] = self.app_path + "/Assets"
        self.misc_values["address"] = self.config.getMisc("Address")
        self.misc_values["website"] = self.config.getMisc("Website")
        self.misc_values["font"] = self.config.getMisc("Font")
        self.misc_values["contactNumber"] = self.config.getMisc("Contact number")
        self.misc_values["abn"] = self.config.getMisc("ABN")

        # Create list of all formlation sheet files
        sheet_paths = []
        for _folder in os.listdir(path):
            print(_folder)
            _folder_path = os.path.join(path, _folder)
            if os.path.isdir(_folder_path):
                for _file in os.listdir(_folder_path):
                    print(_file)
                    _file_path = os.path.join(_folder_path, _file)
                    if os.path.isfile(_file_path) and "Worksheet" in _file:
                        sheet_paths.append(_file_path)

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
            try:
                self.generateReport(headings, paragraphs, name, prod_type)
            except:
                self.warn.displayWarningDialog("Write Failure", f"Failed to generate {name}'s {prod_type} report PDF")

    def fill_instructions(self, name, prod_type, df):
        instructions_filename = f"{prod_type.title()} Instructions"
        
        # Get product instructions
        try:
            if (self.config.masterDict["gdrive"]):
                error_msg = "Failed to fetch product instructions from Google Drive."
                f, file_id = self.gdriveObject.fetch_file(instructions_filename)
            else:
                error_msg = "Failed to fetch product instructions."
                instructions_path = self.config.getDir("Product Instructions Directory") + f"/{instructions_filename}.docx"
                f = open(instructions_path, "rb")
        # If failed to open instructions then return straightaway
        except:
            self.warn.displayWarningDialog("", error_msg)
            return df

        fullText = name + ", "
        doc = docx.Document(f)
        for para in doc.paragraphs:
            fullText += para.text + "\n"

        df[["Recommendations For Use"]] = fullText
        return df

    def fill_dates(self, sheet, df):
        date_blended = sheet["B3"].value
        expiry_date = sheet["B6"].value
        try:
            dt = expiry_date - date_blended
        # Return df if exception to allow for manual user editing
        except:
            self.warn.displayWarningDialog("", "Date not in the format of dd/mm/yyyy")
            return df
        # Always round down to nearest month
        months = math.floor(dt.days / 30)
        text = df.loc[0]["Used By & Best Before Date"]
        df[["Used By & Best Before Date"]] = text.replace("...", f" {months} ")
        
        date_blended_str = datetime.strftime(date_blended, "%d/%m/%Y")
        expiry_date_str = datetime.strftime(expiry_date, "%d/%m/%Y")
        df[["Used By & Best Before Date"]] += f"\n\nDate Blended: {date_blended_str}\
                                                \nBest Before Date: {expiry_date_str}"
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
        # Remove final comma with full stop
        inci_str = inci_str[:-2] + "."

        df[["Ingredients"]] = inci_str
        return df

    def generateReport(self, headings, paragraphs, name, prod_type):
        name = name.title()
        prod_type = prod_type.title()

        # Use male template if a male product
        if "man" in prod_type.lower():
            html_str = self.courTemplate.render(headings=headings, paragraphs=paragraphs,
                name=name, prod_type=prod_type, misc_vals=self.misc_values)
        else:
            html_str = self.template.render(headings=headings, paragraphs=paragraphs,
                name=name, prod_type=prod_type, misc_vals=self.misc_values)

        # HTML is shit. We spent 2 hours debugging code that wasnt used. poop

        output_path = self.config.getDir("Export Directory") + f"/{name}"

        # Create reports folder if it doesnt exist
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        pdfkit.from_string(html_str, 
            output_path + f"/{name} - {prod_type} - PIIS.pdf", 
            configuration=self.pdfkitConfig, options=self.options)

    def split_sections(self, df):
        headings = list(df)
        paragraphs = []
        for i in range(df.shape[1]):
            paragraphs.append(df.iloc[0,i])
        return headings, paragraphs
