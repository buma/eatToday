# coding: utf-8
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
metadata = Base.metadata


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    recipe_id = Column(ForeignKey('recipe.id'))
    category = Column(Text)

    recipe = relationship('Recipe')


class Convtable(Base):
    __tablename__ = 'convtable'

    id = Column(Integer, primary_key=True)
    ckey = Column(String(150))
    value = Column(String(150))


class Crossunitdict(Base):
    __tablename__ = 'crossunitdict'

    id = Column(Integer, primary_key=True)
    cukey = Column(String(150))
    value = Column(String(150))


class Density(Base):
    __tablename__ = 'density'

    id = Column(Integer, primary_key=True)
    dkey = Column(String(150))
    value = Column(String(150))


class Info(Base):
    __tablename__ = 'info'

    version_super = Column(Integer)
    version_major = Column(Integer)
    version_minor = Column(Integer)
    last_access = Column(Integer)
    rowid = Column(Integer, primary_key=True)


class Ingredient(Base):
    __tablename__ = 'ingredients'

    id = Column(Integer, primary_key=True)
    recipe_id = Column(ForeignKey('recipe.id'))
    refid = Column(ForeignKey('recipe.id'))
    unit = Column(Text)
    amount = Column(Float)
    rangeamount = Column(Float)
    item = Column(Text)
    ingkey = Column(Text)
    optional = Column(Boolean)
    shopoptional = Column(Integer)
    inggroup = Column(Text)
    position = Column(Integer)
    deleted = Column(Boolean)

    recipe = relationship('Recipe', primaryjoin='Ingredient.recipe_id == Recipe.id')
    recipe1 = relationship('Recipe', primaryjoin='Ingredient.refid == Recipe.id')


class Keylookup(Base):
    __tablename__ = 'keylookup'

    id = Column(Integer, primary_key=True)
    word = Column(Text)
    item = Column(Text)
    ingkey = Column(Text)
    count = Column(Integer)


class Nutrition(Base):
    __tablename__ = 'nutrition'

    ndbno = Column(Integer, primary_key=True)
    desc = Column(String(100))
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
    gramwt1 = Column(Float)
    gramdsc1 = Column(String(100))
    gramwt2 = Column(Float)
    gramdsc2 = Column(String(100))
    refusepct = Column(Float)
    foodgroup = Column(Text)
    
    def __add__(self, other):
        total_kcal = self.kcal + other.kcal
        total_protein = self.protein + other.protein
        total_lipid = self.lipid + other.lipid
        total_carb = self.carb + other.carb
        total_fiber = self.fiber + other.fiber
        total_sugar = self.sugar + other.sugar
        all_desc = self.desc + " " + other.desc
        return Nutrition(desc=all_desc, kcal=total_kcal,
                protein=total_protein, lipid=total_lipid, carb=total_carb,
                fiber=total_fiber, sugar=total_sugar)
    
    def __rmul__(self, other):
        total_kcal = self.kcal * other
        total_protein = self.protein * other
        total_lipid = self.lipid * other
        total_carb = self.carb * other
        total_fiber = self.fiber * other
        total_sugar = self.sugar * other
        return Nutrition(desc=self.desc, kcal=total_kcal,
                protein=total_protein, lipid=total_lipid, carb=total_carb,
                fiber=total_fiber, sugar=total_sugar)

    def __repr__(self):
        return "<{} {} {} kcal {} g {}>".format(self.desc, self.ndbno, self.kcal,
                self.gramwt1, self.gramdsc1)


class Nutritionaliase(Base):
    __tablename__ = 'nutritionaliases'

    id = Column(Integer, primary_key=True)
    ingkey = Column(Text)
    ndbno = Column(ForeignKey('nutrition.ndbno'))
    density_equivalent = Column(Text(20))

    nutrition = relationship('Nutrition')

    def __repr__(self):
        return "<{} -> {} ({})>".format(self.ingkey, self.ndbno,
                self.density_equivalent)


class Nutritionconversion(Base):
    __tablename__ = 'nutritionconversions'

    id = Column(Integer, primary_key=True)
    ingkey = Column(String(255))
    unit = Column(String(255))
    factor = Column(Float)

    def __repr__(self):
        return "<{} [{}]*{}>".format(self.ingkey, self.unit, self.factor)


class Pantry(Base):
    __tablename__ = 'pantry'

    id = Column(Integer, primary_key=True)
    ingkey = Column(Text(32))
    pantry = Column(Boolean)


class PluginInfo(Base):
    __tablename__ = 'plugin_info'

    plugin = Column(Text)
    id = Column(Integer, primary_key=True)
    version_super = Column(Integer)
    version_major = Column(Integer)
    version_minor = Column(Integer)
    plugin_version = Column(String(32))


class Recipe(Base):
    __tablename__ = 'recipe'

    id = Column(Integer, primary_key=True)
    title = Column(Text)
    instructions = Column(Text)
    modifications = Column(Text)
    cuisine = Column(Text)
    rating = Column(Integer)
    description = Column(Text)
    source = Column(Text)
    preptime = Column(Integer)
    cooktime = Column(Integer)
    servings = Column(Float)
    yields = Column(Float)
    yield_unit = Column(String(32))
    image = Column(LargeBinary)
    thumb = Column(LargeBinary)
    deleted = Column(Boolean)
    recipe_hash = Column(String(32))
    ingredient_hash = Column(String(32))
    link = Column(Text)
    last_modified = Column(Integer)


class Shopcat(Base):
    __tablename__ = 'shopcats'

    id = Column(Integer, primary_key=True)
    ingkey = Column(Text(32))
    shopcategory = Column(Text)
    position = Column(Integer)


class Shopcatsorder(Base):
    __tablename__ = 'shopcatsorder'

    id = Column(Integer, primary_key=True)
    shopcategory = Column(Text(32))
    position = Column(Integer)


class Unitdict(Base):
    __tablename__ = 'unitdict'

    id = Column(Integer, primary_key=True)
    ukey = Column(String(150))
    value = Column(String(150))


class UsdaWeight(Base):
    __tablename__ = 'usda_weights'

    id = Column(Integer, primary_key=True)
    ndbno = Column(Integer)
    seq = Column(Float)
    amount = Column(Float)
    unit = Column(String(80))
    gramwt = Column(Float)
    ndata = Column(Integer)
    stdev = Column(Float)
