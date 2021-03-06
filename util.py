import itertools
import re
import math
from enum import Enum

import dateutil.relativedelta
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import func
from tabulate import tabulate
from database import (
        Item,
        LocalNutrition,
        LocalNutritionaliase,
        FoodNutrition,
        FoodNutritionDetails,
        TagItem,
        Tag,
        UsdaWeight
        )
from gourmet_db import Nutrition

from PyQt5.QtCore import QUrl

class TimeSpan(Enum):
    WEEKLY = 0
    MONTHLY = 1
    DAYS7 = 2
    DAYS14 = 3
    DAYS30 = 4
    YEARLY = 5

class StatType(Enum):
    INGKEY = 0
    TAGS = 1
    FOOD_TAGS = 2


nondigit = re.compile("(?P<number>[\d\.]+)(?P<desc>\D+)")
equation = re.compile("\((?P<eq>(\d+(\.?\d+)?\+?)+)\)")
#Unless it is in bracket
split_on_plus = re.compile('\+\s*(?![^()]*\))')
def get_amounts(nutrition, session=None):
    """
    Gets amounts, weird_amounts and types from nutrition string

    Nutrition string is 1kroznik*POLENTA+1tbsp*CVIRKI+1*WATER
    or (20+20)*SUGAR
    Nutrition can appear multiple times (1*SUGAR+2*SUGAR = 3*SUGAR)

    amounts are just float numbers (1 in this example)
    or equations (5+20)
    weird_amounts are descriptive amounts which float value needs to be
    determined (1kroznik and 1tbsp) in this example

    if session is valid sqlalchemy session
    all weird_amounts are converted to amounts and weird amounts is empty dic


    types are food names (POLENTA, CVIRKI, WATER) in this example
    types are returned in lowercase

    >>> get_amounts("2*SUGAR+5*SUGAR")
    ({'SUGAR': 7.0}, {}, ['sugar'])

    >>> get_amounts("(5+5)*SUGAR")
    ({'SUGAR': 10.0}, {}, ['sugar'])

    Return:
    types are returned lowercase

    """
#Splits items on + except if + is inside ()
    items = split_on_plus.split(nutrition)
    amounts = {}
    weird_amounts = {}
    for item in items:
        #print ("ITEM:|",item,"|")
        amount, type = item.split("*")
        #print ("Amount:{} {}".format(amount, type))
        type = type.strip()
        match = equation.match(amount)
#Solves equation
        if match:
            gd = match.groupdict()
            amount = eval(gd["eq"])
        try:
            val = float(amount)
#Items can now appear multiple times
            amounts[type] = amounts.get(type,0) + val
        except ValueError as e:
            if type in weird_amounts:
                raise Exception("Repeated weird amount for same item:", type)
            weird_amounts[type] = amount
            #print ("No pure value", amount)
    types = list(set(x.lower() for x in itertools.chain(amounts.keys(),
        weird_amounts.keys())))
    if session:
        nutritions = get_nutrition_for(types, session)
        for item, value in weird_amounts.items():
            match = nondigit.match(value)
            #print (item, value, match.groups())
            grams = get_grams(nutritions[item], match.groupdict(), session)
            if grams:
                print (value, "->", grams*100, "g")
                amounts[item]=amounts.get(item, 0)+grams
        weird_amounts = {}

    return amounts, weird_amounts, types

"""
Sorts nutrition string based on item types (AKA food names)
And change them in uppercase
"""
def sort_nutrition_string(nutrition):
    amounts, weird_amounts, types = get_amounts(nutrition)
    types.sort()
    items = []
    for type in types:
        up_type = type.upper()
        if up_type in amounts:
            items.append("{}*{}".format(amounts[up_type], up_type))
        if up_type in weird_amounts:
            items.append("{}*{}".format(weird_amounts[up_type], up_type))
    ret_items = "+".join(items)
    return ret_items

"""
Gets nutrition for each item

items is list of lowerkey aliases for nutrition info.

each item is checked in nutritionalAliases gourmet and LocalNutritionaliases as
ingkey. If nutrition is found it is added to dict, key ingkey value nutrition

if all nutrition info was found dict is returned
"""
def get_nutrition_for(items, session):
    nutritions = {}
    local_query = session.query(LocalNutritionaliase) \
            .filter(LocalNutritionaliase.ingkey.in_(items))

    for n in local_query:
        #print (n.ingkey, n.nutrition)
        nutritions[n.ingkey]=n.nutrition
    if len(items) == len(nutritions):
        return nutritions

"""
Gets gram value for nutrition

nutrition is LocalNutrition, item is dict with desc unit and number value.

This calculates how many grams is 1tsp or 4slices for example.
First gramwt1 or gramwt2 in nutrition itself is checked. Then USDA weights
table for this item if unit is tsp or tbsp standard values are assumed

if nothing is found None is returned otherwise how many grams divided by 100
    this is
"""
def get_grams(nutrition, item, session):
    desc = item["desc"].rstrip('s')
    amount = float(item["number"])
    if nutrition.gramdsc1 is not None and \
        desc in nutrition.gramdsc1:
            return amount*nutrition.gramwt1/100
    if nutrition.gramdsc2 is not None and \
        desc in nutrition.gramdsc2:
            return amount*nutrition.gramwt2/100
    try:
        usda_amount = session.query(UsdaWeight) \
                .filter(UsdaWeight.ndbno==nutrition.ndbno) \
                .filter(UsdaWeight.unit.like("%"+desc+"%")) \
                .one()
        return amount*usda_amount.gramwt/100
    except Exception as a:
        pass
    print ("Guessing weight for ", nutrition.desc, desc)
    if desc.lower() == "tsp":
        return amount*0.05
    if desc.lower() == "tbsp":
        return amount*14.3/100



def calculate_nutrition(nutrition, session, added_sugar=False):
    if nutrition is None:
        return
    amounts, weird_amounts, types = get_amounts(nutrition, session)
    print ("Search for stuff")
    nutritions = get_nutrition_for(types, session)
    if nutritions is not None:
        #print (types, nutritions)
        prev = None
        print ("DOUTNG\n")
        for item, value in amounts.items():
            print ("{} ({})*{} L{}".format(item, value, nutritions[item],
                nutritions[item].lipid))
            current = value*nutritions[item]
            if prev is not None:
                prev = prev + current
            else:
                prev = current
        if added_sugar:
            if "SUGAR" in amounts:
                prev.added_sugar=amounts["SUGAR"]*100
            else:
                prev.added_sugar = 0
        print (prev, "Carb:",  prev.carb, "Belj:", prev.protein, "Masc:", prev.lipid)
        return prev

def get_nutrition(item, session):
    if item.calc_nutrition is None:
        try:
            fn = session.query(FoodNutrition) \
                    .filter(FoodNutrition.nutrition==item.nutrition) \
                    .one()
            item.calc_nutrition = fn.id
            session.merge(item)
            return fn
        except NoResultFound as e:
            calc_nutrition = calculate_nutrition(item.nutrition, session)
            if calc_nutrition is not None:
                nutrition_dict = calc_nutrition.__dict__
                del nutrition_dict["_sa_instance_state"]
                fn = FoodNutrition(**nutrition_dict)
                fn.nutrition = item.nutrition
                session.add(fn)
                session.flush()
                item.calc_nutrition = fn.id
                session.merge(item)

    else:
        return item.nutri_info
"""
    Adds baked items currently in FoodNutrition into nutrition

    It is assumed that weight in FoodNutrition specified weight of whole baked
    item
"""
def add_baked(food_id, ingkey, desc, session):
    foodn_names =set(map(lambda x: x.name, FoodNutrition.__table__.columns))
    n_names =set(map(lambda x: x.name, LocalNutrition.__table__.columns))
    diff = foodn_names.difference(n_names)
    food_n = session.query(FoodNutrition).get(food_id)

    if food_n.weight is None or food_n.weight == 0:
        print ("Error weight isn't set for:", food_n.desc, food_n.nutrition)
        return
    food_weight = food_n.weight
    ratio = 100/food_n.weight
    food_n_dict = food_n.__dict__
    for key in diff:
        del food_n_dict[key]
    del food_n_dict["_sa_instance_state"]
    ln = LocalNutrition(**food_n_dict)
#We have to calculate nutrition to 100g
    ln_100=ratio*ln
    ln_100.made_from=food_id
    ln_100.desc=desc
    ln_100.package_weight=food_weight
    ln_100.gramwt1=food_weight
    ln_100.gramdsc1="package"
    session.add(ln_100)
    session.flush()
    alias = LocalNutritionaliase(ingkey=ingkey, ndbno=ln_100.ndbno)
    session.add(alias)
    session.commit()

def copy_nutrition_to_local(ndbno, ingkey, session):
    """Copies nutrition from Recipes nutrition to local"""
    n_names =set(map(lambda x: x.name, Nutrition.__table__.columns))
    ln_names =set(map(lambda x: x.name, LocalNutrition.__table__.columns))
    diff = n_names.difference(ln_names)
    nutrition = session.query(Nutrition).get(ndbno)

    nutrition_dict = nutrition.__dict__
    for key in diff:
        del nutrition_dict[key]
    del nutrition_dict["_sa_instance_state"]
    ln = LocalNutrition(**nutrition_dict)
    session.add(ln)
    session.flush()
    alias = LocalNutritionaliase(ingkey=ingkey, ndbno=ln.ndbno)
    session.add(alias)
    session.commit()

"""
    Gets list of nutrition descriptions sorted by amount

    If there is nutrition baked from parts. Parts are used

    This is used to show ingredients in food

    Returns: list of descriptions or empty list
"""
def get_nutrition_list(nutrition, session, weights=None):
    amounts, weird_amounts, types = get_amounts(nutrition, session)
    print ("Search for stuff")
    nutritions = get_nutrition_for(types, session)
    partial_list = {}
#Finds nutrition which consists of other parts (Baked items)
    for item, value in nutritions.items():
        #print (item, value)
        if value.foodnutrition is not None:
            #print ("WEIGHT:", value.foodnutrition.weight)
            if item in amounts:
                amount = amounts[item]
            partial_list[item]=get_nutrition_list(value.foodnutrition.nutrition,
                    session, (value.foodnutrition.weight, amount))
    #Makes amount*item list joined with +
    def make_nutrition(nutri_list):
        return "+".join(map(lambda x:str(x[0])+"*"+x[1],nutri_list))
#Replaces each item with it's nutrition
    new_nutrition = nutrition
    for item_key, nutri_list in partial_list.items():
        part_nutri_list = make_nutrition(nutri_list)
        #print (item_key, part_nutri_list)
        new_nutrition = replace_nutrition(new_nutrition, item_key,
                part_nutri_list)
    if new_nutrition != nutrition:
        #print (new_nutrition)
        amounts, weird_amounts, types = get_amounts(new_nutrition, session)
        nutritions = get_nutrition_for(types, session)

    #Partial nutrition we need to recalculate weights
    if weights is not None:
        weights = (weights[0]/100, weights[1])

    if nutritions is not None:
        nutrition_list = []
        for item, value in amounts.items():
            if weights is not None:
                amount = amounts[item]/weights[0]*weights[1]
                #print ("{}/{}*{}={}".format(amounts[item],
                    #weights[0],weights[1], amount))
            else:
                amount = amounts[item]
            if weights is not None:
                nutrition_list.append((amount, item))
            else:
                nutrition_list.append((amount, nutritions[item].desc))

        if weights is not None:
            return nutrition_list
        #else:
            #print ("LIST:", nutri_list)
        #Sorts list according to amounts from larger to lower and returns just
        #the descriptions
        sorted_list = map(lambda x: x[1], sorted(nutrition_list, key=lambda item:
            item[0], reverse=True))
        return sorted_list
    else:
        return []


def replace_nutrition(nutrition, search, replace):
    """Replaces nutrition with expanded nutrition

    Args:
        nutrition(str): whole nutrition string
        search(str): nutrition item to search for (AKA DOM_BUCKWHEAT_BROWNIE)
        replace(str): Whole replaced valid nutrition string

    Returns:
        nutrition string where value and search item are replaced with replace
        values

    For example 1package*DOM_ENERGY_BAR gets replaced with replace string

    Simple example only one item in nutrition
    >>> replace_nutrition('0.33*DOM_BUCKWHEAT_BROWNIE', 'DOM_BUCKWHEAT_BROWNIE', '1tsp*REPLACED')
    '1tsp*REPLACED'

    One at the end
    >>> replace_nutrition('0.33*DOM_BUCKWHEAT_BROWNIE+1tsp*SUGAR', 'DOM_BUCKWHEAT_BROWNIE', '1tsp*REPLACED')
    '1tsp*REPLACED+1tsp*SUGAR'

    Two at end
    >>> replace_nutrition('0.33*DOM_BUCKWHEAT_BROWNIE+1tsp*SUGAR+2medium*EGG', 'DOM_BUCKWHEAT_BROWNIE', '1tsp*REPLACED')
    '1tsp*REPLACED+1tsp*SUGAR+2medium*EGG'

    One at start
    >>> replace_nutrition('1tsp*SUGAR+0.33*DOM_BUCKWHEAT_BROWNIE', 'DOM_BUCKWHEAT_BROWNIE', '1tsp*REPLACED')
    '1tsp*SUGAR+1tsp*REPLACED'

    Two at start
    >>> replace_nutrition('1tsp*SUGAR+1*MILK+0.33*DOM_BUCKWHEAT_BROWNIE', 'DOM_BUCKWHEAT_BROWNIE', '1tsp*REPLACED')
    '1tsp*SUGAR+1*MILK+1tsp*REPLACED'

    One at start and end
    >>> replace_nutrition('1tsp*SUGAR+0.33*DOM_BUCKWHEAT_BROWNIE+1*MILK', 'DOM_BUCKWHEAT_BROWNIE', '1tsp*REPLACED')
    '1tsp*SUGAR+1tsp*REPLACED+1*MILK'

    Two at start and end
    >>> replace_nutrition('1tsp*SUGAR+2*WATER+0.33*DOM_BUCKWHEAT_BROWNIE+1*MILK+3*AIR', 'DOM_BUCKWHEAT_BROWNIE', '1tsp*REPLACED')
    '1tsp*SUGAR+2*WATER+1tsp*REPLACED+1*MILK+3*AIR'

    >>> replace_nutrition('1tsp*SUGAR+2*WATER+0.33*DOM_ČŠŽBUCKWHEAT_BROWNIE+1*MILK+3*AIR',  'DOM_ČŠŽBUCKWHEAT_BROWNIE', '1tsp*REPLŽACED')
    '1tsp*SUGAR+2*WATER+1tsp*REPLŽACED+1*MILK+3*AIR'

    Returns:
    Replaced string
    """
#Finds start of Item name
    start = nutrition.find(search)
    if start == 0:
        start_whole = 0
    else:
#Finds start of amount
        start_whole = nutrition.rfind("+",0,start)+1
    end = start+len(search)
    search_whole = nutrition[start_whole:end]
    return nutrition.replace(search_whole, replace)

def show_before(eat_id, session, hours=24):
    item=session.query(Item).get(eat_id)
    print (item)
    time = item.time
    if hours < 0:
        begin = time
        time = time+dateutil.relativedelta.relativedelta(hours=-1*hours)
    else:
        begin=time-dateutil.relativedelta.relativedelta(hours=hours)
    print (begin,"-",time)
    #TODO: Shorter time display, show time from start on each item
    items = session.query(Item.id, Item.time, Item.type, Item.description) \
            .filter(Item.time.between(begin,time)) \
            .filter(Item.type != "PIPI") \
            .order_by(Item.time)
    return tabulate(items, headers=["id", "time", "type", "description"])

def init_nutrition_view(self):
    self.skip = set(["ndbno", "foodgroup", "gramwt1",
        "gramdsc1", "gramwt2", "gramdsc2", "refusepct",
        "package_weight", "num_of_slices", "source",
        "made_from", "_sa_instance_state"])
    self.dailyValues = {
            "calcium" : 1300,
            "iron": 18,
            "potassium" : 4700,
            }
    self.template = open("./nutrition/demo.html", "r").read()

def show_nutrition_view(self, nutrition, session):
    calculation = calculate_nutrition(nutrition, session, True)
    txt =("{} Calories {} Carb {} Protein {} fat {} fiber" \
            " {} sugar {} water".format(calculation.kcal,
                calculation.carb, calculation.protein,
                calculation.lipid, calculation.fiber,
                calculation.sugar, calculation.water))

    caloric_ratio = calculation.caloric_ratio
    txt = ("Fullness Factor:{}\n Calories from "  \
    "CARB:{} FAT:{} PROT:{}\n"  \
    "percentage CARB:FAT:PROT {}:{}:{}\nMagnesium:{}".format(
            calculation.fullness_factor,caloric_ratio["cal_from_carb"],
            caloric_ratio["cal_from_fat"], caloric_ratio["cal_from_prot"],
            caloric_ratio["perc_carb"], caloric_ratio["perc_fat"],
            caloric_ratio["perc_prot"], calculation.magnesium))

    self.lbl_nutrition.setText(txt)
    nutri_list = ",".join(get_nutrition_list(nutrition, self.session))
    print (nutri_list)
    out = self.template
    data_vars = vars(calculation)
#We need to sort keys so added_sugars are replaced before sugars
    keys = sorted(data_vars.keys())
#TODO: Add vitamins etc. (They need to be recalculated to % of DV)
    for key in keys:
        value = data_vars[key]
        if key not in self.skip:
            #print (key, value)
            if key in self.dailyValues:
                #print ("VALUE:", key,  value)
                calc_value = value/self.dailyValues[key]*100
            else:
                calc_value = value
            out = out.replace(key.upper(), str(calc_value))
    out = out.replace("LIST", nutri_list)
    #vn = open("./nutrition/demo1.html", "w")
    #vn.write(out)
    #vn.close()
    self.webView.setHtml(out,
            QUrl("file:///home/mabu/programiranje/eatToday/nutrition/demo.html"))

def nutrition_equation_solver(nutrition_eq, session):
    """
    Nutrition equation solver

    Equation looks like x*CHICKPEA_PASTA+0.05*PARMESAN=protein:20

    Left part is basically normal nutrition item except, weird amounts aren't
    supported for now and one item has lowecase letter instead of amount.

    Right side has nutrient:value. Nutrient is any nutrient in nutrition (lipid,
    kcal, protein, sugar etc.)
    Value is how many of this nutrient we want.

    solver will calculate how much of item with x we need to have wanted
    amount of nutrient
    """
    left, right = nutrition_eq.split("=")
    wanted_nutrient, amount = right.split(":")
    amount = float(amount)
    amounts, weird_amounts, types = get_amounts(left)
    nutritions = get_nutrition_for(types, session)
    wanted_item = next(iter(weird_amounts.keys()))
    have_nutritions = nutritions[wanted_item]
    if wanted_nutrient not in have_nutritions.__dict__:
        raise Exception ("Want item can be one of:", have_nutritions.__dict__.keys())

#How many of wanted nutrient has 100g of wanted item
    have_nutrient = have_nutritions.__dict__[wanted_nutrient]
    variable = next(iter(weird_amounts.values()))
#We need to calculate how many of wanted item is in the rest of nutrition
    if len(types) > 1:
        new_nutrition = left.replace(variable, "0", 1)
        #print (left, new_nutrition)
        c = calculate_nutrition(new_nutrition, session)
        amount = amount-c.__dict__[wanted_nutrient]
    STR="{}g = {} {}"
    print (STR.format(100, have_nutrient, wanted_nutrient))
    print (STR.format(variable, amount, wanted_nutrient))
    val = math.ceil(amount*100/have_nutrient)
    print ("{} = {}g {}".format(variable, val, wanted_item))

def rename(from_n, to_n, session):
    """Rename nutrition in eats from <from_n> to <to_n>

        Nothing is commited
    """
    nutritions = session.query(Item) \
            .filter(Item.nutrition.contains(from_n))
    for nutri in nutritions:
        replaced = nutri.nutrition.replace(from_n,
                to_n)
        print (nutri.nutrition, replaced, nutri.description)
        nutri.nutrition = sort_nutrition_string(replaced)
        nutri.calc_nutrition = None
        print (nutri)

def show_tags(session, foodgroup=None):
    """Shows nutrition tags

    Can filter them by foodgroup"""
    nutrition_tags = session.query(LocalNutritionaliase.ingkey,
		 LocalNutrition.desc, func.group_concat(Tag.name)) \
        .filter(TagItem.ndbno==LocalNutrition.ndbno) \
	.filter(Tag.id==TagItem.tag_id) \
        .filter(LocalNutritionaliase.ndbno==LocalNutrition.ndbno) 
    if foodgroup is not None:
        nutrition_tags = nutrition_tags \
            .filter(LocalNutrition.foodgroup==foodgroup) 
    nutrition_tags = nutrition_tags \
	.group_by(LocalNutrition.ndbno) \
        .order_by(LocalNutritionaliase.ingkey)
    for ingkey, desc, tags in nutrition_tags:
        print(ingkey, " || ", desc)
        print("   ", tags)

def add_tag(foodgroup, tag, session):
    """Add new tag_items based on foodgroup

    tag can be name or tag_id (number)
    """
    if type(tag)==int:
        tag_id = tag
    else:
        tag_id = session.query(Tag.id) \
                .filter(Tag.name==tag) \
                .one()[0]
    ndbnos_d = {}
#NDBNO ids of all nutritions in specific foodgroup 
    ndbnos = session.query(LocalNutrition.ndbno, LocalNutrition.desc) \
            .filter(LocalNutrition.foodgroup==foodgroup)
    for ndbno, desc in ndbnos:
        ndbnos_d[ndbno]=desc
    ndbnos_l = ndbnos_d.keys()
#NDBNO ids of specific foodgroup that already had tag
    already_added_ndbnos = session.query(TagItem.ndbno) \
            .filter(TagItem.tag_id==tag_id) \
            .filter(TagItem.ndbno.in_(ndbnos_l))
    already_added_ndbnos_s = set((x[0] for x in already_added_ndbnos))
    for ndbno, desc in ndbnos_d.items():
        added = ndbno in already_added_ndbnos_s
        print (ndbno, desc, added)
    all_ndbnos_s = set(ndbnos_l)
    to_add_ndbnos = all_ndbnos_s.difference(already_added_ndbnos_s)
    for ndbno in to_add_ndbnos:
        tag_item = TagItem(ndbno=ndbno, tag_id=tag_id)
        session.add(tag_item)

def get_ingkey_ndbno_map(session):
    """Gets map where key is ingkey and value is ndbno"""
    alias_ndbno = {}

    for alias, ndbno in session.query(LocalNutritionaliase.ingkey,
            LocalNutritionaliase.ndbno):
        alias_ndbno[alias]=ndbno
    return alias_ndbno

def add_nutrition_details(session):
    alias_ndbno = get_ingkey_ndbno_map(session)

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


if __name__ == "__main__":
    import doctest
    doctest.testmod()
