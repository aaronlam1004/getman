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
from PyQt5.QtWidgets import QMenuBar, QToolBar, QAction, QListWidgetItem, QInputDialog, QMessageBox, QStyle
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QModelIndex, QObject
from PyQt5.QtGui import QBrush, QColor, QFont, QStandardItemModel, QStandardItem

from Defines import REQUEST_TYPE_COLORS
from RequestTable import RequestTable
from BodySelector import BodySelection, BodySelector
from Workspace import Workspace, WORKSPACE_PATH
from GetRequester import GetRequester

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

class Getman(QtWidgets.QMainWindow):
    workspace_updated_signal = pyqtSignal()
    add_request_history_signal = pyqtSignal(str)

    def __init__(self):
        super(Getman, self).__init__()
        uic.loadUi(GetUiPath(__file__, 'ui/Getman.ui'), self)
        self.setWindowTitle("Getman")
        self.opened_requests = {}

        self.explorer_model = ExplorerModel(self)
        self.tree_view_explorer.setModel(self.explorer_model.model)

        self.splitter.setStretchFactor(1, 1)

        self.ConnectActions()
        self.InitWorkspace()
        self.InitMenu()

        self.showMaximized()

    def closeEvent(self, event):
        save = QMessageBox.question(self, "Save workspace?", "Do you want to save your workspace before exiting?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        close = (save == QMessageBox.Yes) or (save == QMessageBox.No)
        if save == QMessageBox.Yes:
            pass
            # self.getman.SaveWorkspace()
        if close:
            super(Getman, self).closeEvent(event)
        else:
            event.ignore()

    def ConnectActions(self):
        self.tree_view_explorer.selectionModel().selectionChanged.connect(self.OpenGetmanRequest)
        self.pb_create_request.clicked.connect(self.CreateGetmanRequest)
        self.pb_delete_request.clicked.connect(self.DeleteGetmanRequest)
        self.tabwidget_getman.tabCloseRequested.connect(self.CloseGetmanRequest)
        self.add_request_history_signal.connect(self.AddRequestToHistory)

    def InitWorkspace(self):
        self.workspace_updated_signal.connect(self.HandleWorkspaceUpdated)
        self.workspace = Workspace(self.workspace_updated_signal)
        self.workspace.Init()

    def CreateWorkspace(self, create_dialog: bool = False):
        if create_dialog or self.workspace.name == "":
            name, ok = QInputDialog.getText(self, "Workspace", "Enter name of workspace:")
            if ok and name != "":
                saved = self.workspace.CreateWorkspace(name, overwrite=False)
                if not saved:
                    overwrite = QMessageBox.question(self, "Overwrite workspace?", f"Workspace {name} already exists. Would you like to overwrite it?", QMessageBox.Yes | QMessageBox.No)
                    if overwrite == QMessageBox.Yes:
                        self.workspace.CreateWorkspace(name, overwrite=True)

    def OpenWorkspace(self):
        if os.path.exists(WORKSPACE_PATH):
            workspaces = os.listdir(WORKSPACE_PATH)
            if len(workspaces) > 0:
                workspace, ok = QInputDialog.getItem(self, "Workspace", "Select workspace:", workspaces, 0, False)
                if ok and workspace != "":
                    self.workspace.SetWorkspace(workspace)

    def HandleWorkspaceUpdated(self):
        self.explorer_model.Clear()
        for request in self.workspace.requests:
            request_json = self.ReadGetmanRequest(self.workspace.GetWorkspaceRequestPath(request))
            self.explorer_model.Add(request, request_json["request_type"])
        workspace = self.workspace.name if self.workspace.name != "" else "Untitled"
        title = f"Getman - {workspace}"
        self.setWindowTitle(title)

    def CreateGetmanRequest(self):
        name, ok = QInputDialog.getText(self, "Request", "Enter name of request:")
        if ok and name != "":
            new_request = GetRequester.EmptyRequest()
            self.workspace.SaveRequestInWorkspace(name, new_request)
            self.workspace.ReloadWorkspace()

    def DeleteGetmanRequest(self):
        if len(self.tree_view_explorer.selectedIndexes()) > 0:
            selected_index = self.tree_view_explorer.selectedIndexes()[ExplorerModel.NAME]
            name = self.explorer_model.Get(selected_index.row(), ExplorerModel.NAME).text()
            delete = QMessageBox.question(self, "Delete request?", "Do you want to delete request?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if delete == QMessageBox.Yes:
                self.tree_view_explorer.clearSelection()
                self.tree_view_explorer.setCurrentIndex(QModelIndex())
                self.explorer_model.RemoveRow(selected_index.row())
                self.workspace.DeleteRequestFromWorkspace(name)

    def OpenGetmanRequest(self, selected, deselected):
        if len(selected.indexes()) > 0:
            name_idx = selected.indexes()[ExplorerModel.NAME]
            request_name = self.explorer_model.Get(name_idx.row(), name_idx.column()).text()
            if request_name not in self.opened_requests:
                request_path = self.workspace.GetWorkspaceRequestPath(request_name)
                request_json = self.ReadGetmanRequest(request_path)
                requester = GetRequester(self)
                requester.LoadRequest(request_json)
                self.tabwidget_getman.addTab(requester, request_name)
                self.opened_requests[request_name] = requester

    def CloseGetmanRequest(self, index):
        self.tabwidget_getman.removeTab(index)

    def ReadGetmanRequest(self, request_file):
        request_json = {}
        if os.path.exists(request_file):
            try:
                with open(request_file, 'r') as request:
                    request_json = json.loads(request.read())
            except Exception as exception:
                print(exception)
        return request_json

    @pyqtSlot(str)
    def AddRequestToHistory(self, request_json):
        self.list_widget_history.addItem(request_json)
        # Open script IDE
        # if self.script_ide != None:
        #     self.script_ide.request_script_signal.emit(request_json)

    def InitMenu(self):
        self.menu_bar = QMenuBar(self)
        self.InitializeFileMenuOptions()
        self.InitializeScriptMenuOptions()
        self.setMenuBar(self.menu_bar)

    def InitializeFileMenuOptions(self):
        file_menu = self.menu_bar.addMenu("File")

        new_workspace_action = QAction("New Workspace", self)
        new_workspace_action.triggered.connect(lambda : self.CreateWorkspace(create_dialog=True))
        file_menu.addAction(new_workspace_action)

        open_action = QAction("Open workspace", self)
        # open_action.triggered.connect(self.getman.OpenWorkspace)
        file_menu.addAction(open_action)


        close_action = QAction("Close workspace", self)
        # close_action.triggered.connect(self.getman.workspace.CloseWorkspace)
        file_menu.addAction(close_action)

        file_menu.addSeparator()

        save_action = QAction("Save workspace", self)
        # save_action.triggered.connect(lambda : self.getman.SaveWorkspace())
        file_menu.addAction(save_action)

        save_as_action = QAction("Save workspace as", self)
        # save_as_action.triggered.connect(lambda : self.getman.SaveWorkspace(save_dialog=True))
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

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
        pass
        # self.getman.script_ide.request_script_signal.connect(self.getman.script_ide.AddRequestToScript)
        # self.getman.script_ide.show()

if __name__ == '__main__':
    q_application = QtWidgets.QApplication(sys.argv)
    q_application.setStyle("Fusion")
    app = Getman()
    app.show()
    sys.exit(q_application.exec_())
