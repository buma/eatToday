import itertools
import re

from connectSettings import connectString

import sqlalchemy                                                                                                                                                
from sqlalchemy.orm import sessionmaker                                                                                                                          
from sqlalchemy.exc import DBAPIError
from database import (
        Item,
        LocalNutrition,
        LocalNutritionaliase,
        FoodNutrition,
        FoodNutritionDetails,
        UsdaWeight
        )
from gourmet_db import Nutrition
from util import get_amounts, get_nutrition, calculate_nutrition, add_nutrition_details

engine = sqlalchemy.create_engine(connectString)
gourmet_engine = \
        sqlalchemy.create_engine("sqlite:////home/mabu/.gourmet/recipes_copy.db")

Session = sessionmaker()                                                                                                                          
Session.configure(binds={Item: engine,
    Nutrition: gourmet_engine,
    #Nutritionaliase: gourmet_engine,
    LocalNutrition: engine,
    LocalNutritionaliase: engine,
    FoodNutrition: engine,
    FoodNutritionDetails: engine,
    UsdaWeight: engine
    })

session = Session() 


items = session.query(Item) \
        .filter(Item.nutrition.isnot(None)) \
        .filter(Item.calc_nutrition.is_(None))



#Updates items
for item in items:
    print (item)
    print (get_nutrition(item, session))
    session.commit()
    print ()

add_nutrition_details(session)

#fns = session.query(FoodNutrition) \
        #.filter(FoodNutrition.nutrition.contains("SWEET_COCOA"))
#for fn in fns:
    #print (fn.nutrition, fn)
    ##print(calculate_nutrition(fn.nutrition))
    #calc_nutrition = calculate_nutrition(fn.nutrition, session)
    #if calc_nutrition is not None and calc_nutrition.kcal != fn.kcal:
        #nutrition_dict = calc_nutrition.__dict__
        #del nutrition_dict["_sa_instance_state"]
        #fn1 = FoodNutrition(**nutrition_dict)
        #fn1.nutrition = fn.nutrition
        #fn1.id = fn.id
        #session.merge(fn1)
        #print ("DIF", fn1, fn1.magnesium)
    #print()
#session.commit()

 #c = calculate_nutrition("1.1*GFREE_BUTTER+0.4*DCHOCOLATE_85+1.6*DCHOCOLATE_65+3medium*EGG+0.3*HONEY+1.4*SUGAR+1tsp*VANILLA+1.15*BUC
    #...: KWHEAT_FLOUR+2tsp*CORNSTARCH+1tsp*SALT")
#weight= 110+200+132+170+4.2+115+10+6
