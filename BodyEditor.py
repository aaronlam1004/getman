import sys
import os
import json

from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import QTableWidgetItem

class BodyEditor(QtWidgets.QWidget):
  def __init__(self, parent = None):
    super(BodyEditor, self).__init__(parent)
    uic.loadUi('ui/BodyEditor.ui', self)
    self.ConnectActions()

  def LoadState(self, state_json):
    if "body" in state_json:
      self.te_body.setText(state_json["body"])

  def ConnectActions(self):
    self.te_body.setTabStopWidth(self.te_body.fontMetrics().width(' ') * 4)

  def GetBodyText(self):
    return self.te_body.toPlainText()  

  def GetBody(self):
    body = {}
    try:
      body = json.loads(self.te_body.toPlainText())
    except Exception as exception:
      print(exception)
    return body
