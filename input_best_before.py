from PyQt5.QtCore import *

from PyQt5.QtWidgets import QDialogButtonBox
from PyQt5.QtSql import (
        QSqlRelation,
        QSqlRelationalDelegate,
        QSqlRelationalTableModel,
        )

"""Initializes Best Before tab"""
def init_best_before(self):

    model = QSqlRelationalTableModel()
    model.setTable("best_before")
    model.setEditStrategy(QSqlRelationalTableModel.OnManualSubmit)

    model.setRelation(1, QSqlRelation('nutrition', 'ndbno', 'desc'))
    model.select()
#Nutrition table needs to be populated since otherwise only 256 rows are read
#And all inserts with ndbno > 100169 fail since they aren't found in nutrition
    #table
    nutri_model = model.relationModel(1)
    while nutri_model.canFetchMore():
        nutri_model.fetchMore()
    self.bb_model = model

    nutri_model = self.lv_keys.model()
    #nutri_model = QSqlTableModel()
    #nutri_model.setTable("nutrition")
    ##nutri_model.setRelation(2, QSqlRelation('nutrition', 'ndbno', 'desc'))
    #nutri_model.setEditStrategy(QSqlRelationalTableModel.OnManualSubmit)
    #nutri_model.setSort(1,Qt.AscendingOrder)
    #nutri_model.select()
    self.cb_bb_item.setModel(nutri_model)
    self.cb_bb_item.setModelColumn(0)

    self.tv_best_before.setModel(model)
    self.tv_best_before.setSortingEnabled(True)
    self.tv_best_before.sortByColumn(2, Qt.AscendingOrder)
    self.tv_best_before.setItemDelegate(QSqlRelationalDelegate(self.tv_best_before))
    self.tv_best_before.show()

#From Price
    self.cb_price_item.setModel(nutri_model)
    self.cb_price_item.setModelColumn(0)
#From Tag
    self.cb_item_tag.setModel(nutri_model)
    self.cb_item_tag.setModelColumn(0)

    """Updates Best before table"""
    def update_bb():
        print ("Updating Best Before")
        if not self.bb_model.submitAll():
            QMessageBox.critical(None, "Error updating Best Before",
                    "Couldn't update model: " +
                    self.bb_model.lastError().text())

    """Adds new data to best before table

    update_bb also needs to be called"""
    def add_bb():
        print("Adding to BB")
        ndbno = self._get_selected_ndbno(self.cb_bb_item.model() \
                .record(self.cb_bb_item.currentIndex()))
        print ("IDX:", self.cb_bb_item.currentIndex(),
                ndbno)


        row = self.bb_model.rowCount()
        self.bb_model.insertRow(row)
        #print ("NDBNO INDEX:", self.bb_model.fieldIndex("desc"))
        r = self.bb_model.record()
        #for i in range(r.count()):
            #print ("{} => {}".format(i,r.fieldName(i)))
        #for i in range(100000,100194):
            #out_ndbno = self.bb_model.setData(self.bb_model.createIndex(row,
                #self.bb_model.fieldIndex("desc")), i,
                    #Qt.EditRole)
            #print ("{}? = {}".format(out_ndbno, i))
        out_ndbno = self.bb_model.setData(self.bb_model.createIndex(row,
            self.bb_model.fieldIndex("desc")), ndbno,
                Qt.EditRole)
        out_time = self.bb_model.setData(self.bb_model.createIndex(row,
            self.bb_model.fieldIndex("time")),
                self.de_bb.date(),
                Qt.EditRole)
        print ("NDBNO:", out_ndbno, "TIME:", out_time)

    self.update_bb = update_bb
    self.add_bb = add_bb

    self.buttonBox_3.button(QDialogButtonBox.SaveAll).clicked.connect(self.update_bb)
    self.buttonBox_3.button(QDialogButtonBox.Apply).clicked.connect(self.add_bb)
