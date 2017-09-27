from PyQt5.QtCore import *                                                                                                                                       
from PyQt5.QtGui  import *
from PyQt5.QtWidgets import (
        QDialog
        )

from ui_nutrition import Ui_Dialog
from util import calculate_nutrition, get_amounts, get_nutrition_list

class NutritionDialog(QDialog, Ui_Dialog):
    skip = set(["ndbno", "foodgroup", "gramwt1",
        "gramdsc1", "gramwt2", "gramdsc2", "refusepct",
        "package_weight", "num_of_slices", "source",
        "made_from", "_sa_instance_state"])
    dailyValues = {
            "calcium" : 1300,
            "iron": 18,
            "potassium" : 4700,
            }
    def __init__(self, parent = None, nutrition = None, session=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.session = session
        self.nutrition = nutrition
        self.template = open("./nutrition/demo.html", "r").read()
        calculation = calculate_nutrition(nutrition, self.session)
        self.data = calculation

        print (calculation)

        self.initUI()

    def initUI(self):
        calculation = self.data
        txt =("{} Calories {} Carb {} Protein {} fat {} fiber" \
                " {} sugar {} water".format(calculation.kcal,
                    calculation.carb, calculation.protein,
                    calculation.lipid, calculation.fiber,
                    calculation.sugar, calculation.water))
        self.lbl_nutrition.setText(txt)
        nutri_list = ",".join(get_nutrition_list(self.nutrition, self.session))
        print (nutri_list)
        out = self.template
#TODO: Add vitamins etc. (They need to be recalculated to % of DV)
        for key, value in vars(self.data).items():
            if key not in self.skip:
                #print (key, value)
                if key in self.dailyValues:
                    print ("VALUE:", key,  value)
                    calc_value = value/self.dailyValues[key]*100
                else:
                    calc_value = value
                out = out.replace(key.upper(), str(calc_value))
        out = out.replace("LIST", nutri_list)
        #vn = open("./nutrition/demo1.html", "w")
        #vn.write(out)
        #vn.close()
        self.webView.setHtml(out,
                QUrl("file:///home/mabu/programiranje/eatToday/nutrition/demo.html"))


