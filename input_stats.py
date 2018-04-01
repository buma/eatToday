import dateutil.relativedelta
from collections import defaultdict
from tabulate import tabulate
from util import TimeSpan, StatType
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QDialogButtonBox
from chart_dialog import ChartDialog

from PyQt5.QtWidgets import (
        QCompleter,
        QMessageBox,
        )
from PyQt5.QtSql import (
        QSqlRelation,
        QSqlRelationalTableModel,
        QSqlTableModel,
        QSqlQueryModel,
        QSqlQuery
        )

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

LAST_MONDAY = dateutil.relativedelta.relativedelta(
        weekday=dateutil.relativedelta.MO(-1))
tags_specific_query = """
SELECT tag.name AS tag_name, sum(foodnutrition_details.weight * 100) AS weight_sum,
strftime('%Y-%m-%d', eat.time)
FROM tag, foodnutrition_details, eat, nutritionaliases, tag_item
WHERE eat.time BETWEEN :start AND :end AND foodnutrition_details.ndbno =
nutritionaliases.ndbno AND foodnutrition_details.fn_id = eat.calc_nutrition AND
foodnutrition_details.ndbno = tag_item.ndbno AND tag.id = tag_item.tag_id
AND tag.name IN (:ITEMS:)
GROUP BY strftime('%Y-%m-%d', eat.time), tag.id
ORDER BY eat.time
"""

ingkeys_specific_query = """
SELECT foodnutrition_details_alias_time.nutritionaliases_ingkey AS ingkey, sum(foodnutrition_details_alias_time.foodnutrition_details_weight * 100) AS weight_sum,
strftime('%Y-%m-%d', foodnutrition_details_alias_time.eat_time) as s
FROM foodnutrition_details_alias_time
WHERE foodnutrition_details_alias_time.eat_time BETWEEN :start AND :end
 AND foodnutrition_details_alias_time.nutritionaliases_ingkey IN (:ITEMS:)
 GROUP BY strftime('%Y-%m-%d', foodnutrition_details_alias_time.eat_time), foodnutrition_details_alias_time.foodnutrition_details_ndbno
 ORDER BY foodnutrition_details_alias_time.eat_time
"""

food_tags_specific = """
    SELECT food_tag.name AS tag_name, sum(foodnutrition_details.weight * 100)
    AS weight_sum,
strftime('%Y-%m-%d', eat.time),
    count(DISTINCT eat.id) AS tag_app
FROM food_tag, foodnutrition_details, eat, food_tag_item
WHERE eat.time BETWEEN :start AND :end AND  foodnutrition_details.fn_id = eat.calc_nutrition AND
foodnutrition_details.fn_id = food_tag_item.fn_id
AND food_tag_item.tag_id = food_tag.id
AND food_tag_item.checked = 1
AND food_tag.name IN (:ITEMS:)
GROUP BY strftime('%Y-%m-%d', eat.time), food_tag.id
ORDER BY eat.time
 """

graph_queries = {
        StatType.TAGS: tags_specific_query,
        StatType.INGKEY: ingkeys_specific_query,
        StatType.FOOD_TAGS: food_tags_specific
        }


def init_stats(self):
    print("init stats")
    queries = {}
#Banana weight is from average weight of one banana
#Egg also
    INGKEY_SQL = """
            SELECT foodnutrition_details_alias_time.nutritionaliases_ingkey AS
            ingkey,
            sum(foodnutrition_details_alias_time.foodnutrition_details_weight * 100) AS weight_sum,
            sum(foodnutrition_details_alias_time.foodnutrition_details_weight * 100)/
            CASE foodnutrition_details_alias_time.nutritionaliases_ingkey WHEN "EGG" THEN 62
            WHEN "BANANA" THEN 173
            ELSE nutrition.package_weight
            END   AS num_items,
            nutrition.package_weight AS nutrition_package_weight
    FROM foodnutrition_details_alias_time, nutrition
    WHERE foodnutrition_details_alias_time.eat_time BETWEEN :start AND :end AND
    nutrition.ndbno = foodnutrition_details_alias_time.foodnutrition_details_ndbno
    GROUP BY foodnutrition_details_alias_time.foodnutrition_details_ndbno ORDER BY
    weight_sum DESC
    """
    GET_INGKEY_QUERY = QSqlQuery()
    GET_INGKEY_QUERY.prepare(INGKEY_SQL)
    GET_INGKEY_QUERY1 = QSqlQuery()
    GET_INGKEY_QUERY1.prepare(INGKEY_SQL)

    tags_sql = """
    SELECT tag.name AS tag_name, sum(foodnutrition_details.weight * 100) AS weight_sum, count(tag.id) AS tag_app
FROM tag, foodnutrition_details, eat, nutritionaliases, tag_item
WHERE eat.time BETWEEN :start AND :end AND foodnutrition_details.ndbno =
nutritionaliases.ndbno AND foodnutrition_details.fn_id = eat.calc_nutrition AND
foodnutrition_details.ndbno = tag_item.ndbno AND tag.id = tag_item.tag_id GROUP
BY tag.id ORDER BY weight_sum DESC
    """


    tags_query = QSqlQuery()
    tags_query.prepare(tags_sql)
    tags_query1 = QSqlQuery()
    tags_query1.prepare(tags_sql)

    food_tags_sql = """
    SELECT food_tag.name AS tag_name, sum(foodnutrition_details.weight * 100)
    AS weight_sum, count(DISTINCT eat.id) AS tag_app
FROM food_tag, foodnutrition_details, eat, food_tag_item
WHERE eat.time BETWEEN :start AND :end AND  foodnutrition_details.fn_id = eat.calc_nutrition AND
foodnutrition_details.fn_id = food_tag_item.fn_id
AND food_tag_item.tag_id = food_tag.id
AND food_tag_item.checked = 1
 GROUP BY food_tag.id ORDER BY weight_sum DESC
 """

    food_tags_query = QSqlQuery()
    food_tags_query.prepare(food_tags_sql)
    food_tags_query1 = QSqlQuery()
    food_tags_query1.prepare(food_tags_sql)

    queries[StatType.INGKEY]=(GET_INGKEY_QUERY, GET_INGKEY_QUERY1)
    queries[StatType.TAGS] = (tags_query, tags_query1)
    queries[StatType.FOOD_TAGS] = (food_tags_query, food_tags_query1)
    left_model = QSqlQueryModel()
    right_model = QSqlQueryModel()
    self.tv_stats.setModel(left_model)
    self.tv_stats_right.setModel(right_model)
    self.tv_stats.setSortingEnabled(True)
    self.de_stats.setMaximumDate(QDate.currentDate())
    self.de_stats.setDateTime(QDateTime.currentDateTime())

    

    self.cb_stats.addItems(list((x.name for x in TimeSpan)))
    self.cb_stats_type.addItems(list((x.name for x in StatType)))

    #FIXME: this needs to be made somehow differently
    dates_left, dates_right = [None], [None]


    def update_start_end():
        today = self.de_stats.dateTime().toPyDateTime().date()
        time_span = TimeSpan[self.cb_stats.currentText()]
        stat_type = StatType[self.cb_stats_type.currentText()]
        print ("UPDATING VIEW:", today, time_span, stat_type)
        if time_span == TimeSpan.WEEKLY:
            start = (today+LAST_MONDAY)
        elif time_span == TimeSpan.DAYS7:
            start = today-dateutil.relativedelta.relativedelta(days=7)
        elif time_span == TimeSpan.DAYS14:
            start = today-dateutil.relativedelta.relativedelta(days=14)
        elif time_span == TimeSpan.DAYS30:
            start = today-dateutil.relativedelta.relativedelta(days=30)
        elif time_span == TimeSpan.MONTHLY:
            start = today.replace(day=1)
        elif time_span == TimeSpan.YEARLY:
            start = today.replace(day=1, month=1)
        end = today+dateutil.relativedelta.relativedelta(hour=23,minute=59,second=0)
        return start, end


    def update_view(input):
        stat_type = StatType[self.cb_stats_type.currentText()]
        start, end = update_start_end()
        print (start, "-", end)
        query_both = queries[stat_type]
        if self.rb_left.isChecked():
            print ("LEFT")
            self.lbl_left.setText("{} - {}".format(start, end))
            dates_left[0] = (start, end)
            model = left_model
            query = query_both[0]
        elif self.rb_right.isChecked():
            print ("RIGHT")
            self.lbl_right.setText("{} - {}".format(start, end))
            dates_right[0] = (start, end)
            model = right_model
            query = query_both[1]
        else:
            print ("NONE CHECKED!")
            return
        #print ("IDQ:", id(query), query)
        #print ("MODEL", id(model), model)
        query.bindValue(":start", str(start))
        query.bindValue(":end", str(end))
        if query.exec_():
            model.setQuery(query)
        else:
            print(query.lastError().text())
        #print ("LEFT:", left_model.query().executedQuery())
        #print ("RIGHT:", left_model.query().executedQuery())
        #self.btn_compare.setEnabled(left_model.rowCount()>0 and
                #right_model.rowCount()>0)



    def get_data(model):
        rows = model.rowCount()
        for row in range(rows):
            record = model.record(row)
            yield record.value(0), record.value(1)
            #yield model.data(model.index(row,0)), model.data(model.index(row,
                #1)) # record.value(0), record.value(1)

    def compare():
        print ("LEFT:", left_model.record(0).value(1))
        print ("RIGHT:", right_model.record(0).value(1))

        #print ("LEFT:", left_model.query().executedQuery())
        #print ("RIGHT:", left_model.query().executedQuery())
        #return
        week_before_dict = {item:weight for (item, weight) in get_data(left_model)}
        week_now_dict = {item:weight for (item, weight) in get_data(right_model)}

        before_items = week_before_dict.keys() # [x[0] for x in week_before]
        now_items = week_now_dict.keys() # [x[0] for x in week_now]

        before_items_set = set(before_items)
        now_items_set = set(now_items)
        print ("Eaten before but not this week:")
        for item in before_items_set.difference(now_items_set):
            print(item)

        print()
        print ("Eaten this week but not week before:")
        for item in now_items_set.difference(before_items_set):
            print (item)

        print()
        print ("Eaten both times:")
        table_low = []
        table_high = []
        table_eq = []
        for item in now_items_set.intersection(before_items_set):
            bef = week_before_dict[item]
            now = week_now_dict[item]
            row = [item, week_before_dict[item], week_now_dict[item]]
            if now < bef:
                table_low.append(row)
            elif now > bef:
                table_high.append(row)
            else:
                table_eq.append(row)
        print ("Lower then before:") 
        print (tabulate(table_low, headers=["Item", "before", "after"]))
        print ("Higher then before:") 
        print (tabulate(table_high, headers=["Item", "before", "after"]))
        print ("Same then before:") 
        print (tabulate(table_eq, headers=["Item", "before", "after"]))

    def show_stats_chart():
        print ("Showing stats chart")
        if self.rb_left.isChecked():
            print ("LEFT")
            current_tv = self.tv_stats
            dates = dates_left[0]
        else:
            print ("RIGHT")
            current_tv = self.tv_stats_right
            dates = dates_right[0]

        indexes = current_tv.selectedIndexes()
        print ("DATES:", dates)
        items = []
        for index in indexes:
            #print (index.row())
            record = current_tv.model().record(index.row())
            print (record.value(0))
            items.append(record.value(0))

        stat_type = StatType[self.cb_stats_type.currentText()]
        show_graph(self, items, dates, stat_type)


    self.de_stats.dateChanged.connect(update_view)
    self.cb_stats.currentIndexChanged.connect(update_view)
    self.cb_stats_type.currentIndexChanged.connect(update_view)
    self.btn_compare.clicked.connect(compare)
    self.pb_stats_chart.clicked.connect(show_stats_chart)
    update_view(self.de_stats.dateTime())

def show_graph(self, items, dates, stat_type):
    print ("ITEMS:", items)
    start, end = dates
    print ("{} - {} {}".format(start, end, stat_type))
    query_sql = graph_queries[stat_type]
    if query_sql is not None:
        query_sql = query_sql.replace(":ITEMS:", ", ".join('"{}"'.format(x) for x in
            items))
        #print (query_sql)
        query_ = QSqlQuery()
        query_.prepare(query_sql)
        query_.bindValue(":start", str(start))
        query_.bindValue(":end", str(end))
        min_max = {}
        for item in items:
            min_max[item]={"min": 99999, "max":0}
        hash = defaultdict(dict)
        #TODO: does it make sense to search for mean max of specific items
        #Wouldn't one min/max be better?
        if query_.exec_():
            while query_.next():
                item = query_.value(0)
                weight = query_.value(1)
                item_date = query_.value(2)
                min_max[item]["min"]=min(min_max[item]["min"], weight)
                min_max[item]["max"]=max(min_max[item]["max"], weight)
                hash[item_date][item]=weight
            hash.default_factory = None
            #print (min_max)
            #print (hash)
            #Scales values from min to max to 0-1
            for values in hash.values():
                for item, weight in values.items():
                    min_val = min_max[item]["min"]
                    max_val = min_max[item]["max"]
                    if min_val == max_val:
                        values[item] = weight/max_val
                    else:
                        values[item]=(weight-min_val)/(max_val-min_val)
            #print (hash)
            cd = ChartDialog(self)

            cd.set_calendar_chart(items,hash)
            cd.show()

        else:
            print(query_.lastError().text())
