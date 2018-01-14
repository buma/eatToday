import datetime

import dateutil.relativedelta
import sqlalchemy
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
        t_foodnutrition_details_alias_time
        )
engine = sqlalchemy.create_engine(connectString)
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

items = session.query(FoodNutritionDetailsTime.nutritionaliases_ingkey,
        func.sum(FoodNutritionDetailsTime.foodnutrition_details_weight*100) \
                .label("weight_sum"), LocalNutrition.package_weight) \
                .filter(FoodNutritionDetailsTime.eat_time.between( \
                    week_before.date(), now.date())) \
                .filter(LocalNutrition.ndbno==
			FoodNutritionDetailsTime.foodnutrition_details_ndbno) \
                .group_by(FoodNutritionDetailsTime.foodnutrition_details_ndbno) \
                .order_by(sqlalchemy.desc("weight_sum"))

for amount, value, package_weight in items:
    packages = 0
    if package_weight is not None:
        packages=value/package_weight
        print (amount, package_weight)
    table.append([amount, value, packages])
print (tabulate(table, headers=headers))
