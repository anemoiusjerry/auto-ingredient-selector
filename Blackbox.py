import random
import re

def ingredient_weight_BB(ingredients, prod_type, ingredients_df):
    """ Simulates weighting calc. (The real code would require
        you to install google drive apis and lots of additional inputs)

        inputs: ingredients - list of strings of ingredient names
                product_type - day cream, night cream etc
                ingredients_df - dataframe for ingredients database
        returns: dict {ingredient name: assigned weighting %}
    """

    assigned_vals = {}
    for item in ingredients:
        # Get ingredient types ???????????/// Waiting for answer to simply column
        ind = ingredients_df["INGREDIENT COMMON NAME"].values.tolist().index(item)
        type_list = re.split("\s*[,]\s*", ingredients_df.loc[ind,"TYPE OF INGREDIENT"])

        if "ANHYDROUS BASE" in type_list or "AQUEOUS BASE" in type_list:
            assigned_vals[item] = random.randrange(15,75)

        elif "AQUEOUS HIGH PERFORMANCE" in type_list or "ANHYDROUS HIGH PERFORMANCE" in type_list:
            assigned_vals[item] = random.randrange(1,5)

        elif "ESSENTIAL OIL" in type_list:
            assigned_vals[item] = random.randrange(1,10)/10

        else:
            assigned_vals[item] = random.randrange(1,50)/10

    # Scale to 100
    tot = sum(assigned_vals.values())
    if tot > 100:
        for key in assigned_vals.keys():
            assigned_vals[key] = assigned_vals[key] * 100/tot
    elif tot < 100:
        for key in assigned_vals.keys():
            assigned_vals[key] = assigned_vals[key] * tot/100
    else:
        pass

    return assigned_vals

if __name__ == '__main__':
    a=1
