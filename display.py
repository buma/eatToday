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

import colorama
colorama.init(autoreset=True)

from database import Item, FoodNutrition
from connectSettings import connectString

engine = sqlalchemy.create_engine(connectString)

Session = sessionmaker(bind=engine)

session = Session() 

weight = 64 #6:54 20.6 7:42 21.6 63
needed_kcal = 2200
needed_kcal_lunch = 1300
#First number are actual calories of lunch
diff = 0 #  721-500
#Calculated based on 15:00-7:00/2 per 2 hours
needed_kcal_2_hours_till_lunch=(needed_kcal_lunch)/(8/2) 
lunch_kcal=500
if diff > 0:
    needed_kcal_2_hours_after_lunch=(needed_kcal-4*needed_kcal_2_hours_till_lunch-lunch_kcal)/2-(diff*0.4)/2
    needed_kcal_2_hours_till_lunch-=(diff*0.6)/4
else:
    needed_kcal_2_hours_after_lunch=(needed_kcal-4*needed_kcal_2_hours_till_lunch-lunch_kcal)/2

print ("Needed kcal", needed_kcal, "lunch kcal", lunch_kcal, "tolunch kcal",
        needed_kcal_2_hours_till_lunch, "after lunch",
        needed_kcal_2_hours_after_lunch)


needed_protein = 1.5*weight
needed_protein_lunch= 1300/needed_kcal*needed_protein
lunch_protein = math.ceil(500/2200*needed_protein)
diff = 0 # 56-lunch_protein
needed_protein_2_hours_till_lunch=needed_protein_lunch/(8/2) # needed_kcal_2_hours_till_lunch/needed_kcal*needed_protein
if diff > 0:
    needed_protein_2_hours_after_lunch=(needed_protein-4*needed_protein_2_hours_till_lunch-lunch_protein)/2-(diff*0.4)/2
    needed_protein_2_hours_till_lunch-=(diff*0.6/4)
else:
    needed_protein_2_hours_after_lunch=(needed_protein-4*needed_protein_2_hours_till_lunch-lunch_protein)/2

#needed_kcal_2_hours_after_lunch/needed_kcal*needed_protein
print ("Needed protein", needed_protein, "lunch protein", lunch_protein, "tolunch protein",
        needed_protein_2_hours_till_lunch, "after lunch",
        needed_protein_2_hours_after_lunch)

def item_group(item):
    hour = item.time.hour
    if hour%2==0:
        return hour+1
    else:
        return hour

#filt_items = filter(lambda x: x.nutri_info is not None and x.time > datetime.datetime.now(), items)

#for key, group in itertools.groupby(filt_items, item_group):
    #print (key)
    #for thing in group:
        #print ("   ",thing)


show_part = set()
def display_part(hour, nutritions):
    show_part.add(hour)
    sumpart=sum(nutritions)
    water_factor=(hour-7)/2
    if hour < 17:
        factor=(hour-7)/2
        should_part=FoodNutrition(kcal=-needed_kcal_2_hours_till_lunch*factor,
                protein=-needed_protein_2_hours_till_lunch*factor, 
                carb=0, lipid=0, water=-300*water_factor, fiber=0, sugar=0)
    elif hour==17:
        should_part=FoodNutrition(kcal=-needed_kcal_2_hours_till_lunch*4-lunch_kcal,
                protein=-needed_protein_2_hours_till_lunch*4-lunch_protein, 
                carb=0, lipid=0, water=-300*water_factor, fiber=0, sugar=0)
    elif hour>17:
        factor=(hour-17)/2
        kcal = needed_kcal_2_hours_till_lunch*4+lunch_kcal
        kcal += needed_kcal_2_hours_after_lunch*factor

        protein = needed_protein_2_hours_till_lunch*4+lunch_protein
        protein += needed_protein_2_hours_after_lunch*factor
        should_part=FoodNutrition(kcal=-kcal,protein=-protein, 
                carb=0, lipid=0, water=-300*water_factor, fiber=0, sugar=0)
    #print ("SUM:", hour)
    #print("SUM", "{}".format(sumpart))
    #print("SHOULD", should_part.kcal, should_part.protein)
    print ("DIF:", hour, ":00", " "*55+"{:diff}".format(should_part+sumpart))


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
    ITEM="{time:^5} {type:^8} {description:50.50} {kalorije:^7} {hidrati:^6} {beljakovine:^8}"
    ITEM+=" {fat:^6} {fiber:^6} {sugar:^6} {water:^7}"
    print (ITEM.format(time="time", type="type", description="description",
            kalorije="kcal", hidrati="carb", beljakovine="protein", fat="fat",
            fiber="fiber", sugar="sugar", water="water"))
    sumed_lunch = None
    for item in items:
        #print ("FORMAT:|",item.__format__(""),"|")
        if item.time.hour >= 9 and item.time.hour not in show_part: 
            hour=item.time.hour
            for i in range(9,hour+1,2):
                if i not in show_part:
                    display_part(i, nutritions)
        print ("{}".format(item))
        if item.nutri_info is not None:
            nutritions.append(item.nutri_info)
            if sumed_lunch is None and item.time.hour >= 15:
                sumed_lunch = sum(nutritions)
    sumed = (sum(nutritions))
    if sumed_lunch is None:
        sumed_lunch = sumed
    missing_kcal = needed_kcal-sumed.kcal
    missing_protein = needed_protein-sumed.protein
    if item.time.hour < 9:
        hour=9
        display_part(hour, nutritions)
    elif item.time.hour < 21:
        hour=item.time.hour
        if hour%2==0 and hour+1 not in show_part:
            hour+=1
        elif hour%2==1 and hour+2 not in show_part:
            hour+=2
        if hour%2==1:
            display_part(hour, nutritions)
    for i in range(9,21,2):
        if i not in show_part:
        #display_part(i, [FoodNutrition(kcal=0, protein=0, carb=0, water=0,
            #fiber=0, sugar=0, lipid=0)])
            display_part(i, nutritions)
    print ("SUM:"," "*61+"{}".format(sumed))
    missing_kcal_time = missing_kcal/(hours_to_evening/2) if \
            hours_to_evening > 0 else 0
    missing_protein_time = missing_protein/(hours_to_evening/2) if \
            hours_to_evening > 0 else 0
    print (TEMPL.format(missing_kcal, missing_kcal_time,
        missing_protein, missing_protein_time,
        needed_kcal_lunch-sumed_lunch.kcal))

#dates = dateutil.rrule.rrule(dateutil.rrule.DAILY,
        #dtstart=datetime.datetime(2017,6,5), count=12)
#for date in dates:
    #show_date(date)
now = datetime.datetime.now()
yesterday = (now-dateutil.relativedelta.relativedelta(days=1))
show_date(now)
