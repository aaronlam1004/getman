import sys
import os
import json
import signal

from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtCore import pyqtSignal, pyqtSlot

from RequestTable import RequestTable
from BodyEditor import BodyEditor
from RequestHandler import RequestTypes, RequestHandler

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".state")

host = None

class Getman(QtWidgets.QWidget):
  response_signal = pyqtSignal(dict)
  def __init__(self, parent = None):
    super(Getman, self).__init__(parent)
    uic.loadUi('ui/Getman.ui', self)
    self.setWindowTitle("Getman")

    self.headers_table = RequestTable()
    self.body_editor = BodyEditor()

    self.tabwidget_req_settings.addTab(self.headers_table, "Headers")
    self.tabwidget_req_settings.addTab(self.body_editor, "Body")

    self.ConnectActions()

  def closeEvent(self, event):
    self.SaveState()

  def SaveState(self):
    state_json = {}
    state_json["url"] = self.le_url.text()
    state_json["request_type"] = self.cbox_request_type.currentText()
    state_json["body"] = self.body_editor.GetBodyText()
    with open(STATE_FILE, 'w') as state_file:
      json.dump(state_json, state_file, indent=4)

  def LoadState(self):
    if os.path.exists(STATE_FILE):
      with open(STATE_FILE, 'r') as state_file:
        try:
          state_json = json.loads(state_file.read())
          self.le_url.setText(state_json["url"])
          self.cbox_request_type.setCurrentText(state_json["request_type"])
          self.body_editor.LoadState(state_json)
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
      body = self.body_editor.GetBody()
      headers = self.headers_table.GetRequestFields()
      response_json = RequestHandler.Request(url, self.cbox_request_type.currentData(), body=body)
      self.response_signal.emit(response_json)

  @pyqtSlot(dict)
  def ProcessResponse(self, response: dict):
    self.te_response.setText(json.dumps(response, indent=4)) 

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
  host = application()
  host.show()
  sys.exit(app.exec_())

if __name__ == '__main__':
  RunApp(Getman)
