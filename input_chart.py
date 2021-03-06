from datetime import datetime
import dateutil.relativedelta
import sqlalchemy as sa
from dateutil.rrule import rrule, HOURLY, DAILY
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import func
from PyQt5.QtCore import *                                                                                                                                       
from PyQt5.QtGui import QPainter
from PyQt5.QtChart import (
        QChart, QChartView, QDateTimeAxis, QLineSeries,
QValueAxis, QBarSet, QBarSeries, QBarCategoryAxis, QStackedBarSeries,
QPercentBarSeries, QSplineSeries)
from database import (
        Item, LocalNutrition, LocalNutritionaliase, FoodNutrition,
        Tag, TagItem, UsdaWeight)
from config import (needed_kcal, needed_protein)
from chart_dialog import ChartDialog

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

#TODO k=5/2 n=-1050
#water = k*(hour*60)+n se dobi kolko vode se more spit

def init_chart(self):
    print ("Initialazing")
    self.de_chart.setMaximumDate(QDate.currentDate())
    self.de_chart.setDateTime(QDateTime.currentDateTime())
    limits = {
            "calcium": 1000,
            "iron":8,
            "magnesium":400,
            "potassium": 4700,
            "sodium": 1500,
            "phosphorus": 700,
            "zinc":11,

            "vitaminc":90,
            "vitk":120,
            "vite":15,
            "vitaminb6":1,
            "vitb12":2,
            "thiamin":1
            }
    self.idx_kcal = [
            ("Macronutrients", "Macronutrients from {} to {}",
        #Dictionary where key is what we want to chart from foodnutrition and
        #value is description to show in legend
                {
                "carb": "Oglj. hidrati",
                "lipid": "Maščobe",
                "protein": "Beljakovine",
                "sugar": "Sladkor",
                "fiber": "Vlaknine",
                "fasat": "Nasičene maščobe",
                },
                lambda nutrient, x: x,
                QBarSeries,
                "%.2f g"
                ),
            ("Micronutrients", "Micronutrients from {} to {}",
                {
                    "calcium": "Kalcij",
                    "iron": "Železo",
                    "magnesium": "Magnezij",
                    "potassium": "Kalij",
                    "sodium": "Natrij",
                    "phosphorus": "Fosfor",
                    "zinc": "Zinc"
                    },
                lambda nutrient, x: x,
                QBarSeries,
                "%.2f mg"
                ),
            ("Micronutrients in % RDA", "Micronutrients in % from RDA from {} to {}",
                {
                    "calcium": "Kalcij",
                    "iron": "Železo",
                    "magnesium": "Magnezij",
                    "potassium": "Kalij",
                    "sodium": "Natrij",
                    "phosphorus": "Fosfor",
                    "zinc": "Zinc"
                    },
                lambda nutrient, x: x/limits[nutrient]*100,
                QBarSeries,
                "%d %%"
                ),
            ("Vitamins", "Vitamins from {} to {}",
                {
                    "vitaminc": "Vitamin C",
                    "vitaminb6": "Vitamin B6",
                    "vitb12": "Vitamin B12",
                    "thiamin": "Thiamin",
                    "vite": "Vitamin E",
                    "vitk": "Vitamin K"
                    },
                lambda nutrient, x: x,
                QBarSeries,
                "%.2f mg"
                ),
            ("Vitamins in % RDA", "Vitamins in % from RDA from {} to {}",
                {
                    "vitaminc": "Vitamin C",
                    "vitaminb6": "Vitamin B6",
                    "vitb12": "Vitamin B12",
                    "thiamin": "Thiamin",
                    "vite": "Vitamin E",
                    "vitk": "Vitamin K"
                    },
                lambda nutrient, x: x/limits[nutrient]*100,
                QBarSeries,
                "%.2f %%"
                ),
            ("Macronutrients kcal", "Macronutrients in kcal from {} to {}",
                {
                "protein": "Beljakovine",
                "lipid": "Maščobe",
                "carb": "Oglj. hidrati",
                },
                lambda nutrient, value: value*4 if nutrient=="carb" or \
                nutrient=="protein" else value*9,
                QStackedBarSeries,
                "%.2f kcal"
                ),
            ("Macronutrients kcal %", "Macronutrients in % of kcal from {} to {}",
                {
                "protein": "Beljakovine",
                "lipid": "Maščobe",
                "carb": "Oglj. hidrati",
                },
                lambda nutrient, value: value*4 if nutrient=="carb" or \
                nutrient=="protein" else value*9,
                QPercentBarSeries,
                "%d %"
                ),
            ("Macronutrients line", "Macronutrients from {} to {}",
        #Dictionary where key is what we want to chart from foodnutrition and
        #value is description to show in legend
                {
                "carb": "Oglj. hidrati",
                "lipid": "Maščobe",
                "protein": "Beljakovine",
                "sugar": "Sladkor",
                "fiber": "Vlaknine",
                "fasat": "Nasičene maščobe",
                },
                lambda nutrient, x: x,
                QLineSeries,
                "%.2f g"
                ),
            ]
    self.cb_kcal_chart_type.addItems([
        x[0] for x in self.idx_kcal
        ])

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
        from config import (
                needed_protein_2_hours_till_lunch,
                needed_kcal_2_hours_till_lunch,
                lunch_kcal, lunch_protein, needed_kcal_2_hours_after_lunch,
                needed_protein_2_hours_after_lunch)
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
        self.init_kcal_week_chart(date, self.cb_kcal_chart_type.currentIndex())
        
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

        #Adds current date time as last item in series to see on graph where we
        #are now
        kcal_series.append(QDateTime.currentDateTime().toMSecsSinceEpoch(), sum_kcal)
        protein_series.append(QDateTime.currentDateTime().toMSecsSinceEpoch(), sum_protein)
        water_series.append(QDateTime.currentDateTime().toMSecsSinceEpoch(), sum_water)

            #print (sum_kcal, sum_protein)
        kcal_y.setMax(max(needed_kcal, sum_kcal))
        protein_y.setMax(max(needed_protein, sum_protein))
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
    self.chartView_water.setRenderHint(QPainter.Antialiasing)
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

    def init_kcal_week_chart(today, chart_idx_type):
        today_o = today.toPyDateTime().date()
        today = (today_o+dateutil.relativedelta.relativedelta(days=1))
        last_week = (today+dateutil.relativedelta.relativedelta(days=-7))

        print (last_week, "-", today)
        chart_data = self.idx_kcal[chart_idx_type]
        self.chartView_kcal.chart() \
                .setTitle(chart_data[1].format(last_week.strftime("%a %d. %b"),
                    today_o.strftime("%a %d. %b")))
        keys = chart_data[2]
        sets = {}
        entities = [sa.func.strftime("%Y-%m-%d",Item.time).label("day")]

        is_barchart = True
        if isinstance(chart_data[4](), QLineSeries):
            is_barchart = False

        #print ("BARCHART:", is_barchart, chart_data[4], QLineSeries)

#Creates barsets where each barset is one value in foodnutrition
#Each value in barset is different day
#Also creates sqlalchemy sum select
        func_multiplay = chart_data[3]
        for nutrition, nutrition_name in keys.items():
            if is_barchart:
                sets[nutrition] = QBarSet(nutrition_name)
            else:
                sets[nutrition] = chart_data[4]()
                sets[nutrition].setName(nutrition_name)
            entities.append(
                    sa.func.sum(func_multiplay(nutrition,getattr(FoodNutrition,
                        nutrition))) \
                            .label(nutrition))



#Query which select all foodnutrition between last_week and today and sums it
#up grouped by day
        items = \
        sa.orm.query.Query(entities, session=self.session) \
                .join(FoodNutrition) \
                .filter(Item.time.between(last_week, today)) \
                .group_by("day") \
                .order_by(Item.time)
        #print (items)
        #print (items.column_descriptions)
        #items.column_descriptions
#je list z dictinariy kjer je key name pove imena columnov
        for item in items:
            #print ("ITEM:", item)
            if not is_barchart:
                tm = item.day
                dt = dateutil.parser.parse(tm)
                en = int(dt.timestamp()*1000)
            for key, bar_set in sets.items():
                if key in item.keys():
                    if is_barchart:
                        bar_set.append(getattr(item, key))
                    else:
                        #print (bar_set.name(), en, getattr(item, key))
                        bar_set.append(en, getattr(item,key))
                else:
                    if is_barchart:
                        bar_set.append(0)
                    else:
                        bar_set.append(en, 0)

        #print ("SETS:", sets)
        if is_barchart:
            bar_series = chart_data[4]()
            for value in sets.values():
                bar_series.append(value)
            #Creates x axis with dates
            string_dates = []
            for date in rrule(DAILY, last_week, count=7):
                string_dates.append(date.strftime("%a %d. %b"))
            axis = QBarCategoryAxis()
            axis.append(string_dates)
        else:
            axis = QDateTimeAxis()
            axis.setFormat("d. M. yyyy")
            #Sets date ticks as many as we want to show dates
            axis.setTickCount(list(sets.values())[0].count())
            axis_y = QValueAxis()
            axis_y.setLabelFormat(chart_data[5])
            axis_y.setTickCount(10)

        chart = self.chartView_kcal.chart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.removeAllSeries()
        for cur_axis in chart.axes():
            chart.removeAxis(cur_axis)
        if is_barchart:
            chart.addSeries(bar_series)
        else:
            self.chartView_kcal.setRenderHint(QPainter.Antialiasing)
            chart.addAxis(axis, Qt.AlignBottom)
            chart.addAxis(axis_y, Qt.AlignLeft)
            for series in sets.values():
                #print ("SERIES:", series.name())
                chart.addSeries(series)
                series.attachAxis(axis)
                series.attachAxis(axis_y)
            axis_y.setRange(0, 150)
            #chart.setAxisX(axis, series)
            #chart.setAxisY(axis_y, series)

        if is_barchart:
            chart.createDefaultAxes()
            chart.setAxisX(axis, bar_series)
            chart.axisY(bar_series).setLabelFormat(chart_data[5])
            chart.axisY(bar_series).setTickCount(10)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)

    def show_daily_chart():
        today = self.de_chart.dateTime().toPyDateTime().date()
        tomorow = today+dateutil.relativedelta.relativedelta(hour=23,minute=59,second=0)
        title, chart_title, data, func, *rest  = self.idx_kcal[self.cb_kcal_chart_type.currentIndex()]
        print ("Daily chart:", today, tomorow, title)
        item_datas = []
        items = self.session.query(Item) \
                .options(joinedload(Item.nutri_info)) \
                .filter(Item.calc_nutrition != None) \
                .filter(Item.time.between(today, tomorow)) \
                .order_by(Item.time)
        keys = list(data.keys())
        for item in items:
            item_data = [item.time, item.description[:20]]
            for key in keys:
                #print ("KEY:", key)
                item_data.append(func(key,getattr(item.nutri_info, key)))
            item_datas.append(item_data)
        header = ["time", "desc"] + keys
        #for time, desc, *rest in item_datas:
            #print (time, desc,)
            #for t in rest:
                #print("{:.2f}".format(t))
        cd = ChartDialog(self)
        cd.set_day_chart(header, today, chart_title, item_datas)
        cd.show()


    self.chart_date_changed = chart_date_changed
    self.init_kcal_week_chart = init_kcal_week_chart

    self.de_chart.dateTimeChanged.connect(self.chart_date_changed)
    self.chart_date_changed(self.de_chart.dateTime())
    self.cb_kcal_chart_type.currentIndexChanged.connect(lambda idx:
            self.init_kcal_week_chart(self.de_chart.dateTime(), idx))
    self.pb_show_day_chart.clicked.connect(show_daily_chart)
    #today = self.de_chart.selecte


