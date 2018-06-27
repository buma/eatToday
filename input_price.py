from PyQt5.QtCore import *                                                                                                                                       
from PyQt5.QtWidgets import QDialogButtonBox

from PyQt5.QtSql import (
        QSqlRelation,
        QSqlRelationalDelegate,
        QSqlRelationalTableModel,
        QSqlTableModel,
        QSqlQuery,
        QSqlQueryModel,
        )

def init_price(self):
    currencies = {
            "EUR": u"€",
            "HRK": u"kn"
            }
    model = QSqlTableModel()
    model.setTable("shop")
    model.setEditStrategy(QSqlRelationalTableModel.OnManualSubmit)
    model.select()

    self.shop_model = model

    price_model = QSqlRelationalTableModel()
    price_model.setTable("price")
    price_model.setEditStrategy(QSqlRelationalTableModel.OnManualSubmit)
    price_model.setRelation(1, QSqlRelation('nutrition', 'ndbno', 'desc'))
    price_model.setRelation(2, QSqlRelation('shop', 'id', 'name'))

#Nutrition table needs to be populated since otherwise only 256 rows are read
#And all inserts with ndbno > 100169 fail since they aren't found in nutrition
    #table
    nutri_model = price_model.relationModel(1)
    while nutri_model.canFetchMore():
        nutri_model.fetchMore()

    self.price_model = price_model

    self.price_model.select()

    self.tv_price.setModel(price_model)
    self.tv_price.setSortingEnabled(True)
    self.tv_price.sortByColumn(1, Qt.AscendingOrder)
    self.tv_price.setItemDelegate(QSqlRelationalDelegate(self.tv_price))

    price_sort_model = QSqlQueryModel()
    price_sort_model.setQuery("SELECT nutrition.ndbno, nutrition.desc, shop.name, " +
            "last_updated, price, price/nutrition.package_weight*1000 as " +
            " price_kg,  nutrition.kcal/price as kcal_price_100, " +
            "nutrition.protein/price as protein_price_100," +
            " (nutrition.kcal*nutrition.package_weight/100)/price as " +
            " kcal_price_package, " +
            " (nutrition.protein*nutrition.package_weight/100)/price " +
            " as protein_price_package, " +
            "lowered_price, lowered_untill, " +
            "currency,comment, temporary FROM price " +
            " JOIN shop ON shop.id == price.shop_id " +
            " JOIN nutrition ON price.ndbno = nutrition.ndbno " +
            " WHERE currency = 'EUR' "
            " ORDER BY nutrition.desc, price")
    proxy_model = QSortFilterProxyModel(self)
    proxy_model.setSourceModel(price_sort_model)
    proxy_model.setFilterKeyColumn(0)
    self.price_proxy = proxy_model
    #print (price_sort_model.lastError().text())
    #print (price_sort_model.query().executedQuery())

    self.tv_price_view.setModel(proxy_model)
    self.tv_price_view.setSortingEnabled(True)
    self.tv_price_view.horizontalHeader().setToolTip("protein/kcal_price "
            "higher is better")




    self.cb_shop.setModel(model)
    self.cb_shop.setModelColumn(1)

    #self.cb_shop.lineEdit().editingFinished.connect(self.add_shop)

    model_currency = QStringListModel()
    model_currency.setStringList(["EUR", "HRK"])
    self.cb_currency.setModel(model_currency)

    self.de_last_updated.setMaximumDate(QDate.currentDate())
    self.de_last_updated.setDateTime(QDateTime.currentDateTime())

    def update_price():
        print ("Updating price info")
        if not price_model.submitAll():
            QMessageBox.critical(None, "Error updating price:",
                    "Couldn't update model: " +
                    price_model.lastError().text())

    def reset_price():
        print ("Resetting price info")
        price_model.revertAll()

    """Sets suffix symbols for prices based on currency"""
    def currency_changed(currency):
        symbol = currencies[currency]
        self.dsp_price.setSuffix(symbol)
        self.dsp_low_price.setSuffix(symbol)
    
    """Adds new Shop to DB"""
    def add_shop():
        print (self.cb_shop.currentText())
        row = self.shop_model.rowCount()
        self.shop_model.insertRow(row)
        self.shop_model.setData(self.shop_model.createIndex(row,1),
                self.cb_shop.currentText(), Qt.EditRole)
        self.shop_model.submitAll()

    def add_price():
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
        #print ("ROW:", row, self.price_model.relationModel(1).rowCount())
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

    self.update_price = update_price
    self.reset_price = reset_price
    self.currency_changed = currency_changed

    self.buttonBox_4.button(QDialogButtonBox.SaveAll).clicked.connect(self.update_price)
    self.buttonBox_4.button(QDialogButtonBox.Reset).clicked.connect(self.reset_price)
    self.cb_currency.currentTextChanged.connect(self.currency_changed)
    self.pb_add_shop.pressed.connect(add_shop)
    self.pb_add_price.pressed.connect(add_price)
