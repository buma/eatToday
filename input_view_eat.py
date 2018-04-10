import io
import traceback
import json
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QDialogButtonBox

from PyQt5.QtWidgets import (
        QCompleter,
        QMessageBox,
        QAction,
        QMenu
        )
from PyQt5.QtSql import (
        QSqlRelation,
        QSqlRelationalTableModel,
        QSqlTableModel,
        QSqlQueryModel,
        QSqlQuery
        )

from search_dsl import SQLTransformer, InvalidField
from help_dialog import HelpDialog
from util import show_before as show_before_sql

def init_view_eat(self):
    print ("Init view eat")
    search_model = QSqlQueryModel()
    proxy_model = QSortFilterProxyModel(self)
    proxy_model.setSourceModel(search_model)
    transformer = SQLTransformer()
    self.tv_search_eat.setModel(proxy_model)
    self.tv_search_eat.setSortingEnabled(True)

    saved_searches = json.load(open("searches.json", "r"))

    self.cb_searches.addItems(saved_searches)

    def search():
        query = self.le_search.text()
        try:
            SQL = transformer.get_sql(query)
            search_model.setQuery(SQL)
        except InvalidField as invf:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Invalid search field")
            msg.setInformativeText(str(invf))
            msg.exec_()
        except Exception as e:
            iostream = io.StringIO();
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("It was not possible to search")
            msg.setInformativeText("Error: " + str(e))
            traceback.print_exc(file=iostream)
            msg.setDetailedText(iostream.getvalue())
            msg.exec_()

    def show_help():
        msg = HelpDialog(self)
        msg.setText("Column help")
        msg.setInformativeText(SQLTransformer.get_column_names())
        #TODO: add serch query help
        msg.show()

    def select_saved_search(search):
        print ("SELECTING SAVED SEARCH:", search)
        self.le_search.setText(search)

    def add_saved_search():
        search = self.le_search.text()
        print ("Adding saved search:", search)
        if search in saved_searches:
            print ("SEARCH already in list")
            return
        self.cb_searches.addItem(search)
        saved_searches.append(search)
        json.dump(saved_searches, open("searches.json", "w"))

    def show_context_menu(point):
        print ("POINT:", point)

        x = point.x()
        y = point.y()

        model = self.tv_search_eat.model()
        source_model = model.sourceModel()


        column = self.tv_search_eat.columnAt(x)
        column_title = model.headerData(column, Qt.Horizontal)

        if column_title != "id":
            return
        row = self.tv_search_eat.rowAt(y)

        index = self.tv_search_eat.indexAt(point)
        mapped_index = model.mapToSource(index)

        val = source_model.data(mapped_index)

        #print ("ColID:", column)
        print (model.headerData(column, Qt.Horizontal))
        #print ("VAL:", val)

        def show_before(eat_id):
            print ("SHOWING BEFORE:", eat_id)
            print (show_before_sql(eat_id, self.session, 48))

        def show_after(eat_id):
            print ("SHOWING AFTER:", eat_id)
            print (show_before_sql(eat_id, self.session, -48))


        before_acct = QAction("&Before", self)
        before_acct.setStatusTip("Show food before this time")
        before_acct.triggered.connect(lambda: show_before(val))

        after_acct = QAction("&After", self)
        after_acct.setStatusTip("Show stanje/kaka after this time")
        after_acct.triggered.connect(lambda: show_after(val))

        menu = QMenu(self)
        menu.addAction(before_acct)
        menu.addAction(after_acct)
        menu.exec_(self.tv_search_eat.mapToGlobal(point))

    

    self.pb_search.clicked.connect(search)
    self.pb_search_help.clicked.connect(show_help)
    self.cb_searches.currentTextChanged.connect(select_saved_search)
    self.pb_add_saved_search.clicked.connect(add_saved_search)
    self.tv_search_eat.customContextMenuRequested.connect(show_context_menu)
