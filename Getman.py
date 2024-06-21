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

from Utils import GetUiPath
from RequestHandler import RequestTypes, RequestHandler
from GetScriptIDE import GetScriptIDE
from JsonHighlighter import JsonHighlighter

class ExplorerModel:
    NAME, TYPE = range(2)
    def __init__(self, parent):
        self.model = QStandardItemModel(0, 2, parent)
        self.model.setHorizontalHeaderLabels(["Name", "Type"])
        self.count = 0

    def Add(self, request_name="", request_type=""):
        req_name = QStandardItem(request_name)
        req_type = QStandardItem(request_type)
        req_type.setEditable(False)
        self.model.appendRow([req_name, req_type])
        self.count += 1

    def Get(self, row, col):
        return self.model.item(row, col)

    def RemoveRow(self, row):
        self.model.removeRow(row)

    def Clear(self):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(["Name", "Type"])
        self.count = 0

class Getman(QtWidgets.QWidget):
    response_signal = pyqtSignal(object)
    workspace_updated_signal = pyqtSignal()

    def __init__(self, parent=None):
        super(Getman, self).__init__(parent)
        uic.loadUi(GetUiPath(__file__, 'ui/Getman.ui'), self)
        self.parent = parent
       
        self.request_name = ""
        self.request_json = self.GetEmptyRequest()

        self.response_highlighter = JsonHighlighter(self.te_response_json.document())
        self.headers_table = RequestTable()
        self.params_table = RequestTable()
        self.body_selector = BodySelector()
        self.script_ide = GetScriptIDE()
        self.explorer_model = ExplorerModel(self)
        self.tree_view_explorer.setModel(self.explorer_model.model)

        self.InitActions()
        self.ConnectActions()

        self.workspace = Workspace(self.workspace_updated_signal) 
        self.workspace.Init()

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
        # Explorer
        self.tree_view_explorer.selectionModel().selectionChanged.connect(self.SetRequest)
        self.workspace_updated_signal.connect(self.HandleWorkspaceUpdated)

        # Request
        self.pb_create_request.clicked.connect(self.CreateRequest)
        self.pb_delete_request.clicked.connect(self.DeleteRequest)
        self.pb_send.clicked.connect(self.SendRequest)
        self.cbox_request_type.currentTextChanged.connect(self.ChangeRequestTypesColor)
        self.InitializeRequestTypes()

        # Response
        self.response_signal.connect(self.ProcessResponse)

        # History
        self.list_widget_responses.selectionModel().selectionChanged.connect(self.DisplayResponseJson)

    def ChangeRequestTypesColor(self):
        color = REQUEST_TYPE_COLORS[self.cbox_request_type.currentData()]
        font = QFont()
        font.setBold(True)
        self.cbox_request_type.lineEdit().setFont(font)
        self.cbox_request_type.lineEdit().setStyleSheet(f"color: {color}")

    def InitializeRequestTypes(self):
        for i, (request_type, color) in enumerate(REQUEST_TYPE_COLORS.items()):
            font = QFont()
            font.setBold(True)
            brush = QBrush(QColor(color))
            self.cbox_request_type.addItem(request_type.value, userData=request_type)
            self.cbox_request_type.setItemData(i, brush, Qt.TextColorRole)
            self.cbox_request_type.setItemData(i, font, Qt.FontRole)

    def HandleWorkspaceUpdated(self):
        self.explorer_model.Clear()
        for request in self.workspace.requests:
            request_json = self.ReadRequest(self.workspace.GetRequestJsonPath(request))
            self.explorer_model.Add(request, request_json["request_type"])
        workspace = self.workspace.name if self.workspace.name != "" else "Untitled"
        title = f"Getman - {workspace}"
        if self.parent is None:
            self.setWindowTitle(title)
        else:
            self.parent.setWindowTitle(title)

    def SaveWorkspace(self, save_dialog: bool = False):
        if save_dialog or self.workspace.name == "":
            name, ok = QInputDialog.getText(self, "Workspace", "Enter name of workspace:")
            if ok and name != "":
                saved = self.workspace.SaveWorkspace(name, overwrite=False)
                if not saved:
                    overwrite = QMessageBox.question(self, "Overwrite workspace?", f"Workspace {name} already exists. Would you like to overwrite it?", QMessageBox.Yes | QMessageBox.No)
                    if overwrite == QMessageBox.Yes:
                        self.workspace.SaveWorkspace(name, overwrite=True)

    def OpenWorkspace(self):
        if os.path.exists(WORKSPACE_PATH):
            workspaces = os.listdir(WORKSPACE_PATH)
            if len(workspaces) > 0:
                workspace, ok = QInputDialog.getItem(self, "Workspace", "Select workspace:", workspaces, 0, False)
                if ok and workspace != "":
                    self.workspace.SetWorkspace(workspace)

    def GetEmptyRequest(self):
        return {
            "url": "",
            "request_type": "GET",
            "params": {},
            "headers": {},
            "body": {
                "body_selection": BodySelection.NONE,
                "body_data" : {}
            }
        }
    
    def ReadRequest(self, request_file):
        request_json = {}
        if os.path.exists(request_file):
            try:
                with open(request_file, 'r') as request:
                    request_json = json.loads(request.read())
            except Exception as exception:
                print(exception)
        return request_json

    def SetRequest(self, selected, deselected):
        for selected_index in selected.indexes():
            if selected_index.column() == self.explorer_model.NAME:
                name = self.explorer_model.Get(selected_index.row(), selected_index.column()).text()
                self.request_name = name
                self.request_json = self.ReadRequest(self.workspace.GetRequestJsonPath(name))
                self.LoadRequest(self.request_json)

    def GetRequest(self):
        request_json = self.GetEmptyRequest()
        request_json["url"] = self.le_url.text()
        request_json["request_type"] = self.cbox_request_type.currentText()
        request_json["params"] = self.params_table.GetFields()
        request_json["headers"] = self.headers_table.GetFields()
        body_selection, body_data = self.body_selector.GetBodyData(json_string = True)
        request_json["body"]["body_selection"] = body_selection
        request_json["body"]["body_data"] = body_data
        return request_json

    def LoadRequest(self, request_json: dict):
        # TODO: handle try-except errors
        try:
            self.le_url.setText(request_json["url"])
            self.cbox_request_type.setCurrentText(request_json["request_type"])
            self.params_table.SetFields(request_json["params"])
            self.headers_table.SetFields(request_json["headers"])
            self.body_selector.LoadState(request_json)
        except:
            pass

    def CreateRequest(self):
        if self.request_name != "":
            self.workspace.SaveRequestInWorkspace(self.request_name, self.GetRequest(), overwrite=True)
        name, ok = QInputDialog.getText(self, "Request", "Enter name of request:")
        if ok and name != "":
            new_request = self.GetEmptyRequest()
            self.workspace.SaveRequestInWorkspace(name, new_request)
            self.workspace.ReloadWorkspace()

    def DeleteRequest(self):
        if len(self.tree_view_explorer.selectedIndexes()) > 0:
            selected_index = self.tree_view_explorer.selectedIndexes()[0]
            name = self.explorer_model.Get(selected_index.row(), 0).text()
            delete = QMessageBox.question(self, "Delete request?", "Do you want to delete request?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if delete == QMessageBox.Yes:
                self.explorer_model.RemoveRow(selected_index.row())
                self.workspace.DeleteRequestFromWorkspace(name)

    def SendRequest(self):
        url = self.le_url.text()
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
            request, response_json = RequestHandler.Request(url, self.cbox_request_type.currentData(), params=params, headers=headers, body=body, form=form)
            self.AddRequestHistory(RequestHandler.GetJsonFromRequest(request))
            self.response_signal.emit(response_json)

    def DisplayResponseJson(self):
        response = self.list_widget_responses.currentItem().text()
        if response is not None:
            response_json = json.loads(response)
            self.te_response_json.setText(json.dumps(response_json, indent=4))

    @pyqtSlot(object)
    def ProcessResponse(self, response: dict):
        self.list_widget_responses.addItem(QListWidgetItem(json.dumps(response)))

    def AddRequestHistory(self, request_json):
        self.list_widget_history.addItem(request_json)
        if self.script_ide != None:
            self.script_ide.request_script_signal.emit(request_json)

class GetmanApp(QtWidgets.QMainWindow):   
    def __init__(self):
        super(GetmanApp, self).__init__()
        self.setWindowTitle("Getman")
        self.getman = Getman(self)
        self.setCentralWidget(self.getman)
        self.InitializeMenu()
        self.showMaximized()

    def closeEvent(self, event):
        save = QMessageBox.question(self, "Save workspace?", "Do you want to save your workspace before exiting?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        close = (save == QMessageBox.Yes) or (save == QMessageBox.No)
        if save == QMessageBox.Yes:
            self.getman.SaveWorkspace()
        if close:
            super(GetmanApp, self).closeEvent(event)
        else:
            event.ignore()

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
        close_action.triggered.connect(self.getman.workspace.CloseWorkspace)
        file_menu.addAction(close_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def InitializeScriptMenuOptions(self):
        pass 
        # script_menu = self.menu_bar.addMenu("Scripts")
        # open_script_ide_action = QAction("Launch IDE", self)
        # open_script_ide_action.triggered.connect(self.OpenScriptTool)
        # script_menu.addAction(open_script_ide_action)

    def OpenScriptTool(self):
        self.getman.script_ide.request_script_signal.connect(self.getman.script_ide.AddRequestToScript)
        self.getman.script_ide.show()

if __name__ == '__main__':
    q_application = QtWidgets.QApplication(sys.argv)
    q_application.setStyle("Fusion")
    app = GetmanApp()
    app.show()
    sys.exit(q_application.exec_())
