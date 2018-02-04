from PyQt5.QtCore import *
from PyQt5.QtGui  import *
from PyQt5.QtWidgets import (
        QDialog,
        QLabel,
        )
from ui_help import Ui_Dialog

class HelpDialog(QDialog, Ui_Dialog):
    def __init__(self, parent = None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.initUI()

    def initUI(self):
        pass

    def setText(self, text):
        self.lbl_text.setText(text)

    def setInformativeText(self, text):
        self.lbl_detail.setText(text)
