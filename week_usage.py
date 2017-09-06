import itertools
import datetime
import re
from collections import Counter

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
week_before =  (now-dateutil.relativedelta.relativedelta(days=3))
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
for food_item in items:
    #print (food_item)
    amounts, weird_amounts, types = get_amounts(food_item.nutrition)
    for food, amount in amounts.items():
        sumu[food]+=amount
    nutritions = get_nutrition_for(types, session)
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

print ("{} - {}".format(week_before, now))
for amount, value in sumu.most_common():
    packages = 0
    if amount in package_weight:
        packages = value*100/package_weight[amount]
    print (amount, value*100, "g", packages)
#print ("Weirds:")
#for amount, value in weirds.items():
    #print (amount, value)

#print (all_nutritions.keys())
