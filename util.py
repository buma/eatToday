import itertools
from sqlalchemy.orm.exc import NoResultFound
from database import Item, LocalNutrition, LocalNutritionaliase, FoodNutrition
from gourmet_db import Nutrition, Nutritionaliase, UsdaWeight
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

"""
Gets nutrition for each item

items is list of lowerkey aliases for nutrition info.

each item is checked in nutritionalAliases gourmet and LocalNutritionaliases as
ingkey. If nutrition is found it is added to dict, key ingkey value nutrition

if all nutrition info was found dict is returned
"""
def get_nutrition_for(items, session):
    nutritions = {}
    gourmet_query = session.query(Nutritionaliase) \
            .filter(Nutritionaliase.ingkey.in_(items))
    local_query = session.query(LocalNutritionaliase) \
            .filter(LocalNutritionaliase.ingkey.in_(items))

    for n in itertools.chain(gourmet_query, local_query):
        #print (n.ingkey, n.nutrition)
        nutritions[n.ingkey.upper()]=n.nutrition
    if len(items) == len(nutritions):
        return nutritions

"""
Gets gram value for nutrition

nutrition is LocalNutrition, item is dict with desc unit and number value.

This calculates how many grams is 1tsp or 4slices for example.
First gramwt1 or gramwt2 in nutrition itself is checked. Then USDA weights
table for this item if unit is tsp or tbsp standard values are assumed

if nothing is found None is returned otherwise how many grams divided by 100
    this is
"""
def get_grams(nutrition, item, session):
    desc = item["desc"].rstrip('s')
    amount = float(item["number"])
    if nutrition.gramdsc1 is not None and \
        desc in nutrition.gramdsc1:
            return amount*nutrition.gramwt1/100
    if nutrition.ndbno < 100000:
        if nutrition.gramdsc2 is not None and \
            desc in nutrition.gramdsc2:
                return amount*nutrition.gramwt2/100
        try:
            usda_amount = session.query(UsdaWeight) \
                    .filter(UsdaWeight.ndbno==nutrition.ndbno) \
                    .filter(UsdaWeight.unit.like("%"+desc+"%")) \
                    .one()
            return amount*usda_amount.gramwt/100
        except Exception as a:
            pass
    print ("Guessing weight for ", nutrition.desc, desc)
    if desc.lower() == "tsp":
        return amount*0.05
    if desc.lower() == "tbsp":
        return amount*14.3/100



def calculate_nutrition(nutrition, session):
    if nutrition is None:
        return
    amounts, weird_amounts, types = get_amounts(nutrition)
    print ("Search for stuff")
    nutritions = get_nutrition_for(types, session)
    if nutritions is not None:
        #print (types, nutritions)
        prev = None
        for item, value in weird_amounts.items():
            match = nondigit.match(value)
            #print (item, value, match.groups())
            grams = get_grams(nutritions[item], match.groupdict())
            if grams:
                print (value, "->", grams*100, "g")
                amounts[item]=grams
        print ("DOUTNG\n")
        for item, value in amounts.items():
            print ("{} ({})*{} L{}".format(item, value, nutritions[item],
                nutritions[item].lipid))
            current = value*nutritions[item]
            if prev is not None:
                prev = prev + current
            else:
                prev = current
        print (prev, "Carb:",  prev.carb, "Belj:", prev.protein, "Masc:", prev.lipid)
        return prev

def get_nutrition(item, session):
    if item.calc_nutrition is None:
        try:
            fn = session.query(FoodNutrition) \
                    .filter(FoodNutrition.nutrition==item.nutrition) \
                    .one()
            item.calc_nutrition = fn.id
            session.merge(item)
            return fn
        except NoResultFound as e:
            calc_nutrition = calculate_nutrition(item.nutrition, session)
            if calc_nutrition is not None:
                nutrition_dict = calc_nutrition.__dict__
                del nutrition_dict["_sa_instance_state"]
                fn = FoodNutrition(**nutrition_dict)
                fn.nutrition = item.nutrition
                session.add(fn)
                session.flush()
                item.calc_nutrition = fn.id
                session.merge(item)

    else:
        return item.nutri_info
