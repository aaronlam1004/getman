import sys
import os
import json
import signal
import configparser
from enum import Enum

from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import QMenuBar, QToolBar, QAction, QListWidgetItem, QInputDialog, QMessageBox, QStyle, QTreeWidgetItem
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QModelIndex, QObject
from PyQt5.QtGui import QBrush, QColor, QFont, QStandardItemModel, QStandardItem

from Defines import REQUEST_TYPE_COLORS
from RequestTable import RequestTable
from BodySelector import BodySelection, BodySelector
from Workspace import Workspace, WORKSPACE_PATH
from GetRequester import GetRequester

from Utils import GetUiPath
from RequestHandler import RequestTypes, RequestHandler
from JsonHighlighter import JsonHighlighter

class Getman(QtWidgets.QMainWindow):
    workspace_updated_signal = pyqtSignal()
    add_request_history_signal = pyqtSignal(str)

    def __init__(self):
        super(Getman, self).__init__()
        uic.loadUi(GetUiPath(__file__, 'ui/Getman.ui'), self)
        self.setWindowTitle("Getman")
        self.opened_requests = []

        self.tree_widget_explorer.setColumnCount(2)
        self.splitter.setStretchFactor(1, 1)

        self.ConnectActions()
        self.InitWorkspace()
        self.InitMenu()

        self.showMaximized()

    def closeEvent(self, event):
        if self.SaveWorkspace():
            super(Getman, self).closeEvent(event)
        else:
            event.ignore()

    def ConnectActions(self):
        self.tree_widget_explorer.itemClicked.connect(self.OpenRequest)
        self.pb_create_request.clicked.connect(self.CreateRequest)
        self.pb_delete_request.clicked.connect(self.DeleteRequest)
        self.tabwidget_getman.tabCloseRequested.connect(self.CloseRequest)
        self.add_request_history_signal.connect(self.AddRequestToHistory)

    # -- Workspace --
    def InitWorkspace(self):
        self.workspace_updated_signal.connect(self.UpdateWorkspace)
        self.workspace = Workspace(self.workspace_updated_signal)
        self.workspace.Init()

    def CreateWorkspace(self, prompt: bool = False):
        saved = False
        if prompt or self.workspace.name == "":
            name, ok = QInputDialog.getText(self, "Workspace", "Enter name of workspace:")
            if ok and name != "":
                saved = self.workspace.CreateWorkspace(name, overwrite=False)
                if not saved:
                    overwrite = QMessageBox.question(self, "Overwrite workspace?", f"Workspace {name} already exists. Would you like to overwrite it?", QMessageBox.Yes | QMessageBox.No)
                    if overwrite == QMessageBox.Yes:
                        saved = self.workspace.CreateWorkspace(name, overwrite=True)
        return saved

    def OpenWorkspace(self):
        if os.path.exists(WORKSPACE_PATH):
            workspaces = os.listdir(WORKSPACE_PATH)
            if len(workspaces) > 0:
                workspace, ok = QInputDialog.getItem(self, "Workspace", "Select workspace:", workspaces, 0, False)
                if ok and workspace != "":
                    self.workspace.SetWorkspace(workspace)

    def SaveWorkspace(self):
        close = True
        save = QMessageBox.question(self, "Save workspace?", "Do you want to save your workspace before exiting?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        if save == QMessageBox.Yes:
            self.SaveWorkspaceRequests()
        elif save == QMessageBox.Cancel:
            close = False
        return close

    def SaveWorkspaceRequests(self):
        for requester in self.opened_requests:
            requester.SaveRequest()

    def CloseWorkspace(self):
        if self.SaveWorkspace(): 
            self.workspace.CloseWorkspace()
            self.tree_widget_explorer.clear()
            for _ in range(self.tabwidget_getman.count()):
                self.tabwidget_getman.removeTab(0)

    def UpdateWorkspace(self):
        self.tree_widget_explorer.clear()
        for request in self.workspace.requests:
            request_json = self.ReadRequest(self.workspace.GetWorkspaceRequestPath(request))
            tree_widget_item = QTreeWidgetItem(self.tree_widget_explorer)
            tree_widget_item.setText(0, request)
            self.tree_widget_explorer.insertTopLevelItem(self.tree_widget_explorer.columnCount(), tree_widget_item)
        workspace = self.workspace.name if self.workspace.name != "" else "Untitled"
        title = f"Getman - {workspace}"
        self.setWindowTitle(title)

    # -- Request(s) --
    def CreateRequest(self):
        name, ok = QInputDialog.getText(self, "Request", "Enter name of request:")
        if ok and name != "":
            if self.workspace.IsLoaded() or self.CreateWorkspace(prompt=True):
                new_request = GetRequester.EmptyRequest()
                self.workspace.SaveRequestInWorkspace(name, new_request)
                self.workspace.ReloadWorkspace()

    def DeleteRequest(self):
        selected_items = self.tree_widget_explorer.selectedItems()
        if len(selected_items) == 1:
            item = selected_items[0]
            request_name = item.text(0)
            delete = QMessageBox.question(self, "Delete request?", "Do you want to delete request?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if delete == QMessageBox.Yes:
                self.tree_widget_explorer.clearSelection()
                self.tree_widget_explorer.takeTopLevelItem(self.tree_widget_explorer.indexOfTopLevelItem(item))
                self.workspace.DeleteRequestFromWorkspace(request_name)
                index = self.FindOpenRequest(request_name)
                if index != -1:
                    self.CloseRequest(index, prompt=False)

    def OpenRequest(self, item, column):
        request_name = item.text(0)
        index = self.FindOpenRequest(request_name)
        if index == -1:
            request_path = self.workspace.GetWorkspaceRequestPath(request_name)
            request_json = self.ReadRequest(request_path)
            requester = GetRequester(request_name, self)
            requester.LoadRequest(request_json)
            self.tabwidget_getman.addTab(requester, request_name)
            self.tabwidget_getman.setCurrentIndex(self.tabwidget_getman.count() - 1)
            self.opened_requests.append(requester)
        else:
            self.tabwidget_getman.setCurrentIndex(index)
        self.tree_widget_explorer.clearSelection()

    def FindOpenRequest(self, request_name):
        for index, requester in enumerate(self.opened_requests):
            if requester.GetName() == request_name:
                return index
        return -1

    def SaveRequest(self, requester):
        close = True
        save = QMessageBox.question(self, "Save request?", "Do you want to save request?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        if save == QMessageBox.Yes:
            requester.SaveRequest()
        elif save == QMessageBox.Cancel:
            close = False
        return close
            
    def ReadRequest(self, request_file):
        request_json = {}
        if os.path.exists(request_file):
            try:
                with open(request_file, 'r') as request:
                    request_json = json.loads(request.read())
            except Exception as exception:
                print(exception)
        return request_json

    def CloseRequest(self, index, prompt = True):
        requester = self.opened_requests[index]
        if not prompt:
            self.tabwidget_getman.removeTab(index)
            self.opened_requests.pop(index) 
        elif self.SaveRequest(requester):
            self.tabwidget_getman.removeTab(index)
            self.opened_requests.pop(index) 

    @pyqtSlot(object)
    def ProcessResponse(self, response: dict):
        self.list_widget_responses.addItem(QListWidgetItem(json.dumps(response)))

    @pyqtSlot(str)
    def AddRequestToHistory(self, request_json):
        self.list_widget_history.addItem(request_json)

    def InitMenu(self):
        self.menu_bar = QMenuBar(self)
        self.InitFileMenuOptions()
        self.setMenuBar(self.menu_bar)

    def InitFileMenuOptions(self):
        file_menu = self.menu_bar.addMenu("File")

        new_workspace_action = QAction("New Workspace", self)
        new_workspace_action.triggered.connect(lambda : self.CreateWorkspace(prompt=True))
        file_menu.addAction(new_workspace_action)

        open_action = QAction("Open workspace", self)
        open_action.triggered.connect(self.OpenWorkspace)
        file_menu.addAction(open_action)

        close_action = QAction("Close workspace", self)
        close_action.triggered.connect(self.CloseWorkspace)
        file_menu.addAction(close_action)

        file_menu.addSeparator()

        save_action = QAction("Save workspace", self)
        save_action.triggered.connect(self.SaveWorkspaceRequests)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save workspace as", self)
        # save_as_action.triggered.connect(lambda : self.getman.SaveWorkspace(save_dialog=True))
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

if __name__ == '__main__':
    q_application = QtWidgets.QApplication(sys.argv)
    q_application.setStyle("Fusion")
    app = Getman()
    app.show()
    sys.exit(q_application.exec_())
