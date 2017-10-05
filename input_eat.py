import io
import traceback
from database import (
        LocalNutrition,
        LocalNutritionaliase,
        Item,
        TagItem,
        UsdaWeight
        )
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
        )
from nutritionDialog import NutritionDialog
from util import sort_nutrition_string

def init_add_eat(self):
    calc_button = self.buttonBox.addButton("Calculate", QDialogButtonBox.ActionRole)
    self.local_nutri_query = self.session \
            .query(LocalNutritionaliase.ndbno)
    self.filters = []
    self.fids = []

    eating_model = QSqlTableModel()
    eating_model.setTable("eat")
    eating_model.select()

    nutri_model = QSqlRelationalTableModel()
    nutri_model.setTable("nutrition")
    #nutri_model.fieldIndex("ndbno")
    nutri_model.setRelation(0, QSqlRelation('nutritionaliases', 'ndbno',
        'ingkey'))
    nutri_model.setSort(0, Qt.AscendingOrder)
    nutri_model.select()
    #print (nutri_model.selectStatement())

    self.lv_keys.setModel(nutri_model)
    #self.cb_bb_item.setModel(model_keys)

    self.completer = QCompleter()
    self.le_description.setCompleter(self.completer)
    self.completer.setModel(eating_model)
    self.completer.setCompletionColumn(3)

    self.d_edit.setDateTime(QDateTime.currentDateTime())
    self.cb_type.addItems(["HRANA", "PIPI", "PIJAČA", "STANJE", "ZDRAVILO",
        "KAKA"])


    def enable_usda(state):
        if state==Qt.Checked:
#Remove filter with USDA in it
            self.filters = list(filter(lambda x: 'USDA' not in x, self.filters))
        else:
            self.filters.append("source!='USDA'")
        update_lv_keys()

    def update_lv_keys():
        #print ("FILTER:", self.filters)
        model_keys = self.lv_keys.model()
        if self.filters:
            filter = " AND ".join(self.filters)
            model_keys.setFilter(filter)
        else:
            model_keys.setFilter(None)
        if self.price_proxy is not None:
            if self.fids:
                regexp = "|".join((str(x) for x in self.fids))
                #print (regexp)
                qregexp = QRegExp("("+regexp+")")
                self.price_proxy.setFilterRegExp(qregexp)
            else:
                self.price_proxy.setFilterRegExp("")
        #print ("Filters:", model_keys.filter(), model_keys.selectStatement())

    def filter_add_nutrition(model_index):
        record = self.cb_tag_select.model().record(model_index) 
        print (record.field("id").value(), record.field("name").value())
        id = record.field("id").value()
#Remove filter with IN in it
        self.filters = list(filter(lambda x: 'IN' not in x, self.filters))
        if id == 0:
            self.fids = []
            pass
        else:
            filtered_local = self.local_nutri_query \
                    .join(LocalNutrition) \
                    .join(TagItem) \
                    .filter(TagItem.tag_id==id)
            self.fids = []
            for fid in filtered_local:
                self.fids.append(fid.ndbno)
            if self.fids:
                #print (fids, "|".join((str(x) for x in fids)))
                self.filters.append("nutrition.ndbno IN ("+",".join([str(x) for x in
                    self.fids])+")")
        update_lv_keys()

    def enable_nutrition(val):
        #FIXME: this doesn't filter types currently
        is_nutrition = val == "HRANA" or val == "PIJAČA"
        self.le_nutrition.setEnabled(is_nutrition)
        self.lv_keys.setEnabled(is_nutrition)
        self.model_data = self.session.query(Item.description.distinct()).filter(Item.type==self.cb_type.currentText())
        #self.le_description.completer().model().setFilter("type="+self.cb_type.currentText())
        #print (self.le_description.completer().model().selecStatement())
        items = (x[0] for x in self.model_data.all())
        #self.model.setStringList(items)

    def add_key_to_nutrition(model_index):
        if self.le_nutrition.isEnabled():
            self.le_nutrition.insert(model_index.data())

    def show_usda(model_index):
        if self.le_nutrition.isEnabled():
#Selected nutrition record
            record = self.lv_keys.model() \
                    .record(model_index.row()) 
            ndbno = self._get_selected_ndbno(record)
            status = "Units:"
            units = []
            nutrition = self.session.query(LocalNutrition.gramdsc1,
                    LocalNutrition.gramdsc2) \
                    .filter(LocalNutrition.ndbno==ndbno) \
                    .one()
            gramdsc1 = nutrition.gramdsc1
            gramdsc2 = nutrition.gramdsc2
            usda_amounts = self.session.query(UsdaWeight.unit) \
                    .filter(UsdaWeight.ndbno==ndbno) 
            for usda_amount in usda_amounts:
                units.append(usda_amount[0])
            #gramdsc1 = record.field("gramdsc1").value()
            #gramdsc2 = record.field("gramdsc2").value()
            #print ("NDBNO:", ndbno)
            if gramdsc1 is not None:
                units.append(gramdsc1)
            if gramdsc2 is not None:
                units.append(gramdsc2)
            units.sort()
            try:
                if units:
                    status+=", ".join(units)
                    self.statusbar.showMessage(status)
                else:
                    self.statusbar.clearMessage()
            except Exception as a:
                print ("Problem with units:", units)
                self.statusbar.clearMessage()


    def add_new():
        model = self.le_description.completer().model()
        row = model.rowCount()
        model.insertRow(row)
        def add_data(idx, data):
            model.setData(model.createIndex(row, idx),
                    data, Qt.EditRole)
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
            add_data(1, str(self.d_edit.dateTime().toPyDateTime()))
            add_data(2, self.cb_type.currentText())
            add_data(3, desc)
            add_data(4, nutrition)
            print(item)
            if not model.submitAll():
                raise Exception(model.lastError().text())
            #self.session.merge(item)
            #self.session.commit()
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

    def calculate():
        nutrition = self.le_nutrition.text() if self.le_nutrition.isEnabled() \
            and len(self.le_nutrition.text()) > 3 \
            else None
        try:
            if nutrition is not None:
                dlg = NutritionDialog(None,nutrition, self.session)
                dlg.exec_()
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

    update_lv_keys()
    enable_nutrition(self.cb_type.currentText())
    self.buttonBox.accepted.connect(add_new)
    calc_button.pressed.connect(calculate)
    self.cb_usda.stateChanged.connect(enable_usda)
    self.cb_type.currentTextChanged.connect(enable_nutrition)
    self.lv_keys.doubleClicked.connect(add_key_to_nutrition)
    self.lv_keys.clicked.connect(show_usda)
    self.cb_tag_select.currentIndexChanged.connect(filter_add_nutrition)
