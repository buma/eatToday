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

from search_dsl import SQLTransformer

def init_view_eat(self):
    print ("Init view eat")
    search_model = QSqlQueryModel()
    transformer = SQLTransformer()
    self.tv_search_eat.setModel(search_model)

    def search():
        print("Searching")
        query = self.le_search.text()
        SQL = transformer.get_sql(query)
        search_model.setQuery(SQL)
        

    self.pb_search.clicked.connect(search)
