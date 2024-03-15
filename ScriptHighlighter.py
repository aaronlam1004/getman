from dataclasses import dataclass

from PyQt5 import QtWidgets, QtCore, uic, QtGui
from PyQt5.QtGui import QFont, QColor

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

class JSONHighlighter(IHighlighter):
  def __init__(self, parent=None):
    super(JSONHighlighter, self).__init__(parent)
    self.rules = []

    formatting = QtGui.QTextCharFormat()
    formatting.setFontWeight(QFont.Bold)
    formatting.setForeground(QColor("#000055"))
    self.AddRule(QtCore.QRegExp("(\'\w+\':)"), formatting)


  def highlightBlock(self, text):
    for rule in self.rules:
      expression = QtCore.QRegExp(rule.pattern)
      index = expression.indexIn(text)
      while index >= 0:
        length = expression.matchedLength()
        self.setFormat(index, length, rule.formatting)
        index = expression.indexIn(text, index + length)
