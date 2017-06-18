import itertools
import re
import datetime
import math

nondigit = re.compile("(?P<number>\d+)(?P<desc>\D+)")

import sqlalchemy                                                                                                                                                
from sqlalchemy.orm import sessionmaker                                                                                                                          
from sqlalchemy.exc import DBAPIError   
from sqlalchemy.orm import joinedload

import dateutil.rrule
import dateutil.relativedelta

from database import Item, FoodNutrition
from connectSettings import connectString

engine = sqlalchemy.create_engine(connectString)

Session = sessionmaker(bind=engine)

session = Session() 

weight = 63
needed_kcal = 2200
needed_protein = 1.5*weight


def show_date(date):
    today = date.date()
    tomorow = (date+dateutil.relativedelta.relativedelta(days=1)).date()
    print (today)
# Joinedload loads stuff in one query instead of multiple ones
    items = session.query(Item) \
            .options(joinedload(Item.nutri_info)) \
            .filter(Item.time.between(today, tomorow)) \
            .order_by(Item.time)
#items = session.query(Item).filter(Item.id==274)

    now = datetime.datetime.now()
    evening = datetime.datetime.now()
    evening=evening.replace(hour=20, minute=0, second=0)

    hours_to_evening = math.ceil((evening-now).total_seconds()/60/60)

    TEMPL="Preostale kal:{:.2f}\nKalorij na 2 uri:{}\nPreostale  beljakovine:{:.2f}"
    TEMPL+="\nBeljakovin na 2 uri:{:.2f}\nKalorije do kosila:{:.2f}"

    nutritions = []
    ITEM="{time:^5} {type:^8} {description:50.50} {kalorije:^6} {hidrati:^6} {beljakovine:^7}"
    ITEM+=" {fat:^6} {fiber:^6} {sugar:^6} {water:^10}"
    print (ITEM.format(time="time", type="type", description="description",
            kalorije="kcal", hidrati="carb", beljakovine="protein", fat="fat",
            fiber="fiber", sugar="sugar", water="water"))
    sumed_lunch = None
    for item in items:
        #print ("FORMAT:|",item.__format__(""),"|")
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
    missing_kcal_time = missing_kcal/(hours_to_evening/2) if \
            hours_to_evening > 0 else 0
    missing_protein_time = missing_protein/(hours_to_evening/2) if \
            hours_to_evening > 0 else 0
    print (TEMPL.format(missing_kcal, missing_kcal_time,
        missing_protein, missing_protein_time,
        needed_kcal/2-sumed_lunch.kcal))

#dates = dateutil.rrule.rrule(dateutil.rrule.DAILY,
        #dtstart=datetime.datetime(2017,6,5), count=12)
#for date in dates:
    #show_date(date)
show_date(datetime.datetime.now())
