from enum import Enum
from dataclasses import dataclass

from PyQt5 import QtWidgets, QtCore, uic, QtGui
from PyQt5.QtGui import QFont, QColor

from JsonHighlighter import JsonHighlighter

class ScriptHighlighter(JsonHighlighter):
    def __init__(self, parent=None, keywords={}):
        super(ScriptHighlighter, self).__init__(parent)
        
        formatting = QtGui.QTextCharFormat()
        formatting.setFontWeight(QFont.Bold)
        formatting.setForeground(QColor("#FAAA16"))
        self.AddRule(QtCore.QRegExp("\{\{[\w\d]+\}\}"), formatting)

        for keyword, color in keywords.items():
            formatting = QtGui.QTextCharFormat()
            formatting.setFontWeight(QFont.Bold)
            formatting.setForeground(QColor(color))
            self.AddRule(QtCore.QRegExp(f"({str(keyword)})"), formatting)
