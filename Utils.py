import os
import sys

def GetUiPath(parent_file, ui_file):
    return os.path.join(os.path.dirname(parent_file), ui_file)
