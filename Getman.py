# TODO: handle params
# TODO: handle queries

import sys
import os
import json
import signal
import configparser
from enum import Enum

from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import QMenuBar, QAction, QListWidgetItem, QFileDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QBrush, QColor, QFont

from RequestTable import RequestTable
from BodySelector import BodySelection, BodySelector
from RequestHandler import RequestTypes, RequestHandler
from ScriptIDE import ScriptIDE
from JsonHighlighter import JsonHighlighter

TEMP_WORKSPACE_NAME = ".workspace~"
TEMP_WORKSPACE = os.path.join(os.path.dirname(os.path.abspath(__file__)), TEMP_WORKSPACE_NAME)

CONFIG_FILE_NAME = "config.ini"
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE_NAME)

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
    update_title_signal = pyqtSignal(str)

    def __init__(self, parent=None, update_title=None):
        super(Getman, self).__init__(parent)
        uic.loadUi('ui/Getman.ui', self)

        if update_title is not None:
            self.update_title_signal.connect(update_title)

        self.request_history = []
        self.response_highlighter = JsonHighlighter(self.te_response_json.document())
        self.headers_table = RequestTable()
        self.params_table = RequestTable()
        self.body_selector = BodySelector()
        self.script_ide = ScriptIDE()

        self.InitActions()
        self.ConnectActions()

        # Configuration file
        self.config = configparser.ConfigParser()
        if os.path.exists(CONFIG_FILE):
            self.config.read(CONFIG_FILE)
        else:
            self.config["workspace"] = { "file": TEMP_WORKSPACE_NAME }

        # Workspace
        if "workspace" in self.config and "file" in self.config["workspace"]:
            self.SetWorkspace(self.config["workspace"]["file"])
        else:
            self.SetWorkspace(TEMP_WORKSPACE)

    def UpdateConfig(self):
        if "workspace" not in self.config.sections() or "file" not in self.config["workspace"]:
            self.config["workspace"] = { "file": self.workspace_file }
        else:
            self.config["workspace"]["file"] = self.workspace_file
        with open(CONFIG_FILE, 'w') as config_file:
            self.config.write(config_file)

    def GetEmptyWorkspace(self):
        return {
            "url": "",
            "request_type": "GET",
            "headers": {},
            "body": {
                "body_selection": BodySelection.NONE,
                "body_data" : {}
            }
        }

    def GetWorkspace(self):
        workspace_json = self.GetEmptyWorkspace()
        workspace_json["url"] = self.le_url.text()
        workspace_json["request_type"] = self.cbox_request_type.currentText()
        workspace_json["headers"] = self.headers_table.GetFields()
        body_selection, body_data = self.body_selector.GetBodyData(json_string = True)
        workspace_json["body"]["body_selection"] = body_selection
        workspace_json["body"]["body_data"] = body_data
        return workspace_json

    def SetWorkspace(self, workspace_file, reset_temp_workspace: bool = False):
        self.workspace_file = workspace_file
        self.UpdateConfig()
        if self.workspace_file != TEMP_WORKSPACE:
            self.ReadWorkspace()
            self.update_title_signal.emit(f"Getman - {self.workspace_file}")
        else:
            self.update_title_signal.emit("Getman - Untitled")
            if reset_temp_workspace:
                self.LoadWorkspace(self.GetEmptyWorkspace())

    def SaveWorkspace(self, save_dialog: bool = False):
        self.UpdateConfig()
        workspace_json = self.GetWorkspace()
        workspace_file = self.workspace_file
        if save_dialog or workspace_file == TEMP_WORKSPACE:
            workspace_file, _ = QFileDialog.getSaveFileName(self, "Save workspace", "", "Workspace (*.workspace)")
        if workspace_file != "":
            with open(workspace_file, 'w') as workspace_save_file:
                json.dump(workspace_json, workspace_save_file, indent=4)
            if self.workspace_file != workspace_file:
                self.SetWorkspace(workspace_file)

    def OpenWorkspace(self):
        workspace_file, _ = QFileDialog.getOpenFileName(self, "Open workspace", "", "Workspace (*.workspace)")
        if workspace_file != "":
            self.SetWorkspace(workspace_file)

    def ReadWorkspace(self):
        if os.path.exists(self.workspace_file):
            with open(self.workspace_file, 'r') as workspace_file:
                try:
                    workspace_json = json.loads(workspace_file.read())
                    self.LoadWorkspace(workspace_json)                
                except Exception as exception:
                    self.workspace_file = TEMP_WORKSPACE
                    print(f"Exception occured while to load the state: {exception}")

    def LoadWorkspace(self, workspace_json: dict):
        self.le_url.setText(workspace_json["url"])
        self.cbox_request_type.setCurrentText(workspace_json["request_type"])
        self.headers_table.SetFields(workspace_json["headers"])
        self.body_selector.LoadState(workspace_json)

    def CloseWorkspace(self):
        self.SetWorkspace(TEMP_WORKSPACE)

    def InitActions(self):
        self.tabwidget_req_settings.addTab(self.headers_table, "Headers")
        self.tabwidget_req_settings.addTab(self.params_table, "Params")
        self.tabwidget_req_settings.addTab(self.body_selector, "Body")

        self.cbox_request_type.setEditable(True)
        self.cbox_request_type.lineEdit().setEnabled(False)
        self.cbox_request_type.lineEdit().setReadOnly(True)

        # TODO: make Qt style sheet
        self.cbox_request_type.setStyleSheet("selection-background-color: rgb(0, 0, 0)")

    def ConnectActions(self):
        self.pb_send.clicked.connect(self.SendRequest)
        self.response_signal.connect(self.ProcessResponse)
        self.list_widget_history.selectionModel().selectionChanged.connect(self.LoadHistoryState)
        self.list_widget_responses.selectionModel().selectionChanged.connect(self.DisplayResponseJson)
        self.cbox_request_type.currentTextChanged.connect(self.ChangeRequestTypesColor)
        self.InitializeRequestTypes()

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
            headers = self.headers_table.GetFields()
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
        self.LoadWorkspace(self.request_history[self.list_widget_history.currentRow()])

    @pyqtSlot(dict)
    def ProcessResponse(self, response: dict):
        self.list_widget_responses.addItem(QListWidgetItem(json.dumps(response)))

    def AddRequestHistory(self, request):
        workspace_json = self.GetWorkspace()
        self.request_history.append(workspace_json)
        self.list_widget_history.addItem(str(workspace_json))
        if self.script_ide != None:
            self.script_ide.request_script_signal.emit(request)

class GetmanApp(QtWidgets.QMainWindow):   
    def __init__(self):
        super(GetmanApp, self).__init__()
        self.setWindowTitle("Getman")
        self.getman = Getman(update_title=self.UpdateWindowTitle)
        self.setCentralWidget(self.getman)
        self.InitializeMenu()
        self.showMaximized()

    def closeEvent(self, event):
        save_question = QMessageBox.question(self, "Save workspace?", "Do you want to save your workspace before exiting?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        close = (save_question == QMessageBox.Yes) or (save_question == QMessageBox.No)
        if save_question == QMessageBox.Yes:
            self.getman.SaveWorkspace()
        if close:
            super(GetmanApp, self).closeEvent(event)
        else:
            event.ignore()

    @pyqtSlot(str)
    def UpdateWindowTitle(self, title):
        self.setWindowTitle(title)

    def InitializeMenu(self):
        self.menu_bar = QMenuBar(self)
        self.InitializeFileMenuOptions()
        self.InitializeScriptMenuOptions()
        self.setMenuBar(self.menu_bar)

    def InitializeFileMenuOptions(self):
        file_menu = self.menu_bar.addMenu("File")

        save_action = QAction("Save", self)
        save_action.triggered.connect(lambda : self.getman.SaveWorkspace())
        file_menu.addAction(save_action)

        save_as_action = QAction("Save as", self)
        save_as_action.triggered.connect(lambda : self.getman.SaveWorkspace(save_dialog=True))
        file_menu.addAction(save_as_action)

        open_action = QAction("Open", self)
        open_action.triggered.connect(self.getman.OpenWorkspace)
        file_menu.addAction(open_action)

        close_action = QAction("Close", self)
        close_action.triggered.connect(self.getman.CloseWorkspace)
        file_menu.addAction(close_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def InitializeScriptMenuOptions(self):
        script_menu = self.menu_bar.addMenu("Scripts")
        open_script_ide_action = QAction("Launch IDE", self)
        open_script_ide_action.triggered.connect(self.OpenScriptTool)
        script_menu.addAction(open_script_ide_action)

    def OpenScriptTool(self):
        self.getman.script_ide.request_script_signal.connect(self.getman.script_ide.AddRequestToScript)
        self.getman.script_ide.show()

if __name__ == '__main__':
    q_application = QtWidgets.QApplication(sys.argv)
    q_application.setStyle("Fusion")
    app = GetmanApp()
    app.show()
    sys.exit(q_application.exec_())
