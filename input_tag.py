from database import Tag, TagItem
from PyQt5.QtCore import *

from PyQt5.QtSql import (
        QSqlQuery,
        QSqlRelation,
        QSqlRelationalDelegate,
        QSqlRelationalTableModel,
        QSqlTableModel,
        )

def init_tag(self):

#Selected tags when item is selected
    self.selected_tags = set()


    tag_model = QSqlTableModel()
    tag_model.setTable("tag")
    tag_model.setEditStrategy(QSqlTableModel.OnRowChange)
#It can't be sorted otherwise wrong tags are selected when item is selected
    #tag_model.setSort(1, Qt.AscendingOrder)
    tag_model.select()

    tag_item_model = QSqlRelationalTableModel()
    tag_item_model.setTable("tag_item")
    #tag_item_model.setRelation(1, QSqlRelation('nutrition', 'ndbno', 'desc'))
    #tag_item_model.setRelation(2, QSqlRelation('tag', 'id', 'name'))
    tag_item_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
    #tag_item_model.select()

    self.tag_item_model = tag_item_model

    tag_hier_model = QSqlRelationalTableModel()
    tag_hier_model.setTable("tag_hierarchy")
    tag_hier_model.setRelation(0, QSqlRelation('tag', 'id', 'name'))
    tag_hier_model.setRelation(1, QSqlRelation('tag', 'id', 'name'))
    tag_hier_model.setSort(0, Qt.AscendingOrder)
    tag_hier_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
    tag_hier_model.select()

#From add food
    self.cb_tag_select.setModel(tag_model)
    self.cb_tag_select.setModelColumn(1)

    self.tv_tag.setModel(tag_model)
    #self.tv_tag_item.setModel(tag_item_model)
    self.tv_tag_hierarchy.setModel(tag_hier_model)
    self.lv_tag.setModel(tag_model)
    self.lv_tag.setModelColumn(1)

    #self.tv_tag_item.setItemDelegate(QSqlRelationalDelegate(self.tv_tag_item))
    self.tv_tag_hierarchy.setItemDelegate(QSqlRelationalDelegate(self.tv_tag_hierarchy))

    def add_tag():
        print ("Adding tag:")
        row = self.tv_tag.model().rowCount()
        self.tv_tag.model().insertRow(row)

    def add_hier():
        print ("Adding hier:")
        row = self.tv_tag_hierarchy.model().rowCount()
        self.tv_tag_hierarchy.model().insertRow(row)

    def add_item_tag():
        print ("Adding item_tag:")
        row = self.tv_tag_item.model().rowCount()
        self.tv_tag_item.model().insertRow(row)

    def save_hier():
        print ("Saving hier")
        self.tv_tag_hierarchy.model().submitAll()

    def select_nutri_tag(selectedIndex):
        ndbno = self._get_selected_ndbno(self.cb_item_tag.model() \
                .record(self.cb_item_tag.currentIndex()))
        print ("Item:", self.cb_item_tag.currentText(), ndbno)
        tags = self.session.query(TagItem) \
                .filter(TagItem.ndbno==ndbno) \
                .order_by(TagItem.tag_id)
        if self.lv_tag.selectionModel():
            self.lv_tag.selectionModel().clearSelection()
        self.selected_tags.clear()
        for tag in tags:
            print (tag.tag.name, tag.tag_id)
            index = self.lv_tag.model().createIndex(tag.tag_id, 1)
            if index.isValid():
                print ("Valid index")
                self.lv_tag.selectionModel().select(index,
                        QItemSelectionModel.Select)
                data = self.lv_tag.model().data(index)
                self.selected_tags.add(tag.tag_id)
                #print(data)

    def save_tag_item():
        print ("Saving tag item")
        selected_tags_now = set()
        for index in self.lv_tag.selectedIndexes():
            record = self.lv_tag.model().record(index.row()) 
            selected_tags_now.add(record.field("id").value())
            print (str(record.field("id").value()) + " - " +
                    record.field("name").value())
        added_tag_ids = selected_tags_now.difference(self.selected_tags)
        removed_tag_ids = self.selected_tags.difference(selected_tags_now)
        #print ("Unselected tags:" + ", ".join(map(lambda x: str(x),
                #removed_tag_ids)))
        #print ("New selected tags:" + ", ".join(map(lambda x: str(x),
                #added_tag_ids)))
        ndbno = self._get_selected_ndbno(self.cb_item_tag.model() \
                .record(self.cb_item_tag.currentIndex()))
        print ("Item:", self.cb_item_tag.currentText(), ndbno)

        query = QSqlQuery()
        ret = query.prepare("DELETE FROM tag_item WHERE ndbno = :ndbno and tag_id = :tag_id")
        if not ret:
            print ("Failed to prepare query")


        for tag_id in added_tag_ids:
            row = self.tag_item_model.rowCount()
            self.tag_item_model.insertRow(row)
            self.tag_item_model.setData(self.tag_item_model.createIndex(row,
                1), ndbno, Qt.EditRole)
            self.tag_item_model.setData(self.tag_item_model.createIndex(row,
                2), tag_id, Qt.EditRole)
            print ("Adding tag id:", tag_id)
            #print (record.field("name").value(), record.field("id").value())
        #self.tv_tag_item.model().submitAll()
        if not self.tag_item_model.submitAll():
            QMessageBox.critical(None, "Error submitting",
                    "Couldn't update model: " +
                    self.tag_item_model.lastError().text())
            self.tag_item_model.revertAll()
        query.bindValue(":ndbno", ndbno)
        for tag_id in removed_tag_ids:
            query.bindValue(":tag_id", tag_id)
            print ("Removing tag_id:", tag_id)
            if not query.exec_():
                print ("Failed to executr query")
            #print (query.executedQuery())

    self.pb_add_tag.pressed.connect(add_tag)
    self.pb_add_item_tag.pressed.connect(add_item_tag)
    self.pb_add_hier.pressed.connect(add_hier)
    self.pb_save_hier.pressed.connect(save_hier)
    self.pb_save_tag_item.pressed.connect(save_tag_item)
    self.cb_item_tag.currentIndexChanged.connect(select_nutri_tag)
