import sys
import os
import json

from PyQt5 import QtWidgets, QtCore, uic

from utils.Paths import GetUIPath

class BodyEditor(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super(BodyEditor, self).__init__(parent)
        uic.loadUi(GetUIPath('BodyEditor.ui'), self)
        self.ConnectActions()

    def ConnectActions(self):
        self.te_Body.setTabStopWidth(self.te_Body.fontMetrics().width(' ') * 4)

    def SetBodyText(self, body_data):
        self.te_Body.setText(str(body_data))

    def GetBodyText(self):
        return self.te_Body.toPlainText()

    def GetBody(self):
        body = {}
        try:
            body = json.loads(self.te_Body.toPlainText())
        except Exception as exception:
            print(exception)
        return body
