import itertools
import sqlalchemy                                                                                                                                                
from sqlalchemy.orm import sessionmaker                                                                                                                          
from sqlalchemy.exc import DBAPIError   
from sqlalchemy.orm import joinedload
from database import Price, LocalNutrition, LocalNutritionaliase, Shop

from connectSettings import connectString

engine = sqlalchemy.create_engine(connectString)

Session = sessionmaker(bind=engine)

session = Session() 

prices=session.query(Price) \
        .join(LocalNutrition) \
        .order_by(LocalNutrition.desc) \
        .order_by(Price.price)
def grouper(item):
    return item.ndbno

def price_per_kg(price, it):
    if it.nutrition.package_weight is not None:
        return price/it.nutrition.package_weight*1000
    else:
        return 0

def price_per_kcal(price, it):
    if it.nutrition.kcal is not None:
        return price/it.nutrition.kcal*100
    else:
        return 0

for (item, items) in itertools.groupby(prices, lambda x: x.nutrition.desc):
        #x.nutrition.package_weight):
    print (item)
    for it in items:
        if it.currency == "EUR":
            price = it.price
        else:
            price = it.price*0.14

        print ("  {:2.3f} {} {} {} T:{} {:2.3f} per kg {:2.3f} per kcal".format(price, it.currency, it.last_updated,
            it.shop.name, it.temporary, price_per_kg(price, it), price_per_kcal(price, it)))
        if it.shop_id == 4 and it.currency == "EUR": #Spar
            price = price*0.75
            print ("  {:2.3f} {} {} {} T:{} 25% {:2.3f} per kg {:2.3f} per kcal".format(price, it.currency, it.last_updated,
                it.shop.name, it.temporary, price_per_kg(price, it), price_per_kcal(price, it)))

        if it.lowered_price is not None:
            price = it.lowered_price
            print ("  {:2.3f} {} {}-{} {} T:{} LOW {:2.3f} per kg {:2.3f} per kcal".format(price, it.currency, it.last_updated,
                it.lowered_untill,
                it.shop.name, it.temporary, price_per_kg(price, it),
                price_per_kcal(price, it)))
