import sys
import os
import json

from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import QTableWidgetItem

TABLE_HEADER_LABELS = {
  "": 0,
  "Key": 1,
  "Value": 2,
  "Description": 3
}

class RequestTable(QtWidgets.QWidget):
  def __init__(self, parent = None):
    super(RequestTable, self).__init__(parent)
    uic.loadUi('ui/RequestTable.ui', self)
    self.ConnectActions()

  def LoadState(self, state_json):
    pass 

  def ConnectActions(self):
    self.InitTable()
    self.LoadTable()
    self.tablewidget_req_options.itemChanged.connect(self.CheckChange)

  def InitTable(self):
    self.tablewidget_req_options.setColumnCount(4)
    self.tablewidget_req_options.setRowCount(1)
    self.tablewidget_req_options.verticalHeader().setVisible(False)
    self.tablewidget_req_options.horizontalHeader().setStretchLastSection(True)
    self.tablewidget_req_options.setHorizontalHeaderLabels(TABLE_HEADER_LABELS.keys())

  def LoadTable(self):
    checkbox_widget = QTableWidgetItem()
    checkbox_widget.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
    checkbox_widget.setCheckState(QtCore.Qt.Unchecked)
    self.tablewidget_req_options.setItem(0, 0, checkbox_widget)

  def GetRowCount(self):
    return self.tablewidget_req_options.rowCount()

  def AddNewRow(self):
    self.tablewidget_req_options.insertRow(self.GetRowCount())
    checkbox_widget = QTableWidgetItem()
    checkbox_widget.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
    checkbox_widget.setCheckState(QtCore.Qt.Unchecked)
    self.tablewidget_req_options.setItem(self.GetRowCount() - 1, 0, checkbox_widget)

  def CheckChange(self, item):
    for row in range(self.GetRowCount()):
      key_item = self.tablewidget_req_options.item(row, TABLE_HEADER_LABELS["Key"])
      value_item = self.tablewidget_req_options.item(row, TABLE_HEADER_LABELS["Value"])
      desc_item = self.tablewidget_req_options.item(row, TABLE_HEADER_LABELS["Description"])
      if key_item is not None and key_item.text() != "" or \
         value_item is not None and value_item.text() != "" or \
         desc_item is not None and desc_item.text() != "":
        self.tablewidget_req_options.item(row, 0).setCheckState(QtCore.Qt.Checked)
        if row == self.GetRowCount() - 1:
          self.AddNewRow()
      elif self.GetRowCount() > 1 and row < self.GetRowCount() - 1:
          self.tablewidget_req_options.removeRow(row) 

  def GetRequestFields(self):
    request_fields = {}
    for row in range(self.GetRowCount()):
      key_item = self.tablewidget_req_options.item(row, TABLE_HEADER_LABELS["Key"])
      value_item = self.tablewidget_req_options.item(row, TABLE_HEADER_LABELS["Value"])
      if key_item is not None and value_item is not None:
        request_fields[key_item.text()] = value_item.text()
    return request_fields
