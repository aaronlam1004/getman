import sys
import os
import json
from enum import IntEnum

from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import QTableWidgetItem

from BodyEditor import BodyEditor
from RequestTable import RequestTable

from utils.Paths import GetUIPath

class BodySelection(IntEnum):
    NONE = 0
    FORM = 1
    JSON = 2

class BodySelector(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super(BodySelector, self).__init__(parent)
        uic.loadUi(GetUIPath('BodySelector.ui'), self)

        self.body_selection_radio_buttons = {
            BodySelection.NONE: self.radio_None,
            BodySelection.FORM: self.radio_Form,
            BodySelection.JSON: self.radio_Json
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
            self.stacked_Body.setCurrentIndex(BodySelection.NONE)
        elif self.body_selection_radio_buttons[BodySelection.FORM].isChecked():
            self.stacked_Body.setCurrentIndex(BodySelection.FORM)
        elif self.body_selection_radio_buttons[BodySelection.JSON].isChecked():
            self.stacked_Body.setCurrentIndex(BodySelection.JSON)

    def ConnectActions(self):
        self.stacked_Body.addWidget(RequestTable()) # 1
        self.stacked_Body.addWidget(BodyEditor()) # 2
        for radio_button in self.body_selection_radio_buttons.values():
            radio_button.clicked.connect(self.UpdateBodySelections)

    def GetBodyData(self, json_string = False):
        body_data = (BodySelection.NONE, {})
        if self.body_selection_radio_buttons[BodySelection.FORM].isChecked():
            body = self.stacked_Body.currentWidget().GetRequestFields()
            body_data = (BodySelection.FORM, body)
        elif self.body_selection_radio_buttons[BodySelection.JSON].isChecked():
            body = self.stacked_Body.currentWidget().GetBody() if not json_string else self.stacked_Body.currentWidget().GetBodyText()
            body_data = (BodySelection.JSON, body)
        return body_data

    def SetBodyData(self, body_selection, body_data):
        if body_selection == BodySelection.FORM:
            self.stacked_Body.currentWidget().SetRequestFields(body_data)
        elif body_selection == BodySelection.JSON:
            self.stacked_Body.currentWidget().SetBodyText(body_data)
