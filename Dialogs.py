from typing import List, Optional

from PyQt5.QtWidgets import QWidget, QMessageBox, QInputDialog 

def YesNoDialog(parent: QWidget, title: str, message: str) -> bool:
    answer = QMessageBox.question(parent, title, message, QMessageBox.Yes | QMessageBox.No)
    return answer == QMessageBox.Yes

def YesNoCancelDialog(parent: QWidget, title: str, message: str) -> Optional[bool]:
    answer = QMessageBox.question(parent, title, message, QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
    if answer == QMessageBox.Yes:
        return True
    elif answer == QMessageBox.No:
        return False
    else:
        return None # Cancel

def SelectWorkspaceDialog(parent: QWidget, workspaces: List[str]) -> Optional[str]:
    workspace, ok = QInputDialog.getItem(parent, "Workspace", "Select workspace:", workspaces, 0, False)
    if ok and workspace != "":
        return workspace
    return None
