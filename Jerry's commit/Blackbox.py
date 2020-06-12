import random

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
        type_list = str(self.ingredients_df.loc[ingredient_name]["TYPE OF INGREDIENT"]).lower().split(",")
        ingredient_type = type_list[-1]

        # Remove leading space
        if ingredient_type[0] == " ":
            ingredient_type = ingredient_type[1:]

        if ingredient_type == "anhydrous base" or ingredient_type == "aqueous base":
            assigned_vals[item] = random.randrange(15,75)

        elif "high performance" in ingredient_type:
            assigned_vals[item] = random.randrange(1,5)

        elif "essential oil" in ingredient_type:
            assigned_vals[item] = random.randrange(0,1)

        else:
            assigned_vals[item] = random.randrange(0,5)

    # Scale to 100
    tot = sum(assigned_vals.items)
    if tot > 100:
        for key in assigned_vals.keys():
            assigned_vals[key] = assigned_vals[key] * 100/tot
    elif tot < 100:
        for key in assigned_vals.keys():
            assigned_vals[key] = assigned_vals[key] * tot/100
    else:
        pass

    return assigned_vals

if __name__ == __main__:
    
