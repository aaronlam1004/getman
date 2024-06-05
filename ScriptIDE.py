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

        # Setup editor
        self.highlighter = ScriptHighlighter(self.te_script_step_editor.document())
        self.list_script_steps_delegate = ScriptListDelegate(self.list_script_steps)
        self.list_script_steps.setItemDelegate(self.list_script_steps_delegate)
        self.te_script_step_editor.installEventFilter(self)

        # Setup script runner
        self.script_runner = ScriptRunner()
        self.script_debugging = False
        
        self.ConnectActions()

    def eventFilter(self, obj, event):
        if obj is self.te_script_step_editor and event.type() == QtCore.QEvent.KeyPress:
            if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
                self.AddScriptStep()
                return True
        return super(ScriptIDE, self).eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            if self.list_script_steps.count() == 0 or self.list_script_steps.item(self.list_script_steps.count() - 1).text() != "":
                self.AddScriptStep()
        if self.list_script_steps.hasFocus():   
            if event.key() == Qt.Key_Backspace or event.key() == Qt.Key_Delete:
                self.DeleteScriptSteps()

    def ConnectActions(self):
        self.list_script_steps.itemSelectionChanged.connect(self.EnableEditScriptStep)
        self.te_script_step_editor.textChanged.connect(self.UpdateScriptStep)
        self.pb_run_script.clicked.connect(lambda: self.StartScript(debug=False))
        self.pb_debug_script.clicked.connect(lambda: self.StartScript(debug=True))
        self.pb_step_script.clicked.connect(lambda: self.RunScript(debug=True))

    def EnableEditScriptStep(self):
        if self.list_script_steps.currentItem() is not None:
            self.te_script_step_editor.setEnabled(True)
            self.te_script_step_editor.setText(self.list_script_steps.currentItem().text())
        else:
            self.te_script_step_editor.setEnabled(False)
            self.te_script_step_editor.setText("")

    def AddScriptStep(self, step_text=""):
        self.list_script_steps.addItem(step_text)
        self.list_script_steps.setCurrentRow(self.list_script_steps.count() - 1)
        item = self.list_script_steps.currentItem()
        item.setCheckState(Qt.Unchecked)
        self.te_script_step_editor.setFocus()

    @pyqtSlot(str)
    def AddRequestToScript(self, request_json):
        step_text = f"SEND {request_json};"
        last_step = self.list_script_steps.item(self.list_script_steps.count() - 1)
        if last_step is None or last_step.text() != "":
            self.AddScriptStep(step_text)
        else:
            last_step.setText(step_text)
            self.list_script_steps.setCurrentRow(self.list_script_steps.count() - 1)
            self.te_script_step_editor.setFocus()

    def UpdateScriptStep(self):
        if self.list_script_steps.currentItem() is not None:
            script_step_text = self.te_script_step_editor.toPlainText().replace('\n', ' ')
            self.list_script_steps.currentItem().setText(script_step_text)

    def DeleteScriptSteps(self):
        for item in self.list_script_steps.selectedItems():
            self.list_script_steps.takeItem(self.list_script_steps.row(item))

    def CompileScript(self):
        script_steps = []
        for i in range(self.list_script_steps.count()):
           script_steps.append(self.list_script_steps.item(i).text())
        return script_steps

    def StartScript(self, debug: bool = False):
        compile_status = ScriptCompiler.Compile(self.CompileScript())
        if compile_status["status"] == CompileStatus.OK:
            self.script_runner.Load(compile_status["script"])
            if not debug:
                self.RunScript()
        else:
            error_output = f"Line {compile_status['line_number']} : {compile_status['error']}"
            self.te_console_output.setText(error_output)

    def RunScript(self, debug: bool = False):
        script_output = self.script_runner.Run(verbose=True, step=True)
        self.te_console_output.setText('\n'.join(script_output))

if __name__ == '__main__':
    q_application = QtWidgets.QApplication(sys.argv)
    q_application.setStyle("Fusion")
    script_ide = ScriptIDE()
    script_ide.show()
    sys.exit(q_application.exec_())
