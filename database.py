# coding: utf-8
import datetime

from sqlalchemy import (
        Column, DateTime, Integer, Text, CHAR, Float,
ForeignKey, Boolean, Date )
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from gourmet_db import Nutrition
import colorama


Base = declarative_base()
metadata = Base.metadata



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

    def __init__(self, type, description, nutrition, time=None):
        self.type = type
        self.description = description
        self.nutrition = nutrition
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

class FoodNutrition(Base):
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



class LocalNutrition(Base):
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

    def __add__(self, other):
        together = {}
        skip = set(["ndbno", "desc", "foodgroup", "gramwt1",
            "gramdsc1", "gramwt2", "gramdsc2", "refusepct",
            "package_weight", "num_of_slices", "source",
            "_sa_instance_state"])
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
        return Nutrition(**together)
    
    def __rmul__(self, other_value):
        together = {}
        skip = set(["ndbno", "desc", "foodgroup", "gramwt1",
            "gramdsc1", "gramwt2", "gramdsc2", "refusepct",
            "package_weight", "num_of_slices", "source",
            "_sa_instance_state"])
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

    def __repr__(self):
        return "<Tag {} {}>".format(self.id, self.name)

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




if __name__ == "__main__":
    from connectSettings import connectString
    from sqlalchemy import create_engine

    engine = create_engine(connectString,  echo=True)                                                                                                                
    metadata.create_all(engine)
