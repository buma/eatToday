from database import LocalNutrition, LocalNutritionaliase
from PyQt5.QtCore import *

from PyQt5.QtWidgets import (
        QLabel,
        QFormLayout,
        QMessageBox,
        QSpinBox,
        QDoubleSpinBox,
        QDialogButtonBox,
        QLineEdit
        )

from PyQt5.QtSql import QSqlTableModel

"""Initializes add tab"""
def init_add_nutrition(self):
    skip = set(['ndbno', 'ash', 'phosphorus', 'potassium', 'zinc',
        'copper', 'manganese', 'selenium', 'vitaminc',
        'alphac', 'betac', 'betacrypt', 'cholestrl', 'choline', 'famono',
            'fapoly', 'folateacid', 'folatedfe', 'folatetotal',
            'foodfolate', 'foodgroup', 'lutzea', 'lypocene', 'niacin',
            'pantoacid', 'refusepct', 'retinol', 'riboflavin', 'sodium',
            'source', 'thiamin', 'vitaiu', 'vitaminb6', 'vitarae', 'vitb12',
            'vite', 'vitk'])
    self.unit_g = set(['water', 'protein', 'lipid', 'carb', 'fiber', 'sugar'])
    idx = 1
    self.inputs = {}

    self.nutritionalias = QSqlTableModel()
    self.nutritionalias.setTable("nutritionaliases")
    self.nutritionalias.setEditStrategy(QSqlTableModel.OnManualSubmit)

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
        elif c.name == "package_weight" or c.name == "num_of_slices":
            le = QSpinBox(self)
            if c.name == "package_weight":
                le.setMaximum(5000)
            else:
                le.setMaximum(20)
            le.setSuffix("g")
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
            elif c.name.startswith("gramwt"):
                le.setSuffix("g")
                le.setMaximum(500)
            else:
                le.setSuffix("mg")
                le.setMaximum(1000)
        le.setObjectName("in_"+c.name)
        self.formLayout.setWidget(idx, QFormLayout.FieldRole, le)
        idx+=1

    def add_new_nutrition():
        ingkey = self.in_ingkey.text()
        mandatory = set("kcal")
        mandatory = mandatory.union(self.unit_g)
        line = {}
        for c in filter(lambda x: x.name != "ndbno",
                LocalNutrition.__table__.columns):
            if c.name not in self.inputs:
                continue
            value = self.inputs[c.name]()
            if c.name not in mandatory and value == 0:
                value = None
            if c.name.startswith("gramdsc") and len(value) <= 3:
                value = None
            print(c.name, c.type, value)
            if value is not None:
                line[c.name]=value
        nutri_model = self.lv_keys.model()

        row = nutri_model.rowCount()
        nutri_model.insertRow(row)
        def add_data(key, data):
            idx = nutri_model.fieldIndex(key)
            nutri_model.setData(nutri_model.createIndex(row, idx),
                    data, Qt.EditRole)
        line["source"]="LOCAL"
        for key, value in line.items():
            add_data(key, value)
            #print ("{} => {}".format(key, value))
        add_data("ndbno", ingkey)
        if not nutri_model.submitAll():
            print ("ERROR submiting:", nutri_model.lastError().text())
            return
        ndbno = nutri_model.query().lastInsertId()

        alias_row = self.nutritionalias.rowCount()
        self.nutritionalias.insertRow(alias_row)
        def add_alias_data(key, data):
            idx = self.nutritionalias.fieldIndex(key)
            self.nutritionalias.setData(self.nutritionalias.createIndex(alias_row, idx),
                    data, Qt.EditRole)
        add_alias_data("ingkey", ingkey)
        add_alias_data("ndbno", ndbno)

        nutri = LocalNutrition(**line)
        print (nutri)
        alias = LocalNutritionaliase(ingkey=ingkey, ndbno=nutri.ndbno)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Check if everything is OK:")
        msg.setInformativeText("Nutrition:\n"+str(nutri)+"\nAlias:\n"+repr(alias))
        msg.setStandardButtons(QMessageBox.Save | QMessageBox.Discard)
        result = msg.exec_()
        if result == QMessageBox.Save:
            print ("Inserting")
            if not self.nutritionalias.submitAll():
                print ("ERROR submiting:", self.nutritionalias.lastError().text())
                return

    def reset_add_nutrition():
        for widget in self.tab_add_nutrition.findChildren(QLineEdit):
            widget.clear()

    self.buttonBox_2.accepted.connect(add_new_nutrition)
    self.buttonBox_2.button(QDialogButtonBox.Reset).clicked.connect(reset_add_nutrition)
