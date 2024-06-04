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
        self.script_variables = compiled_script.get("vars", [])
        self.script_commands = compiled_script.get("commands", [])
        self.script_loops = compiled_script.get("loops", [])

    def Run(self, step_num=0, debug=False, verbose=False):
        self.step_num = step_num
        script_output = []
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
                if debug:
                    break
        except Exception as exception:
            script_output.append(str(f"Line {self.step_num}: {exception}"))
        print(self.variables)
        return script_output

    def SubsituteVariablesForCommand(self, command_str):
        command = command_str
        variables = ["{{" + variable + "}}" for variable in self.variables]
        for idx, v in enumerate(self.variables):
            if type(self.variables[v]) is str:
                command = command.replace(variables[idx], '"' + self.variables[v] + '"')
            else:
                command = command.replace(variables[idx], str(self.variables[v]))
        return command

    def Stop(self):
        self.step_num = 0
