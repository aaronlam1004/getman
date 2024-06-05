from enum import Enum
import json

from RequestHandler import RequestTypes

class CompileStatus(Enum):
    OK      = 0
    ERROR   = 1

class ScriptSyntax(Enum):
    ASSIGN  = ":="
    IF      = "IF"
    ELIF    = "ELIF"
    ELSE    = "ELSE"
    ENDIF   = "ENDIF"
    LOOP    = "LOOP"
    ENDLOOP = "ENDLOOP"

class ScriptCommand(Enum):
    ASSERT = "ASSERT"
    SEND   = "SEND"

class ScriptCompiler:
    @staticmethod
    def UpdateCompileStatus(compile_status, status, line_number, line, error_message=""):
        if status == CompileStatus.ERROR:
            compile_status["script"] = {
                "vars": [],
                "commands": [],
                "loops": []
            }
        compile_status["status"] = status
        compile_status["line_number"] = line_number
        compile_status["line"] = line
        compile_status["error"] = error_message

    @staticmethod
    def Compile(command_list):
        compile_status = {
            "status": CompileStatus.OK,
            "line_number": 0,
            "line": "",
            "error": "",
            "script": {
                "vars": [],
                "commands": [],
                "loops": []
            }
        }
        for line_num, command_str in enumerate(command_list):
            if not command_str.endswith(';'):
                ScriptCompiler.UpdateCompileStatus(compile_status, CompileStatus.ERROR, line_num + 1, command_str, "Missing ; to indicate end of line")
                break
            else:
                # Handle syntax
                processed_syntax, command_str, error_msg = ScriptCompiler.ProcessSyntax(compile_status, command_str)
                if error_msg != "":
                    ScriptCompiler.UpdateCompileStatus(compile_status, CompileStatus.ERROR, line_num + 1, command_str, error_msg)
                    break
                # Handle command
                processed_command, error_msg = ScriptCompiler.ProcessCommand(compile_status, command_str)
                if error_msg != "":
                    ScriptCompiler.UpdateCompileStatus(compile_status, CompileStatus.ERROR, line_num + 1, command_str, error_msg)
                    break
        return compile_status

    @staticmethod
    def ProcessSyntax(compile_status, command_str):
        for syntax in ScriptSyntax:
            if syntax.value in command_str:
                return ScriptCompiler.HandleSyntax(compile_status, syntax, command_str)
        compile_status["script"]["vars"].append("")
        compile_status["script"]["loops"].append(tuple())
        return False, command_str, ""

    @staticmethod
    def HandleSyntax(compile_status, syntax, command_str):
        if syntax == ScriptSyntax.ASSIGN:
            assignment = command_str.split(ScriptSyntax.ASSIGN.value)
            if len(assignment) != 2:
                return False, command_str, "Invalid assignment operation"
            else:
                var_name = assignment[0].lstrip().rstrip()
                if var_name.isnumeric():
                    return False, command_str, "Invalid assignment operation"
                else:
                    compile_status["script"]["vars"].append(var_name)
                    command_str = assignment[1].lstrip()
                    return True, command_str, ""
        compile_status["script"]["vars"].append("")
        compile_status["script"]["loops"].append(tuple())
        return False, command_str, ""


    @staticmethod
    def ProcessCommand(compile_status, command_str):
        for command in ScriptCommand:
            if command_str.startswith(command.name) and command_str.endswith(';'):
                command_str = command_str.rstrip(';')
                variables = compile_status["script"]["vars"]
                command_str = ScriptCompiler.EncodeVariablesToProcess(command_str, variables)
                command_call, error_msg = ScriptCompiler.GetCommand(command, command_str, variables)
                if command_call is not None:
                    compile_status["script"]["commands"].append(ScriptCompiler.DecodeVariablesForCommand(command_call, variables))
                    return True, ""
                else:
                    return False, error_msg
        command_str = command_str.rstrip(';')
        if not command_str.isnumeric() and command_str not in ["True", "False"]:
            compile_status["script"]["commands"].append(command_str)
        else:
            compile_status["script"]["commands"].append(command_str)
        return False, ""
    
    @staticmethod
    def EncodeVariablesToProcess(command_str, variables):
        command = command_str
        variable_str = ["{{" + variable + "}}" for variable in variables]
        for i in range(len(variable_str)):
            command = command.replace(variable_str[i], '"' + variable_str[i] + '"')
        return command

    @staticmethod
    def DecodeVariablesForCommand(command_str, variables):
        command = command_str
        variable_str = ["{{" + variable + "}}" for variable in variables]
        for i in range(len(variable_str)):
            command = command.replace('"' + variable_str[i] + '"', variable_str[i])
        return command

    @staticmethod
    def GetCommand(command, command_str, variables):
        if command == ScriptCommand.SEND:
            json_str = command_str.replace(command.name + ' ', '')
            try:
                req_json = json.loads(json_str)
                request_call = ScriptCompiler.GetRequestCall(req_json)
                return request_call, ""
            except Exception as exception:
                return None, str(exception)
        return None, "Cannot process command"

    @staticmethod
    def GetRequestCall(req_json):
        url = req_json["url"]
        request_type = '"' + req_json["method"] + '"'
        headers = req_json["headers"]
        body = req_json["json"]
        form = req_json["data"]
        return f"RequestHandler.Request(\"{url}\", RequestTypes({request_type}), headers={headers}, body={body}, form={form})"
