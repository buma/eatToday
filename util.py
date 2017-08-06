import itertools
"""
    Gets amounts, weird_amounts and types from nutrition string

    Nutrition string is 1kroznik*POLENTA+1tbsp*CVIRKI+1*WATER

    amounts are just float numbers (1 in this example)
    weird_amounts are descriptive amounts which float value needs to be
    determined (1kroznik and 1tbsp) in this example

    types are food names (POLENTA, CVIRKI, WATER) in this example

    Return:
    types are returned lowercase

"""
def get_amounts(nutrition):
    items = nutrition.split("+")
    amounts = {}
    weird_amounts = {}
    for item in items:
        #print ("ITEM:|",item,"|")
        amount, type = item.split("*")
        #print ("Amount:{} {}".format(amount, type))
        type = type.strip()
        try:
            val = float(amount)
            amounts[type] = val
        except ValueError as e:
            weird_amounts[type] = amount
            #print ("No pure value", amount)
    types = [x.lower() for x in itertools.chain(amounts.keys(),
        weird_amounts.keys())]
    return amounts, weird_amounts, types

"""
Sorts nutrition string based on item types (AKA food names)
And change them in uppercase
"""
def sort_nutrition_string(nutrition):
    amounts, weird_amounts, types = get_amounts(nutrition)
    types.sort()
    items = []
    for type in types:
        up_type = type.upper()
        if up_type in amounts:
            items.append("{}*{}".format(amounts[up_type], up_type))
        else:
            items.append("{}*{}".format(weird_amounts[up_type], up_type))
    return "+".join(items)
