from enum import Enum
from dataclasses import dataclass

from PyQt5 import QtWidgets, QtCore, uic, QtGui
from PyQt5.QtGui import QFont, QColor

from Highlighter import Highlighter

class ScriptHighlighter(Highlighter):
    def __init__(self, parent=None, keywords={}):
        super(ScriptHighlighter, self).__init__(parent)
        formatting = QtGui.QTextCharFormat()
        formatting.setFontWeight(QFont.Bold)
        formatting.setForeground(QColor("#000055"))
        self.AddRule(QtCore.QRegExp("(\"\w+\":)"), formatting)

        for keyword, color in keywords.items():
            formatting = QtGui.QTextCharFormat()
            formatting.setFontWeight(QFont.Bold)
            formatting.setForeground(QColor(color))
            self.AddRule(QtCore.QRegExp(f"({str(keyword)})"), formatting)
