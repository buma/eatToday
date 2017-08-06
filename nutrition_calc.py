import itertools
import re

from connectSettings import connectString

import sqlalchemy                                                                                                                                                
from sqlalchemy.orm import sessionmaker                                                                                                                          
from sqlalchemy.exc import DBAPIError
from database import Item, LocalNutrition, LocalNutritionaliase, FoodNutrition
from gourmet_db import Nutrition, Nutritionaliase, UsdaWeight
from util import get_amounts, get_nutrition, calculate_nutrition

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


items = session.query(Item) \
        .filter(Item.nutrition.isnot(None)) \
        .filter(Item.calc_nutrition.is_(None))



#Updates items
for item in items:
    print (item)
    print (get_nutrition(item, session))
    session.commit()
    print ()
