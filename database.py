# coding: utf-8
import datetime

from sqlalchemy import (
        Column, DateTime, Integer, Text, CHAR, Float,
ForeignKey, Boolean, Date, Table, text, Index )
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

import colorama


Base = declarative_base()
metadata = Base.metadata

class CalorieCalc(object):

    @property
    def fullness_factor(self):
        """Fullness factor

        From 0-5 higher the factor more satient is the food

        Calculated based on formula here:
            http://nutritiondata.self.com/topics/fullness-factor
        """
#Calories must be min 30
        CAL = max(30, self.kcal)
#PR proteins max 30
        PR = min(30, self.protein)
#DF fiber 12 max
        fiber = 0 if self.fiber is None else self.fiber
        DF = min(12, fiber)
#TF total fat 50 max
        TF = min(50, self.lipid)
        FF = max(0.5, min(5.0, 41.7/CAL**0.7 
            + 0.05*PR + 6.17E-4*DF**3 -
            7.25E-6*TF**3 + 0.617))
        return round(FF,1)

    @property
    def caloric_ratio(self):
        calories_from_fat = self.lipid*9
        calories_from_carb = self.carb*4
        calories_from_prot = self.protein*4
        return {"cal_from_fat":round(calories_from_fat, 2),
                "cal_from_carb":round(calories_from_carb, 2),
                "cal_from_prot":round(calories_from_prot, 2),
                "perc_fat":round(calories_from_fat/self.kcal*100),
                "perc_carb":round(calories_from_carb/self.kcal*100),
                "perc_prot":round(calories_from_prot/self.kcal*100)
                }



class Item(Base):
    __tablename__ = 'eat'

    id = Column(Integer, primary_key=True)
    time = Column(DateTime)
    type = Column(CHAR(length=8))
    description = Column(Text, nullable=True)
    nutrition = Column(Text(length=100), nullable=True)
    calc_nutrition = Column(ForeignKey('foodnutrition.id'))
    preparing_time = Column(Integer)
    cooking_time = Column(Integer)
    eating_time = Column(Integer)
    prep_supervision = Column(Boolean, server_default="1")
    recipe_in_gourmet = Column(Boolean, nullable=False, server_default=text("0"))
    buku_recipe_id = Column(Integer)


    def __init__(self, type, description, nutrition, time=None,
            recipe_in_gourmet=None, prep_supervision=True, buku_recipe_id=None):
        self.type = type
        self.description = description
        self.nutrition = nutrition
        self.recipe_in_gourmet = recipe_in_gourmet
        self.prep_supervision = prep_supervision
        self.buku_recipe_id = buku_recipe_id
        if time is None:
            self.time = datetime.datetime.now()
        else:
            self.time = time

    def __repr__(self):
        if self.id is None:
            id = -1
        else:
            id = self.id
        return "<Item('%d', '%s', Desc:'%s' Type:'%s', Nutrition:'%s')>" % (id, self.time,
                self.description, self.type, self.nutrition)

    def __format__(self, format):
        ITEM="{time:%H:%M} {type:^8} {description:50.50} {nutri_info}"
        nutri_info = self.nutri_info if self.nutri_info is not None else ""
        desc = self.description if self.description is not None else ""
        return ITEM.format(time=self.time, type=self.type,
                description=desc,
                nutri_info=nutri_info)

class FoodNutrition(Base, CalorieCalc):
    __tablename__ = 'foodnutrition'

    id = Column(Integer, primary_key=True)
    nutrition = Column(Text(length=100), unique=True)
    desc = Column(Text(400))
    water = Column(Float)
    kcal = Column(Float)
    protein = Column(Float)
    lipid = Column(Float)
    ash = Column(Float)
    carb = Column(Float)
    fiber = Column(Float)
    sugar = Column(Float)
    calcium = Column(Float)
    iron = Column(Float)
    magnesium = Column(Float)
    phosphorus = Column(Float)
    potassium = Column(Float)
    sodium = Column(Float)
    zinc = Column(Float)
    copper = Column(Float)
    manganese = Column(Float)
    selenium = Column(Float)
    vitaminc = Column(Float)
    thiamin = Column(Float)
    riboflavin = Column(Float)
    niacin = Column(Float)
    pantoacid = Column(Float)
    vitaminb6 = Column(Float)
    folatetotal = Column(Float)
    folateacid = Column(Float)
    foodfolate = Column(Float)
    folatedfe = Column(Float)
    choline = Column(Float)
    vitb12 = Column(Float)
    vitaiu = Column(Float)
    vitarae = Column(Float)
    retinol = Column(Float)
    alphac = Column(Float)
    betac = Column(Float)
    betacrypt = Column(Float)
    lypocene = Column(Float)
    lutzea = Column(Float)
    vite = Column(Float)
    vitk = Column(Float)
    fasat = Column(Float)
    famono = Column(Float)
    fapoly = Column(Float)
    cholestrl = Column(Float)
    weight = Column(Float)
    items = relationship("Item", backref="nutri_info")


    def __repr__(self):
        return "<kcal {:3.2f} carb: {:.2f} belj:{:.2f} masc:{:.2f}>".format(self.kcal,
                self.carb, self.protein, self.lipid)

    def __format__(self, format):
        if format == "diff":
            kcal = "{:7.2f}".format(self.kcal)
            protein = "{:7.2f}".format(self.protein)
            water = "{:7.2f}".format(0.0 if self.water is None else self.water)

            if self.kcal > 0:
                kcal = colorama.Fore.GREEN + kcal + colorama.Style.RESET_ALL
            else:
                kcal = colorama.Fore.RED + kcal + colorama.Style.RESET_ALL
            if self.protein > 0:
                protein = colorama.Fore.GREEN + protein + colorama.Style.RESET_ALL
            else:
                protein = colorama.Fore.RED + protein + colorama.Style.RESET_ALL
            if self.water > 0:
                water = colorama.Fore.GREEN + water + colorama.Style.RESET_ALL
            else:
                water = colorama.Fore.RED + water + colorama.Style.RESET_ALL
            return "{} {:6.2f} {} {:6.2f} {:6.2f} {:6.2f} {}".format(kcal,
                    self.carb, protein, self.lipid, self.fiber, self.sugar,
                    water)

        else:
            return "{:7.2f} {:7.2f} {:6.2f} {:6.2f} {:6.2f} {:6.2f} {:7.2f}".format(self.kcal,
                    self.carb, self.protein, self.lipid, self.fiber, self.sugar,
                    0.0 if self.water is None else self.water)

    #Sum items together
    def __add__(self, other):
        together = {}
        skip = set(["items", "id", "desc", "nutrition", "_sa_instance_state"])
        self_vars = vars(self)
        other_vars = vars(other)
        for key, value in self_vars.items():
            if key not in skip:
                self_value = 0 if self_vars[key] is None else self_vars[key]
                other_value = 0 if other_vars[key] is None else other_vars[key]
                together[key]=self_value+other_value
        return FoodNutrition(**together)

    def __radd__(self, other):
        #Add support for sum
        if other == 0:
            return self
        else:
            raise  NotImplementedError()

class FoodNutritionDetails(Base):
    __tablename__ = 'foodnutrition_details'
    fn_id = Column(ForeignKey('foodnutrition.id'), primary_key=True,
            nullable=False)
    ndbno = Column(ForeignKey('nutrition.ndbno'), primary_key=True,
            nullable=False)
    weight = Column(Float, nullable=False)
    foodnutrition = relationship("FoodNutrition")
    nutrition = relationship("LocalNutrition")
    #items = relationship("Item", backref="nutri_info")

class FoodNutritionTags(Base):
    __tablename__ = 'foodnutrition_tags'
    fn_id = Column(ForeignKey('foodnutrition.id'), primary_key=True,
            nullable=False)
    foodnutrition = relationship("FoodNutrition")
    tags = Column(Text(200))




class LocalNutrition(Base, CalorieCalc):
    __tablename__ = 'nutrition'

    ndbno = Column(Integer, primary_key=True)
    desc = Column(Text(100))
    water = Column(Float)
    kcal = Column(Float)
    protein = Column(Float)
    lipid = Column(Float)
    ash = Column(Float)
    carb = Column(Float)
    sugar = Column(Float)
    fiber = Column(Float)
    calcium = Column(Float)
    iron = Column(Float)
    magnesium = Column(Float)
    phosphorus = Column(Float)
    potassium = Column(Float)
    sodium = Column(Float)
    zinc = Column(Float)
    copper = Column(Float)
    manganese = Column(Float)
    selenium = Column(Float)
    vitaminc = Column(Float)
    thiamin = Column(Float)
    riboflavin = Column(Float)
    niacin = Column(Float)
    pantoacid = Column(Float)
    vitaminb6 = Column(Float)
    folatetotal = Column(Float)
    folateacid = Column(Float)
    foodfolate = Column(Float)
    folatedfe = Column(Float)
    choline = Column(Float)
    vitb12 = Column(Float)
    vitaiu = Column(Float)
    vitarae = Column(Float)
    retinol = Column(Float)
    alphac = Column(Float)
    betac = Column(Float)
    betacrypt = Column(Float)
    lypocene = Column(Float)
    lutzea = Column(Float)
    vite = Column(Float)
    vitk = Column(Float)
    fasat = Column(Float)
    famono = Column(Float)
    fapoly = Column(Float)
    cholestrl = Column(Float)
    gramwt1 = Column(Float)
    gramdsc1 = Column(Text(100))
    gramwt2 = Column(Float)
    gramdsc2 = Column(Text(100))
    refusepct = Column(Float)
    foodgroup = Column(Text)
#From where nutri data comes USDA/label
    source = Column(Text(10))
#Weight of bought package
    package_weight = Column(Integer)
#For bread
    num_of_slices = Column(Integer)
    made_from = Column(ForeignKey('foodnutrition.id'))
    foodnutrition = relationship("FoodNutrition")


    def __add__(self, other):
        together = {}
        skip = set(["ndbno", "desc", "foodgroup", "gramwt1",
            "gramdsc1", "gramwt2", "gramdsc2", "refusepct",
            "package_weight", "num_of_slices", "source",
            "made_from", "_sa_instance_state"])
        self_vars = vars(self)
        other_vars = vars(other)
        for key, value in self_vars.items():
            if key not in skip:
                self_value = 0 if self_vars[key] is None else self_vars[key]
                other_value = 0 if key not in other_vars or other_vars[key] is None else other_vars[key]
                together[key]=self_value+other_value
        together["desc"] = self.desc + " | " + other.desc
#if we are adding LocalNutrition+Nutrition this adds Nutrition data which would
        #otherwise be forgotten
        for key, value in other_vars.items():
            if key not in together and key not in skip:
                together[key] = value
        return LocalNutrition(**together)
    
    def __rmul__(self, other_value):
        together = {}
        skip = set(["ndbno", "desc", "foodgroup", "gramwt1",
            "gramdsc1", "gramwt2", "gramdsc2", "refusepct",
            "package_weight", "num_of_slices", "source",
            "made_from", "_sa_instance_state"])
        self_vars = vars(self)
        for key, value in self_vars.items():
            if key not in skip:
                self_value = 0 if self_vars[key] is None else self_vars[key]
                together[key]=self_value * other_value
        together["desc"] = self.desc
        return LocalNutrition(**together)

    def __repr__(self):
        return "<{} {} {} kcal {} g {}>".format(self.desc, self.ndbno,
                self.kcal, self.gramwt1, self.gramdsc1)

    def __str__(self):
        str_out = []
        for key, value in vars(self).items():
            if key != "_sa_instance_state":
                if value != 0 and value is not None:
                    if type(value) == float:
                        str_out.append("{}: {:.2f}".format(key,value))
                    else:
                        str_out.append("{}: {}".format(key,value))
        return ",".join(str_out)


class LocalNutritionaliase(Base):
    __tablename__ = 'nutritionaliases'

    id = Column(Integer, primary_key=True)
    ingkey = Column(Text)
    ndbno = Column(ForeignKey('nutrition.ndbno'))
    density_equivalent = Column(Text(20))

    nutrition = relationship('LocalNutrition')

    def __repr__(self):
        return "<{} -> {} ({})>".format(self.ingkey, self.ndbno,
                self.density_equivalent)

class BestBefore(Base):
    __tablename__ = 'best_before'
    id = Column(Integer, primary_key=True)
    ndbno = Column(ForeignKey('nutrition.ndbno'))
    time = Column(Date)
    eaten = Column(Boolean)

    nutrition = relationship('LocalNutrition', backref="best_before")

    def __repr__(self):
        return "<BB {} ndbno:{}, time:{}, eaten:{}>".format(self.id,\
                self.ndbno, self.time, self.eaten)

class Shop(Base):
    __tablename__ = 'shop'
    id = Column(Integer, primary_key=True)
    name = Column(Text(100))

    def __repr__(self):
        return "<Shop {} {}>".format(self.id, self.name)

class Price(Base):
    __tablename__ = 'price'
    id = Column(Integer, primary_key=True)
    ndbno = Column(ForeignKey('nutrition.ndbno'))
    shop_id = Column(ForeignKey('shop.id'))
    last_updated = Column(Date)
#Normal price in a shop
    price = Column(Float)
#Mojih 10 Current action etc.
    lowered_price = Column(Float)
#Mojih 10 has limited timespan
    lowered_untill = Column(Date)
    currency = Column(Text(4))
    comment = Column(Text(100))
#Is this price or offer temporary or not (Hofer usually)
    temporary = Column(Boolean())

    nutrition = relationship('LocalNutrition')
    shop = relationship('Shop', backref="prices")

    def __repr__(self):
        out_str = []
        self_vars = vars(self)
        for key, value in self_vars.items():
            if key != "_sa_instance_state" and key != "nutrition":
                if value is not None:
                    out_str.append("{}: {}".format(key, value))
        return "<Price " + ",".join(out_str) + ">"

class Tag(Base):
    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True)
    name = Column(Text(100))
    main = Column(Boolean, server_default=text("0"))

    def __repr__(self):
        return "<Tag {} {} {}>".format(self.id, self.name, self.main)

class TagItem(Base):
    __tablename__ = 'tag_item'

    id = Column(Integer, primary_key=True)
    ndbno = Column(ForeignKey('nutrition.ndbno'))
    tag_id = Column(ForeignKey('tag.id'))
    
    nutrition = relationship('LocalNutrition')
    tag = relationship('Tag')

class TagHierarchy(Base):
    __tablename__ = 'tag_hierarchy'

    tag_id = Column(ForeignKey('tag.id'), primary_key=True)
    child_tag_id = Column(ForeignKey('tag.id'), primary_key=True)

class FoodTag(Base):
    __tablename__ = 'food_tag'

    id = Column(Integer, primary_key=True)
    name = Column(Text(100))
    #main = Column(Boolean, server_default=text("0"))

    def __repr__(self):
        return "<FoodTag {} {}>".format(self.id, self.name)

class FoodTagItem(Base):
    __tablename__ = 'food_tag_item'
    __table_args__ = (
        Index('Unique foodnutrition tag', 'fn_id', 'tag_id', unique=True),
    )


    id = Column(Integer, primary_key=True)
    fn_id = Column(ForeignKey('foodnutrition.id'))
    tag_id = Column(ForeignKey('food_tag.id'))
    item_id = Column(ForeignKey('eat.id'))
    
    foodnutrition = relationship('FoodNutrition')
    tag = relationship('FoodTag')
    item = relationship('Item')

class UsdaWeight(Base):
    __tablename__ = 'usda_weights'

    id = Column(Integer, primary_key=True)
    ndbno = Column(Integer)
    seq = Column(Float)
    amount = Column(Float)
    unit = Column(Text(80))
    gramwt = Column(Float)
    ndata = Column(Integer)
    stdev = Column(Float)


t_foodnutrition_details_alias = Table(
    'foodnutrition_details_alias', metadata,
    Column('foodnutrition_details_fn_id', Integer, primary_key=True),
    Column('foodnutrition_details_ndbno', Integer),
    Column('foodnutrition_details_weight', Float),
    Column('nutritionaliases_ingkey', Text)
)
"""SELECT foodnutrition_details.fn_id AS foodnutrition_details_fn_id, foodnutrition_details.ndbno AS foodnutrition_details_ndbno, foodnutrition_details.weight AS foodnutrition_details_weight, nutritionaliases.ingkey AS nutritionaliases_ingkey 
FROM foodnutrition_details, nutritionaliases 
WHERE foodnutrition_details.ndbno = nutritionaliases.ndbno
"""


t_foodnutrition_details_alias_time = Table(
    'foodnutrition_details_alias_time', metadata,
    Column('foodnutrition_details_weight', Float),
    Column('nutritionaliases_ingkey', Text),
    Column('eat_time', DateTime),
    Column('foodnutrition_details_fn_id', Integer, primary_key=True),
    Column('foodnutrition_details_ndbno', Integer)
)

"""SELECT foodnutrition_details.weight AS foodnutrition_details_weight, nutritionaliases.ingkey AS nutritionaliases_ingkey, eat.time AS eat_time,
foodnutrition_details.fn_id AS foodnutrition_details_fn_id, foodnutrition_details.ndbno AS foodnutrition_details_ndbno 
FROM foodnutrition_details, nutritionaliases, eat 
WHERE foodnutrition_details.ndbno = nutritionaliases.ndbno AND
foodnutrition_details.fn_id = eat.calc_nutrition
"""
class FoodNutritionDetailsTime(Base):
    __table__ = t_foodnutrition_details_alias_time




if __name__ == "__main__":
    from connectSettings import connectString
    from sqlalchemy import create_engine

    engine = create_engine(connectString,  echo=True)                                                                                                                
    metadata.create_all(engine)
