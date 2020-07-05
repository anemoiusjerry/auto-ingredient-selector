import os
import pandas as pd
from PySide2.QtCore import QObject, Signal
# Spreadsheet library
from openpyxl import load_workbook
from datetime import *
from collections import defaultdict as dd
import re

from config.configParser import FigMe
from BespokeAutoSystem.WarningRaiser import WarningRaiser

class FormulationFiller:
    SOF = 7

    def __init__(self, ingredients_df, gdriveObject):
        self.config = FigMe()
        self.gdriveObject = gdriveObject
        self.warn = WarningRaiser()

    def process_all(self, results):
        for soln in results:
            name = soln["CustomerName"].title()
            product_type = soln["ProductType"].title()
            try:
                self.write_to_template(soln["Ingredients"], name, product_type)
            except:
                self.warn.displayWarningDialog("Write Failure",
                    f"Failed to write {name}'s {product_type} formulation sheet.\nCheck that the template file has no embbed formating.")
        print("All form sheet generated.")

    def write_to_template(self, ingredients, customer_name, prod_type):
        """ Take information from ingredients selector and fill in
            formulation worksheet.
            inputs: ingredients - list of strings of ingredients
                    customer_name - str of customer name
                    prod_type - str of product type
        """
        # Get template path to read it
        path = self.config.getDir("Formulation Sheets Directory")
        template_path = path + "/" + prod_type + " Worksheet.xlsx"

        # Load the excel sheet
        workbook = load_workbook(filename=template_path)
        sheet = workbook.active


        ww_dict, phase_dict, realloc_dict, assigned_vals, EOF = self.get_misc_items(sheet)
        assigned_vals = self.calc_ingredient_weight(ingredients, prod_type, self.ingredients_df)

        # Fill header info
        sheet["B1"] = customer_name
        sheet["B2"] = prod_type
        if sheet["B5"].value == None:
            sheet["B5"] = 100 # placeholder (varies)

        i=0
        while len(assigned_vals) > 0:
            print(f"i={i}       length={len(assigned_vals)}")
            # End loop if not enough slots
            if len(realloc_dict) <= 0 or i >= len(assigned_vals):
                sheet = self.too_few_slots(assigned_vals, phase_dict, EOF, sheet)
                break

            ingredient_name = list(assigned_vals.keys())[i]
            # Insert ingredient into the correct row
            j=self.SOF
            while sheet[f"C{j}"].value != None:

                # Only fill w/w% if fixed ingredient
                if ("doesn't change" in ingredient_name.lower()) or ("does not change" in ingredient_name.lower()):
                    if ingredient_name.lower() == sheet[f"B{j}"].value.lower():
                        # Fill w/w%
                        sheet[f"D{j}"] = assigned_vals[ingredient_name]

                        realloc_dict.pop(f"D{j}", None)
                        assigned_vals.pop(ingredient_name)
                        break

                else:
                    # Get ingredient types ???????????/// Waiting for answer to simply column
                    type_list = self.ingredients_df.loc[ingredient_name]["TYPE OF INGREDIENT"]

                    for ingredient_type in type_list:

                        if "essential oil" in ingredient_type:
                            ingredient_type = "eo " + self.ingredients_df.loc[ingredient_name]["ESSENTIAL OIL NOTE"].lower()

                        # Fill row in ingredient types match
                        if (ingredient_type == sheet[f"B{j}"].value.lower()):
                            # INCI
                            sheet[f"A{j}"] = self.ingredients_df.loc[ingredient_name]["INGREDIENT INCI NAME"]
                            # Ingredient Name
                            sheet[f"B{j}"] = ingredient_name
                            # w/w%
                            sheet[f"D{j}"] = assigned_vals[ingredient_name]
                            # Fill needs targted column if applicable
                            try:
                                if sheet[f"F{6}"].value.lower() == "needs targetting":
                                    sheet[f"F{6}"] = self.ingredients_df.loc[ingredient_name]["SKIN PROBLEM"]
                            except:
                                print("No needs targetting column.")

                            realloc_dict.pop(f"D{j}", None)
                            assigned_vals.pop(ingredient_name)
                            break
                    # break out of inner while loop of ingredient is assigned
                    if ingredient_name not in assigned_vals.keys():
                        break
                j+=1

            # Move onto next if cannot write ingredient
            if ingredient_name in assigned_vals.keys():
                i+=1

        # Reallocate surplus %
        if len(realloc_dict) > 0:
            sheet = self.too_many_slots(realloc_dict, sheet)

        sheet = self.write_grams(sheet)
        filename = customer_name + "-" + prod_type + ".xlsx"
        path = self.export_to_file(workbook, filename)

    def calc_ingredient_weight(self, ingredients, prod_type, ingredients_df):
        """ Takes parameters from ingredient selector and calculates to ingredient weights
            inputs: ingredients - [ingredient names]
                    product type - product type string
                    ingredients_df - dataframe of ingredient database
        """
        # Get template folder path
        path = self.config.getDir("Formulation Sheets Directory") + "/"
        template_path = path + prod_type + " Worksheet.xlsx"

        # Load the excel sheet
        workbook = load_workbook(filename=template_path)
        sheet = workbook.active

        # Get all required data to fill sheet
        ww_dict, phase_dict, realloc_dict, assigned_vals, EOF = self.get_misc_items(sheet)

        # Fill main table entries
        for ingredient_name in ingredients:

            # Get ingredient types ???????????/// Waiting for answer to simplify column
            type_list = ingredients_df.loc[ingredient_name]["TYPE OF INGREDIENT"]

            for ingredient_type in type_list:
                #if "essential oil" in ingredient_type:
                #    ingredient_type = "eo " + ingredients_df.loc[ingredient_name]["ESSENTIAL OIL NOTE"].lower()

                if "essential oil" in ingredient_type:                              # Haydens Fix
                    note = ingredients_df.loc[ingredient_name]["ESSENTIAL OIL NOTE"]#       |
                    if note:                                                        #       |
                        ingredient_type = "eo " + note                              #       |
                    else:                                                           #       \/
                        ingredient_type = "eo middle"                               # ---------------

                if ingredient_type in ww_dict:
                    # Pop off and use first weight of ingredient type
                    if len(ww_dict[ingredient_type]) > 1:
                        assigned_vals[ingredient_name] = ww_dict[ingredient_type].pop(0)
                    # If only one is left then keep using that one
                    else:
                        assigned_vals[ingredient_name] = ww_dict[ingredient_type][0]

        # Scale to 100
        tot = sum(assigned_vals.values())
        if tot > 100:
            for key in assigned_vals.keys():
                assigned_vals[key] = round(assigned_vals[key] * 100/tot, 1)
        elif tot < 100:
            leftover = 100 - tot
            for key in assigned_vals.keys():
                assigned_vals[key] = round(assigned_vals[key] + leftover * assigned_vals[key]/tot, 1)
        else:
            pass
        return assigned_vals

    def get_misc_items(self, sheet):
        """ Creates the dicts and values needed for reallocation
            Returns: ww_dict - dict { ingredient type: w/w% }
                     phase_dict - dict { ingredient type: phase }
                     realloc_dict - dict { cell ID: assigned % } Every time cell is filled, it is removed from realloc_dict
                     assigned_dict - dict { ingredient type: w/w% } init. filled with all does not change names
                     EOF - index of last row for ingredients
        """
        ww_dict = dd(list)
        phase_dict = {}
        realloc_dict = {}
        assigned_dict = {}

        i = self.SOF
        # Record the w/w% for all types
        while sheet[f"C{i}"].value != None:
            cell_ingredient = sheet[f"B{i}"].value.lower()
            cell_weight = sheet[f"D{i}"].value

            ww_dict[cell_ingredient].append(cell_weight)
            phase_dict[cell_ingredient] = sheet[F"C{i}"].value

            # Add fixed ingredient to assigned dict
            if ("doesn't change" in cell_ingredient) or ("does not change" in cell_ingredient):
                assigned_dict[cell_ingredient] = cell_weight
            # If no fixed, add to dict to be reallocated
            else:
                realloc_dict[f"D{i}"] = cell_weight

            i += 1
        EOF = i
        return ww_dict, phase_dict, realloc_dict, assigned_dict, EOF

    def too_many_slots(self, realloc_dict, sheet):
        """ Reallocates extra percentages to other ingredients.
            Inputs: realloc_dict - { cell ID (D?): w/w% } ingredients still need to be allocated
            Returns: sheet with new values written
        """
        # Write 0 to unallocated rows to mark for delete
        for cell in realloc_dict.keys():
            sheet[cell] = 0

        i = self.SOF
        while sheet[f"C{i}"].value != None:
            if sheet[f"D{i}"].value == 0:
                sheet.delete_rows(i)
            else:
                i+=1
        return sheet

    def too_few_slots(self, leftovers, phase_dict, EOF, sheet):
        """
            inputs: leftovers - dict { ingredient name: w/w% } of remaining ingredients
                    phase_dict - { ingredient type: phase }
                    EOF - last row of ingredients table
                    sheet - active sheet to write info to
        """

        for ingredient, weight in leftovers.items():
            # No need to add fixed ingredients as they are already in sheet
            if ("doesn't change" in ingredient) or ("does not change" in ingredient):
                continue

            # Get ingredient type and assign corresponding w/w%
            type_list = self.ingredients_df.loc[ingredient]["TYPE OF INGREDIENT"]
            for i_type in type_list:
                if i_type in phase_dict.keys():
                    # Insert leftovers at end of sheet
                    sheet.insert_rows(EOF)
                    sheet[f"A{EOF}"] = self.ingredients_df.loc[ingredient]["INGREDIENT INCI NAME"]  # INCI name
                    sheet[f"B{EOF}"] = ingredient                                              # name
                    sheet[f"C{EOF}"] = phase_dict[i_type]                                      # Phase
                    sheet[f"D{EOF}"] = weight                                                  # w/w%
        return sheet

    def write_grams(self, sheet):
        default_gram = 100
        i=self.SOF
        while sheet[f"C{i}"].value != None:
            try:
                sheet[f"E{i}"] = sheet[f"D{i}"].value/100 * float(sheet["B5"].value)
            except:
                sheet[f"E{i}"] = sheet[f"D{i}"].value/100 * default_gram
            i+=1
        return sheet

    def export_to_file(self, workbook, filename):
        """ Export as excel file to current working directory
        """
        save_path = self.config.getDir("Export Directory") + "/Formulation Sheets/"
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        workbook.save(save_path + filename)
        print("Done exporting...")
        return save_path + filename
