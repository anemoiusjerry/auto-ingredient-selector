from config.configParser import FigMe
from BespokeAutoSystem.dlx3 import DLX
import re
import os

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
        self.inameCol = config.getColname("Ingredients Spreadsheet", "name") # nameCol
        self.typeCol = config.getColname("Ingredients Spreadsheet", "type") # ingredTypeCol
        self.skinProbCol = config.getColname("Ingredients Spreadsheet", "skin problem")
        self.contrainsCol = config.getColname("Ingredients Spreadsheet", "contraindications") # contrainCol
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
        orders = orders.applymap(lambda x:str(x).lower())
        orders[customerCol] = orders[customerCol].apply(lambda x:" ".join(x.split()))
        self.orders = orders

        ingredients = ingredients.applymap(lambda x:str(x).lower())
        for colname in [typeCol, skinProbCol, contrainsCol]:
            ingredients[colname] = ingredients[colname].apply(lambda x: re.split("\s*[,]\s*", x))
        self.ingredients = ingredients

        qnair = qnair.applymap(lambda x:str(x).lower())
        qnair[qnameCol] = qnair[qnameCol].apply(lambda x:" ".join(x.split()))
        for colname in skinProbCols:
            qnair[colname] = qnair[colname].apply(lambda x: re.split("\s*[,]\s*", x))
        self.qnair = qnair

        catalog = catalog.applymap(lambda x:str(x).lower())
        catalog[productCol] = catalog[productCol].apply(lambda x: re.split("\s*[,]\s*", x[3:-5]) if x and "privacy policy" not in x else [])
        catalog.set_index(itemCol, inplace=True)
        self.catalog = catalog

        """ You module should return a list of dict objects containing:
            - list of selected ingredients
            - customer name whom ordered the product
            - product type
        """

    def select_ingredients(self):

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

                solutions, cols, unresolved = self.orderParser(product, qdata, self.ingredients, self.config, self.filler)

                # create a new worksheet for each solution
                self.writeToWorkbook(workbook, solutions, cols, unresolved)
                workbook.close()

                for solution in solutions:
                    returns.append({"Ingredients": solution[0],
                                    "CustomerName": name,
                                    "ProductType": product})

        return returns

    def writeToWorkbook(self, workbook, solutions, cols, unresolved):

        i=1
        for solution in solutions:
            worksheet = workbook.add_worksheet("Solution " + str(i))
            # Write the row headers (skin problems)
            row = 2
            col = 0
            worksheet.write(1,col,"Skin Problems")
            for problem in cols:
                worksheet.write(row, col, problem[0])
                row = row+1

            # Write the headings (ingredient names)
            row = 1
            col = 1
            for ingredient in solution[0]:
                worksheet.write(row, col, ingredient)
                col = col+1

            i = i+1

    def orderParser(self, product, qdata):

        types = self.config.getProduct(product, "types")
        target = self.config.getTarget(product)
        # Filetring and retrieving the skin problems from customer info
        ailments = [a for col in ailmentCols for a in qdata[col] if a]

        # Finding the customers contraindications
        usercons = conFinder(qdata[self.allergyCol], qdata[self.medicalCol])

        # retrieve the rows and columns that will make up the dlx matrix
        rows, cols = matrixGen(product, ailments, usercons)

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
        while len(solutions) < 100 and upBound < maxupBound:
            upBound = upBound + 1
            for i in range(len(cols)):
                cols[i] = list(cols[i])
                if cols[i][0] not in ["aqueous base","aqueous high performance","anhydrous high performance","anhydrous base","essential oil"]: # Hardcoded
                    cols[i][3] = upBound
                cols[i] = tuple(cols[i])

            matrix = DLX(cols, rows)
            solutions = matrix.dance()

        print("Name: ", qdata["Full Name"], ", Product: ", product,", Rows: ", len(rows), ", Cols: ", len(cols), ", Solutions: ", end="")
        print(len(solutions))

        # Finding the best solutions
        chosen = []
        _lenlst = [len(s) for s in solutions]
        maxlen, minlen = max(_lenlst), min(_lenlst)

        if len(solutions) > 10:
            solutions = solutions[:10]

        for solution in solutions[:]:
            # calculating fit
            vals = dd(list)
            for ingredient in solution:
                #ind = ingredients["INGREDIENT COMMON NAME"].values.tolist().index(ingredient)

                # Retrieve comodegenic rating
                _como = ingredients.loc[ingredient,comedogenicCol]
                vals[ingredient].append(0) if _como == "" else vals[ingredient].append(comeConst.index(int(float(_como))))
                # Retrieve Viscocity
                key = ingredients.loc[ingredient,viscocityCol]
                try:
                    vals[ingredient].append(viscConst.index(key))
                except:
                    vals[ingredient].append(1)
                # Retrieve  absoption rate
                key = ingredients.loc[ingredient,absorptionCol]
                try:
                    vals[ingredient].append(absorbConst.index(key))
                except:
                    vals[ingredient].append(1)
            # Returns the percentage composition of each ingredient in the product
            composition = filler.calc_ingredient_weight(solution, product, ingredients)
            # Returns the point that this current solution occupies
            point = pointGen(composition, vals)
            # Returns the maximum distance from the target point and the distance to the point
            # Need to generate the point from the config file. this will change types[product][1]<-----------------------------------------------------------

            maxdist, dist = distFinder(target, point, config)
            # Calculate fit score (lower is better)
            fit = fitWeight * dist * 100 / maxdist
            # Calculate the score of the number of ingredients (lower is better)
            numIngred = numIngredWeight * (len(solution)-minlen) * 100 / (maxlen-minlen) if maxlen-minlen else 0
            score = fit + numIngred
            # Need to find the additional benefits <----------------------------------------------------------------------

            if len(chosen) < maxSols:
                chosen.append((solution, score))
            elif score < max([sol[1] for sol in chosen]):
                # remove the old maximum and add the solution to the list
                for i in range(len(chosen)):
                    if chosen[i][1] > score:
                        chosen[i] = (solution, score)
                        break

        print("Best solutions: ")
        for sol in chosen:
            print(sol)
        print("Unresolved: ", unresolved)
        return chosen, cols, unresolved
