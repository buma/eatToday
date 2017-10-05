from PyQt5.QtCore import *                                                                                                                                       
from PyQt5.QtWidgets import QDialogButtonBox

from PyQt5.QtSql import (
        QSqlRelation,
        QSqlRelationalDelegate,
        QSqlRelationalTableModel,
        QSqlTableModel,
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




    self.cb_shop.setModel(model)
    self.cb_shop.setModelColumn(1)

    #self.cb_shop.lineEdit().editingFinished.connect(self.add_shop)
    self.pb_add_shop.pressed.connect(self.add_shop)
    self.pb_add_price.pressed.connect(self.add_price)

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

    self.update_price = update_price
    self.reset_price = reset_price
    self.currency_changed = currency_changed

    self.buttonBox_4.button(QDialogButtonBox.SaveAll).clicked.connect(self.update_price)
    self.buttonBox_4.button(QDialogButtonBox.Reset).clicked.connect(self.reset_price)
    self.cb_currency.currentTextChanged.connect(self.currency_changed)
