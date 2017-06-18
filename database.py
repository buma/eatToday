# coding: utf-8
import datetime

from sqlalchemy import Column, DateTime, Integer, Text, CHAR, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from gourmet_db import Nutrition


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
        return "{:6.2f} {:6.2f} {:6.2f} {:6.2f} {:6.3} {:6.3} {:10.5}".format(self.kcal,
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
    carb = Column(Float)
    fiber = Column(Float)
    sugar = Column(Float)
    calcium = Column(Float)
    gramwt1 = Column(Float)
    gramdsc1 = Column(Text(100))

    def __add__(self, other):
        together = {}
        skip = set(["ndbno", "desc", "foodgroup", "gramwt1",
            "gramdsc1", "gramwt2", "gramdsc2", "refusepct",
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

if __name__ == "__main__":
    from connectSettings import connectString
    from sqlalchemy import create_engine

    engine = create_engine(connectString,  echo=True)                                                                                                                
    metadata.create_all(engine)
