import itertools
from PyQt5.QtCore import *                                                                                                                                       
from PyQt5.QtGui  import *
from PyQt5.QtWidgets import (
        QMainWindow,
        QMessageBox
        )

from PyQt5.QtSql import QSqlDatabase

from ui_input import Ui_MainWindow

from connectSettings import connectString                                                                                                                        
import sqlalchemy                                                                                                                                                
from sqlalchemy.orm import sessionmaker                                                                                                                          
from sqlalchemy.exc import DBAPIError   
from database import (
        Item, LocalNutrition, LocalNutritionaliase, FoodNutrition,
        Tag, TagItem, UsdaWeight)

import input_chart as i_c
import input_price as i_p
import input_best_before as i_bb
import input_tag as i_t
import input_nutrition as i_n
import input_eat as i_e
import input_eat_edit as i_e_e
import input_view_eat as i_v_e
import input_stats as input_stats

class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, parent = None, calculate=[False]):
        QMainWindow.__init__(self, parent)
        self.setupUi(self)

        self.initUI()
        self.calculate=calculate


    def initUI(self):
        engine = sqlalchemy.create_engine(connectString)
        gourmet_engine = \
                sqlalchemy.create_engine("sqlite:////home/mabu/.gourmet/recipes_copy.db")
        Session = sessionmaker()
        Session.configure(binds={Item: engine,
                #Nutrition: gourmet_engine,
                #Nutritionaliase: gourmet_engine,
                LocalNutrition: engine,
                LocalNutritionaliase: engine,
                Tag: engine,
                TagItem: engine,
                FoodNutrition: engine,
                UsdaWeight: engine
            })
        self.session = Session()

        self.init_db()

        self.price_proxy = None 


        self.init_add_eat()
        self.init_add_nutrition()
        self.init_best_before()
        self.init_price()
        self.init_tag()
        self.init_chart()
        self.init_edit_eat()
        self.init_view_eat()
        self.init_stats()

        self.tabWidget.currentChanged.connect(self.tabWidgetTabChanged)


    def init_add_eat(self):
        i_e.init_add_eat(self)

    def init_add_nutrition(self):
        i_n.init_add_nutrition(self)

    def init_tag(self):
        i_t.init_tag(self)

    def init_price(self):
        i_p.init_price(self)

    def init_edit_eat(self):
        i_e_e.init_edit_eat(self)

    def init_view_eat(self):
        i_v_e.init_view_eat(self)

    def init_stats(self):
        input_stats.init_stats(self)

    def show_graph(self, items, dates, stat_type):
        input_stats.show_graph(self, items, dates, stat_type)

    """Initializes Qt DB connection"""
    def init_db(self):
        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName(connectString.replace("sqlite:///", ""))
        if not self.db.open():
            QMessageBox.critical(None, "Cannot open database",
                    "Unable to establish a database connection.\n"
                "This example needs SQLite support. Please read the Qt SQL "
                "driver documentation for information how to build it.\n\n"
                "Click Cancel to exit.",
                QMessageBox.Cancel)
            return


    def init_best_before(self):
        i_bb.init_best_before(self)

    def _get_selected_ndbno(self, record):
        ingkey = record.field(0).value()
#Nutritionaliases table
        relation_model = self.lv_keys.model().relationModel(0)
#Selects ingkey selected in list in nutritionaliases table
        relation_model.setFilter("ingkey='"+ingkey+"'")
        ndbno = relation_model.data(relation_model.index(0,2))
        return ndbno

    def init_chart(self):
        i_c.init_chart(self)

    def tabWidgetTabChanged(self, tabIndex):
        print("Tab switched to {}".format(tabIndex))
        if tabIndex == 1:
            i_e_e.start(self)

