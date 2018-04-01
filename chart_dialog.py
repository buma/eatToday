from PyQt5.QtCore import *
from PyQt5.QtGui  import *
from PyQt5.QtWidgets import (
        QDialog,
        QLabel,
        QGraphicsScene
        )

from ui_chart_view import Ui_ChartDialog
from canvas_test import SceneCalendar

class ChartDialog(QDialog, Ui_ChartDialog):
    def __init__(self, parent = None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.initUI()

    def initUI(self):
        #TODO: size this based on dialog size?
        self.scene = QGraphicsScene(0,0,900,1500, self)
        self.gv.setScene(self.scene)

    def set_calendar_chart(self, items, hash):
        self.lbl_title.setText("Calendar showing of {}".format(
            ",".join(items)))
        sc = SceneCalendar(scene=self.scene)
        sc.add_data(items, hash)
        if len(sc.specific_months) == 1:
            sc.height=50
            sc.prmonth(sc.specific_months[0][0], sc.specific_months[0][1], w=50)
        else:
            sc.height=35
            sc.formatyear(None, w=35)
