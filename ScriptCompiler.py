from enum import IntEnum
import json

from RequestHandler import RequestTypes

class CompileStatus(IntEnum):
  OK = 0
  ERROR = 1

class ScriptCompiler:
  @staticmethod
  def Compile(command_list):
    compile_status = {
      "status": CompileStatus.OK,
      "error": "",
      "commands": []
    }
    for line_num, command in enumerate(command_list):
      var = ""
      cmd = ""

      if "=" in command:
        var = command[:command.find("=")].strip()
      if "REQ" in command:
        cmd_parts = command.split("REQ")
        if len(cmd_parts) == 2:
          arg = cmd_parts[1].strip()
          try:
            req_json = json.loads(arg)
            cmd = f"RequestHandler.Request(\"{req_json['url']}\", {RequestTypes(req_json['method'])}, form={req_json['data']}, body={req_json['json']})"
          except Exception as exception:
            compile_status["status"] = CompileStatus.ERROR,
            compile_status["error"] = f"Line {line_num} : {exception}"
            compile_status["commands"] = []
            break

      if var != "" and cmd == "":
        value = command[command.find("=") + 1:].strip()
        if value == "":
          compile_status["status"] = CompileStatus.ERROR,
          compile_status["error"] = f"Line {line_num} : No value defined for variable {var}"
          compile_status["commands"] = []
          break
        else:
          compile_status["commands"].append((var,value))
      else:
          compile_status["commands"].append((var,cmd))
    return compile_status
