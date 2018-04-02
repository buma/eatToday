from PyQt5.QtCore import *
from PyQt5.QtGui  import (
        QFont,
        QColor,
        QBrush,
        QPen
        )
from PyQt5.QtWidgets import (
        QGraphicsTextItem,
        QGraphicsRectItem
        )
from PyQt5.QtChart import (
        QChart, 
QValueAxis, QBarSet, QBarSeries, QHorizontalBarSeries, QBarCategoryAxis, QStackedBarSeries,
QPercentBarSeries)

class ComparisionChart(object):
    font = QFont("sans-serif", 9)
    arial_font = QFont("arial", 12)
    arial_font.setBold(True)
    color1 = QColor("red")
    color2 = QColor("cyan")
    color1.setAlpha(40)
    color2.setAlpha(40)
    color1_brush = QBrush(color1)
    color2_brush = QBrush(color2)
    no_pen = QPen(Qt.NoPen)
    def __init__(self, scene, eaten_before, eaten_this_week, table_low,
            table_high, table_eq):
        self.scene = scene
        self.eaten_before = eaten_before
        self.eaten_this_week = eaten_this_week
        self.table_low = table_low
        self.table_high = table_high
        self.table_eq = table_eq

    def draw(self):
        group_before = self.add_text("Eaten before but not this week:",
                self.eaten_before)
        group_now = self.add_text("Eaten this week but not week before:",
                self.eaten_this_week)
        #Bottom of previous text
        #group_now.setPos(0, group_before.boundingRect().height()+5)

        #Right of previous text
        group_now.setPos(group_before.boundingRect().width()+5, 0)

        y = max(group_before.boundingRect().height(),
                group_now.boundingRect().height())

        width = group_before.boundingRect().width() \
                +5+group_now.boundingRect().width()

        group_comp = self.add_chart("Lower then before:", self.table_low,
        False)
        group_comp.setPos(0, y)
        y+=group_comp.boundingRect().height()+5
        group_comp1 = self.add_chart("Higher then before:", self.table_high,
                False)
        group_comp1.setPos(0, y)
        y+=group_comp1.boundingRect().height()+5
        group_comp2 = self.add_chart("Same then before:", self.table_eq,
                True)
        group_comp2.setPos(0, y)




    def add_text(self, text, item_list):
        items = []
        text_item = QGraphicsTextItem(text)
        text_item.setFont(ComparisionChart.arial_font)
        text_item.setPos(0,0)
        items.append(text_item)
        next_y = text_item.boundingRect().height()+5

        html = "<br />".join(sorted(item_list))
        text_item = QGraphicsTextItem()
        text_item.setHtml(html)
        text_item.setFont(ComparisionChart.font)
        text_item.setPos(5,next_y)
        items.append(text_item)
        group = self.scene.createItemGroup(items)
        return group
        #return (text_item.boundingRec().width(),
                #text_item.boundingRect().height())
        
    def add_chart(self, text, data, eq=False):
        items = []
        text_item = QGraphicsTextItem(text)
        text_item.setFont(ComparisionChart.arial_font)
        text_item.setPos(0,0)
        items.append(text_item)
        next_y = text_item.boundingRect().height()+5

        item_max = 0
        before_max = len("before")
        after_max = len("after")

        def fmt_num(number):
            return "{:.2f}".format(number)
        def fmt_num_align(number, width):
            fmt = "{:^%d.2f}" % width
            return fmt.format(number)

        for item, before, after in data:
            item_max = max(item_max, len(item))
            before_max = max(before_max, len(fmt_num(before)))
            after_max = max(after_max, len(fmt_num(after)))

        before_larger = False
        if before > after:
            before_larger = True


        item_max_s= item_max*9
        before_max_s= before_max*9
        after_max_s= after_max*9

        full_size = before_max_s+5+after_max_s
        start_chart = item_max_s+5

        for item, before, after in data:
            if before_larger:
                large = before
                small = after
            else:
                large = after
                small = before

            if not eq:
                rect_item = QGraphicsRectItem()
                old_height = 0.8*text_item.boundingRect().height()
                rect_item.setRect(start_chart,next_y, full_size,
                        old_height)
                if before_larger:
                    rect_item.setBrush(ComparisionChart.color1_brush)
                else:
                    rect_item.setBrush(ComparisionChart.color2_brush)
                rect_item.setPen(ComparisionChart.no_pen)
                items.append(rect_item)

                rect_item = QGraphicsRectItem()
                new_height = 0.4*text_item.boundingRect().height()
                rect_item.setRect(start_chart,next_y+(old_height-new_height)/2,
                        full_size*(small/large),
                        new_height)
                if before_larger:
                    rect_item.setBrush(ComparisionChart.color2_brush)
                else:
                    rect_item.setBrush(ComparisionChart.color1_brush)
                rect_item.setPen(ComparisionChart.no_pen)
                items.append(rect_item)

            text_item = QGraphicsTextItem(item)
            text_item.setFont(ComparisionChart.font)
            text_item.setPos(0, next_y)
            items.append(text_item)
            
            text_item = QGraphicsTextItem(fmt_num_align(before, before_max))
            text_item.setFont(ComparisionChart.font)
            text_item.setPos(item_max_s, next_y)
            items.append(text_item)

            text_item = QGraphicsTextItem(fmt_num_align(after, after_max))
            text_item.setFont(ComparisionChart.font)
            text_item.setPos(item_max_s+5+before_max_s, next_y)
            items.append(text_item)

            next_y+=text_item.boundingRect().height()


        #barsets = [QBarSet("previous"), QBarSet("current")]
        #cats = []
        #for i, (item, before, now) in enumerate(data):
            #print (item, before, now)
            #barsets[1].append(before)
            #barsets[0].append(now)
            #cats.append(item)
        #axis_y = QBarCategoryAxis()
        #axis_y.append(cats)
        #barseries = QHorizontalBarSeries()
        #barseries.append(barsets)
        #chart = QChart()
        #chart.addSeries(barseries)
        #chart.setTitle(text)
        #chart.setAnimationOptions(QChart.SeriesAnimations)
        #chart.setAxisY(axis_y, barseries)
        #chart.setPos(0, next_y)
        #chart.setPreferredWidth(width)
        #chart.setPreferredHeight(500)
        ##chart.setSize(200,200)
        ##print ("SIZE:", chart.size().toSize().width(),
                ##chart.size().toSize().height())
        ##print ("CHART:", chart.boundingRect().width(),
                ##chart.boundingRect().height())
        #items.append(chart)

        group = self.scene.createItemGroup(items)
        return group
