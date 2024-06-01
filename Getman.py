import sys
import os
import json
import signal
from enum import Enum

from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import QMenuBar, QAction, QListWidgetItem
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QBrush, QColor, QFont

from RequestTable import RequestTable
from BodySelector import BodySelection, BodySelector
from RequestHandler import RequestTypes, RequestHandler
from ScripterTool import ScripterTool
from JsonHighlighter import JsonHighlighter

DEFAULT_STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".workspace")
host = None

REQUEST_TYPE_UI = {
    RequestTypes.GET: "#08C751",
    RequestTypes.POST: "#DEB11F",
    RequestTypes.PUT: "#143EC9",
    RequestTypes.PATCH: "#7D11BF",
    RequestTypes.DELETE: "#C41B0C",
    RequestTypes.HEAD: "#C90E85",
    RequestTypes.OPTIONS: "#7FB80D"
}

class Getman(QtWidgets.QWidget):
    response_signal = pyqtSignal(dict)

    def __init__(self, parent = None):
        super(Getman, self).__init__(parent)
        uic.loadUi('ui/Getman.ui', self)
        self.setWindowTitle("Getman")
        self.state_file = DEFAULT_STATE_FILE

        self.request_history = []

        self.response_highlighter = JsonHighlighter(self.te_response_json.document())

        self.headers_table = RequestTable()
        self.params_table = RequestTable()
        self.body_selector = BodySelector()
        self.scripter_tool = None

        self.tabwidget_req_settings.addTab(self.headers_table, "Headers")
        self.tabwidget_req_settings.addTab(self.params_table, "Params")
        self.tabwidget_req_settings.addTab(self.body_selector, "Body")

        self.cbox_request_type.setEditable(True)
        self.cbox_request_type.lineEdit().setEnabled(False)
        self.cbox_request_type.lineEdit().setReadOnly(True)

        # TODO: make Qt style sheet
        self.cbox_request_type.setStyleSheet("selection-background-color: rgb(0, 0, 0)")

        self.ConnectActions()

    def OpenScriptTool(self):
        self.scripter_tool = ScripterTool()
        self.scripter_tool.request_script_signal.connect(self.scripter_tool.AddRequestToScript)
        self.scripter_tool.show()

    # TODO: close event

    def GetState(self):
        state_json = {}
        state_json["url"] = self.le_url.text()
        state_json["request_type"] = self.cbox_request_type.currentText()
        state_json["headers"] = self.headers_table.GetRequestFields()
        body_selection, body_data = self.body_selector.GetBodyData(json_string = True)
        state_json["body"] = {
            "body_selection": body_selection,
            "body_data": body_data
        }
        return state_json

    def SaveState(self):
        state_json = self.GetState()
        with open(self.state_file, 'w') as state_file:
            json.dump(state_json, state_file, indent=4)

    def OpenState(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as state_file:
                try:
                    state_json = json.loads(state_file.read())
                    self.LoadState(state_json)
                except Exception as exception:
                    print(f"Exception occured while to load the state: {exception}")
                    pass

    def LoadState(self, state_json: dict):
        self.le_url.setText(state_json["url"])
        self.cbox_request_type.setCurrentText(state_json["request_type"])
        self.headers_table.SetRequestFields(state_json["headers"])
        self.body_selector.LoadState(state_json)

    def ConnectActions(self):
        self.pb_send.clicked.connect(self.SendRequest)
        self.response_signal.connect(self.ProcessResponse)
        self.list_widget_history.selectionModel().selectionChanged.connect(self.LoadHistoryState)
        self.list_widget_responses.selectionModel().selectionChanged.connect(self.DisplayResponseJson)
        self.cbox_request_type.currentTextChanged.connect(self.ChangeRequestTypesColor)
        self.InitializeRequestTypes()
        self.OpenState()

    def ChangeRequestTypesColor(self):
        color = REQUEST_TYPE_UI[self.cbox_request_type.currentData()]
        font = QFont()
        font.setBold(True)
        self.cbox_request_type.lineEdit().setFont(font)
        self.cbox_request_type.lineEdit().setStyleSheet(f"color: {color}")

    def InitializeRequestTypes(self):
        for i, (request_type, color) in enumerate(REQUEST_TYPE_UI.items()):
            font = QFont()
            font.setBold(True)
            brush = QBrush(QColor(color))
            self.cbox_request_type.addItem(request_type.value, userData=request_type)
            self.cbox_request_type.setItemData(i, brush, Qt.TextColorRole)
            self.cbox_request_type.setItemData(i, font, Qt.FontRole)

    def SendRequest(self):
        url = self.le_url.text()
        if url != "":
            headers = self.headers_table.GetRequestFields()
            form = {}
            body = {}
            body_selection, body_data = self.body_selector.GetBodyData()
            if body_selection == BodySelection.FORM:
                form = body_data
            if body_selection == BodySelection.JSON:
                body = body_data
            request, response_json = RequestHandler.Request(url, self.cbox_request_type.currentData(), headers=headers, body=body, form=form)
            self.AddRequestHistory(RequestHandler.GetJsonFromRequest(request))
            self.response_signal.emit(response_json)

    def DisplayResponseJson(self):
        response = self.list_widget_responses.currentItem().text()
        if response is not None:
            response_json = json.loads(response)
            self.te_response_json.setText(json.dumps(response_json, indent=4))

    def LoadHistoryState(self):
        self.LoadState(self.request_history[self.list_widget_history.currentRow()])

    @pyqtSlot(dict)
    def ProcessResponse(self, response: dict):
        self.list_widget_responses.addItem(QListWidgetItem(json.dumps(response)))

    def AddRequestHistory(self, request):
        state_json = self.GetState()
        self.request_history.append(state_json)
        self.list_widget_history.addItem(str(state_json))
        if self.scripter_tool != None:
            self.scripter_tool.request_script_signal.emit(request)

class GetmanApp(QtWidgets.QMainWindow):
    def __init__(self):
        super(GetmanApp, self).__init__()
        self.getman = Getman()
        self.setCentralWidget(self.getman)
        self.setWindowTitle("Getman")
        self.InitializeMenu()
        self.showMaximized()

    def InitializeMenu(self):
        self.menu_bar = QMenuBar(self)
        self.InitializeFileMenuOptions()
        self.setMenuBar(self.menu_bar)

    def InitializeFileMenuOptions(self):
        file_menu = self.menu_bar.addMenu("File")

        save_action = QAction("Save Workspace", self)
        save_action.triggered.connect(self.getman.SaveState)
        file_menu.addAction(save_action)

        load_action = QAction("Load Workspace", self)
        # load_Action.triggered.connect()
        file_menu.addAction(load_action)

        open_scripts_action = QAction("Open Script Tool", self)
        open_scripts_action.triggered.connect(self.getman.OpenScriptTool)
        file_menu.addAction(open_scripts_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

def ExceptionHandler(exctype, value, traceback):
    global host
    if host is not None:
        host.SaveState()
    sys.__excepthook__(exctype, value, traceback)
    sys.exit(1)

if __name__ == '__main__':
    # sys.excepthook = ExceptionHandler
    q_application = QtWidgets.QApplication(sys.argv)
    q_application.setStyle("Fusion")
    app = GetmanApp()
    app.show()
    sys.exit(q_application.exec_())
