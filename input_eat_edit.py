import itertools
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
eating_model = None

def fill_eating_model():
    global eating_model
    eating_model = QSqlTableModel()
    eating_model.setTable("eat")
    eating_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
    eating_model.setSort(1,Qt.DescendingOrder)
    eating_model.select()

def fill_food_tags_model():
    global eating_model
    eating_model = QSqlQueryModel()
    eating_model.setQuery("""
SELECT foodnutrition.id AS fn_id,
       min(eat.id) AS eat_id,
       tags,
       eat.description
FROM foodnutrition
JOIN eat ON eat.calc_nutrition == foodnutrition.id
LEFT JOIN
  ( SELECT group_concat(food_tag.name) AS "tags",
           food_tag_item.fn_id AS ffn_id
   FROM food_tag_item
   JOIN food_tag ON food_tag.id == food_tag_item.tag_id
   GROUP BY food_tag_item.fn_id) ON ffn_id ==foodnutrition.id
GROUP BY foodnutrition.id
ORDER BY foodnutrition.id DESC
    """)
    


def init_edit_eat(self):
    global eating_model
    print("Editing eat init")
    #food_tag_item_model = QSqlRelationalTableModel()
    #food_tag_item_model.setTable("food_tag_item")
    #food_tag_item_model.setRelation(2, QSqlRelation("food_tag", "id", "name"))
    add_food_tag_query = QSqlQuery()
    add_food_tag_query.prepare("INSERT INTO food_tag (name) VALUES (:name)")
    add_food_item_query = QSqlQuery()
    add_food_item_query.prepare("""
    INSERT INTO food_tag_item (fn_id, tag_id, item_id) VALUES
    (:fn_id, :tag_id, :item_id)
    """)
    get_food_item_tags_query = QSqlQuery()
    get_food_item_tags_query.prepare("""
    SELECT food_tag.id, food_tag.name FROM food_tag_item
    JOIN food_tag ON
    food_tag.id == food_tag_item.tag_id
    WHERE food_tag_item.fn_id == :fn_id
    """)
    query = QSqlQuery()
    query.prepare("""
    SELECT group_concat(food_tag.name) as "tags", food_tag_item.fn_id
FROM food_tag_item
JOIN food_tag ON
food_tag.id == food_tag_item.tag_id
WHERE food_tag_item.fn_id == :fn_id
AND food_tag_item.item_id == :eat_id
GROUP BY food_tag_item.fn_id""")

    QUERY_TAGS = """
    SELECT id, name
FROM food_tag
WHERE name in (:tags)
ORDER BY id
"""

    query_in_tags = QSqlQuery()
    #query_in_tags.prepare(QUERY_TAGS)



    def update_model():
        print ("Updating")
        if not eating_model.submitAll():
            print ("ERROR submitting:", eating_model.lastError().text())

    def reset_update_model():
        print ("Reset model")
        eating_model.revertAll()


    def update_food_tags():
        print ("Updating food tags")
        indexes = self.tv_eat_view.selectedIndexes()
        tags = self.le_eat_tags.text().split(",")
        for tag in tags:
            print (tag)
        sql_tags = ",".join(('"{}"'.format(x) for x in tags))
        print (sql_tags)
        tag_id_name = {}
        #FIXME: query with IN can't be prepared for some reason
        #query_in_tags.bindValue(":tags", sql_tags)
        #query_in_tags.setQuery()
        #gets Ids of all used tags if tags aren't in table they are inserted
        if query_in_tags.exec_(QUERY_TAGS.replace(":tags", sql_tags)):
            #print (query_in_tags.lastQuery())
            #print (query_in_tags.boundValues())
            #Gets all used tag ids
            while query_in_tags.next():
                #print (query_in_tags.value(1))
                tag_id_name[query_in_tags.value(1)] = query_in_tags.value(0)
            print (tag_id_name)
            #Which tags aren't in the database yet
            missing_tags = set(tags)-set(tag_id_name.keys())
            print ("MISSING TAGS:", missing_tags)
            for missing_tag in missing_tags:
                add_food_tag_query.bindValue(":name", missing_tag)
                print ("Adding ", missing_tag)
                if add_food_tag_query.exec_():
                    tag_id_name[missing_tag] = \
                            add_food_tag_query.lastInsertId()
                else:
                    print ("ERROR ADD FOOD",
                            add_food_tag_query.lastError().text())
                    return
            print (tag_id_name)
            for index in indexes:
                print (index.row())
                record = self.tv_eat_view.model().record(index.row())
                fn_id = record.value("fn_id")
                eat_id = record.value("eat_id")
                _update_food_tags(tag_id_name, fn_id, eat_id)
        else:
            print (query_in_tags.lastError().text())

    def _update_food_tags(tag_id_name, fn_id, eat_id):
        #sql_tags = "({})".format(sql_tags)
        #print (sql_tags, fn_id, eat_id)
        print ("FN ID:", fn_id, "EAT ID:", eat_id)
        tag_id_to_insert = {}

        get_food_item_tags_query.bindValue(":fn_id", fn_id)

        existing_tag_id_name = {}
        if get_food_item_tags_query.exec_():
            while get_food_item_tags_query.next():
                food_tag_id = get_food_item_tags_query.value(0)
                food_tag_name = get_food_item_tags_query.value(1)
                existing_tag_id_name[food_tag_name] = food_tag_id
                print ("EXISTING TAG:", food_tag_name, food_tag_id)

            to_insert_tags = set(tag_id_name.keys()) - \
                    set(existing_tag_id_name.keys())
            print ("TO insert tags:", to_insert_tags)

            tag_id_to_insert = []
            for to_insert_tag in to_insert_tags:
                tag_id_to_insert.append(tag_id_name[to_insert_tag])

            print ("To insert ids:", tag_id_to_insert)
        
            #Adds list of food_items:
            #- list of fn_ids,
            #- list of tag_ids
            #- list of item_ids
            num_tags = len(tag_id_to_insert)
            if num_tags:
                fn_ids = list(itertools.repeat(fn_id, num_tags))
                tag_ids = list(tag_id_to_insert) 
                item_ids = list(itertools.repeat(eat_id, num_tags))

                print (fn_ids, tag_ids, item_ids)

                add_food_item_query.bindValue(":fn_id", fn_ids)
                add_food_item_query.bindValue(":tag_id", tag_ids)
                add_food_item_query.bindValue(":item_id", item_ids)
                    
                print (add_food_item_query.boundValues())
                if not add_food_item_query.execBatch():
                    print (add_food_item_query.lastError().text())
        else:
            print (get_food_item_tags_query.lastError().text())



    def switch_model(checked):
        print ("Switching")
        try:
            self.buttonBox_edit_eat.accepted.disconnect()
        except Exception:
            pass
        try:
            self.buttonBox_edit_eat.button(QDialogButtonBox.Reset).clicked.disconnect()
        except Exception:
            pass
        #try:
            #self.tv_eat_view.doubleClicked.disconnect()
        #except Exception:
            #pass
        if self.rb_eat.isChecked():
            fill_eating_model()
            self.buttonBox_edit_eat.accepted.connect(update_model)
            self.buttonBox_edit_eat.button(QDialogButtonBox.Reset).clicked.connect(reset_update_model)
            self.tv_eat_view.horizontalHeader().setStretchLastSection(False)
            self.tv_eat_view.setSortingEnabled(True)
            #for i in [2,5,6,7,8]:
            for i in [2,5,9]:
                self.tv_eat_view.setColumnHidden(i, True)
        else:
            fill_food_tags_model()
            self.buttonBox_edit_eat.accepted.connect(update_food_tags)
            #self.tv_eat_view.doubleClicked.connect(edit_food_tags)
            self.tv_eat_view.horizontalHeader().setStretchLastSection(True)

        self.tv_eat_view.setModel(eating_model)

    def edit_food_tags():
        indexes = self.tv_eat_view.selectedIndexes()
        for index in indexes:
            print (index.row())
            record = self.tv_eat_view.model().record(index.row())
            fn_id = record.value("fn_id")
            eat_id = record.value("eat_id")
            break
        #TODO: select all fn_ids and add all tags into tags edit field
        print ("FN ID:", fn_id, "EAT ID:", eat_id)
        query.bindValue(":fn_id", fn_id)
        query.bindValue(":eat_id", eat_id)
        if query.exec_():
            if query.first():
                tags = query.value(0)
            else:
                tags = ""
            self.le_eat_tags.setText(tags)
            print("TAGS:", tags)
        else:
            print("TAGS: EMPTY")


    switch_model(True)
    #self.tv_eat_view.setModel(eating_model)
    #self.tv_eat_view.setModel(self.eating_model)
    self.pb_editTags.clicked.connect(edit_food_tags)

    self.rb_eat.toggled.connect(switch_model)
    self.rb_eat_tags.toggled.connect(switch_model)

def start(self):
    global eating_model
    print("Starting eat init")
    #eating_model.select()
