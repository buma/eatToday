from PyQt5.QtCore import *                                                                                                                                       
from PyQt5.QtGui  import *
from PyQt5.QtWidgets import (
        QDialog
        )

from ui_nutrition import Ui_Dialog

class NutritionDialog(QDialog, Ui_Dialog):
    skip = set(["ndbno", "foodgroup", "gramwt1",
        "gramdsc1", "gramwt2", "gramdsc2", "refusepct",
        "package_weight", "num_of_slices", "source",
        "made_from", "_sa_instance_state"])
    def __init__(self, parent = None, data = None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.data = data
        self.template = open("./nutrition/demo.html", "r").read()

        self.initUI()

    def initUI(self):
        calculation = self.data
        txt =("{} Calories {} Carb {} Protein {} fat {} fiber" \
                " {} sugar {} water".format(calculation.kcal,
                    calculation.carb, calculation.protein,
                    calculation.lipid, calculation.fiber,
                    calculation.sugar, calculation.water))
        self.lbl_nutrition.setText(txt)
        out = self.template
#TODO: Add vitamins etc. (They need to be recalculated to % of DV)
        for key, value in vars(self.data).items():
            if key not in self.skip:
                print (key, value)
                out = out.replace(key.upper(), str(value))
        self.webView.setHtml(out,
                QUrl("file:///home/mabu/programiranje/eatToday/nutrition/demo.html"))


