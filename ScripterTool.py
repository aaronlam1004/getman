import sys
import os
import json

from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import QTableWidgetItem

from ScriptHighlighter import ScriptHighlighter
from ScriptCompiler import CompileStatus, ScriptCompiler
from ScriptRunner import ScriptRunner

class ScripterTool(QtWidgets.QWidget):
  def __init__(self, parent = None):
    super(ScripterTool, self).__init__(parent)
    uic.loadUi('ui/ScripterTool.ui', self)
    self.highlighter = ScriptHighlighter(self.te_script_body.document())
    self.ConnectActions()

  def ConnectActions(self):
    self.pb_run_script.clicked.connect(self.RunScript)

  def SetScriptBody(self):
    pass

  def RunScript(self):
    commands = self.te_script_body.toPlainText().split('\n')
    compile_status = ScriptCompiler.Compile(commands)
    if compile_status["status"] != CompileStatus.OK.value:
      print(compile_status["error"])
    else:
      runner = ScriptRunner()
      runner.Run(compile_status["commands"]) 

  def AddRequest(self, request_json):
    curr_text = self.te_script_body.toPlainText()
    if curr_text != "":
      curr_text += '\n'
    new_text = f"{curr_text}REQ {str(request_json)}".replace('\'', '\"').replace("None", "null")
    self.te_script_body.setText(new_text)
