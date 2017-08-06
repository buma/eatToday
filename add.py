from PyQt5.QtCore import *                                                                                                                                       
from PyQt5.QtGui  import *
from PyQt5.QtWidgets import (
        QDialog,
        QLabel,
        QMessageBox,
        QFormLayout,
        QSpinBox,
        QDoubleSpinBox,
        QLineEdit
        )
from ui_add import Ui_Dialog

from connectSettings import connectString                                                                                                                        
import sqlalchemy                                                                                                                                                
from sqlalchemy.orm import sessionmaker                                                                                                                          
from sqlalchemy.exc import DBAPIError   
from database import LocalNutrition, LocalNutritionaliase

class AddDialog(QDialog, Ui_Dialog):
    def __init__(self, parent = None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.initUI()

    def initUI(self):
        self.buttonBox.accepted.connect(self.add_new)
        engine = sqlalchemy.create_engine(connectString)
        Session = sessionmaker(bind=engine)
        self.session = Session()
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
                le = QSpinBox(self)
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

    def add_new(self):
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
            self.accept()
        else:
            self.reject()
    
