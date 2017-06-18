import itertools
import re
import datetime
import math

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

now = datetime.datetime.now()
evening = datetime.datetime.now()
evening=evening.replace(hour=20, minute=0, second=0)

hours_to_evening = math.ceil((evening-now).total_seconds()/60/60)
weight = 63
needed_kcal = 2200
needed_protein = 1.5*weight

TEMPL="Preostale kal:{:.2f}\nKalorij na 2 uri:{}\nPreostale  beljakovine:{:.2f}"
TEMPL+="\nBeljakovin na 2 uri:{:.2f}\nKalorije do kosila:{:.2f}"

nutritions = []
ITEM="{time:^5} {type:^8} {description:50.50} {kalorije:^6} {hidrati:^6} {beljakovine:^7}"
ITEM+=" {fat:^6} {fiber:^6} {sugar:^6}"
print (ITEM.format(time="time", type="type", description="description",
        kalorije="kcal", hidrati="carb", beljakovine="protein", fat="fat",
        fiber="fiber", sugar="sugar"))
sumed_lunch = None
for item in items:
    print ("{}".format(item))
    if item.nutri_info is not None:
        nutritions.append(item.nutri_info)
        if sumed_lunch is None and item.time.hour >= 14:
            sumed_lunch = sum(nutritions)
sumed = (sum(nutritions))
if sumed_lunch is None:
    sumed_lunch = sumed
missing_kcal = needed_kcal-sumed.kcal
missing_protein = needed_protein-sumed.protein
print ("SUM:"," "*61+"{}".format(sumed))
print (TEMPL.format(missing_kcal, missing_kcal/(hours_to_evening/2),
    missing_protein, missing_protein/(hours_to_evening/2),
    needed_kcal/2-sumed_lunch.kcal))
