import os
import sys

BASE_PATH = os.path.join(os.path.dirname(__file__), "..")
UI_PATH = os.path.join(BASE_PATH, "ui")

def GetUIPath(ui_file: str) -> str:
    return os.path.join(UI_PATH, ui_file)
