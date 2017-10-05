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
        QSqlTableModel,
        QSqlQueryModel
        )

from ui_input import Ui_MainWindow

from connectSettings import connectString                                                                                                                        
import sqlalchemy                                                                                                                                                
from sqlalchemy.orm import sessionmaker                                                                                                                          
from sqlalchemy.exc import DBAPIError   
from database import (
        Item, LocalNutrition, LocalNutritionaliase, FoodNutrition,
        Tag, TagItem, UsdaWeight)
from util import sort_nutrition_string, calculate_nutrition

from nutritionDialog import NutritionDialog
import input_chart as i_c
import input_price as i_p
import input_best_before as i_bb

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
        self.cb_usda.stateChanged.connect(self.enable_usda)
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

        self.local_nutri_query = self.session \
                .query(LocalNutritionaliase.ndbno)
        self.filters = []

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
        self.update_lv_keys()
#Do we want all nutritions or just local?
        #self.cb_bb_item.setModel(model_keys)
        self.lv_keys.doubleClicked.connect(self.add_key_to_nutrition)
        self.lv_keys.clicked.connect(self.show_usda)

        self.completer = QCompleter()
        self.le_description.setCompleter(self.completer)
        self.completer.setModel(eating_model)
        self.completer.setCompletionColumn(3)

        self.d_edit.setDateTime(QDateTime.currentDateTime())
        self.cb_type.addItems(["HRANA", "PIPI", "PIJAČA", "STANJE", "ZDRAVILO",
            "KAKA"])

        self.cb_tag_select.currentIndexChanged.connect(self.filter_add_nutrition)

        self.init_add_nutrition()
        self.init_best_before()
        self.init_price()
        self.init_tag()
        self.init_chart()

    def enable_usda(self, state):
        if state==Qt.Checked:
#Remove filter with USDA in it
            self.filters = list(filter(lambda x: 'USDA' not in x, self.filters))
        else:
            self.filters.append("source!='USDA'")
        self.update_lv_keys()

    def update_lv_keys(self):
        #print ("FILTER:", self.filters)
        model_keys = self.lv_keys.model()
        if self.filters:
            filter = " AND ".join(self.filters)
            model_keys.setFilter(filter)
        else:
            model_keys.setFilter(None)
        #print ("Filters:", model_keys.filter(), model_keys.selectStatement())

    def filter_add_nutrition(self, model_index):
        record = self.cb_tag_select.model().record(model_index) 
        print (record.field("id").value(), record.field("name").value())
        id = record.field("id").value()
#Remove filter with IN in it
        self.filters = list(filter(lambda x: 'IN' not in x, self.filters))
        if id == 0:
            pass
        else:
            filtered_local = self.local_nutri_query \
                    .join(LocalNutrition) \
                    .join(TagItem) \
                    .filter(TagItem.tag_id==id)
            fids = []
            for fid in filtered_local:
                fids.append(fid.ndbno)
            if fids:
                self.filters.append("nutrition.ndbno IN ("+",".join([str(x) for x in
                    fids])+")")
        self.update_lv_keys()

    def init_tag(self):

#Selected tags when item is selected
        self.selected_tags = set()
        self.pb_add_tag.pressed.connect(self.add_tag)
        self.pb_add_item_tag.pressed.connect(self.add_item_tag)
        self.pb_add_hier.pressed.connect(self.add_hier)
        self.pb_save_hier.pressed.connect(self.save_hier)
        self.pb_save_tag_item.pressed.connect(self.save_tag_item)
        self.cb_item_tag.currentIndexChanged.connect(self.select_nutri_tag)


        tag_model = QSqlTableModel()
        tag_model.setTable("tag")
        tag_model.setEditStrategy(QSqlTableModel.OnRowChange)
#It can't be sorted otherwise wrong tags are selected when item is selected
        #tag_model.setSort(1, Qt.AscendingOrder)
        tag_model.select()

        tag_item_model = QSqlRelationalTableModel()
        tag_item_model.setTable("tag_item")
        #tag_item_model.setRelation(1, QSqlRelation('nutrition', 'ndbno', 'desc'))
        #tag_item_model.setRelation(2, QSqlRelation('tag', 'id', 'name'))
        tag_item_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        #tag_item_model.select()

        self.tag_item_model = tag_item_model

        tag_hier_model = QSqlRelationalTableModel()
        tag_hier_model.setTable("tag_hierarchy")
        tag_hier_model.setRelation(0, QSqlRelation('tag', 'id', 'name'))
        tag_hier_model.setRelation(1, QSqlRelation('tag', 'id', 'name'))
        tag_hier_model.setSort(0, Qt.AscendingOrder)
        tag_hier_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        tag_hier_model.select()

#From add food
        self.cb_tag_select.setModel(tag_model)
        self.cb_tag_select.setModelColumn(1)

        self.tv_tag.setModel(tag_model)
        #self.tv_tag_item.setModel(tag_item_model)
        self.tv_tag_hierarchy.setModel(tag_hier_model)
        self.lv_tag.setModel(tag_model)
        self.lv_tag.setModelColumn(1)

        #self.tv_tag_item.setItemDelegate(QSqlRelationalDelegate(self.tv_tag_item))
        self.tv_tag_hierarchy.setItemDelegate(QSqlRelationalDelegate(self.tv_tag_hierarchy))

    def add_tag(self):
        print ("Adding tag:")
        row = self.tv_tag.model().rowCount()
        self.tv_tag.model().insertRow(row)
    
    def add_hier(self):
        print ("Adding hier:")
        row = self.tv_tag_hierarchy.model().rowCount()
        self.tv_tag_hierarchy.model().insertRow(row)

    def add_item_tag(self):
        print ("Adding item_tag:")
        row = self.tv_tag_item.model().rowCount()
        self.tv_tag_item.model().insertRow(row)

    def save_hier(self):
        print ("Saving hier")
        self.tv_tag_hierarchy.model().submitAll()

    def select_nutri_tag(self, selectedIndex):
        ndbno = self._get_selected_ndbno(self.cb_item_tag.model() \
                .record(self.cb_item_tag.currentIndex()))
        print ("Item:", self.cb_item_tag.currentText(), ndbno)
        tags = self.session.query(TagItem) \
                .filter(TagItem.ndbno==ndbno) \
                .order_by(TagItem.tag_id)
        if self.lv_tag.selectionModel():
            self.lv_tag.selectionModel().clearSelection()
        self.selected_tags.clear()
        for tag in tags:
            print (tag.tag.name, tag.tag_id)
            index = self.lv_tag.model().createIndex(tag.tag_id, 1)
            if index.isValid():
                print ("Valid index")
                self.lv_tag.selectionModel().select(index,
                        QItemSelectionModel.Select)
                data = self.lv_tag.model().data(index)
                self.selected_tags.add(tag.tag_id)
                #print(data)

    def save_tag_item(self):
        print ("Saving tag item")
        selected_tags_now = set()
        for index in self.lv_tag.selectedIndexes():
            record = self.lv_tag.model().record(index.row()) 
            selected_tags_now.add(record.field("id").value())
            print (str(record.field("id").value()) + " - " +
                    record.field("name").value())
        added_tag_ids = selected_tags_now.difference(self.selected_tags)
        removed_tag_ids = self.selected_tags.difference(selected_tags_now)
        #print ("Unselected tags:" + ", ".join(map(lambda x: str(x),
                #removed_tag_ids)))
        #print ("New selected tags:" + ", ".join(map(lambda x: str(x),
                #added_tag_ids)))
        ndbno = self._get_selected_ndbno(self.cb_item_tag.model() \
                .record(self.cb_item_tag.currentIndex()))
        print ("Item:", self.cb_item_tag.currentText(), ndbno)

        query = QSqlQuery()
        ret = query.prepare("DELETE FROM tag_item WHERE ndbno = :ndbno and tag_id = :tag_id")
        if not ret:
            print ("Failed to prepare query")


        for tag_id in added_tag_ids:
            row = self.tag_item_model.rowCount()
            self.tag_item_model.insertRow(row)
            self.tag_item_model.setData(self.tag_item_model.createIndex(row,
                1), ndbno, Qt.EditRole)
            self.tag_item_model.setData(self.tag_item_model.createIndex(row,
                2), tag_id, Qt.EditRole)
            print ("Adding tag id:", tag_id)
            #print (record.field("name").value(), record.field("id").value())
        #self.tv_tag_item.model().submitAll()
        if not self.tag_item_model.submitAll():
            QMessageBox.critical(None, "Error submitting",
                    "Couldn't update model: " +
                    self.tag_item_model.lastError().text())
            self.tag_item_model.revertAll()
        query.bindValue(":ndbno", ndbno)
        for tag_id in removed_tag_ids:
            query.bindValue(":tag_id", tag_id)
            print ("Removing tag_id:", tag_id)
            if not query.exec_():
                print ("Failed to executr query")
            #print (query.executedQuery())


    def init_price(self):
        i_p.init_price(self)

    """Adds new Shop to DB"""
    def add_shop(self):
        print (self.cb_shop.currentText())
        row = self.shop_model.rowCount()
        self.shop_model.insertRow(row)
        self.shop_model.setData(self.shop_model.createIndex(row,1),
                self.cb_shop.currentText(), Qt.EditRole)
        self.shop_model.submitAll()


    def add_price(self):
        shop_id = self.shop_model.record(self.cb_shop.currentIndex()) \
                .field("id").value()
        print ("Shop ID:", shop_id, self.cb_shop.currentText())
        record = self.cb_price_item.model() \
                .record(self.cb_price_item.currentIndex()) 
        ndbno = self._get_selected_ndbno(record)
        package_weight = record.field("package_weight").value()
        slices = record.field("num_of_slices").value()

        last_updated = self.de_last_updated.date()
        price = self.dsp_price.value()
        lowered_price = self.dsp_low_price.value() if \
                self.dsp_low_price.value() > 0 else None
        lowered_untill = self.de_low_untill.date() if \
                self.de_low_untill.date() > QDate.currentDate() else None
        currency = self.cb_currency.currentText()
        comment = self.le_comment.text() if \
                len(self.le_comment.text()) > 3 else None
        temporary = self.cb_temporary.isChecked()

        print ("ITEM:", self.cb_price_item.currentText(), ndbno)
        print ("Weight:", package_weight, " Slices: ", slices)
        print ("LU:" , last_updated)
        print ("PRICE:", price, " Low Price:", lowered_price)
        print ("LOWU:" , lowered_untill)
        print ("CU:", currency)
        print ("COMMENT:", comment)
        print ("Temp:", temporary)
        print ("NDBNO:", ndbno, type(ndbno))
        print ("SHOP ID:", shop_id, type(shop_id))
        row = self.price_model.rowCount()
        self.price_model.insertRow(row)

        def add_data(idx, data):
            return self.price_model.setData(self.price_model.createIndex(row, idx),
                    data, Qt.EditRole)
        #for i in range(100000,100194):
        #for i in self.session.query(LocalNutrition.ndbno).filter(LocalNutrition.ndbno
                #< 100000).order_by(LocalNutrition.ndbno):
            #out_ndbno = add_data(1, QVariant(i[0]))
            #print ("{}? = {}".format(out_ndbno, i[0]))
        #for i in range(100000,100194):
        ##for i in self.session.query(LocalNutrition.ndbno).filter(LocalNutrition.ndbno
                ##< 100000).order_by(LocalNutrition.ndbno):
            #out_ndbno = add_data(1, QVariant(i))
            #print ("{}? = {}".format(out_ndbno, i))
        #FIXME: Why is ndbno found in nutrtition only if it lower then 100169

        #relation = self.price_model.relation(1)
        #print(relation, relation.displayColumn(), relation.indexColumn())
        #print (relation.dictionary.contains(ndbno))

        #return

        add_data(1, ndbno)
        add_data(2, shop_id)
        add_data(3, last_updated)
        add_data(4, price)
        if lowered_price is not None and lowered_untill is not None:
            add_data(5, lowered_price)
            add_data(6, lowered_untill)
        add_data(7, currency)
        if comment is not None:
            add_data(8, comment)
        add_data(9, temporary)
        self.price_model.submitAll()

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


    """Initializes add tab"""
    def init_add_nutrition(self):
        self.buttonBox_2.accepted.connect(self.add_new_nutrition)
        self.buttonBox_2.button(QDialogButtonBox.Reset).clicked.connect(self.reset_add_nutrition)
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


    def enable_nutrition(self, val):
        #FIXME: this doesn't filter types currently
        is_nutrition = val == "HRANA" or val == "PIJAČA"
        self.le_nutrition.setEnabled(is_nutrition)
        self.lv_keys.setEnabled(is_nutrition)
        self.model_data = self.session.query(Item.description.distinct()).filter(Item.type==self.cb_type.currentText())
        #self.le_description.completer().model().setFilter("type="+self.cb_type.currentText())
        #print (self.le_description.completer().model().selecStatement())
        items = (x[0] for x in self.model_data.all())
        #self.model.setStringList(items)

    def add_key_to_nutrition(self, model_index):
        if self.le_nutrition.isEnabled():
            self.le_nutrition.insert(model_index.data())

    def _get_selected_ndbno(self, record):
        ingkey = record.field(0).value()
#Nutritionaliases table
        relation_model = self.lv_keys.model().relationModel(0)
#Selects ingkey selected in list in nutritionaliases table
        relation_model.setFilter("ingkey='"+ingkey+"'")
        ndbno = relation_model.data(relation_model.index(0,2))
        return ndbno


    def show_usda(self, model_index):
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


    #@pyqtSlot("")
    def add_new(self):
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
            
            
    def calculate(self):
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

    def init_chart(self):
        i_c.init_chart(self)

