import sys
import os
import json

from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtCore import Qt

from utils.Paths import GetUIPath

TABLE_HEADER_LABELS = {
    "Key": 0,
    "Value": 1,
    "Description": 2
}

class RequestTable(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super(RequestTable, self).__init__(parent)
        uic.loadUi(GetUIPath('RequestTable.ui'), self)
        self.ConnectActions()

    def ConnectActions(self):
        self.InitTable()
        self.table_RequestOptions.itemChanged.connect(self.CheckChange)

    def InitTable(self):
        self.table_RequestOptions.setColumnCount(3)
        self.table_RequestOptions.setRowCount(1)
        self.table_RequestOptions.verticalHeader().setVisible(False)
        self.table_RequestOptions.horizontalHeader().setStretchLastSection(True)
        self.table_RequestOptions.setHorizontalHeaderLabels(TABLE_HEADER_LABELS.keys())

    def GetRowCount(self):
        return self.table_RequestOptions.rowCount()

    def AddNewRow(self):
        self.table_RequestOptions.insertRow(self.GetRowCount())

    def CheckChange(self, item):
        for row in range(self.GetRowCount()):
            key_item = self.table_RequestOptions.item(row, TABLE_HEADER_LABELS["Key"])
            value_item = self.table_RequestOptions.item(row, TABLE_HEADER_LABELS["Value"])
            desc_item = self.table_RequestOptions.item(row, TABLE_HEADER_LABELS["Description"])
            if key_item is not None and key_item.text() != "" or \
                value_item is not None and value_item.text() != "" or \
                desc_item is not None and desc_item.text() != "":
                if row == self.GetRowCount() - 1:
                    self.AddNewRow()
            elif self.GetRowCount() > 1 and row < self.GetRowCount() - 1:
                    self.table_RequestOptions.removeRow(row)

    def GetFields(self):
        request_fields = {}
        for row in range(self.GetRowCount()):
            key_item = self.table_RequestOptions.item(row, TABLE_HEADER_LABELS["Key"])
            value_item = self.table_RequestOptions.item(row, TABLE_HEADER_LABELS["Value"])
            if key_item is not None:
                request_fields[key_item.text()] = value_item.text() if value_item is not None else ""
        return request_fields

    def SetFields(self, request_fields):
        if len(request_fields) == 0:
            self.table_RequestOptions.clearContents()
        for i, (k, v) in enumerate(request_fields.items()):
            self.AddNewRow()
            self.table_RequestOptions.setItem(i, 0, QTableWidgetItem(k))
            self.table_RequestOptions.setItem(i, 1, QTableWidgetItem(v))
