from dlx3 import DLX
import pandas as pd
import sys


def matrixGen(product, ingredients, ailments, userCons):
    # fname = filepath of the ingredients csv
    # userCons = list of user contraindications
    rows = []
    rownames = []
    # In the form [[ingredient types], [viscocity, Absorption rate, Comodegenic rating]]
    types = {"Oil Cleanser"     :[["ANHYDROUS","ESSENTIAL OIL"], [1,1,1]],
            "Cleansing Lotion"  :[["AQUEOUS","ANHYDROUS","ESSENTIAL OIL"], [1,1,1]],
            "Toner"             :[["AQUEOUS"], [0,2,0]],
            "Oil Serum"         :[["ANHYDROUS","ESSENTIAL OIL"], [0,1,0]],
            "Hydration Serum"   :[["AQUEOUS"], [0,2,0]],
            "Man Cream"         :[["AQUEOUS","ANHYDROUS","ESSENTIAL OIL"], [1,1,0]],
            "Day Cream"         :[["AQUEOUS","ANHYDROUS","ESSENTIAL OIL"], [0,2,0]],
            "Night Cream"       :[["AQUEOUS","ANHYDROUS","ESSENTIAL OIL"], [2,0,0]]}

    keywords = ["DRY","INFLAMED","CRACKING","FINE LINES","WRINKLES","DAMAGE FROM SUN",
                "ECZEMA","IRRITATED","ACNE","AGE SPOTS","TEWL","FIRMNESS","SEBUM",
                "CLOGGED","ENLARGED","SCARRING","REGENERATION","FLAKY","T-ZONE",
                "FINE DEHYDRATION LINES","ROUGH","ITCHING","REDNESS","DULL","FLAKING",
                "SCALING","PEELING","TIGHTNESS","DEHYDRAT"]

    problems = [k for a in ailments for k in keywords if k in a]
    problems = list(dict.fromkeys(problems))

    for i in range(ingredients.shape[0]):
        # Attain current stock, constraindications and ingredient type
        stock = ingredients.loc[i,"In Stock"]
        ingredCons = ingredients.loc[i,"CONTRAINDICATIONS"].split(",")
        type = ingredients.loc[i,"TYPE OF INGREDIENT"].split(",")

        # Filter the ingredients associated cures to contain keywords
        cures = ingredients.loc[i,"SKIN PROBLEM"].split(",")
        cures = [k for i in cures for k in keywords if k in i]
        cures = list(dict.fromkeys(cures))

        # check if the ingredient is in stock, not a contraindication and useable
        if checkStock(stock) \
          and contrainCheck(ingredCons, userCons) \
          and useablecheck(cures, problems) \
          and typeCheck(types[product][0], type):

            # Create and append nodes for each row of the dlx matrix created
            nodes = dlxRowFormat(cures, problems)
            rows.append((nodes, ingredients.loc[i,"INGREDIENT COMMON NAME"]))

    return rows, problems

def orderParser(product, qdata, ingredients):
    lowBound = 1
    upBound = 1
    chosen = []

    # Filetring and retrieving the skin problems from customer info
    ailments = qdata["Multi Selection Field 4"].split(", ") + qdata["Multi Selection Field 5"].split(", ")
    ailments = [a for a in ailments if a and a!="I DON'T KNOW...THAT'S WHAT I NEED YOU FOR :)"]

    # Finding the customers contraindications
    usercons = conFinder(qdata["Multi Selection Field"], qdata["Multi Selection Field 2"])

    # retrieve the rows and columns that will make up the dlx matrix
    rows, cols = matrixGen(product, ingredients, ailments, usercons)

    # Check that all cols can be stisfied at least once
    colsCovered = []

    # Convert cols into dlx useable format
    cols = [(cols[i],0,lowBound,upBound) for i in range(len(cols))]

    matrix = DLX(cols, rows)
    solutions = matrix.dance()


    print("Name: ", qdata["Full Name"], ", Product: ", product,", Rows: ", len(rows), ", Cols: ", len(cols), ", Solutions: ", end="")
    print(len(solutions))

    return chosen

def conFinder(allergies, medcons):
    cons = []
    for allergy in allergies.split(", "):
        if allergy == "NUT ALLERGIES":
            cons.append("NUT ALLERGY")

    for medcon in medcons.split(", "):
        if medcon == "HIGH BLOOD PRESSURE":
            cons.append("HIGH BLOOD PRESSURE")
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

def useablecheck(ingredSolves, problems):
    for i in ingredSolves:
        for k in problems:
            if k == i:
                return True
    return False

def typeCheck(types, type):
    for t1 in types:
        for t2 in type:
            if t1 in t2:
                return True
    return False

def dlxRowFormat(cures, problems):
    nodes = []
    for cure in cures:
        if cure in problems:
            nodes.append((problems.index(cure),None))
    return nodes

def runOrders():
    orderfname = "/Users/HG/Desktop/orders.csv"
    orders = pd.read_csv(orderfname)
    orders.fillna("", inplace = True)

    ingredFname = "/Users/HG/Desktop/Ingredients.csv"
    ingredients = pd.read_csv(ingredFname)
    ingredients.fillna("", inplace = True)
    ingredients = ingredients.applymap(lambda x:str(x).upper())

    qfname = "/Users/HG/Desktop/questionairre.csv"
    qnair = pd.read_csv(qfname)#.loc[:,"Full Name":]
    qnair.fillna("", inplace = True)
    qnair = qnair.applymap(lambda x:x.upper())
    qnair["Full Name"] = qnair["Full Name"].apply(lambda x:" ".join(x.split()))

    # Attaining the questionnaire information for the customer of each order
    # If it cant find the questionairre, the next order is attempted
    for i in range(orders.shape[0]):
        order = orders.loc[i,:]

        # Find the customer questionnaire using the name or email address
        # !!!! NOTE: A dialog should be added to check that the email corresponds to the correct person
        name = " ".join(order["Billing Customer"].upper().split())
        email = order["Buyer's Email"].upper()

        if name in qnair["Full Name"].values.tolist():
            qdata = qnair.loc[qnair["Full Name"].values.tolist().index(name)]
        elif email in qnair["Email"].values.tolist():
            qdata = qnair.loc[qnair["Email"].values.tolist().index(email)]
        else:
            #print("couldnt find", name)
            continue

        knownItems = {"Courageous Oil Serum"                :["Oil Serum"],
                      "Courageous Man Cream 30g"            :["Man Cream"],
                      "Confidence 2 Birds 30ml"             :["Hydration Serum", "Toner"],
                      "Confidence Goodness Pack 10ml each"  :["Oil Cleanser", "Oil Serum", "Hydration Serum"],
                      "Confidence Intro Set 30ml each"      :["Oil Cleanser", "Oil Serum", "Hydration Serum"],
                      "Confidence Cleanse Kit 30ml each"    :["Oil Cleanser", "Cleansing Lotion"],
                      "Confidence Hydrate & Moisture Set"   :["Oil Serum", "Hydration Serum"],
                      "Confidence Moisturiser Set 30g each" :["Day Cream", "Night Cream"],
                      "Confidence Complete Set 30ml each"   :["Oil Cleanser", "Cleansing Lotion", "Toner", "Oil Serum", "Hydration Serum"],
                      "Confidence Hydration Serum 30ml"     :["Hydration Serum"],
                      "Confidence Toner 30ml"               :["Toner"],
                      "Confidence Cleansing Lotion 30ml"    :["Cleansing Lotion"],
                      "Confidence Oil Cleanser 30ml"        :["Oil Cleanser"],
                      "Confidence Oil Serum 30ml"           :["Oil Serum"],
                      "Confidence Night Cream 30g"          :["Night Cream"],
                      "Confidence Day Cream 30g"            :["Day Cream"]}
        # Finding the products required to fulfil the order. if they cannot be found, skip to next order
        item = order["Item's Name"]
        if item in knownItems.keys():
            products = knownItems[item]
        else:
            #print("For customer:",name,", product:", item,"couldn't be found")
            continue

        for product in products:
            solutions = orderParser(product, qdata, ingredients)

if __name__ == '__main__':

    #sys.setrecursionlimit(1000)
    #print("recursion limit: ", sys.getrecursionlimit())

    runOrders()
