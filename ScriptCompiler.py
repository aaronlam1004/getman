from enum import Enum
import json

from RequestHandler import RequestTypes

class CompileStatus(Enum):
    OK      = 0
    ERROR   = 1
    WARNING = 2

class ScriptCommand(Enum):
    ASSERT = 0
    SEND   = 1

class ScriptCompiler:    
    KEYWORDS = {
    }

    @staticmethod
    def Compile(command_list):
        compile_status = {
            "status": CompileStatus.OK,
            "line_number": 0,
            "line": "",
            "error": "",
            "commands": []
        }
        for line_num, command_str in enumerate(command_list):
            valid_command = False
            for command in ScriptCommand:
                if command_str.startswith(command.name):
                    valid_command = True
                    command_call, valid_syntax = ScriptCompiler.GetCommand(command, command_str)
                    if valid_syntax:
                        compile_status["commands"].append(command_call)
                    else:
                        ScriptCompiler.UpdateCompileStatus(compile_status, CompileStatus.ERROR, line_num, command_str, "Invalid syntax")
            if not valid_command:
                ScriptCompiler.UpdateCompileStatus(compile_status, CompileStatus.ERROR, line_num, command_str, "Not a valid command")
        return compile_status

    @staticmethod
    def UpdateCompileStatus(compile_status, status, line_number, line, error_message=""):
        if status == CompileStatus.ERROR:
            compile_status["commands"] = []
        compile_status["status"] = status
        compile_status["line_number"] = line_number
        compile_status["line"] = line
        compile_status["error"] = error_message

    @staticmethod
    def GetCommand(command, command_str):
        if command == ScriptCommand.SEND:
            json_str = command_str.replace(command.name + ' ', '')
            try:
                req_json = json.loads(json_str)
                request_call = ScriptCompiler.GetRequestCall(req_json)
                return request_call, True
            except:
                return None, False
        return None, False

    @staticmethod
    def GetRequestCall(req_json):
        url = req_json["url"]
        request_type = RequestTypes(req_json["method"])
        headers = req_json["headers"]
        body = req_json["json"]
        form = req_json["data"]
        return f"RequestHandler.Request({url}, {request_type}, headers={headers}, body={body}, form={form})"
