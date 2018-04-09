from tabulate import tabulate
from PyQt5.QtCore import *
from PyQt5.QtGui  import *
from PyQt5.QtWidgets import (
        QDialog,
        QLabel,
        QGraphicsScene,
        QFileDialog,
        QGraphicsTextItem
        )

from ui_chart_view import Ui_ChartDialog
from canvas_test import SceneCalendar
from ComparisionChart import ComparisionChart



class ChartDialog(QDialog, Ui_ChartDialog):
    def __init__(self, parent = None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.initUI()

    def initUI(self):
        #TODO: size this based on dialog size?
        self.imgx, self.imgy = 900,1800
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

    def set_comparision_chart(self, stat_type, time_span, date_range,
            eaten_before, eaten_this_week, table_low, table_high, table_eq):
        #import pickle
        #with open("cache_chart.pkl", "wb") as cache_chart:
            #pickle.dump((eaten_before, eaten_this_week, table_low, table_high,
                #table_eq), cache_chart)
        #with open("cache_chart.pkl", "rb") as cache_chart:
            #eaten_before, eaten_this_week, table_low, \
                #table_high, table_eq = pickle.load(cache_chart)
        start, end = date_range
        self.lbl_title.setText(
                "Showing {} comparision in {} between {} - {}".format(
                    time_span, stat_type,start, end))

        cc = ComparisionChart(self.scene, eaten_before, eaten_this_week,
                table_low, table_high, table_eq)
        cc.draw()

    def set_day_chart(self,header, day, chart_title, data):
        self.lbl_title.setText(chart_title.format(day,day))
        print (chart_title.format(day, day))
        maxes = []
        for i in range(len(header)-2):
            maxes.append(0)
        #print (header, maxes)
        for line in data:
            for i in range(len(maxes)):
                maxes[i]=max(line[i+2],maxes[i])
        #print (maxes)
        #FIXME: temporary display
        #TODO: this needs to be shown as text items, so that barchart can be
        #shown in each column in percentage of max or percentage of all
        #TODO: maybe clicking on food would open nutrition with same info?
        txt= (tabulate(data, headers=header))
        font = QFont("monospace", 9)
        text_item = QGraphicsTextItem(txt)
        text_item.setFont(font)
        self.scene.addItem(text_item)


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
