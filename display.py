import itertools
import re

nondigit = re.compile("(?P<number>\d+)(?P<desc>\D+)")
from connectSettings import connectString

import sqlalchemy                                                                                                                                                
from sqlalchemy.orm import sessionmaker                                                                                                                          
from sqlalchemy.exc import DBAPIError   
from database import Item, LocalNutrition, LocalNutritionaliase
from gourmet_db import Nutrition, Nutritionaliase, UsdaWeight
from util import get_amounts

engine = sqlalchemy.create_engine(connectString)
gourmet_engine = \
        sqlalchemy.create_engine("sqlite:////home/mabu/.gourmet/recipes_copy.db")

Session = sessionmaker()                                                                                                                          
Session.configure(binds={Item: engine,
    Nutrition: gourmet_engine,
    Nutritionaliase: gourmet_engine,
    LocalNutrition: engine,
    LocalNutritionaliase: engine,
    UsdaWeight: gourmet_engine
    })

session = Session() 


items = session.query(Item) \
        .filter(Item.time.between('2017-06-16', '2017-06-17')) \
        .order_by(Item.time)

"""
Gets nutrition for each item

items is list of lowerkey aliases for nutrition info.

each item is checked in nutritionalAliases gourmet and LocalNutritionaliases as
ingkey. If nutrition is found it is added to dict, key ingkey value nutrition

if all nutrition info was found dict is returned
"""
def get_nutrition_for(items):
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
def get_grams(nutrition, item):
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
            print ("Guessing weight for ", nutrition.desc, desc)
            if desc.lower() == "tsp":
                return amount*0.05
            if desc.lower() == "tbsp":
                return amount*14.3/100



def get_nutrition(nutrition):
    if nutrition is None:
        return
    amounts, weird_amounts, types = get_amounts(nutrition)
    print ("Search for stuff")
    nutritions = get_nutrition_for(types)
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
            #print ("{} ({})*{} L{}".format(item, value, nutritions[item],
                #nutritions[item].lipid))
            current = value*nutritions[item]
            if prev is not None:
                prev = prev + current
            else:
                prev = current
        print (prev, "Carb:",  prev.carb, "Belj:", prev.protein, "Masc:", prev.lipid)
        return prev



for item in items:
    print (item)
    print (get_nutrition(item.nutrition))
    print ()
