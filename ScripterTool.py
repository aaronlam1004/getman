import sys
import os
import json

from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import QTableWidgetItem

from ScriptHighlighter import JSONHighlighter

class ScripterTool(QtWidgets.QWidget):
  def __init__(self, parent = None):
    super(ScripterTool, self).__init__(parent)
    uic.loadUi('ui/ScripterTool.ui', self)
    self.highlighter = JSONHighlighter(self.te_script_body.document())

  def SetScript(self):
    pass

  def AddRequest(self, request_json):
    curr_text = self.te_script_body.toPlainText()
    if curr_text != "":
      curr_text += '\n'
    self.te_script_body.setText(f"{curr_text}{str(request_json)}")
