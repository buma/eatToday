from datetime import datetime
import dateutil.relativedelta
from dateutil.rrule import rrule, HOURLY
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import func
from PyQt5.QtCore import *                                                                                                                                       
from PyQt5.QtGui import QPainter
from PyQt5.QtChart import (
        QChart, QChartView, QDateTimeAxis, QLineSeries,
QValueAxis)
from database import (
        Item, LocalNutrition, LocalNutritionaliase, FoodNutrition,
        Tag, TagItem, UsdaWeight)

def to_qdate(date, add=0):
    """Creates QDateTime from pytho date

    Parameters:
        date - Python datetime
        add - hours to add (default 0)

    Returns: QDateTime
    """
    qt_date = QDateTime()
    qt_date.setSecsSinceEpoch(date.timestamp()+add*3600)
    return qt_date

def init_chart(self):
    print ("Initialazing")
    self.de_chart.setMaximumDate(QDate.currentDate())
    self.de_chart.setDateTime(QDateTime.currentDateTime())

    series = []
    series2 = []
    axisX = None
    axisX2 = None
    protein_y = None
    kcal_y = None
    water_y = None

    def default_values(today):
        """
        Calculates default values for kcal and protein

        KCAL:
        Based on 2200 kcal. 1300 should be consumed before lunch.

        Protein is similar
        """
        #TODO: join this values calculation with display
        needed_kcal = 2200
        needed_kcal_lunch = 1300
        lunch_kcal=500
        diff = 0
        needed_kcal_2_hours_till_lunch=(needed_kcal_lunch)/(8/2) 
        needed_kcal_2_hours_after_lunch=(needed_kcal-4*needed_kcal_2_hours_till_lunch-lunch_kcal)/2
        needed_protein = 99
        lunch_protein = 23
        needed_protein_2_hours_till_lunch = 14.625
        needed_protein_2_hours_after_lunch = 8.75
        ds = datetime(today.year,today.month,today.day,7)
        now = datetime.today()
        print (now)
        qt_now = to_qdate(now)
        print (qt_now)
        default_series = QLineSeries()
        default_series.setName("default kcal")

        protein_series = QLineSeries()
        protein_series.setName("default protein")
        #default_series.setUseOpenGL(True)

        water_series = QLineSeries()
        water_series.setName("default voda")
        sum_kcal = 0 
        sum_protein = 0 
        sum_water = 0
        for date in rrule(HOURLY, ds, 2, count=8):
            qdate = to_qdate(date)
            #print (date, qdate, date.timestamp()*1000, qdate.toMSecsSinceEpoch())
            date_msec = int(date.timestamp()*1000)
            default_series.append(date_msec, sum_kcal)
            protein_series.append(date_msec, sum_protein)
            water_series.append(date_msec, sum_water)

            #print (sum_kcal)
            if date.hour < 15:
                sum_kcal+=needed_kcal_2_hours_till_lunch
                sum_protein+=needed_protein_2_hours_till_lunch
            elif date.hour == 15:
                sum_kcal+=lunch_kcal
                sum_protein+=lunch_protein
            else:
                sum_kcal += needed_kcal_2_hours_after_lunch
                sum_protein += needed_protein_2_hours_after_lunch
            sum_water += 300
        #print (sum_kcal)
        return default_series, protein_series, water_series

    def chart_date_changed(date):
        """
        Updates chart with selected date

        It also needs to update axis x and set range on it
        """
        #print(date)
        today = date.toPyDateTime().date()
        #today = datetime(today.year, today.month, today.day)
        tomorow = (today+dateutil.relativedelta.relativedelta(days=1))
        print (today, "-", tomorow)
# Joinedload loads stuff in one query instead of multiple ones
        #def query(start, end):
                    ##func.sum(FoodNutrition.kcal).label("kcal_sum"),
                    ##func.sum(FoodNutrition.protein).label("protein_sum")) \
            #items = self.session.query(
                    #FoodNutrition.kcal, FoodNutrition.protein) \
                            #.join(Item) \
                    #.filter(Item.time.between(start, end)) 
                    ##.filter(Item.calc_nutrition != None) \
                    ##.group_by(True) 
                    ##.order_by(Item.time)
                    ##.filter(FoodNutrition.id==Item.calc_nutrition) \
            #return items
        #today_date = today.date()
        #ds =datetime(today.date().year,today.date().month,today.date().day,9)
        #for date in rrule(HOURLY, ds, 2, count=8):
            #items = query(today, date)
            #for item in items:
                #print(item)
        items = self.session.query(Item) \
                .options(joinedload(Item.nutri_info)) \
                .filter(Item.calc_nutrition != None) \
                .filter(Item.time.between(today, tomorow)) \
                .order_by(Item.time)
        kcal_series = QLineSeries()
        kcal_series.setName("kcal")

        protein_series = QLineSeries()
        protein_series.setName("protein")

        water_series = QLineSeries()
        water_series.setName("water")
        sum_kcal = 0
        sum_protein = 0
        sum_water = 0
# Calculates sum of kcal and protein
        for item in items:
            #print (item.description, item.nutri_info.kcal, item.nutri_info.protein)
            sum_kcal+=item.nutri_info.kcal
            sum_protein+=item.nutri_info.protein
            sum_water+=item.nutri_info.water
            kcal_series.append(int(item.time.timestamp()*1000), sum_kcal)
            protein_series.append((item.time.timestamp()*1000), sum_protein)
            water_series.append((item.time.timestamp()*1000), sum_water)

            #print (sum_kcal, sum_protein)
        kcal_y.setMax(max(2200, sum_kcal))
        protein_y.setMax(max(99, sum_protein))
        water_y.setMax(max(2100, sum_water))
        #print ("BEFORE CHANGE:")
        #print (axisX.min(), axisX.max())
        #print (datetime.fromtimestamp(default_kcal_s.at(0).x()/1000))
#Updates X axis so current datetime is used
        ds = datetime(today.year,today.month,today.day,7)
        for idx, date in enumerate(rrule(HOURLY, ds, 2, count=8)):
            point = default_kcal_s.at(idx)
            default_kcal_s.replace(idx, int(date.timestamp()*1000), point.y())
            default_protein_s.replace(idx, int(date.timestamp()*1000),
                    default_protein_s.at(idx).y())
            default_water_s.replace(idx, int(date.timestamp()*1000),
                    default_water_s.at(idx).y())
        #print ("AFTER")
#Currently x axis is from current date (input of this function) + 15 hours
        axisX.setRange(to_qdate(ds), to_qdate(ds,15))
        axisX2.setRange(to_qdate(ds), to_qdate(ds,15))
        #print (axisX.min(), axisX.max())
        #print (datetime.fromtimestamp(default_kcal_s.at(0).x()/1000))
            #print (point.x(), point.y())
            #print (idx, date, datetime.fromtimestamp(point.x()/1000), point.y())


        chart = self.chartView_bar.chart()
        for serie in series:
            chart.removeSeries(serie)
        series.clear()
        series.append(kcal_series)
        series.append(protein_series)
        chart.addSeries(kcal_series)
        kcal_series.attachAxis(axisX)
        kcal_series.attachAxis(kcal_y)
        chart.addSeries(protein_series)
        protein_series.attachAxis(axisX)
        protein_series.attachAxis(protein_y)

        chart2 = self.chartView_water.chart()
        for serie in series2:
            chart2.removeSeries(serie)
        series2.clear()
        series2.append(water_series)

        chart2.addSeries(water_series)
        water_series.attachAxis(axisX2)
        water_series.attachAxis(water_y)
        #print(kcal_series)

    default_kcal_s, default_protein_s, default_water_s = default_values(datetime.today().date())
    #self.chartView_bar.chart().removeAllSeries()
    self.chartView_bar.setRenderHint(QPainter.Antialiasing)
    chart = self.chartView_bar.chart()
#Sets X Axis
    axisX = QDateTimeAxis()
    axisX.setFormat("h:mm")
    self.chartView_bar.chart().addAxis(axisX, Qt.AlignBottom)
    self.chartView_bar.chart().addSeries(default_kcal_s)
#Sets kcal axis
    kcal_y = QValueAxis()
    kcal_y.setLinePenColor(default_kcal_s.pen().color())
    kcal_y.setLabelFormat("%.2f kcal")
    chart.addAxis(kcal_y, Qt.AlignLeft)
    default_kcal_s.attachAxis(axisX)
    default_kcal_s.attachAxis(kcal_y)

    chart.addSeries(default_protein_s)
#Sets protein axis
    protein_y = QValueAxis()
    protein_y.setLinePenColor(default_protein_s.pen().color())
    protein_y.setLabelFormat("%.2f g")
    #protein_y.setGridLinePen((default_protein_s.pen()))

    chart.addAxis(protein_y, Qt.AlignRight)
    default_protein_s.attachAxis(axisX)
    default_protein_s.attachAxis(protein_y)

    chart2 = self.chartView_water.chart()
#Sets X Axis
    axisX2 = QDateTimeAxis()
    axisX2.setFormat("h:mm")

    chart2.addSeries(default_water_s)
    water_y = QValueAxis()
    water_y.setLinePenColor(default_water_s.pen().color())
    water_y.setLabelFormat("%.2f g")
    chart2.addAxis(water_y, Qt.AlignLeft)
    chart2.addAxis(axisX2, Qt.AlignBottom)
    default_water_s.attachAxis(axisX2)
    default_water_s.attachAxis(water_y)



    self.chart_date_changed = chart_date_changed

    self.de_chart.dateTimeChanged.connect(self.chart_date_changed)
    self.chart_date_changed(self.de_chart.dateTime())
    #today = self.de_chart.selecte

