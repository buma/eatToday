import itertools
def get_amounts(nutrition):
    items = nutrition.split("+")
    amounts = {}
    weird_amounts = {}
    for item in items:
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
Sorts nutrition string based on items
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
