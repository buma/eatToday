import datetime

import dateutil.relativedelta
import sqlalchemy
import itertools
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker

from tabulate import tabulate

from connectSettings import connectString
from database import (
        Item,
        FoodNutritionDetails,
        FoodNutritionDetailsTime,
        FoodNutrition,
        LocalNutrition,
        LocalNutritionaliase,
        t_foodnutrition_details_alias_time,
        Tag,
        TagItem,
        FoodNutritionTags,
        FoodTag,
        FoodTagItem,
        )
engine = sqlalchemy.create_engine(connectString, echo=True)
Session = sessionmaker(bind=engine)
session = Session() 
LAST_MONDAY = dateutil.relativedelta.relativedelta(
        weekday=dateutil.relativedelta.MO(-1))

now = datetime.datetime.now()
START_OF_MONTH=now.replace(day=1)
week_before =  (now+LAST_MONDAY)
#week_before = START_OF_MONTH
now = (now+dateutil.relativedelta.relativedelta(days=1))

print ("{} - {}".format(week_before, now))
headers = ["INGKEY", "weight", "packages"]
table = []
items1 = session.query(LocalNutritionaliase.ingkey,
        FoodNutritionDetails.weight*100, 
        Item.time) \
       .filter(FoodNutritionDetails.ndbno==LocalNutritionaliase.ndbno) \
       .filter(FoodNutritionDetails.fn_id==Item.calc_nutrition) \
       .filter(FoodNutritionDetails.ndbno==TagItem.ndbno) \
       .filter(Tag.id==TagItem.tag_id)
#List of nutrition, tags for each nutrition part and weight for each nutrition
#with eaten time and ingkey
items_1 = session.query(Item.time, FoodNutrition.nutrition,
        LocalNutritionaliase.ingkey, Tag.name,(FoodNutritionDetails.weight*100).label("weight_sum")) \
        .filter(Item.time.between(
             week_before.date(), now.date())) \
        .filter(FoodNutritionDetails.ndbno==LocalNutritionaliase.ndbno) \
        .filter(FoodNutritionDetails.fn_id==Item.calc_nutrition)  \
        .filter(FoodNutritionDetails.ndbno==TagItem.ndbno) \
        .filter(FoodNutritionDetails.fn_id==FoodNutrition.id) \
        .filter(Tag.id==TagItem.tag_id).order_by(Item.time)
items_s = session.query(Tag.name, Tag.id) \
        .filter(FoodNutritionDetails.ndbno==TagItem.ndbno) \
        .filter(Tag.id==TagItem.tag_id) \

#Prints list of all used ingkeys and its counts
items_i = session.query(LocalNutritionaliase.ndbno, LocalNutritionaliase.ingkey,
        func.count(LocalNutritionaliase.ingkey).label("count_ingkey")) \
        .filter(FoodNutritionDetails.ndbno==LocalNutritionaliase.ndbno) \
        .group_by(FoodNutritionDetails.ndbno) \
        .order_by("count_ingkey")
#print (tabulate(items_i))

#Prints all ingkeys with usages which doesn't have tags
tag_items = session.query(TagItem.ndbno.distinct())
items_t = session.query(LocalNutritionaliase.ingkey,
        func.count(LocalNutritionaliase.ingkey).label("count_ingkey")) \
        .filter(FoodNutritionDetails.ndbno==LocalNutritionaliase.ndbno) \
        .filter(~FoodNutritionDetails.ndbno.in_(tag_items)) \
        .group_by(FoodNutritionDetails.ndbno) \
        .order_by("count_ingkey")
#print (tabulate(items_t))

#fillFoodnutritionTags(session)
def fillFoodnutritionTags(session):
    ids = session.query(FoodNutritionTags.fn_id.distinct())
#Gets list of foodnutritions with nutrition, ingkeys and tags
#Only distinct tags on each foodnutriton this means that not all ingkeys are
#outputed
#Filters out Brez * and Za v * tags
    items = session.query(FoodNutritionDetails.fn_id, FoodNutrition.nutrition,
            LocalNutritionaliase.ingkey, Tag.name) \
            .filter(FoodNutritionDetails.ndbno==LocalNutritionaliase.ndbno) \
            .filter(FoodNutritionDetails.ndbno==TagItem.ndbno) \
            .filter(FoodNutritionDetails.fn_id==FoodNutrition.id) \
            .filter(Tag.id==TagItem.tag_id) \
            .filter(~Tag.name.startswith("Brez")) \
            .filter(~Tag.name.startswith("Za v")) \
            .filter(~Tag.name.startswith("Vsebuje ")) \
            .group_by(FoodNutritionDetails.fn_id, Tag.id) \
            .order_by(sqlalchemy.desc(FoodNutritionDetails.fn_id)) \
            #.limit(15)
            #.filter(~FoodNutritionDetails.fn_id.in_(ids)) \

    print (items)

    headers = ["time", "nutrition", "ingkey", "tag_name", "weight"]

#import csv

#with open("./items.csv", "w") as f:
        #data = csv.writer(f)
        #data.writerow(headers)
        #data.writerows(items)

#print (tabulate(items))

    def keyfunc(item):
        return (item[0], item[1])

    for nutrition, tags in itertools.groupby(items, key=keyfunc):
        print (nutrition)
        #print (list(tags))
        ingkey_tags = ((x[2],x[3]) for x in tags)
        ingkey_list, tags_list = zip(*ingkey_tags)
        tags_list = sorted(tags_list)
        print (" ",", ".join(tags_list))
        print (" ",", ".join(ingkey_list))
        food_tags = FoodNutritionTags(fn_id=nutrition[0],
                tags=",".join(tags_list))
        session.add(food_tags)
    session.commit()


items_fd = session.query(func.group_concat(FoodTag.name) 
        .label("food_tag_names"), FoodNutritionTags.tags) \
    .join(FoodTagItem) \
    .filter(FoodTagItem.fn_id==FoodNutritionTags.fn_id) \
    .group_by(FoodTagItem.fn_id) \
    .order_by("food_tag_names", FoodNutritionTags.tags)
print (tabulate(items_fd, headers=["Food tags", "tags"]))

#a=5/0
