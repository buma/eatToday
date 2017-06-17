import itertools
import re

nondigit = re.compile("(?P<number>\d+)(?P<desc>\D+)")
from connectSettings import connectString

import sqlalchemy                                                                                                                                                
from sqlalchemy.orm import sessionmaker                                                                                                                          
from sqlalchemy.exc import DBAPIError   
from database import Item, FoodNutrition

engine = sqlalchemy.create_engine(connectString)
gourmet_engine = \
        sqlalchemy.create_engine("sqlite:////home/mabu/.gourmet/recipes_copy.db")

Session = sessionmaker(bind=engine)

session = Session() 


items = session.query(Item) \
        .filter(Item.time.between('2017-06-17', '2017-06-18')) \
        .order_by(Item.time)
#items = session.query(Item).filter(Item.id==274)


for item in items:
    print (item)
    if item.nutri_info is not None:
        print (item.nutri_info)
    #print (get_nutrition(item.nutrition))
    #print ()
#get_nutrition("2cup*SPINACH+2*COOKED_NOSKIN_POTATO+2tsp*GLUTENFREE_BUTTER")
#get_nutrition("2cup*SPINACH+2*COOKED_NOSKIN_POTATO+2tsp*OLIVE OIL")
#get_nutrition("1.0*BROWN_LENTIL+0.53*CARROT+0.11*GARLIC+0.05*OLIVE OIL+0.65*ONION")
