import itertools
import datetime
import re
from collections import Counter

from tabulate import tabulate

import dateutil.rrule
import dateutil.relativedelta
import sqlalchemy                                                                                                                                                
from sqlalchemy.orm import sessionmaker                                                                                                                          
from sqlalchemy.exc import DBAPIError   
from sqlalchemy.orm import joinedload
from database import Item, FoodNutrition, LocalNutrition, LocalNutritionaliase
from gourmet_db import Nutrition, Nutritionaliase, UsdaWeight

from connectSettings import connectString

from util import get_amounts, get_grams, get_nutrition_for
nondigit = re.compile("(?P<number>[\d\.]+)(?P<desc>\D+)")
LAST_MONDAY = dateutil.relativedelta.relativedelta(
        weekday=dateutil.relativedelta.MO(-1))

engine = sqlalchemy.create_engine(connectString)
gourmet_engine = \
        sqlalchemy.create_engine("sqlite:////home/mabu/.gourmet/recipes_copy.db")

Session = sessionmaker()                                                                                                                          
Session.configure(binds={Item: engine,
    Nutrition: gourmet_engine,
    Nutritionaliase: gourmet_engine,
    LocalNutrition: engine,
    LocalNutritionaliase: engine,
    FoodNutrition: engine,
    UsdaWeight: gourmet_engine
    })

session = Session() 
now = datetime.datetime.now()
START_OF_MONTH=now.replace(day=1)
now = (now+dateutil.relativedelta.relativedelta(days=1))
week_before =  (now+LAST_MONDAY)
items = session.query(Item) \
        .filter(Item.time.between(week_before.date(), now.date())) \
        .filter(Item.type.in_(["HRANA", "PIJAČA"])) \
        .filter(Item.nutrition != None) \
        .order_by(Item.time)
        #.options(joinedload(Item.nutri_info)) \
sumu = Counter()
weirds = {}
all_nutritions = {}
#TODO set weight for irregular items (banana, hrenovke, potato), add prices,
#kcal etc
package_weight = {}
specific_weights = {
        "EGG":"1medium",
        "HRENOVKA":"2par",
        "BANANA":"1medium",
        "NECTARINE":"1medium"
        }

for food_item in items:
    #print (food_item)
    amounts, weird_amounts, types = get_amounts(food_item.nutrition)
    for food, amount in amounts.items():
        sumu[food]+=amount
    nutritions = get_nutrition_for(types, session)
    if not nutritions:
        continue
    for nutrition, v in filter(lambda x: isinstance(x[1],LocalNutrition),
            nutritions.items()):
        if v.package_weight is not None:
            package_weight[nutrition] = v.package_weight
    all_nutritions.update(nutritions)
    if weird_amounts:
        if nutritions is not None:
            for item, value in weird_amounts.items():
                match = nondigit.match(value)
                #print (item, value, match.groups())
                grams = get_grams(nutritions[item], match.groupdict(), session)
                if grams:
                    #print (value, "->", grams*100, "g")
                    sumu[item]+=grams
        for food, amount in weird_amounts.items():
            weirds[food]=amount

for food_item, value in specific_weights.items():
    if food_item in all_nutritions:
        print ("Have ", food_item)
        if isinstance(value, str):
            match = nondigit.match(value)
            print (item, value, match.groups())
            grams = get_grams(all_nutritions[food_item], match.groupdict(), session)
            if grams:
                package_weight[food_item]=grams*100
        else:
            package_weight[food_item]=value
    else:
        print (food_item, "not in ", all_nutritions.keys())



print ("{} - {}".format(week_before, now))
headers = ["INGKEY", "weight", "packages"]
table = []
for amount, value in sumu.most_common():
    packages = 0
    if amount in package_weight:
        packages = value*100/package_weight[amount]
        #packages = package_weight[amount]
    table.append([amount, value*100, packages])
print (tabulate(table, headers=headers))
#print ("Weirds:")
#for amount, value in weirds.items():
    #print (amount, value)

#print (all_nutritions.keys())
