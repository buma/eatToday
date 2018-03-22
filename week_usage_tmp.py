import datetime

import dateutil.relativedelta
import sqlalchemy
import itertools
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker, joinedload, subqueryload

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
        Price
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
            .filter(~Tag.name.startswith("Sledi")) \
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
#print (tabulate(items_fd, headers=["Food tags", "tags"]))
def make_food_tags(ingkeys, tag_names, descs):
    food_tags = set()
    one_tag = [
            "Sadje",
            "Čokolada",
            "Keksi",
            "Pecivo",
            "Stročnice",
            "Sladoled",
            "Slani prigrizek"
            ]
    desc_search = [
            ("rižot", "rižota"),
            ("hash", "hash"),
            ("palačink", "palačinke"),
            ("šmorn", "šmorn"),
            ("sarma", "sarma"),
            ("žganci", "žganci"),
            ("grostl", "grostl"),
            ("ričet", "ričet"),
            ("polpeti", "polpeti"),
            ("špecli", "špecli"),
            ("quesadillas", ["quesadillas", "tortilla_stuff"]),
            ("tortilje", "tortilla_stuff"),
            ("juha", "juha"),
            ("golaž", "golaž"),
            ("obara", "obara")
            ]

    in_desc= lambda q: all([q in x.lower() for x in descs])
    descs_starts= lambda q: all([x.lower().startswith(q) for x in descs])

    if "Kruh" in tag_names:
        if "HRENOVKA" in ingkeys or "TEL_HRENOVKA" in ingkeys \
            or "Meso" in tag_names:
            food_tags.add("kruh z")
        else:
            food_tags.add("kruh")
            if "Marmelada" in tag_names:
                food_tags.add("sladki namaz")
            elif "Namaz" in tag_names:
                food_tags.add("slan namaz")
            #tahini, klobase, sir, slani namaz
    if in_desc("palačink") and "Krompir" in tag_names:
        return set(["palačinke", "krompir", "slane_palačinke"])
    if "RED_LENTIL" in ingkeys:
        if in_desc("juha"):
            return set(["juha"])
        elif descs_starts("čili"):
            return set(["čili"])
        elif not any(True for key, _ in desc_search if in_desc(key)):
            return set(["rdeča_leča"])

    for search, tag in desc_search:
        if in_desc(search):
            if search == "šmorn" and in_desc("palačink"):
                return set()
            elif search == "palačink" and in_desc("šmorn"):
                return set()
            if isinstance(tag, list):
                return set(tag)
            else:
                return set([tag])
    for tag_name in one_tag:
        if tag_name in tag_names and len(tag_names) == 1:
            return set([tag_name.lower()])
    if "MILLET" in ingkeys or "MILLET_COOKED" in ingkeys:
        #Doesn't set prosena_kaša when it is used as side dish
        if len(set(["Meso", "Stročnice"]) & tag_names) == 0 and \
            "OATMEAL" not in ingkeys:
                #TODO: add support for oatmeal
                return set(["prosena_kaša"])
    if "SPINACH" in ingkeys:
        return set(["špinača"])
    if "Testenine" in tag_names:
        #Izlocit treba jusne testenine pa tiste v fizolovih stvareh
        if not (in_desc("juha") or in_desc("enolončnica") or in_desc("pašta")):
            return set(["testenine"])
    elif "Mleko" in tag_names and "Keksi" in tag_names:
        return set(["mleko s keksi"])
    elif set(["Mleko", "Kosmiči"]) == tag_names:
        return set(["mleko s kosmiči"])
    elif "Zelenjava" in tag_names and "Meso" in tag_names:
        if not in_desc("grostl"):
            return set(["meso z zelenjavo"])
    elif "Zelenjava" in tag_names and "Ribe" in tag_names:
        return set(["ribe z zelenjavo"])
    return food_tags

def add_food_tags(session, items=None):
    if items is None:
        items = session.query(FoodNutritionDetails) \
                .options(joinedload(FoodNutritionDetails.nutrition)) \
                .options(joinedload(FoodNutritionDetails.foodnutrition)) \
                .order_by(FoodNutritionDetails.fn_id.desc()) 
                #.limit(32)
    tag_hier = add_food_hier(session)

    def hierahize_tags(tags):
        tags_ret = set()
        for tag in tags:
            tags_ret.add(tag.name)
            parents = tag_hier.get(tag.id, [])
            tags_ret.update(parents)
        return tags_ret
    def get_food_tags(session):
        items = session.query(FoodTag)
        name_tag = {}
        for item in items:
            name_tag[item.name] = item
        return name_tag
    food_tags = get_food_tags(session)
    to_add = set()
    rets = []
    for fn_id, nutris in itertools.groupby(items, key=lambda x:x.fn_id):
        foodnutrition = None
        current_food_tags = []
        food_tags_set = set()
        eat_items = []
        eat_id = None
        ingkeys = []
        tags = []
        for nutri in nutris:
            if foodnutrition is None:
                foodnutrition = nutri.foodnutrition
                current_food_tags = foodnutrition.food_tags
                food_tags_set = set((x.tag.name for x in current_food_tags))
                if foodnutrition.items: 
                    eat_id = foodnutrition.items[0].id
                eat_items = [x.description for x in foodnutrition.items]
                print (fn_id,)
            ingkeys.append(nutri.nutrition.alias.ingkey)
            tags += filter(lambda tag:not tag.cosmetic, nutri.nutrition.tags) # map(lambda tag:tag.name, nutri.nutrition.tags)
        if eat_id is None:
            continue
        tags = set(tags)
        print ("TAGS:", tags)
        tags = hierahize_tags(tags)
        print ("NUTRITION:", foodnutrition.nutrition)
        print ("  DESC:", eat_items)
        print ("  ID:", eat_id)
        print ("  FOOD_TAGS:", food_tags_set)
        print ("  INGKEY:", ingkeys)
        print ("  TAGS:", tags)
        new_food_tags = make_food_tags(ingkeys, tags, eat_items)
        #to_add.update(new_food_tags-food_tags_set)
        to_add_tags = new_food_tags-food_tags_set
        to_add.update(to_add_tags)
        print ("  NFOOD_TAG:", new_food_tags)
        print ("  NEW TAGS:", to_add_tags)
        if to_add_tags:
            rets.append((foodnutrition.id, foodnutrition.nutrition, tags, ingkeys,
                    eat_items, food_tags_set, new_food_tags))
        for to_add_tag in to_add_tags:
            if to_add_tag in food_tags:
                tag = food_tags[to_add_tag]
            else:
                tag = FoodTag(name=to_add_tag)
                food_tags[to_add_tag] = tag
            food_tag_item = FoodTagItem(item_id=eat_id)
            #food_tag_item.checked = True
            food_tag_item.tag = tag
            foodnutrition.food_tags.append(food_tag_item)
        #session.flush()
            #food_tag_item.foodnutrition=foodnutrition

    #session.commit()
    print ("TO ADD TAGS", to_add)
    return rets


def add_food_hier(session):
    parents = {}
    parent_child = {}
    for tag_h in session.query(TagHierarchy):
        if tag_h.parent_tag.cosmetic:
            continue
        print (tag_h.parent_tag, " -> ", tag_h.tag)
        cur_parents = parents.get(tag_h.tag,
                []) 
        cur_parents.append(tag_h.parent_tag)
        parents[tag_h.tag] = cur_parents 
        if tag_h.tag in parent_child:
            parents[parent_child[tag_h.tag]].append(tag_h.parent_tag)
        parent_child[tag_h.parent_tag] = tag_h.tag
        
    clean_parents = {}
    for pid, tag in parents.items():
        print (pid, tag)
        clean_parents[pid.id] = [x.name for x in tag]
    #print (clean_parents)
    return clean_parents

def get_ingkeys_without_foodtags(session):
    existing_food_tags = session.query(FoodTagItem.fn_id.distinct())
    items = session.query(func.count(FoodNutritionDetails.ndbno).label("app"),
            FoodNutritionDetails.ndbno, LocalNutritionaliase.ingkey) \
            .join(LocalNutritionaliase,
                    LocalNutritionaliase.ndbno==FoodNutritionDetails.ndbno) \
            .filter(~FoodNutritionDetails.fn_id.in_(existing_food_tags)) \
            .group_by(FoodNutritionDetails.ndbno) \
            .order_by(sqlalchemy.desc("app"))
    print (items)

    print (tabulate(items))

get_ingkeys_without_foodtags(session)

def get_ingkey_without_foodtags(session, ndbno, show_desc=False):
    existing_food_tags = session.query(FoodTagItem.fn_id.distinct())
    columns = [FoodNutrition.id, FoodNutrition.nutrition]
    if show_desc:
        columns.append(Item.description)

    items = session.query(*columns) \
            .join(FoodNutritionDetails) \
            .filter(~FoodNutritionDetails.fn_id.in_(existing_food_tags)) \
            .filter(FoodNutritionDetails.ndbno==ndbno) \
            .order_by(FoodNutrition.id)
    if show_desc:
        items = items \
            .join(FoodNutrition.items) 
    print (items)

    print (tabulate(items))

def get_price_for_food(session, fn_id, price_get="MIN"):
    if price_get == "MIN":
        sql_func = lambda x: func.min(x)
    elif price_get == "MAX":
        sql_func = lambda x: func.min(x)
    elif price_get == "MEAN" or price_get == "AVG":
        sql_func = lambda x: func.avg(x)
    #Gets all nutritions with weight and min/max/avg price for each nutrition
    #or None
    #For this foodnutrition
    fnds = session.query(FoodNutritionDetails.ndbno,
	 FoodNutritionDetails.weight*100,sql_func(Price.price)) \
	.outerjoin(Price, Price.ndbno==FoodNutritionDetails.ndbno) \
        .filter(FoodNutritionDetails.fn_id==fn_id) \
        .group_by(FoodNutritionDetails.ndbno)
    missing_price = 0
    missing_package_weight = 0
    all = 0
    all_price = 0
    for ndbno, weight, price in fnds:
        all+=1
        price_ok = False
        package_weight_ok = False
        lnt = session.query(LocalNutrition.package_weight, LocalNutrition.desc) \
                .filter(LocalNutrition.ndbno==ndbno) \
                .one()
        if price is None:
            missing_price+=1
            print ("MISSING PRICE:{}".format(lnt[1]))
        else:
            price_ok=True

        if lnt[0] is None:
            missing_package_weight+=1
            print ("MISSING PACKAGE WEIGHT:{}".format(lnt[1]))
        else:
            package_weight_ok = True
            package_weight = lnt[0]

        if package_weight_ok and price_ok:
            part_price = weight/package_weight*price
            print ("{} {}g package:{}g price:{}€ PART PRICE:{}".format(
                lnt[1],
                weight,
                package_weight, price, part_price))
            all_price+=part_price
    print ("Missing price:{} missing_p_weight:{}  price:{}".format(
        missing_price, missing_package_weight, all_price))




#get_ingkey_without_foodtags(session, 12155)


#kasa=session.query(Tag).filter(Tag.name=="Kaša").one()
#kasa_ndbno=[x.ndbno for x in kasa.nutritions]
#q=session.query(Item.id, Item.description,).filter(FoodNutritionDetails.ndbno.in_(kasa_ndbno)).filter(Item.calc_nutrition==FoodNutritionDetails.fn_id).group_by(Item.id)
#for a in q.all():
    #print(a)


#add_food_hier(session)
add_food_tags(session)

#a=5/0
