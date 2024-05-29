from RequestHandler import RequestTypes, RequestHandler

class ScriptRunner:
    def __init__(self):
        self.vars = {}

    def Run(self, commands):
        try:
            for var, command in commands:
                if var != "":
                    self.vars[var] = eval(command)
                    print(self.vars)
                else:
                    result = eval(command)
                    print(result)
        except Exception as exception:
            print(exception)
