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

    def Run(self, step_num=0, debug_mode=False):
        self.step_num = step_num
        script_output = []
        try:
            while self.step_num < len(self.script_commands):
                idx = self.step_num
                if self.script_commands[idx] != "":
                    if debug_mode:
                        script_output.append(f"> {self.script_commands[idx]}")
                    if self.script_variables[idx] != "":
                        self.variables[self.script_variables[idx]] = eval(self.script_commands[idx])
                    else:
                        script_output.append(str(eval(self.script_commands[idx])))
                self.step_num += 1
                if debug_mode:
                    break
        except Exception as exception:
            script_output.append(str(exception))
        print(self.variables)
        return script_output

    def Stop(self):
        self.step_num = 0
