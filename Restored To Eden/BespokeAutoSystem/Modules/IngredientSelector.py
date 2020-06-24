from .FormulationFiller import FormulationFiller
from config.configParser import FigMe
from ..dlx3 import DLX
import pandas as pd
import re
import math
import os
import xlsxwriter
from datetime import date
from collections import defaultdict as dd

class IngredientSelector:
    def __init__(self, orders, ingredients, qnair, catalog, filler):
        config = FigMe()
        self.config = config
        self.filler = filler
        # orders columns
        self.customerCol = config.getColname("Orders Spreadsheet", "customer")
        self.orderCol = config.getColname("Orders Spreadsheet", "order number")
        self.emailCol = config.getColname("Orders Spreadsheet", "email")
        self.oitemCol = config.getColname("Orders Spreadsheet", "item")

        # ingredients columns
        self.inameCol = config.getColname("Ingredients Spreadsheet", "name")
        self.typeCol = config.getColname("Ingredients Spreadsheet", "type")
        self.skinProbCol = config.getColname("Ingredients Spreadsheet", "skin problem")
        self.contrainsCol = config.getColname("Ingredients Spreadsheet", "contraindications")
        self.stockCol = config.getColname("Ingredients Spreadsheet", "stock")
        self.comedogenicCol = config.getColname("Ingredients Spreadsheet", "comedogenic")
        self.viscocityCol = config.getColname("Ingredients Spreadsheet", "viscosity")
        self.absorptionCol = config.getColname("Ingredients Spreadsheet", "absorption")

        # questionnaire columns
        self.qnameCol = config.getColname("Customer Questionnaire", "name")
        self.skinProbCols = config.getColname("Customer Questionnaire", "skin problem")
        self.qemailCol = config.getColname("Customer Questionnaire", "email")
        self.ailmentCols = config.getColname("Customer Questionnaire", "skin problem")
        self.allergyCol = config.getColname("Customer Questionnaire", "allergies")
        self.medicalCol = config.getColname("Customer Questionnaire", "medical")

        # catalog columns
        self.itemCol = config.getColname("Product Catalog", "item")
        self.productCol = config.getColname("Product Catalog", "products")

        # Constants and values
        self.comeConst = config.getConst("ComedogenicRating")
        self.viscConst = config.getConst("Viscosity")
        self.absorbConst = config.getConst("Absorbency")
        self.lowBound = config.getVal("lowBound")
        self.upBound = config.getVal("upBound")
        self.maxupBound = config.getVal("maxupBound")
        self.tpyeoverlap_low = config.getVal("tpyeoverlap_low")
        self.typeoverlap_up = config.getVal("typeoverlap_up")
        self.maxSols = config.getVal("maxsols")
        self.fitWeight = config.getVal("fitweight")
        self.numIngredWeight = config.getVal("numingredweight")
        self.addedBenefitWeight = config.getVal("addedbenefitweight") # need to finish this part


        # initialising the dataframes
        """
        orders = orders.applymap(lambda x:str(x).lower())
        orders[self.customerCol] = orders[self.customerCol].apply(lambda x:" ".join(x.split()))
        self.orders = orders

        ingredients = ingredients.applymap(lambda x:str(x).lower())
        for colname in [self.typeCol, self.skinProbCol, self.contrainsCol]:
            ingredients[colname] = ingredients[colname].apply(lambda x: re.split("\s*[,]\s*", x))
        self.ingredients = ingredients

        qnair = qnair.applymap(lambda x:str(x).lower())
        qnair[self.qnameCol] = qnair[self.qnameCol].apply(lambda x:" ".join(x.split()))
        for colname in self.skinProbCols + [self.allergyCol] + [self.medicalCol]:
            qnair[colname] = qnair[colname].apply(lambda x: re.split("\s*[,]\s*", x))
        self.qnair = qnair

        catalog = catalog.applymap(lambda x:str(x).lower())
        catalog[self.productCol] = catalog[self.productCol].apply(lambda x: re.split("\s*[,]\s*", x[3:-5]) if x and "privacy policy" not in x else [])
        catalog.set_index(self.itemCol, inplace=True)
        self.catalog = catalog
        """
        self.orders = orders
        self.ingredients = ingredients
        self.qnair = qnair
        self.catalog = catalog

    def selectIngredients(self):

        # Creating new file for the orders to be saved into
        savedir = self.config.getDir("Export Directory")
        parentFolderPath = savedir+"/"+"Sheets"
        if not os.path.exists(parentFolderPath):
            os.makedirs(parentFolderPath)

        returns = []
        for index, order in self.orders.iterrows():

            # Find the customer questionnaire using the name or email address
            # !!!! NOTE: A dialog should be added to check that the email corresponds to the correct person
            name = order[self.customerCol]
            email = order[self.emailCol]

            if name in self.qnair.index.tolist():
                qdata = self.qnair.loc[name,:]
            elif email in self.qnair[self.qemailCol].values.tolist():
                # Add a dialog that asks if the customer name is indeed the corect customer linked to the email address
                qdata = self.qnair.loc[self.qnair[self.qemailCol].values.tolist().index(email)]
            else:
                # Add a warning dialog that says the name does not match any on the questionnaire
                continue

            # Finding the products required to fulfil the order. if they cannot be found, skip to next order
            item = order[self.oitemCol]

            try:
                products = self.catalog.loc[item,self.productCol]
            except:
                # add a check to make sure that all the products are within the known products
                continue

            # Create a folder for the order
            ordername = str(order[self.customerCol]) + " " + str(date.today().strftime("%b-%d-%Y"))
            orderFolderName = parentFolderPath + "/" + ordername
            if not os.path.exists(orderFolderName):
                os.makedirs(orderFolderName)

            for product in products:
                # Get the solutions
                # create a new excel workbook for the order
                wbookname = orderFolderName + "/" + str(product) + ".xlsx"
                workbook = xlsxwriter.Workbook(wbookname)

                solutions, rows, cols, unresolved = self.orderParser(product, qdata)

                # create a new worksheet for each solution
                self.writeToWorkbook(workbook, solutions, rows, cols, unresolved)
                workbook.close()

                for solution in solutions:
                    returns.append({"Ingredients": solution[0],
                                    "CustomerName": name,
                                    "ProductType": product})

        return returns

    def writeToWorkbook(self, workbook, solutions, rows, cols, unresolved):
        # Create the format for the ailment rows
        _ailDict = {"bold": True,
                    "align": "right",
                    "bg_color": "#DB7093"}
        ailment_format = workbook.add_format(_ailDict)

        # Create the format for the ingredient columns
        _ingDict = {"bold": True,
                    "align": "right",
                    "bg_color": "#C71585",
                    "font_color": "white"}
        ingred_format = workbook.add_format(_ingDict)

        # Create the format for the nodes
        _nodDict = {"bold": True,
                    "align": "center",
                    "bg_color": "#D8BFD8"}
        node_format = workbook.add_format(_nodDict)

        i=1
        for solution in solutions:
            worksheet = workbook.add_worksheet("Solution " + str(i))
            # Write the row headers (skin problems)
            row = 2
            col = 0
            worksheet.write(1,col,"Skin Problems",ailment_format)
            _strLen = 0
            for problem in cols:
                _strLen = len(problem[0]) if len(problem[0]) > _strLen else _strLen
                worksheet.write(row, col, problem[0],ailment_format)
                row = row+1
            worksheet.set_column(col, col, round(_strLen*0.9))
            # Write the headings (ingredient names) and populate nodes
            hrow = 1
            hcol = 1
            nrow = 2
            ncol = 1
            for ingredient in solution[0]:
                # write the heading
                worksheet.write(hrow, hcol, ingredient,ingred_format)
                worksheet.set_column(hcol, hcol, round(len(ingredient)*0.9))
                hcol = hcol+1

                # populate the nodees
                for _row in rows:
                    if _row[1] == ingredient:
                        for node in _row[0]:
                            nrow = node[0] + 2
                            worksheet.write(nrow, ncol, "X", node_format)
                        break
                ncol = ncol + 1

            i = i+1

    def orderParser(self, product, qdata):

        types = self.config.getProduct(product, "types")
        # Retrieving the skin problems from customer info
        ailments = [a for col in self.ailmentCols for a in qdata[col] if a]
        # Finding the customers contraindications
        usercons = self.conFinder(qdata[self.allergyCol], qdata[self.medicalCol])

        # Retrieve the rows and columns that will make up the dlx matrix
        rows, cols = self.matrixGen(product, ailments, usercons)

        # Convert cols into dlx useable format
        cols = [(cols[i],0,self.lowBound,self.upBound) for i in range(len(cols))]

        # If Essential oils are part of the product recipe, make sure they are included at least once
        for type in types:
            cols.append((type,0,self.tpyeoverlap_low,self.typeoverlap_up))
            colind = len(cols) - 1
            for row in rows:
                # ind = ingredients["INGREDIENT COMMON NAME"].values.tolist().index(row[1])
                # ^^ this was removed due to the set_index function. If something is wrong check here
                ingredtype = self.ingredients.loc[row[1],self.typeCol]
                if type in ingredtype:
                    row[0].append((colind, None))

        # Check that all cols can be stisfied at least once, remove cols that cant be
        colsCovered = set([node[0] for row in rows for node in row[0]])
        unresolved = []
        for col in range(len(cols)-1, 0, -1):
            if col not in colsCovered:
                unresolved.append(cols.pop(col)[0])
                for i in range(len(rows)):
                    rows[i][0] = [node for node in rows[i][0] if node[0] != col]


        # Run the DLX to find all the solutions
        matrix = DLX(cols, rows)
        solutions = matrix.dance()

        print("cols: ", cols)
        # Run the DLX with an increased upper bound until max is reached or enough solutions are found
        while len(solutions) < 100 and self.upBound < self.maxupBound:
            self.upBound = self.upBound + 1
            for i in range(len(cols)):
                cols[i] = list(cols[i])
                if cols[i][0] not in ["aqueous base","aqueous high performance","anhydrous high performance","anhydrous base","essential oil"]: # Hardcoded
                    cols[i][3] = self.upBound
                cols[i] = tuple(cols[i])

            matrix = DLX(cols, rows)
            solutions = matrix.dance()

        print("Name: ", qdata["Full Name"], ", Product: ", product,", Rows: ", len(rows), ", Cols: ", len(cols), ", Solutions: ", end="")
        print(len(solutions))

        bestSols = self.findBestSol(solutions, product, ailments)
        print("Unresolved: ", unresolved)
        return bestSols, rows, cols, unresolved

    def findBestSol(self, solutions, product, ailments):
        # Finding the best solutions
        target = self.config.getTarget(product)
        chosen = []
        _lenlst = [len(s) for s in solutions]
        maxlen, minlen = max(_lenlst), min(_lenlst)
        maxBenefits, leastBenefits = 0, 0

        if len(solutions) > 10:
            solutions = solutions[:10]

        for solution in solutions[:]:
            vals = dd(list)
            benefits = 0
            benefits_lst = []
            for ingredient in solution:
                # Finding information to calculate fit
                # Retrieve comodegenic rating
                _como = self.ingredients.loc[ingredient,self.comedogenicCol]
                vals[ingredient].append(0) if _como == "" else vals[ingredient].append(self.comeConst.index(int(float(_como))))
                # Retrieve Viscocity
                key = self.ingredients.loc[ingredient,self.viscocityCol]
                try:
                    vals[ingredient].append(self.viscConst.index(key))
                except:
                    vals[ingredient].append(1)
                # Retrieve  absoption rate
                key = self.ingredients.loc[ingredient,self.absorptionCol]
                try:
                    vals[ingredient].append(self.absorbConst.index(key))
                except:
                    vals[ingredient].append(1)

                # Finding additional benefits
                for skinProb in self.ingredients.loc[ingredient,self.skinProbCol]:
                    if skinProb in ailments:
                        benefits = benefits + 1
                        benefits_lst.append(skinProb)
                if benefits > maxBenefits:
                    maxBenefits = benefits
                elif benefits < leastBenefits:
                    leastBenefits = benefits
            # Returns the percentage composition of each ingredient in the product
            composition = self.filler.calc_ingredient_weight(solution, product, self.ingredients)
            # Returns the point that this current solution occupies
            point = self.pointGen(composition, vals)
            # Returns the maximum distance from the target point and the distance to the point
            maxdist, dist = self.distFinder(target, point)
            # Calculate fit score (lower is better)
            fit = self.fitWeight * dist * 100 / maxdist
            # Calculate the score of the number of ingredients (lower is better)
            numIngred = self.numIngredWeight * (len(solution)-minlen) * 100 / (maxlen-minlen) if maxlen-minlen else 0
            # Calculating the score of the number of additional benefits (lower is better)
            addedBenefit = self.addedBenefitWeight * (maxBenefits - benefits) * 100 / (maxBenefits-leastBenefits) if maxBenefits-leastBenefits else 0
            score = fit + numIngred + addedBenefit
            # Need to find the additional benefits <----------------------------------------------------------------------

            if len(chosen) < self.maxSols:
                chosen.append((solution, score))
            elif score < max([sol[1] for sol in chosen]):
                # remove the old maximum and add the solution to the list
                for i in range(len(chosen)):
                    if chosen[i][1] > score:
                        chosen[i] = (solution, score, list(set(benefits_lst)))
                        break

        print("Best solutions: ")
        for sol in chosen:
            print(sol)
        return chosen

    def matrixGen(self, product, ailments, userCons):

        rows = []
        rownames = []
        # In the form [[ingredient types], [viscocity, Absorption rate, Comodegenic rating]]
        types = self.config.getProduct(product, "types")

        for index, ingredient in self.ingredients.iterrows():
            # Attain current stock, constraindications and ingredient type
            stock = ingredient[self.stockCol]
            ingredCons = ingredient[self.contrainsCol]
            type = ingredient[self.typeCol]

            # Filter the ingredients associated cures to contain keywords
            cures = ingredient[self.skinProbCol]

            # check if the ingredient is in stock, not a contraindication and useable
            if self.stockCheck(stock) \
              and self.contrainCheck(ingredCons, userCons) \
              and self.useablecheck(cures, ailments) \
              and self.typeCheck(types, type):

                # Create and append nodes for each row of the dlx matrix created
                nodes = self.dlxRowFormat(cures, ailments)
                rows.append((nodes, index))

        return rows, ailments

    def pointGen(self, composition, vals):

        point = []
        for i in range(3):
            val = 0
            for ingredient in vals.keys():
                val = val + vals[ingredient][i] * composition[ingredient]/100
            point.append(val)
        return point

    def distFinder(self,t, p):
        # t is the target point, p is the point
        # Find the distance of the point to the target point
        dist = math.sqrt((t[0]-p[0])**2 + (t[1]-p[1])**2 + (t[2]-p[2])**2)

        # find the maximum distance possible from the point
        maxX = max([5-t[0], t[0]]) # comedogenic rating
        maxY = max([len(self.config.getConst("Viscosity"))-1-t[1], t[1]]) # viscocity
        maxZ = max([len(self.config.getConst("Absorbency"))-1-t[2], t[2]]) # absorption
        maxdist = math.sqrt((t[0]-maxX)**2 + (t[1]-maxY)**2 + (t[2]-maxZ)**2)

        return maxdist, dist

    def conFinder(self, allergies, medcons):
        cons = []
        print("allergies", allergies)
        print("medcons", medcons)
        for allergy in allergies:
            if allergy == "nut allergies":
                cons.append("nut allergy")

        for medcon in medcons:
            if medcon == "high blood pressure":
                cons.append("high blood pressure")
        return cons

    def stockCheck(self, stock):
        if not stock.lower() == "no":
                return True
        return False

    def contrainCheck(self, ingredCons, userCons):
        # ingredCons = list of ingredient contraindications
        # userCons = list of user contraindications
        if ingredCons and userCons:
            for con in userCons:
                if con in ingredCons:
                    return False
        return True

    def useablecheck(self, ingredSolves, problems):
        for i in ingredSolves:
            for k in problems:
                if k == i:
                    return True
        return False

    def typeCheck(self, types, type):
        for t1 in types:
            for t2 in type:
                if t1 == t2:
                    return True
        return False

    def dlxRowFormat(self, cures, problems):
        nodes = []
        for cure in cures:
            if cure in problems:
                nodes.append((problems.index(cure),None))
        return nodes
