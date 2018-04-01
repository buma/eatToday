import sys
import calendar
import csv
from itertools import groupby

from PyQt5 import QtGui
from PyQt5.QtCore import Qt,QCoreApplication
from PyQt5.QtWidgets import QGraphicsScene, QApplication
from PyQt5 import QtWidgets
from enum import Enum

#Color palete
from palettable.tableau import GreenOrange_6 as Palette
#Qt.qputenv("QT_QPA_PLATFORM", QByteArrayLiteral("minimal"));

imgx, imgy = (900,1500)
#imgx, imgy = (500,500)
grid_size = (20,20)

class FormatFunc(Enum):
    CIRCLE = 0
    BAR_CHART = 1

class SceneCalendar(calendar.Calendar):
    """This calendar renders scene"""

    def __init__(self, firstweekday=0, scene=None):
        self.scene = scene
        super().__init__(firstweekday)
        self.gray_pen = QtGui.QPen(QtGui.QColor(220, 220, 220, 128))
        self.no_pen = QtGui.QPen(Qt.NoPen)
        self.black_pen = QtGui.QPen(QtGui.QColor("black"))
        self.blue_t_brush = QtGui.QBrush(QtGui.QColor(0,170,255, 128))
        self.font = QtGui.QFont("sans-serif", 10)
        self.arial_font = QtGui.QFont("arial", 12)
        self.arial_font.setBold(True)
        self.height=50
        self.data_added = False
        self.make_colors()
        self.format_type = FormatFunc.BAR_CHART
        if self.format_type == FormatFunc.BAR_CHART:
            self.format_func = self.bar_chart
        elif self.format_type == FormatFunc.CIRCLE:
            self.format_func = self.circle_chart

    def make_colors(self):
        self.colors = []
        self.brushes = []
        alpha=128
        for rgb_color in Palette.colors:
            r,g,b = rgb_color
            qcolor = QtGui.QColor(r, g,b, alpha)
            self.colors.append(qcolor)
            self.brushes.append(QtGui.QBrush(qcolor))




    def add_legend(self):
        if not self.data_added:
            return 0
        for i, item in enumerate(self.items):
            #Name of item
            text_item = QtWidgets.QGraphicsTextItem(item)
            text_item.setFont(self.font)
            text_height = text_item.boundingRect().height()

            #Colored square at the start
            rect = QtWidgets.QGraphicsRectItem()
            rect.setRect(10, i*text_height, text_height*0.8, text_height*0.8)
            rect.setPen(self.no_pen)
            rect.setBrush(self.brushes[i])

            text_item.setPos(10+text_height*0.8+10, i*text_height)
            self.scene.addItem(text_item)
            self.scene.addItem(rect)
        return (i+1)*text_height


    def prmonth(self, theyear, themonth, w=0, l=0, withyear=True):
        """
        Print a month's calendar.
        """
        down = self.add_legend()
        group = self.formatmonth(theyear, themonth, w, l, withyear)

        group.setPos(0, down)

    def formatmonth(self, theyear, themonth, w=0, l=0, withyear=True):
        """
        Return a month's calendar string (multi-line).
        """
        self.year = theyear
        self.month = themonth
        items = []
        month_item = self.formatmonthname(theyear, themonth, w, withyear)
        week_header_items = self.formatweekheader(w)
        items.append(month_item)
        items.extend(week_header_items)
        for week in self.monthdays2calendar(theyear, themonth):
            week_items = self.formatweek(week, w)
            items.extend(week_items)
        month_group = self.scene.createItemGroup(items)
        return month_group

    def formatmonthname(self, theyear, themonth, width, withyear=True):
        """
        Return a formatted month name.
        """
        full_size = 7*width
        s = calendar.month_name[themonth]
        if withyear:
            s = "%s %r" % (s, theyear)
        text_item = QtWidgets.QGraphicsTextItem(s)
        text_item.setFont(self.arial_font)
        text_width = text_item.boundingRect().width()
        new_width=(0+full_size)/2
        text_item.setPos(new_width-text_width/2,
                text_item.boundingRect().height()/2)
        print ("FULL Width:{} TW:{}".format(full_size, text_width))
        print ("MONTH x:{} y:{}".format(text_item.pos().x(), text_item.pos().y()))

        #rect = QtWidgets.QGraphicsRectItem()
        #rect.setRect(self.imgx, self.imgy, full_size, 6*self.height)
        #self.scene.addItem(rect)

        #self.scene.addItem(text_item)
        self.next_y = text_item.boundingRect().height()+10
        return text_item

    def formatweekday(self, day, width):
        """
        Returns a formatted week day name.
        """
        if width >= 90:
            names = calendar.day_name
        else:
            names = calendar.day_abbr
        return names[day][:width]

    def formatweekheader(self, width):
        """
        Return a header for a week.
        """
        items = []
        for i in self.iterweekdays():
            wd = self.formatweekday(i, width)
            text_item = QtWidgets.QGraphicsTextItem(wd)
            text_item.setFont(self.arial_font)
            #text_item.setTextWidth(width)
            text_width = text_item.textWidth()
            new_width=(0+7*width)/2
            #print ("IW:", i*width, text_item.boundingRect().width())
            text_item.setPos(i*width+width/2-text_item.boundingRect().width()/2,
                    self.next_y)
            #print ("SW x:{} y:{} {}".format(text_item.pos().x(),
                #text_item.pos().y(), wd))
            #scene.addItem(text_item)
            items.append(text_item)
        self.next_y+=text_item.boundingRect().height()+10
        return items

    def formatday(self, day, weekday, width):
        """
        Returns a formatted day.
        """
        if day == 0:
            s = ''
        else:
            s = '%2i' % day             # right-align single-digit days
        return s.center(width)

    def formatweek(self, theweek, width):
        """
        Returns a single week in a string (no newline).
        """
        items = []
        for d, wd in theweek:
            fd = self.formatday(d, wd, width)
            if d != 0:
                #print (d, wd)
                rect = QtWidgets.QGraphicsRectItem()
                rect.setPen(self.black_pen)
                rect_x = wd*width
                rect_y = self.next_y
                rect.setRect(rect_x, rect_y, width, self.height)
                #self.scene.addItem(rect)
                items.append(rect)
                #Date:
                text_item = QtWidgets.QGraphicsTextItem(str(d))
                text_item.setFont(self.font)
                text_width = text_item.boundingRect().width()
                text_item.setPos(rect_x+width/2-text_width/2,
                        rect_y+self.height/2-text_item.boundingRect().height()/2)
                #self.scene.addItem(text_item)
                items.append(text_item)
                if self.data_added:
                    cur_items = self.format(d, rect, rect_x, rect_y, width)
                    if cur_items:
                        items.extend(cur_items)
        self.next_y+=self.height
        return items
        #print ("END")

    def bar_chart(self, datas, rect, x, y):
        """Draws bar chart in calendar box"""
        items = []
        boundingRect = rect.boundingRect()
        width = boundingRect.width()
        num_items = len(self.items)
        bar_width = 8
        left_right_padding = 2
        paddings_needed = max(num_items-1,1)
        padding = (width-2*left_right_padding-bar_width*num_items)/paddings_needed
        #Center one bar
        if num_items == 1:
            cur_x = x+(width/2)-bar_width/2
        else:
            cur_x = x+left_right_padding
        #print ("PADDING:", padding)
        #cur_x+=bar_width+padding
        for i, item in enumerate(self.items):
            transformed = datas.get(item, None)
            #print ("cur_x", cur_x)
            if transformed is not None:
                bar = QtWidgets.QGraphicsRectItem(rect)
                bar.setBrush(self.brushes[i])
                bar.setPen(self.no_pen)
                bar_height = transformed*boundingRect.height()
                bar.setRect(cur_x, y+(boundingRect.height()-bar_height), bar_width,
                        bar_height)
                items.append(bar)
            cur_x+=bar_width+padding
        return items

    def circle_chart(self, datas, rect, x, y):
        """Draws a circle in a center of a chart. Size depends on value"""
        if len(self.items) > 1:
            raise Exception("Circle formatting is only supported for one item")
        transformed = datas[self.items[0]]
        #print ("{}-{}-{}".format(self.year, self.month, day), has_data)
        #print ("X: {} Y:{}".format(x, y))
        boundingRect = rect.boundingRect()
        allowed_max = min(boundingRect.width(), boundingRect.height())*0.9
        new_size = allowed_max*transformed

        item = QtWidgets.QGraphicsEllipseItem()
        item.setPen(self.no_pen)
        item.setBrush(self.brushes[0])
        item.setRect(x+boundingRect.width()/2-new_size/2,
                y+self.height/2-new_size/2, new_size, new_size)
        #print ("CIRC: x:{} y:{}".format(item.pos().x(), item.pos().y()))
        return [item]

    def format(self, day, rect, x, y, width):
        #TODO: do this with dates not strings
        #FIXME: position better
        has_data = self.hash.get("{}-{:02d}-{:02d}".format(self.year, self.month, day),
                False)
        if not has_data:
            return None

        return self.format_func(has_data,rect, x, y)



    def add_data(self, items, hash):
        self.items = items
        self.hash = hash
        self.data_added = True
        if len(items) > Palette.number:
            raise Exception(
                    "Curently no more then {} colors are supported".format(
                        Palette.number))
        #Groups by year and month so that only some months can be shown
        self.specific_months=[]
        for key,g in groupby(self.hash.keys(), lambda x:
                x.split("-")[:2]):
            #print (key)
            year, month = key
            self.specific_months.append((int(year), int(month)))


    def formatyear(self, theyear, w=2, l=1, c=6, m=3):
        """
        Returns a year's calendar as a multi-line string.
        """
        y_add = self.add_legend()
        #print ("YADD:", y_add)
        self.padding=10
        #Size of month 7*days*number of month columns
        full_size=7*w*m
        left_right_padding = 10
        padding = (self.scene.width()-2*left_right_padding-full_size)/(m-1)
        print ("FULL:", full_size, padding)
        if theyear is None:
            year = "Delno"
        else:
            year = theyear
        text_item = QtWidgets.QGraphicsTextItem(str(year))
        text_item.setFont(self.arial_font)
        text_width = text_item.boundingRect().width()
        text_item.setPos(self.scene.width()/2-text_width/2,
                y_add)
        self.scene.addItem(text_item)
        line = 0
        #line_height = 0
        if theyear is None:
            num_months = len(self.specific_months)
        else:
            num_months = 12
        for i in range(0, num_months):
            if i%m == 0:
                line+=1
                #line_height = 0
            print (i+1, line)
            if theyear is None:
                year, month = self.specific_months[i]
                group = self.formatmonth(year, month, w, l, withyear=True)
            else:
                group = self.formatmonth(theyear, i+1, w, l, withyear=False)
            #line_height = max(line_height, group.boundingRect().height())
            group.setPos(left_right_padding+i%m*7*w+i%m*padding,
                    (line-1)*(6*self.height+80)+10+y_add)

if __name__ == "__main__":
    #app = QCoreApplication(sys.argv)
    app = QApplication(sys.argv)

    scene = QGraphicsScene(0,0, imgx,imgy, app)
    print ("scene")
    gray_pen = QtGui.QPen(QtGui.QColor(220, 220, 220, 128))
    black_pen = QtGui.QPen(QtGui.QColor("black"))
    font = QtGui.QFont("sans-serif", 10)


    #for x_grid in range(0, imgx, grid_size[0]):
        #scene.addLine(x_grid,0, x_grid, imgy, gray_pen)
    #for y_grid in range(0, imgy, grid_size[1]):
        #scene.addLine(0, y_grid, imgx, y_grid, gray_pen)

    def month(month):
        cal = calendar.monthcalendar(2018,3)
        text_item = QtWidgets.QGraphicsTextItem(month)
        text_item.setFont(font)
        text_item.setPos(imgx-text_item.boundingRect().width()/2,
                text_item.boundingRect().height()/2)
        scene.addItem(text_item)
        line=-1
        for i in range(30):
            if i%7==0:
                line+=1
            print (i,i%7,line)


    #month("Januar")
    mm = SceneCalendar(scene=scene)
    w=35
    l=1
    year=2017
    month=3
    mm.height=w
    #print(mm.formatmonthname(year,month,w))
    #print (mm.formatweekheader(w))
    #mm.prmonth(year,month,w=w, l=l)

    with open("./tags_sadje.csv", "r") as f:
        data = csv.DictReader(f)
        hash = {}
        min_sum=500000
        max_sum=0
        for line in data:
            ws = float(line["weight_sum"])
            hash[line["date"]]={"Sadje":ws}
            min_sum=min(min_sum, ws)
            max_sum=max(max_sum, ws)
        for values in hash.values():
            for item, weight in values.items():
                min_val = min_sum
                max_val = max_sum
                values[item]=(weight-min_val)/(max_val-min_val)

        mm.add_data(["Sadje"], hash)
    mm.formatyear(year,w=w, l=l)
    #mm.formatmonth(2017, 10, w)


    fname="test.png"
    image = QtGui.QImage(imgx, imgy,
            QtGui.QImage.Format_ARGB32)
    painter = QtGui.QPainter(image)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    scene.render(painter)
    image.save(fname)
