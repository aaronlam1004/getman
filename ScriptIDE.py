import sys
import os
import json

from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import QTableWidgetItem, QStyledItemDelegate
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt

from ScriptHighlighter import ScriptHighlighter
from ScriptCompiler import CompileStatus, ScriptCompiler
from ScriptRunner import ScriptRunner

class ScriptListDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.text = f"{index.row() + 1}: {option.text}"

class ScriptIDE(QtWidgets.QWidget):
    request_script_signal = pyqtSignal(str)

    def __init__(self, parent = None):
        super(ScriptIDE, self).__init__(parent)
        uic.loadUi('ui/ScriptIDE.ui', self)
        self.highlighter = ScriptHighlighter(self.te_script_step_editor.document())
        self.list_script_steps_delegate = ScriptListDelegate(self.list_script_steps)
        self.list_script_steps.setItemDelegate(self.list_script_steps_delegate)
        self.ConnectActions()

    def keyPressEvent(self, event):
        if self.list_script_steps.hasFocus():
            if event.key() == Qt.Key_Return:
                if self.list_script_steps.count() == 0 or self.list_script_steps.item(self.list_script_steps.count() - 1).text() != "":
                    self.AddEmptyScriptStep()
            elif event.key() == Qt.Key_Backspace or event.key() == Qt.Key_Delete:
                print("Delete")

    def ConnectActions(self):
        self.list_script_steps.itemSelectionChanged.connect(self.EnableEditScriptStep)
        self.te_script_step_editor.textChanged.connect(self.UpdateScriptStep)
        self.pb_run_script.clicked.connect(self.RunScript)

    def EnableEditScriptStep(self):
        self.te_script_step_editor.setEnabled(True)
        self.te_script_step_editor.setText(self.list_script_steps.currentItem().text())

    def UpdateScriptStep(self):
        script_step_text = self.te_script_step_editor.toPlainText().replace('\n', ' ')
        self.list_script_steps.currentItem().setText(script_step_text)

    def AddEmptyScriptStep(self):
        self.list_script_steps.addItem("")
        self.list_script_steps.setCurrentRow(self.list_script_steps.count() - 1)

    @pyqtSlot(str)
    def AddRequestToScript(self, request_json):
        script_text = f"SEND {request_json};"
        last_step = self.list_script_steps.item(self.list_script_steps.count() - 1)
        if last_step is None or last_step.text() != "":
            self.list_script_steps.addItem(script_text)
        else:
            last_step.setText(script_text)
        self.list_script_steps.setCurrentRow(self.list_script_steps.count() - 1)
        self.te_script_step_editor.setText(self.list_script_steps.currentItem().text())

    def RunScript(self):
        script_steps = []
        for i in range(self.list_script_steps.count()):
           script_steps.append(self.list_script_steps.item(i).text())
        compile_status = ScriptCompiler.Compile(script_steps)
        if compile_status["status"] == CompileStatus.OK:
            script_runner = ScriptRunner()
            script_runner.Run(compile_status["script"])

if __name__ == '__main__':
    q_application = QtWidgets.QApplication(sys.argv)
    q_application.setStyle("Fusion")
    script_ide = ScriptIDE()
    script_ide.show()
    sys.exit(q_application.exec_())
