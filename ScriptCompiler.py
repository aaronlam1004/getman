from enum import Enum
import json

from RequestHandler import RequestTypes

class CompileStatus(Enum):
    OK    = 0
    ERROR = 1

class ScriptCompiler:
    VALID_COMMANDS = [
        "ASSERT",
        "SEND"
    ]

    @staticmethod
    def Compile(command_list):
        compile_status = {
            "status": CompileStatus.OK,
            "error": "",
            "commands": []
        }
        for line_num, command_str in enumerate(command_list):
            valid_command = False
            for command in ScriptCompiler.VALID_COMMANDS:
                if command in command_str:
                    valid_command = True
                    print(command_str)
            if not valid_command:
                print("Invalid command")
