import itertools
import io
import traceback
from PyQt5.QtCore import *                                                                                                                                       
from PyQt5.QtGui  import *
from PyQt5.QtWidgets import (
        QMainWindow,
        QCompleter,
        QMessageBox,
        QDialogButtonBox
        )

from ui_input import Ui_MainWindow

from connectSettings import connectString                                                                                                                        
import sqlalchemy                                                                                                                                                
from sqlalchemy.orm import sessionmaker                                                                                                                          
from sqlalchemy.exc import DBAPIError   
from database import Item, LocalNutrition, LocalNutritionaliase, FoodNutrition
from gourmet_db import Nutrition, Nutritionaliase, UsdaWeight
from util import sort_nutrition_string, calculate_nutrition

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent = None):
        QMainWindow.__init__(self, parent)
        self.setupUi(self)

        self.initUI()


    def initUI(self):
        self.buttonBox.accepted.connect(self.add_new)
        calc_button = self.buttonBox.addButton("Calculate", QDialogButtonBox.ActionRole)
        calc_button.pressed.connect(self.calculate)
        self.cb_type.currentTextChanged.connect(self.enable_nutrition)
        engine = sqlalchemy.create_engine(connectString)
        gourmet_engine = \
                sqlalchemy.create_engine("sqlite:////home/mabu/.gourmet/recipes_copy.db")
        Session = sessionmaker()
        Session.configure(binds={Item: engine,
                Nutrition: gourmet_engine,
                Nutritionaliase: gourmet_engine,
                LocalNutrition: engine,
                LocalNutritionaliase: engine,
                FoodNutrition: engine,
                UsdaWeight: gourmet_engine
            })
        self.session = Session()

        model_keys = QStringListModel()
        aliases = itertools.chain(self.session \
                .query(LocalNutritionaliase.ingkey),
                self.session.query(Nutritionaliase.ingkey))
        aliases_list = sorted(x[0].upper() for x in aliases)
        model_keys.setStringList(aliases_list)

        self.lv_keys.setModel(model_keys)
        self.lv_keys.doubleClicked.connect(self.add_key_to_nutrition)

        self.completer = QCompleter()
        self.le_description.setCompleter(self.completer)
        self.model = QStringListModel()
        self.completer.setModel(self.model)

        self.d_edit.setDateTime(QDateTime.currentDateTime())
        self.cb_type.addItems(["HRANA", "PIPI", "PIJAČA", "STANJE", "ZDRAVILO",
            "KAKA"])


    def enable_nutrition(self, val):
        is_nutrition = val == "HRANA" or val == "PIJAČA"
        self.le_nutrition.setEnabled(is_nutrition)
        self.lv_keys.setEnabled(is_nutrition)
        self.model_data = self.session.query(Item.description.distinct()).filter(Item.type==self.cb_type.currentText())
        items = (x[0] for x in self.model_data.all())
        self.model.setStringList(items)

    def add_key_to_nutrition(self, model_index):
        if self.le_nutrition.isEnabled():
            self.le_nutrition.insert(model_index.data())


    #@pyqtSlot("")
    def add_new(self):
        desc = self.le_description.text()
        nutrition = self.le_nutrition.text() if self.le_nutrition.isEnabled() \
            and len(self.le_nutrition.text()) > 3 \
            else None
        try:
            if nutrition is not None:
                nutrition = sort_nutrition_string(nutrition)
            item = Item(description=desc, nutrition=nutrition,
                    time=self.d_edit.dateTime().toPyDateTime(),
                    type=self.cb_type.currentText())
            self.session.merge(item)
            print(item)
            self.session.commit()
            self.le_description.setText("")
            self.le_nutrition.setText("")
        except Exception as e:
            iostream = io.StringIO();
            #Shows error dialog:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("It was not possible to save data")
            msg.setInformativeText("Error: " + str(e))
            traceback.print_exc(file=iostream)
            msg.setDetailedText(iostream.getvalue())
            msg.exec_()
            
            
    def calculate(self):
        nutrition = self.le_nutrition.text() if self.le_nutrition.isEnabled() \
            and len(self.le_nutrition.text()) > 3 \
            else None
        try:
            if nutrition is not None:
                calculation = calculate_nutrition(nutrition, self.session)
                print (calculation)
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("{} Calories {} Carb {} Protein {} fat {} fiber" \
                        " {} sugar {} water".format(calculation.kcal,
                            calculation.carb, calculation.protein,
                            calculation.lipid, calculation.fiber,
                            calculation.sugar, calculation.water))
                msg.exec_()
#TODO make nicer label: https://github.com/nutritionix/nutrition-label
        except Exception as e:
            iostream = io.StringIO();
            #Shows error dialog:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("It was not possible to save data")
            msg.setInformativeText("Error: " + str(e))
            traceback.print_exc(file=iostream)
            msg.setDetailedText(iostream.getvalue())
            msg.exec_()

