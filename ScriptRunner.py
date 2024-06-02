from RequestHandler import RequestTypes, RequestHandler

class ScriptRunner:
    def __init__(self):
        self.variables = {}

    def Run(self, compiled_script):
        print(compiled_script)
        variables = compiled_script.get("vars", [])
        commands = compiled_script.get("commands", [])
        loops = compiled_script.get("loops", [])
        try:
            for i in range(len(commands)):
                if variables[i] != "":
                    self.variables[variables[i]] = eval(commands[i])
                else:
                    eval(commands[i])
            print(self.variables)
        except Exception as exception:
            print(exception)
