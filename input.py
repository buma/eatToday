import itertools
import io
import traceback
from PyQt5.QtCore import *                                                                                                                                       
from PyQt5.QtGui  import *
from PyQt5.QtWidgets import (
        QMainWindow,
        QLabel,
        QFormLayout,
        QSpinBox,
        QDoubleSpinBox,
        QLineEdit,
        QCompleter,
        QMessageBox,
        QDialogButtonBox
        )

from PyQt5.QtSql import (
        QSqlDatabase,
        QSqlQuery,
        QSqlRelation,
        QSqlRelationalDelegate,
        QSqlRelationalTableModel,
        QSqlTableModel
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
#Do we want all nutritions or just local?
        #self.cb_bb_item.setModel(model_keys)
        self.lv_keys.doubleClicked.connect(self.add_key_to_nutrition)

        self.completer = QCompleter()
        self.le_description.setCompleter(self.completer)
        self.model = QStringListModel()
        self.completer.setModel(self.model)

        self.d_edit.setDateTime(QDateTime.currentDateTime())
        self.cb_type.addItems(["HRANA", "PIPI", "PIJAČA", "STANJE", "ZDRAVILO",
            "KAKA"])

        self.init_add_nutrition()
        self.init_best_before()

    """Initializes Best Before tab"""
    def init_best_before(self):
        self.buttonBox_3.button(QDialogButtonBox.SaveAll).clicked.connect(self.update_bb)
        self.buttonBox_3.button(QDialogButtonBox.Apply).clicked.connect(self.add_bb)
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

        model = QSqlRelationalTableModel()
        model.setTable("best_before")
        model.setEditStrategy(QSqlRelationalTableModel.OnManualSubmit)

        model.setRelation(1, QSqlRelation('nutrition', 'ndbno', 'desc'))
        model.select()
        self.bb_model = model

        nutri_model = QSqlTableModel()
        nutri_model.setTable("nutrition")
        #nutri_model.setRelation(2, QSqlRelation('nutrition', 'ndbno', 'desc'))
        nutri_model.setEditStrategy(QSqlRelationalTableModel.OnManualSubmit)
        nutri_model.select()
        self.cb_bb_item.setModel(nutri_model)
        self.cb_bb_item.setModelColumn(1)

        self.tv_best_before.setModel(model)
        self.tv_best_before.setItemDelegate(QSqlRelationalDelegate(self.tv_best_before))
        self.tv_best_before.show()

    """Updates Best before table"""
    def update_bb(self):
        print ("Updating Best Before")
        if not self.bb_model.submitAll():
            QMessageBox.error(None, "Couldn't update model",
                    QMessageBox.Cancel)

    """Adds new data to best before table

    update_bb also needs to be called"""
    def add_bb(self):
        print("Adding to BB")
        ndbno = self.cb_bb_item.model() \
                .record(self.cb_bb_item.currentIndex()) \
                .field("ndbno").value()
        #print ("IDX:", self.cb_bb_item.currentIndex(),
                #ndbno)


        row = self.bb_model.rowCount()
        self.bb_model.insertRow(row)
        self.bb_model.setData(self.bb_model.createIndex(row, 1), ndbno,
                Qt.EditRole)
        self.bb_model.setData(self.bb_model.createIndex(row, 2),
                self.de_bb.date(),
                Qt.EditRole)


    """Initializes add tab"""
    def init_add_nutrition(self):
        self.buttonBox_2.accepted.connect(self.add_new_nutrition)
        self.buttonBox_2.button(QDialogButtonBox.Reset).clicked.connect(self.reset_add_nutrition)
        skip = set(["ndbno"])
        self.unit_g = set(["water", "protein", "lipid", "carb", "fiber", "sugar"])
        idx = 1
        self.inputs = {}
        for c in filter(lambda x: x.name not in skip,
                LocalNutrition.__table__.columns):
            label = QLabel(self)
            label.setObjectName("label_"+c.name)
            label.setText(c.name)
            self.formLayout.setWidget(idx, QFormLayout.LabelRole,
                   label)
            if c.name == "kcal":
                le = QDoubleSpinBox(self)
                le.setMaximum(2000)
                le.setSuffix("kcal")
                self.inputs[c.name]=le.value
            elif "TEXT" in str(c.type):
                le = QLineEdit(self)
                self.inputs[c.name]=le.text
            else:
                le = QDoubleSpinBox(self)
                self.inputs[c.name]=le.value
                if c.name in self.unit_g:
                    le.setMaximum(100)
                    le.setSuffix("g")
                elif c.name == "gramwt1":
                    le.setSuffix("g")
                    le.setMaximum(500)
                else:
                    le.setSuffix("mg")
                    le.setMaximum(1000)
            le.setObjectName("in_"+c.name)
            self.formLayout.setWidget(idx, QFormLayout.FieldRole, le)
            idx+=1

    def reset_add_nutrition(self):
        for widget in self.tab_add_nutrition.findChildren(QLineEdit):
            widget.clear()

    def add_new_nutrition(self):
        ingkey = self.in_ingkey.text()
        mandatory = set("kcal")
        mandatory = mandatory.union(self.unit_g)
        line = {}
        for c in filter(lambda x: x.name != "ndbno",
                LocalNutrition.__table__.columns):
            value = self.inputs[c.name]()
            if c.name not in mandatory and value == 0:
                value = None
            if c.name == "gramdsc1" and len(value) <= 3:
                value = None
            print(c.name, c.type, value)
            if value is not None:
                line[c.name]=value
        nutri = LocalNutrition(**line)
        self.session.add(nutri)
        self.session.flush()
        print (nutri)
        alias = LocalNutritionaliase(ingkey=ingkey, ndbno=nutri.ndbno)
        self.session.add(alias)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Check if everything is OK:")
        msg.setInformativeText("Nutrition:\n"+str(nutri)+"\nAlias:\n"+repr(alias))
        msg.setStandardButtons(QMessageBox.Save | QMessageBox.Discard)
        result = msg.exec_()
        if result == QMessageBox.Save:
            print ("Inserting")
            self.session.commit()


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

