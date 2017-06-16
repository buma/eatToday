import itertools
import re

nondigit = re.compile("(?P<number>\d+)(?P<desc>\D+)")
from connectSettings import connectString

import sqlalchemy                                                                                                                                                
from sqlalchemy.orm import sessionmaker                                                                                                                          
from sqlalchemy.exc import DBAPIError   
from database import Item, LocalNutrition, LocalNutritionaliase
from gourmet_db import Nutrition, Nutritionaliase, UsdaWeight

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

def get_nutrition_for(items):
    nutritions = {}
    gourmet_query = session.query(Nutritionaliase) \
            .filter(Nutritionaliase.ingkey.in_(items))
    local_query = session.query(LocalNutritionaliase) \
            .filter(LocalNutritionaliase.ingkey.in_(items))

    for n in itertools.chain(gourmet_query, local_query):
        print (n.ingkey, n.nutrition)
        nutritions[n.ingkey.upper()]=n.nutrition
    if len(items) == len(nutritions):
        return nutritions

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
            amount = session.query(UsdaWeight) \
                    .filter(UsdaWeight.ndbno==nutrition.ndbno) \
                    .filter(UsdaWeight.unit.like("%"+desc+"%")) \
                    .one()
        except Exception as a:
            if "powder" in  nutrition.desc.lower():
                if desc.lower() == "tsp":
                    return amount*0.05
                if desc.lower() == "tbsp":
                    return amount*14.3/100
        if amount:
            return amount*amount.gramwt/100



def get_nutrition(nutrition):
    if nutrition is None:
        return
    items = nutrition.split("+")
    amounts = {}
    weird_amounts = {}
    for item in items:
        amount, type = item.split("*")
        print ("Amount:{} {}".format(amount, type))
        try:
            val = float(amount)
            amounts[type] = val
        except ValueError as e:
            weird_amounts[type] = amount
            print ("No pure value", amount)
    types = [x.lower() for x in itertools.chain(amounts.keys(),
        weird_amounts.keys())]
    print ("Search for stuff")
    nutritions = get_nutrition_for(types)
    if nutritions is not None:
        print (types, nutritions)
        prev = None
        for item, value in weird_amounts.items():
            match = nondigit.match(value)
            print (item, value, match.groups())
            grams = get_grams(nutritions[item], match.groupdict())
            if grams:
                print (value, "->", grams)
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
        print (prev, prev.carb, prev.protein, prev.lipid)
        return prev



for item in items:
    print (item)
    print (get_nutrition(item.nutrition))
    print ()
