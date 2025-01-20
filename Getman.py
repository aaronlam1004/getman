import sys
import os
import json
import signal
import configparser
from enum import Enum
from typing import Dict, Any

from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import QMenuBar, QToolBar, QAction, QListWidgetItem, QInputDialog, QMessageBox, QStyle, QTreeWidgetItem
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QModelIndex, QObject, QEvent
from PyQt5.QtGui import QBrush, QColor, QFont, QStandardItemModel, QStandardItem

from Defines import REQUEST_TYPE_COLORS
from RequestTable import RequestTable
from BodySelector import BodySelection, BodySelector
from Workspace import Workspace, WORKSPACE_PATH
from Requester import Requester

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
        self.SetupActions()
        self.ConnectActions()
        self.InitWorkspace()
        self.InitMenu()
        self.showMaximized()

    def closeEvent(self, event: QEvent) -> None:
        if self.SaveWorkspace():
            super(Getman, self).closeEvent(event)
        else:
            event.ignore()

    def SetupActions(self) -> None:
        self.tree_Explorer.setColumnCount(2)
        self.tree_Explorer.setHeaderLabels(["Name", "Type"])
        self.splitter.setStretchFactor(1, 1)

    def ConnectActions(self) -> None:
        self.pb_CreateRequest.clicked.connect(self.CreateRequester)
        self.pb_DeleteRequest.clicked.connect(self.DeleteRequester)
        self.tree_Explorer.itemClicked.connect(self.OpenRequester)
        self.tabs_GetRequests.tabCloseRequested.connect(self.CloseRequester)
        self.add_request_history_signal.connect(self.AddRequestToHistory)

    # -- Workspace --
    def InitWorkspace(self) -> None:
        self.workspace_updated_signal.connect(self.UpdateWorkspace)
        self.workspace = Workspace(self.workspace_updated_signal)
        self.workspace.Init()

    def CreateWorkspace(self, prompt: bool = False) -> bool:
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

    def OpenWorkspace(self) -> None:
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

    def SaveWorkspaceRequests(self) -> None:
        for requester in self.opened_requests:
            requester.SaveRequest()

    def CloseWorkspace(self) -> None:
        if self.SaveWorkspace(): 
            self.workspace.CloseWorkspace()
            self.tree_Explorer.clear()
            for _ in range(self.tabs_GetRequests.count()):
                self.tabs_GetRequests.removeTab(0)

    def UpdateWorkspace(self) -> None:
        self.tree_Explorer.clear()
        for request in self.workspace.requests:
            request_json = self.ReadRequester(self.workspace.GetWorkspaceRequestPath(request))
            tree_widget_item = QTreeWidgetItem(self.tree_Explorer)
            tree_widget_item.setText(0, request)
            tree_widget_item.setText(1, request_json["type"])
            self.tree_Explorer.insertTopLevelItem(self.tree_Explorer.columnCount(), tree_widget_item)
        workspace = self.workspace.name if self.workspace.name != "" else "Untitled"
        title = f"Getman - {workspace}"
        self.setWindowTitle(title)

    # -- Requester(s) --
    def CreateRequester(self) -> None:
        name, ok = QInputDialog.getText(self, "Request", "Enter name of request:")
        if ok and name != "":
            if self.workspace.IsLoaded() or self.CreateWorkspace(prompt=True):
                new_request = Requester.EmptyRequester()
                self.workspace.SaveRequestInWorkspace(name, new_request)
                self.workspace.ReloadWorkspace()

    def DeleteRequester(self) -> None:
        selected_items = self.tree_Explorer.selectedItems()
        if len(selected_items) == 1:
            item = selected_items[0]
            request_name = item.text(0)
            delete = QMessageBox.question(self, "Delete request?", "Do you want to delete request?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if delete == QMessageBox.Yes:
                self.tree_Explorer.clearSelection()
                self.tree_Explorer.takeTopLevelItem(self.tree_Explorer.indexOfTopLevelItem(item))
                self.workspace.DeleteRequestFromWorkspace(request_name)
                index = self.FindOpenRequester(request_name)
                if index != -1:
                    self.CloseRequester(index, prompt=False)

    def OpenRequester(self, item: QTreeWidgetItem, column: int) -> None:
        request_name = item.text(0)
        index = self.FindOpenRequester(request_name)
        if index == -1:
            request_path = self.workspace.GetWorkspaceRequestPath(request_name)
            request_json = self.ReadRequester(request_path)
            requester = Requester(request_name, self)
            requester.LoadRequest(request_json)
            self.tabs_GetRequests.addTab(requester, request_name)
            self.tabs_GetRequests.setCurrentIndex(self.tabs_GetRequests.count() - 1)
            self.opened_requests.append(requester)
        else:
            self.tabs_GetRequests.setCurrentIndex(index)

    def FindOpenRequester(self, request_name: str) -> int:
        for index, requester in enumerate(self.opened_requests):
            if requester.GetName() == request_name:
                return index
        return -1

    def SaveRequester(self, requester: Requester) -> bool:
        close = True
        save = QMessageBox.question(self, "Save request?", "Do you want to save request?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        if save == QMessageBox.Yes:
            requester.SaveRequest()
        elif save == QMessageBox.Cancel:
            close = False
        return close
            
    def ReadRequester(self, request_file: str) -> Dict[str, Any]:
        request_json = {}
        if os.path.exists(request_file):
            try:
                with open(request_file, 'r') as request:
                    request_json = json.loads(request.read())
            except Exception as exception:
                print(exception)
        return request_json

    def CloseRequester(self, index: int, prompt = True) -> None:
        requester = self.opened_requests[index]
        if not prompt:
            self.tabs_GetRequests.removeTab(index)
            self.opened_requests.pop(index) 
        elif self.SaveRequester(requester):
            self.tabs_GetRequests.removeTab(index)
            self.opened_requests.pop(index) 
        self.tree_Explorer.clearSelection()

    # -- Signals --
    @pyqtSlot(str)
    def AddRequestToHistory(self, request_json: Dict[str, Any]) -> None:
        self.list_RequestHistory.addItem(request_json)

    @pyqtSlot(str)
    def UpdateRequestTypeInExplorer(self, request_type: str):
        print(request_type)
        pass

    # -- Menu --
    def InitMenu(self) -> None:
        self.menu_bar = QMenuBar(self)
        self.InitFileMenuOptions()
        self.setMenuBar(self.menu_bar)

    def InitFileMenuOptions(self) -> None:
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

        # save_as_action = QAction("Save workspace as", self)
        # save_as_action.triggered.connect(lambda : self.CreateWorkspace(prompt=True))
        # file_menu.addAction(save_as_action)

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
