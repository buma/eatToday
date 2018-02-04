import io
import traceback
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
        QSqlQueryModel,
        QSqlQuery
        )

from search_dsl import SQLTransformer, InvalidField
from help_dialog import HelpDialog

def init_view_eat(self):
    print ("Init view eat")
    search_model = QSqlQueryModel()
    proxy_model = QSortFilterProxyModel(self)
    proxy_model.setSourceModel(search_model)
    transformer = SQLTransformer()
    self.tv_search_eat.setModel(proxy_model)
    self.tv_search_eat.setSortingEnabled(True)

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

    self.pb_search.clicked.connect(search)
    self.pb_search_help.clicked.connect(show_help)
