import sys
import os
import json
import signal

from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import QMenuBar, QAction, QListWidgetItem
from PyQt5.QtCore import pyqtSignal, pyqtSlot

from RequestTable import RequestTable
from BodySelector import BodySelection, BodySelector
from RequestHandler import RequestTypes, RequestHandler
from ScripterTool import ScripterTool

DEFAULT_STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".state")
host = None

class Getman(QtWidgets.QWidget):
  response_signal = pyqtSignal(dict)

  def __init__(self, parent = None):
    super(Getman, self).__init__(parent)
    uic.loadUi('ui/Getman.ui', self)
    self.setWindowTitle("Getman")
    self.state_file = DEFAULT_STATE_FILE

    self.request_history = []

    self.headers_table = RequestTable()
    self.params_table = RequestTable()
    self.body_selector = BodySelector()
    # self.scripter_tool = ScripterTool()

    self.tabwidget_req_settings.addTab(self.headers_table, "Headers")
    self.tabwidget_req_settings.addTab(self.params_table, "Params")
    self.tabwidget_req_settings.addTab(self.body_selector, "Body")
    self.ConnectActions()
    self.showMaximized()

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
    self.pb_save.clicked.connect(self.SaveState)
    self.pb_send.clicked.connect(self.SendRequest)
    self.response_signal.connect(self.ProcessResponse)
    self.list_widget_history.selectionModel().selectionChanged.connect(self.LoadHistoryState)
    self.list_widget_responses.selectionModel().selectionChanged.connect(self.DisplayResponseJson)
    self.InitRequestTypes()
    self.OpenState()

  def InitRequestTypes(self):
    for request_type in RequestTypes:
      self.cbox_request_type.addItem(request_type.value, userData=request_type)

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
      self.AddRequestHistory()
      self.response_signal.emit(response_json)

  def DisplayResponseJson(self):
    response = self.list_widget_responses.currentItem().text()
    response_json = json.loads(response)
    self.te_response_json.setText(json.dumps(response_json, indent=4))

  def LoadHistoryState(self):
    self.LoadState(self.request_history[self.list_widget_history.currentRow()])

  @pyqtSlot(dict)
  def ProcessResponse(self, response: dict):
    self.list_widget_responses.addItem(QListWidgetItem(json.dumps(response)))

  def AddRequestHistory(self):
    state_json = self.GetState()
    self.request_history.append(state_json)
    self.list_widget_history.addItem(str(state_json))

def ExceptionHandler(exctype, value, traceback):
  global host
  if host is not None:
    host.SaveState()
  sys.__excepthook__(exctype, value, traceback)
  sys.exit(1)

def RunApp(application):
  global host
  sys.excepthook = ExceptionHandler
  app = QtWidgets.QApplication(sys.argv)
  app.setStyle("Fusion")
  window = application()
  window.show()
  sys.exit(app.exec_())

if __name__ == '__main__':
  RunApp(Getman)
