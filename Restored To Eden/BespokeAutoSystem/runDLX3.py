from dlx3 import DLX
import pandas as pd
import re
import math
import os
import xlsxwriter
from datetime import date
from collections import defaultdict as dd
from Modules.formulationfiller import calc_ingredient_weight as weighter
from ..configParser import FigMe

def matrixGen(product, ingredients, ailments, userCons, config):
    # fname = filepath of the ingredients csv
    # userCons = list of user contraindications
    nameCol = config.getColname("Ingredients Spreadsheet", "name")
    contrainCol = config.getColname("Ingredients Spreadsheet", "contraindications")
    typeCol = config.getColname("Ingredients Spreadsheet", "type")
    stockCol = config.getColname("Ingredients Spreadsheet", "stock")
    skinProbCol = config.getColname("Ingredients Spreadsheet", "skin problem")

    rows = []
    rownames = []
    # In the form [[ingredient types], [viscocity, Absorption rate, Comodegenic rating]]
    types = config.getProduct(product, "types")

    keywords = ["dry","inflamed","cracking","fine lines","wrinkles","damage from sun",
                "eczema","irritated","acne","age spots","tewl","firmness","sebum",
                "clogged","enlarged","scarring","regeneration","flaky","t-zone",
                "fine dehydration lines","rough","itching","redness","dull","flaking",
                "scaling","peeling","tightness","dehydrat"]

    problems = [k for a in ailments for k in keywords if k in a]
    problems = list(dict.fromkeys(problems))

    for i in range(ingredients.shape[0]):
        # Attain current stock, constraindications and ingredient type
        stock = ingredients.loc[i,stockCol]
        ingredCons = ingredients.loc[i,contrainCol]
        type = ingredients.loc[i,typeCol]

        # Filter the ingredients associated cures to contain keywords
        cures = ingredients.loc[i,skinProbCol]
        cures = [k for i in cures for k in keywords if k in i]
        cures = list(dict.fromkeys(cures))

        # check if the ingredient is in stock, not a contraindication and useable
        if checkStock(stock) \
          and contrainCheck(ingredCons, userCons) \
          and useablecheck(cures, problems) \
          and typeCheck(types, type):

            # Create and append nodes for each row of the dlx matrix created
            nodes = dlxRowFormat(cures, problems)
            rows.append((nodes, ingredients.loc[i,nameCol]))

    return rows, problems

def orderParser(product, qdata, ingredients, config):
    ailmentCols = config.getColname("Customer Questionnaire", "skin problem")
    allergyCol = config.getColname("Customer Questionnaire", "allergies")
    medicalCol = config.getColname("Customer Questionnaire", "medical")
    ingredTypeCol = config.getColname("Ingredients Spreadsheet", "type")
    comedogenicCol = config.getColname("Ingredients Spreadsheet", "comedogenic")
    viscocityCol = config.getColname("Ingredients Spreadsheet", "viscosity")
    absorptionCol = config.getColname("Ingredients Spreadsheet", "absorption")

    comeConst = config.getConst("ComedogenicRating")
    viscConst = config.getConst("Viscosity")
    absorbConst = config.getConst("Absorbency")

    # Upper and lower bound for the amount of times a skin condition can be covered
    lowBound = config.getVal("lowBound")
    upBound = config.getVal("upBound")
    maxupBound = config.getVal("maxupBound")
    # Range of allowed amounts of ingredient types
    tpyeoverlap_low = config.getVal("tpyeoverlap_low")
    typeoverlap_up = config.getVal("typeoverlap_up")
    # Maximum amount of solutions that will be returned
    maxSols = config.getVal("maxsols")
    fitWeight = config.getVal("fitweight")
    numIngredWeight = config.getVal("numingredweight")
    addedBenefitWeight = config.getVal("addedbenefitweight") # need to finish this part

    types = config.getProduct(product, "types")
    # Filetring and retrieving the skin problems from customer info
    ailments = [a for col in ailmentCols for a in qdata[col] if a and a!="I DON'T KNOW...THAT'S WHAT I NEED YOU FOR :)"]

    # Finding the customers contraindications
    usercons = conFinder(qdata[allergyCol], qdata[medicalCol])

    # retrieve the rows and columns that will make up the dlx matrix
    rows, cols = matrixGen(product, ingredients, ailments, usercons, config)

    # Convert cols into dlx useable format
    cols = [(cols[i],0,lowBound,upBound) for i in range(len(cols))]

    # If Essential oils are part of the product recipe, make sure they are included at least once
    for type in types:
        cols.append((type,0,tpyeoverlap_low,typeoverlap_up))
        colind = len(cols) - 1
        for row in rows:
            # ind = ingredients["INGREDIENT COMMON NAME"].values.tolist().index(row[1])
            # ^^ this was removed due to the set_index function. If something is wrong check here
            ingredtype = ingredients.loc[row[1],ingredTypeCol]
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
    for solution in solutions:
        # calculating fit
        vals = dd(list)
        for ingredient in solution:
            #ind = ingredients["INGREDIENT COMMON NAME"].values.tolist().index(ingredient)
            info = ingredients.loc[ingredient,:]
            # Retrieve comodegenic rating
            _como = info[comedogenicCol]
            vals[ingredient].append(0) if _como == "" else vals[ingredient].append(comeConst.index(_como))
            # Retrieve Viscocity
            key = info[viscocityCol]
            vals[ingredient].append(viscConst.index(key))
            # Retrieve  absoption rate
            key = info[absorptionCol]
            vals[ingredient].append(absorbConst.index(key))

        # Returns the percentage composition of each ingredient in the product
        composition = weighter(solution, product, ingredients)
        # Returns the point that this current solution occupies
        point = pointGen(composition, vals)
        # Returns the maximum distance from the target point and the distance to the point
        # Need to generate the point from the config file. this will change types[product][1]<-----------------------------------------------------------
        maxdist, dist = distFinder(types[product][1], point)
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

def pointGen(composition, vals):
    point = []
    for i in range(3):
        val = 0
        for ingredient in vals.keys():
            val = val + vals[ingredient][i] * composition[ingredient]/100
        point.append(val)
    return point

def distFinder(t, p):
    # t is the target point, p is the point
    # Find the distance of the point to the target point
    dist = math.sqrt((t[0]-p[0])**2 + (t[1]-p[1])**2 + (t[2]-p[2])**2)

    # find the maximum distance possible from the point
    maxX = max([5-t[0], t[0]]) # comedogenic rating
    maxY = max([len(config.getConst("Viscosity"))-1-t[1], t[1]]) # viscocity
    maxZ = max([len(config.getConst("Absorbency"))-1-t[2], t[2]]) # absorption
    maxdist = math.sqrt((t[0]-maxX)**2 + (t[1]-maxY)**2 + (t[2]-maxZ)**2)

    return maxdist, dist

def conFinder(allergies, medcons):
    cons = []
    for allergy in re.split("\s*[,]\s*", allergies):
        if allergy == "nut allergies":
            cons.append("nut allergy")

    for medcon in re.split("\s*[,]\s*", medcons):
        if medcon == "high blood pressure":
            cons.append("high blood pressure")
    return cons

def checkStock(stock):
    if not stock.lower() == "no":
            return True
    return False

def contrainCheck(ingredCons, userCons):
    # ingredCons = list of ingredient contraindications
    # userCons = list of user contraindications
    if ingredCons and userCons:
        for con in userCons:
            if con in ingredCons:
                return False
    return True

def useablecheck(ingredSolves, problems):
    for i in ingredSolves:
        for k in problems:
            if k == i:
                return True
    return False

def typeCheck(types, type):
    for t1 in types:
        for t2 in type:
            if t1 == t2:
                return True
    return False

def dlxRowFormat(cures, problems):
    nodes = []
    for cure in cures:
        if cure in problems:
            nodes.append((problems.index(cure),None))
    return nodes

def IngredientSelector(orders, ingredients, qnair, catalog):
    config = FigMe()
    # orders columns
    customerCol = config.getColname("Orders Spreadsheet", "customer")
    orderCol = config.getColnames("Orders Spreadsheet", "order number")

    # ingredients columns
    inameCol = config.getColnames("Ingredients Spreadsheet", "name")
    typeCol = config.getColnames("Ingredients Spreadsheet", "type")
    skinProbCol = config.getColnames("Ingredients Spreadsheet", "skin problem")
    contrainsCol = config.getColnames("Ingredients Spreadsheet", "contraindications")

    # questionnaire columns
    qnameCol = config.getColnames("Customer Questionnaire", "name")
    skinProbCols = config.getColnames("Customer Questionnaire", "skin problem")

    # catalog columns
    itemCol = config.getColnames("Product Catalog", "item")
    productCol = config.getColnames("Product Catalog", "products")

    # Convert all data in dataframes to lowercase
    # Readjust all names of customers to have one space between names
    orders = orders.applymap(lambda x:str(x).lower())
    orders[customerCol] = orders[customerCol].apply(lambda x:" ".join(x.split()))
    orders.set_index(orderCol, inplace=True)

    # Convert relevant column data to lists
    ingredients = ingredients.applymap(lambda x:str(x).lower())
    for colname in [typeCol, skinProbCol, contrainsCol]:
        ingredients[colname] = ingredients[colname].apply(lambda x: re.split("\s*[,]\s*", x))
    ingredients.set_index(inameCol, inplace=True)

    # Readjust all names of customers to have one space between names
    # Convert relevant column data to lists
    qnair = qnair.applymap(lambda x:str(x).lower())
    qnair[qnameCol] = qnair[qnameCol].apply(lambda x:" ".join(x.split()))
    for colname in skinProbCols:
        qnair[colname] = qnair[colname].apply(lambda x: re.split("\s*[,]\s*", x))
    qnair.set_index(qnameCol, inplace=True)

    catalog = catalog.applymap(lambda x:str(x).lower())
    catalog[productCol] = catalog[productCol].apply(lambda x: re.split("\s*[,]\s*", x[3:-4]) if x and "privacy policy" not in x else [])
    catalog.set_index(itemCol, inplace=True)

    # Creating new file for the orders to be saved into
    savedir = config.getDir("Export Directory")
    parentFolderPath = savedir+"/"+"Sheets"
    if not os.path.exists(parentFolderPath):
        os.makedirs(parentFolderPath)

    # Attaining the questionnaire information for the customer of each order
    # If it cant find the questionairre, the next order is attempted
    returns = []
    for i in range(orders.shape[0]):
        order = orders.loc[i,:]

        # Find the customer questionnaire using the name or email address
        # !!!! NOTE: A dialog should be added to check that the email corresponds to the correct person
        name = order["Billing Customer"]
        email = order["Buyer's Email"]

        if name in qnair["Full Name"].values.tolist():
            qdata = qnair.loc[name,:]
        elif email in qnair["Email"].values.tolist():
            # Add a dialog that asks if the customer name is indeed the corect customer linked to the email address
            qdata = qnair.loc[qnair["Email"].values.tolist().index(email)]
        else:
            # Add a warning dialog that says the name does not match any on the questionnaire
            continue

        # Finding the products required to fulfil the order. if they cannot be found, skip to next order
        item = order["Item's Name"]
        itemConstituents = catalog.loc[catalog["name"].values.tolist().index(item),"additionalInfoDescription6"]
        if itemConstituents:
            products = itemConstituents
        else: # add a check to make sure that all the products are within the known products
            #print("For customer:",name,", product:", item,"couldn't be found")
            continue

        # Create a folder for the order
        ordername = str(order["Billing Customer"]) + " " + str(date.today().strftime("%b-%d-%Y"))
        orderFolderName = parentFolderPath + "/" + ordername
        if not os.path.exists(orderFolderName):
            os.makedirs(orderFolderName)

        for product in products:
            # Get the solutions
            # create a new excel workbook for the order
            wbookname = orderFolderName + "/" + str(product) + ".xlsx"
            workbook = xlsxwriter.Workbook(wbookname)

            solutions, cols, unresolved = orderParser(product, qdata, ingredients)

            # create a new worksheet for each solution
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
            workbook.close()

if __name__ == '__main__':
    IngredientSelector(orders, ingredients, qnair)
