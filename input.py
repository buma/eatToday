from PyQt5.QtCore import *                                                                                                                                       
from PyQt5.QtGui  import *
from PyQt5.QtWidgets import QMainWindow, QCompleter

from ui_input import Ui_MainWindow

from connectSettings import connectString                                                                                                                        
import sqlalchemy                                                                                                                                                
from sqlalchemy.orm import sessionmaker                                                                                                                          
from sqlalchemy.exc import DBAPIError   
from database import Item
from util import sort_nutrition_string

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent = None):
        QMainWindow.__init__(self, parent)
        self.setupUi(self)

        self.initUI()


    def initUI(self):
        self.buttonBox.accepted.connect(self.add_new)
        self.cb_type.currentTextChanged.connect(self.enable_nutrition)
        engine = sqlalchemy.create_engine(connectString)
        Session = sessionmaker(bind=engine)
        self.session = Session()

        self.completer = QCompleter()
        self.le_description.setCompleter(self.completer)
        self.model = QStringListModel()
        self.completer.setModel(self.model)

        self.d_edit.setDateTime(QDateTime.currentDateTime())
        self.cb_type.addItems(["HRANA", "PIPI", "PIJAČA", "STANJE", "ZDRAVILO",
            "KAKA"])


    def enable_nutrition(self, val):
        is_nutrition = val == "HRANA" or val == "PIJAČA"
        self.le_nutrition.setEnabled(is_nutrition)
        self.model_data = self.session.query(Item.description.distinct()).filter(Item.type==self.cb_type.currentText())
        items = (x[0] for x in self.model_data.all())
        self.model.setStringList(items)


    #@pyqtSlot("")
    def add_new(self):
        desc = self.le_description.text()
        nutrition = self.le_nutrition.text() if self.le_nutrition.isEnabled() \
            and len(self.le_nutrition.text()) > 3 \
            else None
        if nutrition is not None:
            nutrition = sort_nutrition_string(nutrition)
        item = Item(description=desc, nutrition=nutrition,
                time=self.d_edit.dateTime().toPyDateTime(),
                type=self.cb_type.currentText())
        self.session.merge(item)
        print(item)
        self.session.commit()
        self.le_description.setText("")
        self.le_nutrition.setText("")

