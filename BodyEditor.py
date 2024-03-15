import sys
import os
import json

from PyQt5 import QtWidgets, QtCore, uic

class BodyEditor(QtWidgets.QWidget):
  def __init__(self, parent = None):
    super(BodyEditor, self).__init__(parent)
    uic.loadUi('ui/BodyEditor.ui', self)
    self.ConnectActions()

  def ConnectActions(self):
    self.te_body.setTabStopWidth(self.te_body.fontMetrics().width(' ') * 4)

  def SetBodyText(self, body_data):
    self.te_body.setText(str(body_data))

  def GetBodyText(self):
    return self.te_body.toPlainText()  

  def GetBody(self):
    body = {}
    try:
      body = json.loads(self.te_body.toPlainText())
    except Exception as exception:
      print(exception)
    return body
