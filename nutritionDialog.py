from PyQt5.QtCore import *                                                                                                                                       
from PyQt5.QtGui  import *
from PyQt5.QtWidgets import (
        QDialog
        )

from ui_nutrition import Ui_Dialog

class NutritionDialog(QDialog, Ui_Dialog):
    def __init__(self, parent = None, data = None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.data = data

        self.initUI()

    def initUI(self):
        self.lbl_nutrition.setText(self.data)
        pass


