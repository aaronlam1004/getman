import sys
import os
import json
from enum import IntEnum

from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import QTableWidgetItem

from BodyEditor import BodyEditor
from RequestTable import RequestTable

class BodySelection(IntEnum):
  NONE = 0
  FORM = 1
  JSON = 2

class BodySelector(QtWidgets.QWidget):
  def __init__(self, parent = None):
    super(BodySelector, self).__init__(parent)
    uic.loadUi('ui/BodySelector.ui', self)

    self.body_selection_radio_buttons = {
      BodySelection.NONE: self.rb_none,
      BodySelection.FORM: self.rb_form,
      BodySelection.JSON: self.rb_json
    }

    self.ConnectActions()

  def LoadState(self, state_json):
    if "body" in state_json and "body_selection" in state_json["body"] and "body_data" in state_json["body"]:
      body_selection = state_json["body"]["body_selection"]
      body_data = state_json["body"]["body_data"]
      self.body_selection_radio_buttons[body_selection].setChecked(True)
      self.UpdateBodySelections()
      self.SetBodyData(body_selection, body_data)

  def UpdateBodySelections(self):
    if self.body_selection_radio_buttons[BodySelection.NONE].isChecked():
      self.sw_body_selection.setCurrentIndex(BodySelection.NONE)
    elif self.body_selection_radio_buttons[BodySelection.FORM].isChecked():
      self.sw_body_selection.setCurrentIndex(BodySelection.FORM)
    elif self.body_selection_radio_buttons[BodySelection.JSON].isChecked():
      self.sw_body_selection.setCurrentIndex(BodySelection.JSON)

  def ConnectActions(self):
    self.sw_body_selection.addWidget(RequestTable()) # 1
    self.sw_body_selection.addWidget(BodyEditor()) # 2
    for radio_button in self.body_selection_radio_buttons.values():
      radio_button.clicked.connect(self.UpdateBodySelections)

  def GetBodyData(self, json_string = False):
    body_data = (BodySelection.NONE, {})
    if self.body_selection_radio_buttons[BodySelection.FORM].isChecked():
      body = self.sw_body_selection.currentWidget().GetRequestFields()
      body_data = (BodySelection.FORM, body)
    elif self.body_selection_radio_buttons[BodySelection.JSON].isChecked():
      body = self.sw_body_selection.currentWidget().GetBody() if not json_string else self.sw_body_selection.currentWidget().GetBodyText()
      body_data = (BodySelection.JSON, body)
    return body_data

  def SetBodyData(self, body_selection, body_data):
    if body_selection == BodySelection.FORM:
      self.sw_body_selection.currentWidget().SetRequestFields(body_data)
    elif body_selection == BodySelection.JSON:
      self.sw_body_selection.currentWidget().SetBodyText(body_data)
