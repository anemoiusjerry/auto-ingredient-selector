
import pandas as pd

fname = "ingredientsList.csv"

data = pd.read_csv(fname, usecols=lambda x: x.upper() in ['INGREDIENT NAME','MULTI SELECTION FIELD', 'MULTI SELECTION FIELD 7', 'MULTI SELECTION FIELD 2', 'MULTI SELECTION FIELD 3', 'MULTI SELECTION FIELD 4', 'MULTI SELECTION FIELD 5', 'MULTI SELECTION FIELD 6'])


print(data)
