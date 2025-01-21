from PyQt5 import QtWidgets, QtCore, uic, QtGui
from PyQt5.QtGui import QFont, QColor

from ui.highlighters.Highlighter import Highlighter

class JsonHighlighter(Highlighter):
  def __init__(self, parent=None):
    super(JsonHighlighter, self).__init__(parent)

    formatting = QtGui.QTextCharFormat()
    formatting.setFontWeight(QFont.Bold)
    formatting.setForeground(QColor("#005500"))
    self.AddRule(QtCore.QRegExp("(\".*\")"), formatting)

    formatting = QtGui.QTextCharFormat()
    formatting.setFontWeight(QFont.Bold)
    formatting.setForeground(QColor("#000055"))
    self.AddRule(QtCore.QRegExp("(\".*\":)"), formatting)

    formatting = QtGui.QTextCharFormat()
    formatting.setFontWeight(QFont.Bold)
    formatting.setForeground(QColor("#005500"))
    self.AddRule(QtCore.QRegExp("(\'.*\')"), formatting)

    formatting = QtGui.QTextCharFormat()
    formatting.setFontWeight(QFont.Bold)
    formatting.setForeground(QColor("#000055"))
    self.AddRule(QtCore.QRegExp("(\'.*\':)"), formatting)

    formatting = QtGui.QTextCharFormat()
    formatting.setFontWeight(QFont.Bold)
    formatting.setForeground(QColor("#550000"))
    self.AddRule(QtCore.QRegExp("(\d+)"), formatting)
