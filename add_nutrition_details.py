from connectSettings import connectString

import sqlalchemy
from sqlalchemy.orm import sessionmaker                                                                                                                          
from sqlalchemy.exc import DBAPIError
from database import (
        Item,
        LocalNutrition,
        LocalNutritionaliase,
        FoodNutrition,
        FoodNutritionDetails
        )
from util import get_amounts, get_nutrition, calculate_nutrition

engine = sqlalchemy.create_engine(connectString)# echo=True)

Session = sessionmaker(bind=engine)
session = Session() 

alias_ndbno = {}

for alias, ndbno in session.query(LocalNutritionaliase.ingkey,
        LocalNutritionaliase.ndbno):
    alias_ndbno[alias]=ndbno

def get_ndbno(nutritionalias):
    return alias_ndbno[nutritionalias]
    #return session.query(LocalNutritionaliase.ndbno) \
            #.filter(LocalNutritionaliase.ingkey==nutritionalias) \
            #.scalar()

ids = session.query(FoodNutritionDetails.fn_id.distinct())

        #.filter(~FoodNutrition.id.in_(ids)) \
food_nutri_q = session.query(FoodNutrition) \
        .filter(~FoodNutrition.id.in_(ids)) \
        .filter(FoodNutrition.nutrition != None)
        #.limit(1)

for foodnutrition in food_nutri_q:
    nutrition = foodnutrition.nutrition
    if "BORANJA" in nutrition:
        print ("SKIPPING BORANJA")
        continue
    print(nutrition, foodnutrition.id)
    amounts, weird_amounts, types = get_amounts(nutrition, session)
    for nutrition_alias, weight in amounts.items():
        ndbno = get_ndbno(nutrition_alias)
        print(nutrition_alias, ndbno, weight)
        fn_details = FoodNutritionDetails(fn_id=foodnutrition.id, ndbno=ndbno,
                weight=weight)
        session.add(fn_details)
    session.commit()

