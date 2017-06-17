# coding: utf-8
import datetime

from sqlalchemy import Column, DateTime, Integer, Text, CHAR, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


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
        return "<kcal {} carb: {:.2f} belj:{:.2f} masc:{:.2f}>".format(self.kcal,
                self.carb, self.protein, self.lipid)

class LocalNutrition(Base):
    __tablename__ = 'nutrition'

    ndbno = Column(Integer, primary_key=True)
    desc = Column(Text(100))
    kcal = Column(Float)
    protein = Column(Float)
    lipid = Column(Float)
    carb = Column(Float)
    fiber = Column(Float)
    sugar = Column(Float)
    gramwt1 = Column(Float)
    gramdsc1 = Column(Text(100))

    def __add__(self, other):
        total_kcal = self.kcal + other.kcal
        total_protein = self.protein + other.protein
        total_lipid = self.lipid + other.lipid
        total_carb = self.carb + other.carb
        total_fiber = self.fiber + other.fiber
        total_sugar = self.sugar + other.sugar
        all_desc = self.desc + " " + other.desc
        return LocalNutrition(desc=all_desc, kcal=total_kcal,
                protein=total_protein, lipid=total_lipid, carb=total_carb,
                fiber=total_fiber, sugar=total_sugar)
    
    def __rmul__(self, other):
        total_kcal = self.kcal * other
        total_protein = self.protein * other
        total_lipid = self.lipid * other
        total_carb = self.carb * other
        total_fiber = self.fiber * other
        total_sugar = self.sugar * other
        return LocalNutrition(desc=self.desc, kcal=total_kcal,
                protein=total_protein, lipid=total_lipid, carb=total_carb,
                fiber=total_fiber, sugar=total_sugar)

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
