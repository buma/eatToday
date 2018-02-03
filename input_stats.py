from enum import Enum
import dateutil.relativedelta
from tabulate import tabulate
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QDialogButtonBox

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

class TimeSpan(Enum):
    WEEKLY = 0
    MONTHLY = 1

class StatType(Enum):
    INGKEY = 0
    TAGS = 1
    FOOD_TAGS = 2
LAST_MONDAY = dateutil.relativedelta.relativedelta(
        weekday=dateutil.relativedelta.MO(-1))


def init_stats(self):
    print("init stats")
    queries = {}
    INGKEY_SQL = """
            SELECT foodnutrition_details_alias_time.nutritionaliases_ingkey AS
            ingkey,
            sum(foodnutrition_details_alias_time.foodnutrition_details_weight * 100) AS weight_sum,
--            CASE WHEN (nutrition.package_weight IS NOT NULL) THEN
--            CAST(weight_sum AS FLOAT) /
--            nutrition.package_weight END AS package_weight1,
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

    def update_view(input):
        today = self.de_stats.dateTime().toPyDateTime().date()
        time_span = TimeSpan[self.cb_stats.currentText()]
        stat_type = StatType[self.cb_stats_type.currentText()]
        print ("UPDATING VIEW:", today, time_span, stat_type)
        if time_span == TimeSpan.WEEKLY:
            start = (today+LAST_MONDAY)
            end = today
        else:
            start = today.replace(day=1)
            end = today
        print (start, "-", end)
        query_both = queries[stat_type]
        if self.rb_left.isChecked():
            print ("LEFT")
            self.lbl_left.setText("{} - {}".format(start, end))
            model = left_model
            query = query_both[0]
        elif self.rb_right.isChecked():
            print ("RIGHT")
            self.lbl_right.setText("{} - {}".format(start, end))
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

    self.de_stats.dateChanged.connect(update_view)
    self.cb_stats.currentIndexChanged.connect(update_view)
    self.cb_stats_type.currentIndexChanged.connect(update_view)
    self.btn_compare.clicked.connect(compare)
    update_view(self.de_stats.dateTime())
