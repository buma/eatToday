import datetime

import dateutil.relativedelta
import sqlalchemy
import itertools
from sqlalchemy.sql import func, case, literal_column, cast
from sqlalchemy import Float
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
        FoodNutritionTags
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
def get_ingkey():
    xpr = case([
        (LocalNutrition.package_weight != None,
        cast(literal_column("weight_sum"), Float)/LocalNutrition.package_weight)],
        else_=None)
#Week usage on ingkeys
    items = session.query(FoodNutritionDetailsTime.nutritionaliases_ingkey,
            func.sum(FoodNutritionDetailsTime.foodnutrition_details_weight*100) \
                    .label("weight_sum"), xpr) \
                    .filter(FoodNutritionDetailsTime.eat_time.between( \
                        week_before.date(), now.date())) \
                    .filter(LocalNutrition.ndbno==
                            FoodNutritionDetailsTime.foodnutrition_details_ndbno) \
                    .group_by(FoodNutritionDetailsTime.foodnutrition_details_ndbno) \
                    .order_by(sqlalchemy.desc("weight_sum"))
    print(items)
    return items
    for amount, value, package_weight in items:
        packages = 0
        if package_weight is not None:
            packages=value/package_weight
            print (amount, package_weight)
        yield (amount, value, packages)

def get_tag():
#Week usage on tags
    items_tag = session.query(Tag.name,
            func.sum(FoodNutritionDetails.weight*100).label("weight_sum"),
            func.count(Tag.id).label("tag_app")
            ) \
            .filter(Item.time.between( \
                week_before.date(), now.date())) \
        .filter(FoodNutritionDetails.ndbno==LocalNutritionaliase.ndbno) \
        .filter(FoodNutritionDetails.fn_id==Item.calc_nutrition) \
        .filter(FoodNutritionDetails.ndbno==TagItem.ndbno) \
        .filter(Tag.id==TagItem.tag_id) \
        .group_by(Tag.id) \
        .order_by(sqlalchemy.desc("weight_sum"))
    return items_tag

def get_tags():
#Week usage on tags
    items_tag = session.query(FoodNutritionTags.tags,
            func.count(FoodNutritionTags.tags).label("weight_sum") 
            ) \
            .filter(Item.time.between( \
                week_before.date(), now.date())) \
        .filter(FoodNutritionTags.fn_id==Item.calc_nutrition) \
        .group_by(FoodNutritionTags.tags) \
        .order_by(sqlalchemy.desc("weight_sum"))
    return items_tag

dbs = {
        "ingkey": (["INGKEY", "weight", "packages"],
            get_ingkey()
            ),
        "tag": (["Tag", "weight", "appearances"],
            get_tag()
            ),
        "tags": (["tags", "appearances"],
            get_tags()
            )
        }

DB = "ingkey"




headers, table = dbs[DB]
print(tabulate(table, headers=headers))
