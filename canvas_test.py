import sys
import calendar
import csv

from PyQt5 import QtGui
from PyQt5.QtCore import Qt,QCoreApplication
from PyQt5.QtWidgets import QGraphicsScene, QApplication
from PyQt5 import QtWidgets

#Qt.qputenv("QT_QPA_PLATFORM", QByteArrayLiteral("minimal"));

imgx, imgy = (900,1500)
#imgx, imgy = (500,500)
grid_size = (20,20)

class SceneCalendar(calendar.Calendar):
    """This calendar renders scene"""

    def __init__(self, firstweekday=0, scene=None):
        self.scene = scene
        super().__init__(firstweekday)
        self.gray_pen = QtGui.QPen(QtGui.QColor(220, 220, 220, 128))
        self.black_pen = QtGui.QPen(QtGui.QColor("black"))
        self.blue_t_brush = QtGui.QBrush(QtGui.QColor(0,170,255, 128))
        self.font = QtGui.QFont("sans-serif", 10)
        self.arial_font = QtGui.QFont("arial", 12)
        self.arial_font.setBold(True)
        self.height=50
        self.data_added = False

    def prmonth(self, theyear, themonth, w=0, l=0):
        """
        Print a month's calendar.
        """
        print(self.formatmonth(theyear, themonth, w, l), end='')

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
                    item = self.format(d, rect, rect_x, rect_y, width)
                    if item:
                        items.append(item)
        self.next_y+=self.height
        return items
        #print ("END")

    def format(self, day, rect, x, y, width):
        #TODO: do this with dates not strings
        #FIXME: position better
        has_data = self.hash.get("{}-{:02d}-{:02d}".format(self.year, self.month, day),
                False)
        if not has_data:
            return None
        #FIXME: temporary hack so that only one hash is used
        has_data = has_data.get(self.items[0], None) 
        if not has_data:
            return None

        #print ("{}-{}-{}".format(self.year, self.month, day), has_data)
        #print ("X: {} Y:{}".format(x, y))
        boundingRect = rect.boundingRect()
        transformed = has_data
        allowed_max = min(boundingRect.width(), boundingRect.height())*0.9
        new_size = allowed_max*transformed

        item = QtWidgets.QGraphicsEllipseItem()
        item.setPen(self.gray_pen)
        item.setBrush(self.blue_t_brush)
        item.setRect(x+width/2-new_size/2,
                y+self.height/2-new_size/2, new_size, new_size)
        #print ("CIRC: x:{} y:{}".format(item.pos().x(), item.pos().y()))
        return item


    def add_data(self, items, hash):
        self.items = items
        self.hash = hash
        self.data_added = True

    def formatyear(self, theyear, w=2, l=1, c=6, m=3):
        """
        Returns a year's calendar as a multi-line string.
        """
        self.padding=10
        #Size of month 7*days*number of month columns
        full_size=7*w*m
        left_right_padding = 10
        padding = (self.scene.width()-2*left_right_padding-full_size)/(m-1)
        print ("FULL:", full_size, padding)
        text_item = QtWidgets.QGraphicsTextItem(str(theyear))
        text_item.setFont(self.arial_font)
        text_width = text_item.boundingRect().width()
        text_item.setPos(self.scene.width()/2-text_width/2,
                0)
        self.scene.addItem(text_item)
        line = 0
        #line_height = 0
        for i in range(0, 12):
            if i%m == 0:
                line+=1
                #line_height = 0
            print (i+1, line)
            group = self.formatmonth(theyear, i+1, w, l, withyear=False)
            #line_height = max(line_height, group.boundingRect().height())
            group.setPos(left_right_padding+i%m*7*w+i%m*padding,
                    (line-1)*(6*self.height+80)+10)

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
