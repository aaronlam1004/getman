import sys
import os
import json
import signal

from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import QMenuBar, QAction
from PyQt5.QtCore import pyqtSignal, pyqtSlot

from RequestTable import RequestTable
from BodySelector import BodySelection, BodySelector 
from RequestHandler import RequestTypes, RequestHandler

DEFAULT_STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".state")
host = None

class Getman(QtWidgets.QWidget):
  response_signal = pyqtSignal(dict)
  def __init__(self, parent = None):
    super(Getman, self).__init__(parent)
    uic.loadUi('ui/Getman.ui', self)
    self.setWindowTitle("Getman")
    self.state_file = DEFAULT_STATE_FILE

    self.headers_table = RequestTable()
    self.body_selector = BodySelector()

    self.tabwidget_req_settings.addTab(self.headers_table, "Headers")
    self.tabwidget_req_settings.addTab(self.body_selector, "Body")

    self.ConnectActions()

  def closeEvent(self, event):
    self.SaveState()

  def SaveState(self):
    state_json = {}
    state_json["state_file"] = self.state_file
    state_json["url"] = self.le_url.text()
    state_json["request_type"] = self.cbox_request_type.currentText()
    body_selection, body_data = self.body_selector.GetBodyData(json_string = True)
    state_json["body"] = {
      "body_selection": body_selection,
      "body_data": body_data
    }
    with open(self.state_file, 'w') as state_file:
      json.dump(state_json, state_file, indent=4)

  def LoadState(self):
    if os.path.exists(self.state_file):
      with open(self.state_file, 'r') as state_file:
        try:
          state_json = json.loads(state_file.read())
          self.le_url.setText(state_json["url"])
          self.cbox_request_type.setCurrentText(state_json["request_type"])
          self.body_selector.LoadState(state_json)
        except Exception as exception:
          print(f"Exception occured while to load the state: {exception}")
          pass 

  def InitRequestTypes(self):
    for request_type in RequestTypes:
      self.cbox_request_type.addItem(request_type.value, userData=request_type)

  def ConnectActions(self):
    self.pb_send.clicked.connect(self.SendRequest)
    self.response_signal.connect(self.ProcessResponse)
    self.InitRequestTypes()
    self.LoadState()

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

      response_json = RequestHandler.Request(url, self.cbox_request_type.currentData(), body=body, form=form)
      self.response_signal.emit(response_json)

  @pyqtSlot(dict)
  def ProcessResponse(self, response: dict):
    self.te_response.setText(json.dumps(response, indent=4)) 

class GetmanWindow(QtWidgets.QMainWindow):
  def __init__(self, application):
    super(GetmanWindow, self).__init__()
    self.InitMenu()
    self.app = application()
    self.setCentralWidget(self.app)

  def closeEvent(self, event):
    self.app.closeEvent(event)

  def InitMenu(self):
    self.menu_bar = QMenuBar(self)
    self.setMenuBar(self.menu_bar)
    self.menu_bar.setNativeMenuBar(False)
    self.InitFileMenu()

  def InitFileMenu(self):
    file_menu = self.menu_bar.addMenu("File")
    save_action = QAction("Save", self)
    file_menu.addAction(save_action)
    exit_action = QAction("Exit", self)
    exit_action.triggered.connect(self.close)
    file_menu.addAction(exit_action)

def ExceptionHandler(exctype, value, traceback):
  global host
  if host is not None:
    host.SaveState()
  sys.__excepthook__(exctype, value, traceback)
  sys.exit(1)

def RunApp(window, application):
  global host
  sys.excepthook = ExceptionHandler
  app = QtWidgets.QApplication(sys.argv)
  app.setStyle("Fusion")
  window = window(application)
  window.show()
  sys.exit(app.exec_())

if __name__ == '__main__':
  RunApp(GetmanWindow, Getman)
