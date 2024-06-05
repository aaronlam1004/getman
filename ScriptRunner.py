from RequestHandler import RequestTypes, RequestHandler

class ScriptRunner:
    def __init__(self):
        self.step_num = 0
        self.variables = {}
        self.script_variables = []
        self.script_commands = []
        self.script_loops = []

    def Load(self, compiled_script):
        print(compiled_script)
        self.step_num = 0
        self.script_variables = compiled_script.get("vars", [])
        self.script_commands = compiled_script.get("commands", [])
        self.script_loops = compiled_script.get("loops", [])

    def GetVariables(self):
        return self.variables

    def Run(self, step=False, verbose=False):
        script_output = []
        command = ""
        try:
            while self.step_num < len(self.script_commands):
                command = self.SubsituteVariablesForCommand(self.script_commands[self.step_num])
                script_var = self.script_variables[self.step_num]
                if command != "":
                    cmd_str = "> "
                    result_str = ""
                    if script_var != "":
                        cmd_str += f"{script_var} = {command}"
                        self.variables[script_var] = eval(command)
                    else:
                        cmd_str += command
                        result_str = str(eval(command))
                    if verbose:
                        script_output.append(cmd_str)
                    if result_str != "":
                        script_output.append(result_str)
                self.step_num += 1
                if step:
                    break
        except Exception as exception:
            if verbose:
                script_output.append(f"> {command}")
            script_output.append(str(f"Line {self.step_num + 1}: {exception}"))
        print(self.variables)
        return script_output

    def SubsituteVariablesForCommand(self, command_str):
        command = command_str
        variables = ["{{" + variable + "}}" for variable in self.variables]
        for idx, v in enumerate(self.variables):
            command = command.replace('"' + variables[idx] + '"', f'f"{{{variables[idx]}}}"')
            command = command.replace(variables[idx], f"self.variables['{v}']")
        return command

    def Stop(self):
        self.step_num = 0
