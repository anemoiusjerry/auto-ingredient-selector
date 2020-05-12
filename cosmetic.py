from dlx import DLX, DLXStatistics
import sqlalchemy as db
import pandas as pd
#import os
import xlsxwriter
import time
# sqlalchemy and xlsxwriter must be installed prior to the use of this script

# Path to database
db_file = "/Users/HG/Documents/GitHub/ingredient-sorter/cosmeticTest.db"
#db_file = "/Users/HG/Desktop/Coding/Projects/Cosmetics/cosmeticTest.db"
#db_file = os.path.abspath(os.getcwd())+"/cosmeticTest.db"

# Ingredient table indexing info
IngredientNameIndex = 0
CuresIndex = 1
StockIndex = 2
ContradictIndex = 3
RcmndUseIndex = 4
QualityIndex = 5
AbsorbIndex = 6
ComoRatingIndex = 7

# Patient table indexing info
Nameindex = 0
IdIndex = 1
Ageindex = 2
SexIndex = 3
AilmentIndex = 4
AllergyIndex = 5

# Global varibales used in the _row_recurser and row_gen functions.
# *Note* combos should be cleared after each use of row_gen.
combos = []
temp_lst = []

def initialise_data(filepath):
    # Set up SQLAlchemy connection
    engine = db.create_engine('sqlite:///' + filepath)
    cnxn = engine.connect()

    # Copy table information in database
    metadata = db.MetaData()
    metadata.reflect(cnxn)

    # Retrieve table - string is name of table
    Patients = metadata.tables['patients']
    Ingredients = metadata.tables['ingredients']

    # Select query
    queryIngredient = db.select([Ingredients])
    queryPatient = db.select([Patients])
    IngredientData = cnxn.execute(queryIngredient).fetchall()
    PatientData = cnxn.execute(queryPatient).fetchall()

    return IngredientData, PatientData

def insert_query(table, data):
    query = table.insert().values(data)
    cnxn.execute(query)

def update_query(table, data):
    query = db.update(table).values(data)
    cnxn.execute(query)

def xlsx_write(ingredientLst):
    a=1

def create_dlx():
    # create the columns for the dlx instance. these represent the constraints that must be met
    constraints = [(almnt,DLX.PRIMARY) for almnt in patient[AilmentIndex].split(", ")]
    dlxInstance = DLX(constraints)
    # Creating the rows which will populate the dlx instance
    rows, rowNames = row_gen()
    dlxInstance.appendRows(rows, rowNames)

    return dlxInstance

def solve_dlx(grid):
    validSolutions = []
    for sol in grid.solve():
        solution = [name for i in sol for name in grid.N[i]]
        if contradiction_check(solution):
            validSolutions.append(solution)
    return validSolutions

def row_gen():
    ailments = patient[AilmentIndex].split(", ")
    rows = []
    rowNames = []
    # Inputting individual ingredients as rows as long as they contribute to the cure
    for ingredient in IngredientData[1:]:
        cures = ingredient[CuresIndex].split(", ")
        # create a list whose elements represent the index of an ailment within
        # the ailment list if that ingredient can treat that ailment
        row = [ailments.index(ailment) for ailment in ailments if ailment in cures]
        if row:
            rows.append(row)
            rowNames.append([ingredient])

    # inputting the overlapping ingredients as a row
    for ailment in ailments:
        # create a list of ingredients that can cure the same ailment
        overlapIngredients = [ingredient for ingredient in IngredientData[1:]
                                if (ailment in ingredient[CuresIndex].split(", "))]
        if len(overlapIngredients) > 1:
            # get all unique combinations of ingredients
            _row_recurser(overlapIngredients)
    for combo in combos:
        # create list of all ailments the combo of ingredients can cure
        cures = [i for ingredient in combo for i in ingredient[CuresIndex].split(", ")]
        row = sorted(list(set([ailments.index(ailment) for ailment in ailments if ailment in cures])))
        rows.append(row)
        rowNames.append(combo)

    return rows, rowNames

def _row_recurser(_vars):
    # recursive function that will append all unique combinations of list elements
    # to the global variable combos
    if _vars:
        for var in _vars:
            # if the contradiction list is empty
            if not var[ContradictIndex]:
                temp_lst.append(var)
                if len(temp_lst) > 1:
                    combos.append(temp_lst.copy())
                _row_recurser(_vars[_vars.index(var) + 1:])
                temp_lst.pop(-1)
            # if contradictions are present, make sure that an invalid combo isnt made
            else:
                contradictions = var[ContradictIndex].split(", ")
                comparitor = contradictions + [i[IngredientNameIndex] for i in temp_lst]
                if len(set(comparitor)) == len(comparitor):
                    temp_lst.append(var)
                    if len(temp_lst) > 1:
                        combos.append(temp_lst.copy())
                    _row_recurser(_vars[_vars.index(var) + 1:])
                    temp_lst.pop(-1)
    else:
        return

def get_patient(patientnumber):
    for patient in PatientData:
        if patientnumber == patient[IdIndex]:
            return list(patient)

def filter_ingredients():
    allergies = patient[AllergyIndex]
    for ingredient in IngredientData[1:]:
        # Remove the ingredient if it not in stock, Remove the ingredient if is an allergy of the patient
        cond1 = bool(ingredient[StockIndex] == 0)
        cond2 = bool(allergies and ingredient[IngredientNameIndex] in allergies.split(", "))
        if cond1 or cond2:
            IngredientData.remove(ingredient)

def get_min_ingredients(solutions):
    results = []
    min = 1000
    for solution in solutions:
        if len(solution) == min:
            results.append(solution)
        elif len(solution) < min:
            min = len(solution)
            results.clear()
            results.append(solution)
    return results

def contradiction_check(ingredients):
    for ingredient in ingredients:
        temp = ingredients.copy()
        temp.remove(ingredient)
        contradictions = ingredient[ContradictIndex]
        if contradictions:
            for contradiction in contradictions.split(", "):
                if contradiction in temp:
                    return False
    return True

if __name__ == '__main__':
    # Get the ingredient and patient data from the database
    IngredientData, PatientData = initialise_data(db_file)

    # Getting the relevant patient information
    print("Input patient id: ", end = "")
    id = input()
    start = time.time()
    patient = get_patient(id)

    # filter the ingredients for things such as stock and allergies
    filter_ingredients()

    # Create and then run the dlx solver
    grid = create_dlx()
    validSolutions = solve_dlx(grid)

    # printing all the solutions with the minimum number of ingredients
    for solution in get_min_ingredients(validSolutions):
        print([ingred[IngredientNameIndex] for ingred in solution])

    # Testing script performance
    end = time.time()
    print('Time Elapsed: ', end='')
    print(end - start, end='')
    print('seconds')
