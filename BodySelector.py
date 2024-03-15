import sys
import os
import json

from PyQt5 import QtWidgets, QtCore, uic
from PyQt5.QtWidgets import QTableWidgetItem

class BodySelector(QtWidgets.QWidget):
  def __init__(self, parent = None):
    super(BodySelector, self).__init__(parent)
    uic.loadUi('ui/BodySelector.ui', self)
    self.ConnectActions()

  def LoadState(self, state_json):
    pass

  def ConnectActions(self):
    pass
