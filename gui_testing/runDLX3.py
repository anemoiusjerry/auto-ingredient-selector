from dlx3 import DLX
import pandas as pd

def ingredientParser(ingredients, ailments, userCons):
    # fname = filepath of the ingredients csv
    # userCons = list of user contraindications
    rows = []
    rownames = []

    for i in range(ingredients.shape[0]):
        stock = str(ingredients.loc[i,"In Stock"])
        ingredCons = str(ingredients.loc[i,"CONTRAINDICATIONS"]).split(",")
        if checkStock(stock) and contrainCheck(ingredCons, userCons):
            #print(ingredients.iloc[i,:],"\n", ailments, "\n")
            nodes = dlxRowFormat(ingredients.iloc[i,:], ailments)
            if nodes:
                rows.append(nodes)
                rownames.append(ingredients.loc[i,"INGREDIENT COMMON NAME"])

    return rows, rownames

def customerParser(cfname, ifname):
    up = lambda x: return str(x).upper() if isinstance(x, str)
    overlap = 3
    # Retrieve relevant customer and product information
    ccols = ["FULL NAME", "MULTI SELECTION FIELD", "MULTI SELECTION FIELD 2", "MULTI SELECTION FIELD 3",
             "MULTI SELECTION FIELD 4", "MULTI SELECTION FIELD 5"]
    products = pd.read_csv(cfname, usecols=lambda x: x.upper() in ccols)

    #retrieve relevant ingredient information
    icols = ["INGREDIENT COMMON NAME", "IN STOCK", "PRODUCT TYPE", "SKIN TYPE",
            "TYPE OF INGREDIENT", "ESSENTIAL OIL NOTE", "SOLUBILITY",
            "SKIN PROBLEM", "CONTRAINDICATIONS"]
    ingredients = pd.read_csv(ifname, usecols=lambda x: x.upper() in icols)

    #retrieve ingredient list for each product
    for i in range(products.shape[0]):
        ailments = str(products.loc[i,"Multi Selection Field 3"]).split(", ") + \
                   str(products.loc[i,"Multi Selection Field 4"]).split(", ") + \
                   str(products.loc[i,"Multi Selection Field 5"]).split(", ")
        usercons = conFinder(str(products.loc[i,"Multi Selection Field"]), str(products.loc[i,"Multi Selection Field 2"]))

        rows, rownames = ingredientParser(ingredients, ailments, usercons)
        print("\n\nPatient name: ", products.loc[i,"Full Name"])
        print("\nUsercons", usercons)
        print("\nailments: ", ailments)
        print("\nRows: ",len(rownames), rownames)

def conFinder(allergies, medcons):
    cons = []
    for allergy in allergies.split(", "):
        if allergy == "nut allergies":
            cons.append("Nut allergy")

    for medcon in medcons.split(", "):
        if medcon == "High blood pressure":
            cons.append("High blood pressure")
    return cons

def checkStock(stock):
    if not stock.upper() == "NO":
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

def dlxRowFormat(row, items):
    nodes = []
    cures = str(row["SKIN PROBLEM"]).split(",")
    for cure in cures:
        if cure in items:
            nodes.append((items.index(cure),0))
    return nodes


if __name__ == '__main__':
    ingredFname = "/Users/HG/Desktop/Ingredients.csv"
    userFname = "/Users/HG/Desktop/customers.csv"

    customerParser(userFname, ingredFname)
