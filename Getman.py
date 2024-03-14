import sys
import os
import json

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import pyqtSignal, pyqtSlot

from RequestHandler import RequestTypes, RequestHandler

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".state")
TABLE_HEADER_LABELS = ["Key", "Value", "Description"]

class Getman(QtWidgets.QWidget):
  response_signal = pyqtSignal(dict)

  def __init__(self, parent = None):
    super(Getman, self).__init__(parent)
    self.setWindowTitle("Getman")
    uic.loadUi('Getman.ui', self)

    self.ConnectActions()

  def closeEvent(self, event):
    state_json = {}
    state_json["url"] = self.le_url.text()
    state_json["request_type"] = self.cbox_request_type.currentText()
    with open(STATE_FILE, 'w') as state_file:
      json.dump(state_json, state_file, indent=4)

  def InitState(self):
    if os.path.exists(STATE_FILE):
      with open(STATE_FILE, 'r') as state_file:
        try:
          state_json = json.loads(state_file.read())
          self.le_url.setText(state_json["url"])
          self.cbox_request_type.setCurrentText(state_json["request_type"])
        except Exception as exception:
          print(f"Exception occured while to load the state: {exception}")
          pass 

  def InitRequestTypes(self):
    for request_type in RequestTypes:
      self.cbox_request_type.addItem(request_type.value, userData=request_type)

  def InitTables(self):
    self.tableview_headers.setHorizontalHeaderLabels(TABLE_HEADER_LABELS)

  def ConnectActions(self):
    self.pb_send.clicked.connect(self.SendRequest)
    self.response_signal.connect(self.ProcessResponse)
    self.InitRequestTypes()
    # self.InitTables()
    self.InitState()

  def SendRequest(self):
    url = self.le_url.text()
    if url != "":
      self.response_signal.emit(RequestHandler.Request(url, self.cbox_request_type.currentData()))

  @pyqtSlot(dict)
  def ProcessResponse(self, response: dict):
    self.te_response.setText(str(response))

if __name__ == '__main__':
  app = QtWidgets.QApplication(sys.argv)
  app.setStyle("Fusion")
  Getman = Getman()
  Getman.show()
  sys.exit(app.exec_())
