import itertools
from datetime import datetime
import sqlalchemy                                                                                                                                                

from sqlalchemy import or_
from sqlalchemy.orm import sessionmaker                                                                                                                          
from sqlalchemy.exc import DBAPIError   
from sqlalchemy.orm import joinedload
from database import (
        Price, LocalNutrition, LocalNutritionaliase, Shop,
        Tag, TagItem)

from connectSettings import connectString

engine = sqlalchemy.create_engine(connectString)

Session = sessionmaker(bind=engine)

session = Session() 

ndbnos_tus = session.query(Price.ndbno.distinct()) \
        .filter(Price.shop_id==0)

#Crni kruh 3 beli 2
prices=session.query(Price) \
        .join(LocalNutrition) \
        .join(TagItem) \
        .filter(or_(TagItem.tag_id==2, TagItem.tag_id==3) ) \
        .order_by(LocalNutrition.desc) \
        #.order_by(Price.price)
        #.filter(Price.ndbno.in_(ndbnos_tus)) \
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

now = datetime.now().date()

for (item, items) in itertools.groupby(prices, lambda x: x.nutrition.desc):
        #x.nutrition.package_weight):
    sort_items = []
    tus_inside = False
    for it in items:
        if it.currency == "EUR":
            price = it.price
        else:
            price = it.price*0.14
        if it.shop_id == 0:
            tus_inside = True

        sort_items.append((price, "  {:2.3f} {} {} {} T:{} {:2.3f} per kg {:2.3f} per kcal".format(price, it.currency, it.last_updated,
            it.shop.name, it.temporary, price_per_kg(price, it),
            price_per_kcal(price, it))))
        if (it.shop_id == 4 or it.shop_id == 0) and it.currency == "EUR": #Spar
            price = price*0.75
            sort_items.append((price, ("  {:2.3f} {} {} {} T:{} 25% {:2.3f} per kg {:2.3f} per kcal".format(price, it.currency, it.last_updated,
                it.shop.name, it.temporary, price_per_kg(price, it),
                price_per_kcal(price, it)))))

        if it.lowered_price is not None:
#Skip actions which are not actual anymore
            if it.lowered_untill is not None and it.lowered_untill < now:
                continue
            price = it.lowered_price
            sort_items.append((price, ("  {:2.3f} {} {}-{} {} T:{} LOW {:2.3f} per kg {:2.3f} per kcal".format(price, it.currency, it.last_updated,
                it.lowered_untill,
                it.shop.name, it.temporary, price_per_kg(price, it),
                price_per_kcal(price, it)))))
        #13% popust v tusu
        #if it.shop_id == 0:
            #price = it.price*(1.00-0.13)
            #sort_items.append((price, ("  {:2.3f} {} {} {} T:{} 13% {:2.3f} per kg {:2.3f} per kcal".format(price, it.currency, it.last_updated,
                #it.shop.name, it.temporary, price_per_kg(price, it),
                #price_per_kcal(price, it)))))
    #if tus_inside:
    print (item)
    for price, sorted_item in sorted(sort_items, key=lambda x: x[0]):
        print (sorted_item)
