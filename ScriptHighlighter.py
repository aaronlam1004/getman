from enum import Enum
from dataclasses import dataclass

from PyQt5 import QtWidgets, QtCore, uic, QtGui
from PyQt5.QtGui import QFont, QColor

SCRIPT_KEYWORDS = {
  "REQ": "#FF0000",
  "RES": "#FF0000",
  "ASSERT": "#0000FF"
}

@dataclass
class HighlightRule:
    pattern: QtCore.QRegExp
    formatting: QtGui.QTextCharFormat

class IHighlighter(QtGui.QSyntaxHighlighter):
  def __init__(self, parent=None):
    super(IHighlighter, self).__init__(parent)
    self.rules = []

  def AddRule(self, pattern, formatting):
    self.rules.append(HighlightRule(pattern, formatting))

class ScriptHighlighter(IHighlighter):
  def __init__(self, parent=None):
    super(ScriptHighlighter, self).__init__(parent)
    self.rules = []

    formatting = QtGui.QTextCharFormat()
    formatting.setFontWeight(QFont.Bold)
    formatting.setForeground(QColor("#000055"))
    self.AddRule(QtCore.QRegExp("(\"\w+\":)"), formatting)

    for keyword, color in SCRIPT_KEYWORDS.items():
      formatting = QtGui.QTextCharFormat()
      formatting.setFontWeight(QFont.Bold)
      formatting.setForeground(QColor(color))
      self.AddRule(QtCore.QRegExp(f"({str(keyword)})"), formatting)


  def highlightBlock(self, text):
    for rule in self.rules:
      expression = QtCore.QRegExp(rule.pattern)
      index = expression.indexIn(text)
      while index >= 0:
        length = expression.matchedLength()
        self.setFormat(index, length, rule.formatting)
        index = expression.indexIn(text, index + length)
