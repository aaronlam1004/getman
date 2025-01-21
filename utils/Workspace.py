import os
import glob
import configparser
import json
import shutil
from typing import Dict, Any

from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtCore import pyqtSignal

from utils.Paths import WORKSPACE_PATH, CONFIG_FILE

TEMP_WORKSPACE = ""

class Workspace:
    def __init__(self, workspace_updated: pyqtSignal):
        self.workspace_updated = workspace_updated

        os.makedirs(WORKSPACE_PATH, exist_ok=True)

        self.name = ""
        self.path= ""
        self.requests = []

    def Init(self) -> None:
        # Configuration file
        self.config = configparser.ConfigParser()
        if os.path.exists(CONFIG_FILE):
            self.config.read(CONFIG_FILE)
        else:
            self.config["workspace"] = { "name": "" }

        # Workspace
        if "workspace" in self.config and "name" in self.config["workspace"]:
            self.SetWorkspace(self.config["workspace"]["name"])
        else:
            self.SetWorkspace(TEMP_WORKSPACE)

    def UpdateConfig(self) -> None:
        if "workspace" not in self.config.sections() or "name" not in self.config["workspace"]:
            self.config["workspace"] = { "name": self.name }
        else:
            self.config["workspace"]["name"] = self.name
        with open(CONFIG_FILE, 'w') as config_file:
            self.config.write(config_file)

    def IsLoaded(self) -> bool:
        return self.name != "" and self.path != ""

    def SetWorkspace(self, workspace_name: str) -> None:
        self.path = ""
        self.requests = []
        self.name = workspace_name
        self.UpdateConfig()
        self.LoadWorkspace()

    def CreateWorkspace(self, workspace_name: str, overwrite: bool = False) -> bool:
        if not overwrite:
            for directory in os.listdir(WORKSPACE_PATH):
                if workspace_name in directory:
                    return False

        # Workspace
        workspace_dir = os.path.join(WORKSPACE_PATH, workspace_name)
        os.makedirs(workspace_dir, exist_ok=True)

        # Requests
        request_dir = os.path.join(WORKSPACE_PATH, workspace_name, "requests")
        if os.path.isdir(request_dir):
            shutil.rmtree(request_dir)

        # Copy if saving as new workspace
        if self.name != "":
            workspace_request_dir = os.path.join(self.path, "requests")
            if os.path.exists(self.path) and os.path.exists(workspace_request_dir):
                shutil.copytree(workspace_request_dir, request_dir)
            else:
                os.makedirs(request_dir, exist_ok=True)
        self.SetWorkspace(workspace_name)

        # Update config
        self.UpdateConfig()
        return True

    def LoadWorkspace(self) -> None:
        if self.name == "":
            self.path = ""
        else:
            self.path = os.path.join(WORKSPACE_PATH, self.name)
            if os.path.isdir(self.path):
                requests_path = os.path.join(self.path, "requests")
                os.makedirs(requests_path, exist_ok=True)
                self.requests = sorted([os.path.basename(req_json).split('.')[0] for req_json in glob.glob(f"{requests_path}/*.req.json")])
        if self.workspace_updated is not None:
            self.workspace_updated.emit()

    def GetWorkspaceRequestPath(self, request_name: str) -> str:
        return os.path.join(self.path, "requests", f"{request_name}.req.json")

    def SaveRequestInWorkspace(self, name: str, request_json: Dict[str, Any],
                               overwrite: bool = False) -> bool:
        if name != "":
            requests_path = os.path.join(self.path, "requests")
            if not overwrite:
                curr_requests = [os.path.basename(req_json).split('.')[0] for req_json in glob.glob(f"{requests_path}/*.req.json")]
                if name in curr_requests:
                    return False
            with open(f"{requests_path}/{name}.req.json", 'w') as json_file:
                json.dump(request_json, json_file)
            return True
        return False

    def DeleteRequestFromWorkspace(self, request_name: str):
        if request_name != "":
            requests_path = os.path.join(self.path, "requests")
            request = os.path.join(requests_path, f"{request_name}.req.json")
            if os.path.exists(request):
                os.remove(request)

    def CloseWorkspace(self):
        self.SetWorkspace(TEMP_WORKSPACE)
        self.LoadWorkspace()
