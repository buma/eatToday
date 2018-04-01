from PyQt5.QtCore import *
from PyQt5.QtGui  import *
from PyQt5.QtWidgets import (
        QDialog,
        QLabel,
        QGraphicsScene,
        QFileDialog
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
        self.imgx, self.imgy = 900,1500
        self.scene = QGraphicsScene(0,0,self.imgx,self.imgy, self)
        #self.scene = QGraphicsScene(0,0,500,500, self)
        self.gv.setScene(self.scene)
        self.pb_save_image.clicked.connect(self.save_image)
        #self.actionSave_image.trigger(self.save_image)

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

    def save_image(self, checked):
        fname = QFileDialog.getSaveFileName(self, "Save scene")
        if fname and fname[0]:
            print(fname)
            image = QImage(self.imgx, self.imgy,
                    QImage.Format_ARGB32)
            painter = QPainter(image)
            painter.setRenderHint(QPainter.Antialiasing)
            self.scene.render(painter)
            image.save(fname[0])
            painter.end()
