#!/usr/bin/env python2
import sys
from PyQt5.QtCore import QLocale, QTranslator
from PyQt5.QtWidgets import QApplication
from input import MainWindow

__version__ = "0.26"

def nutri_calc():
    import sqlalchemy
    from sqlalchemy.orm import sessionmaker
    from database import (
            Item,
            LocalNutrition,
            LocalNutritionaliase,
            FoodNutrition,
            FoodNutritionDetails,
            UsdaWeight
            )
    from connectSettings import connectString
    from util import get_nutrition, add_nutrition_details

    engine = sqlalchemy.create_engine(connectString)
    Session = sessionmaker(bind=engine)
    session = Session() 


    items = session.query(Item) \
            .filter(Item.nutrition.isnot(None)) \
            .filter(Item.calc_nutrition.is_(None))



##Updates items
    for item in items:
        print (item)
        print (get_nutrition(item, session))
        session.commit()
        print ()

    add_nutrition_details(session)

if __name__ == "__main__":
    reload = [False]

    app = QApplication(sys.argv)
    window = MainWindow(calculate=reload)
    window.show()
    out = app.exec_()
    print ("RELOAD:", reload)
    if reload[0]:
        nutri_calc()
    sys.exit(out)
