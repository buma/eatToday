from PyQt5.QtCore import *                                                                                                                                       
from PyQt5.QtGui  import *
from PyQt5.QtWidgets import (
        QDialog
        )

from ui_nutrition import Ui_Dialog
from util import show_nutrition_view, init_nutrition_view

class NutritionDialog(QDialog, Ui_Dialog):
    def __init__(self, parent = None, nutrition = None, session=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.session = session
        self.nutrition = nutrition
        init_nutrition_view(self)

        self.initUI()

    def initUI(self):
        show_nutrition_view(self, self.nutrition, self.session)


