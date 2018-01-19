from PyQt5.QtCore import *
from PyQt5.QtWidgets import QDialogButtonBox

from PyQt5.QtWidgets import (
        QCompleter,
        QMessageBox,
        )
from PyQt5.QtSql import (
        QSqlRelation,
        QSqlRelationalTableModel,
        QSqlTableModel,
        QSqlQueryModel
        )
eating_model = None

def fill_eating_model():
    global eating_model
    eating_model = QSqlTableModel()
    eating_model.setTable("eat")
    eating_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
    eating_model.setSort(1,Qt.DescendingOrder)
    eating_model.select()

def fill_food_tags_model():
    global eating_model
    eating_model = QSqlQueryModel()
    eating_model.setQuery("""
    SELECT id, calc_nutrition, "" AS tags, description
     FROM eat
    WHERE eat.calc_nutrition IS NOT NULL
    AND type == "HRANA"
    """)


def init_edit_eat(self):
    global eating_model
    print("Editing eat init")


    def update_model():
        print ("Updating")
        if not eating_model.submitAll():
            print ("ERROR submitting:", eating_model.lastError().text())

    def reset_update_model():
        eating_model.revertAll()

    def switch_model(checked):
        print ("Switching")
        if self.rb_eat.isChecked():
            fill_eating_model()
        else:
            fill_food_tags_model()

        self.tv_eat_view.setModel(eating_model)
    switch_model(True)
    #self.tv_eat_view.setModel(eating_model)
    #self.tv_eat_view.setModel(self.eating_model)

    self.buttonBox_edit_eat.accepted.connect(update_model)
    self.buttonBox_edit_eat.button(QDialogButtonBox.Reset).clicked.connect(reset_update_model)
    self.rb_eat.toggled.connect(switch_model)
    self.rb_eat_tags.toggled.connect(switch_model)

def start(self):
    global eating_model
    print("Starting eat init")
    #eating_model.select()
