from enum import Enum
from dataclasses import dataclass

from PyQt5 import QtWidgets, QtCore, uic, QtGui
from PyQt5.QtGui import QFont, QColor

from Highlighter import Highlighter

SCRIPT_KEYWORDS = {
  "REQ": "#FF0000",
  "RES": "#FF0000",
  "ASSERT": "#0000FF"
}

class ScriptHighlighter(Highlighter):
  def __init__(self, parent=None):
    super(ScriptHighlighter, self).__init__(parent)
    formatting = QtGui.QTextCharFormat()
    formatting.setFontWeight(QFont.Bold)
    formatting.setForeground(QColor("#000055"))
    self.AddRule(QtCore.QRegExp("(\"\w+\":)"), formatting)

    for keyword, color in SCRIPT_KEYWORDS.items():
      formatting = QtGui.QTextCharFormat()
      formatting.setFontWeight(QFont.Bold)
      formatting.setForeground(QColor(color))
      self.AddRule(QtCore.QRegExp(f"({str(keyword)})"), formatting)