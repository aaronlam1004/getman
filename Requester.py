import sys
import os
import json
import signal
import configparser
from enum import Enum

FILE_PATH = os.path.dirname(__file__)
GETSCRIPT_PATH = os.path.join(FILE_PATH, 'getscript')
sys.path.append(GETSCRIPT_PATH)

from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import QMenuBar, QAction, QListWidgetItem, QInputDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QBrush, QColor, QFont, QStandardItemModel, QStandardItem

from Defines import REQUEST_TYPE_COLORS
from RequestTable import RequestTable
from BodySelector import BodySelection, BodySelector
from Workspace import Workspace, WORKSPACE_PATH

from RequestHandler import RequestTypes, RequestHandler
from JsonHighlighter import JsonHighlighter
from utils.Paths import GetUIPath

class Requester(QtWidgets.QWidget):
    response_signal = pyqtSignal(object)
    request_type_updated_signal = pyqtSignal(str, str)

    def __init__(self, request_name: str, parent = None):
        super(Requester, self).__init__(parent)
        uic.loadUi(GetUIPath('Requester.ui'), self)
        self.parent = parent

        self.request_name = request_name
        self.request_json = self.EmptyRequest()

        self.response_highlighter = JsonHighlighter(self.te_ResponseJsons.document())
        self.headers_table = RequestTable()
        self.params_table = RequestTable()
        self.body_selector = BodySelector()

        self.SetupActions()
        self.ConnectActions()

    @staticmethod
    def EmptyRequest():
        return {
            "url": "",
            "type": "GET",
            "params": {},
            "headers": {},
            "body": {
                "body_selection": BodySelection.NONE,
                "body_data" : {}
            }
        }

    def GetName(self):
        return self.request_name

    def SetupActions(self):
        self.tabs_RequestSettings.addTab(self.headers_table, "Headers")
        self.tabs_RequestSettings.addTab(self.params_table, "Params")
        self.tabs_RequestSettings.addTab(self.body_selector, "Body")

        self.cbox_RequestTypes.setEditable(True)
        self.cbox_RequestTypes.lineEdit().setEnabled(False)
        self.cbox_RequestTypes.lineEdit().setReadOnly(True)

        # TODO: make Qt style sheet
        self.cbox_RequestTypes.setStyleSheet("selection-background-color: rgb(0, 0, 0)")

    def ConnectActions(self):
        # Request
        self.pb_Send.clicked.connect(self.SendRequest)
        self.cbox_RequestTypes.currentTextChanged.connect(self.UpdateRequestType)
        self.InitRequestTypes()

        # Response
        self.response_signal.connect(self.ProcessResponse)

        # History
        self.list_Responses.selectionModel().selectionChanged.connect(self.DisplayResponseJson)

    def UpdateRequestType(self):
        request_type = self.cbox_RequestTypes.currentData()
        self.request_type_updated_signal.emit(self.request_name, request_type.value)
        color = REQUEST_TYPE_COLORS[request_type]
        font = QFont()
        font.setBold(True)
        self.cbox_RequestTypes.lineEdit().setFont(font)
        self.cbox_RequestTypes.lineEdit().setStyleSheet(f"color: {color}")

    def InitRequestTypes(self):
        for i, (request_type, color) in enumerate(REQUEST_TYPE_COLORS.items()):
            font = QFont()
            font.setBold(True)
            brush = QBrush(QColor(color))
            self.cbox_RequestTypes.addItem(request_type.value, userData=request_type)
            self.cbox_RequestTypes.setItemData(i, brush, Qt.TextColorRole)
            self.cbox_RequestTypes.setItemData(i, font, Qt.FontRole)

    def GetRequest(self):
        request_json = self.EmptyRequest()
        request_json["url"] = self.le_URL.text()
        request_json["type"] = self.cbox_RequestTypes.currentText()
        request_json["params"] = self.params_table.GetFields()
        request_json["headers"] = self.headers_table.GetFields()
        body_selection, body_data = self.body_selector.GetBodyData(json_string = True)
        request_json["body"]["body_selection"] = body_selection
        request_json["body"]["body_data"] = body_data
        return request_json

    def LoadRequest(self, request_json: dict):
        # TODO: handle try-except errors
        try:
            self.le_URL.setText(request_json["url"])
            self.cbox_RequestTypes.setCurrentText(request_json["type"])
            self.params_table.SetFields(request_json["params"])
            self.headers_table.SetFields(request_json["headers"])
            self.body_selector.LoadState(request_json)
        except KeyError:
            pass

    def SaveRequest(self):
        if self.request_name != "":
            self.parent.workspace.SaveRequestInWorkspace(self.request_name, self.GetRequest(), overwrite=True)

    def SendRequest(self):
        url = self.le_URL.text()
        if url != "":
            headers = self.headers_table.GetFields()
            params = self.params_table.GetFields()
            form = {}
            body = {}
            body_selection, body_data = self.body_selector.GetBodyData()
            if body_selection == BodySelection.FORM:
                form = body_data
            if body_selection == BodySelection.JSON:
                body = body_data
            request, response_json = RequestHandler.Request(url, self.cbox_RequestTypes.currentData(), params=params, headers=headers, body=body, form=form)
            self.response_signal.emit(response_json)
            if self.parent is not None:
                self.parent.add_request_history_signal.emit(RequestHandler.GetJsonFromRequest(request))

    def DisplayResponseJson(self):
        response = self.list_Responses.currentItem().text()
        if response is not None:
            response_json = json.loads(response)
            self.te_ResponseJsons.setText(json.dumps(response_json, indent=4))

    @pyqtSlot(object)
    def ProcessResponse(self, response: dict):
        self.list_Responses.addItem(QListWidgetItem(json.dumps(response)))
